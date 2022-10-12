from wikibrain import wikimedia_link_issue_reporter
from wikibrain import wikipedia_knowledge
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import config
import download
import load_osm_file
import json
import sqlite3
import generate_webpage_with_error_output
import os

def existing_tables(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_listing = cursor.fetchall()
    returned = []
    for entry in table_listing:
        returned.append(entry[0])
    return returned

def create_table_if_needed(cursor):
    if "osm_data" in existing_tables(cursor):
        print("osm_data table exists already, delete file with database to recreate")
    else:
        # validator_complaint needs to hold
        # - not checked
        # - checked, no problem found
        # - error data
        #
        # right now for "checked, no error" I plan to use empty string but I am not too happy
        cursor.execute('''CREATE TABLE osm_data
                    (type text, id number, lat float, lon float, tags text, area_identifier text, download_timestamp integer, validator_complaint text)''')
    if "osm_data_update_log" in existing_tables(cursor):
        print("osm_data_update_log table exists already, delete file with database to recreate")
    else:
        # register when data was downloaded so update can be done without downloading
        # and processing the entire dataset
        #
        # instead just entries that were changed since then
        # - and carry *(wikipedia|wikidata)* tags
        # - that previously had problem reported about them
        # should be downloaded
        cursor.execute('''CREATE TABLE osm_data_update_log
                    (area_identifier text, filename text, download_type text, download_timestamp integer)''')

def main():
    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    create_table_if_needed(cursor)
    connection.commit()
    wikimedia_connection.set_cache_location(config.get_wikimedia_connection_cache_location())

    total_entry_count = len(config.get_entries_to_process())
    processed_entries = 0
    for entry in config.get_entries_to_process():
        print(processed_entries, "/", total_entry_count)
        processed_entries += 1
        internal_region_name = entry['internal_region_name']
        print(internal_region_name)
        if "hidden" in entry:
            if entry["hidden"] == True:
                continue
        process_given_area(connection, entry)
    generate_webpage_with_error_output.write_index(cursor)
    connection.close()
    commit_changes_in_report_directory()


def process_given_area(connection, entry):
    # TODO: properly update by fetching new info about entries which were modified and entries currently carrying reports (as wikipedia tag could be simply removed!)
    merged_output_file = entry.get('merged_output_file', None) # TODO! support this!
    identifier_of_region_for_overpass_query=entry['identifier']
    downloaded_filepath = download.download_entry(entry['internal_region_name'], identifier_of_region_for_overpass_query)
    timestamp_when_file_was_downloaded = "1970" # TODO fix fake timestamp
    load_osm_file.load_osm_file(downloaded_filepath, entry['internal_region_name'], timestamp_when_file_was_downloaded)

    cursor = connection.cursor()
    update_validator_reports_for_given_area(cursor, entry['internal_region_name'], entry.get('language_code', None))
    connection.commit()
    generate_website_file_for_given_area(cursor, entry)

def update_validator_reports_for_given_area(cursor, internal_region_name, language_code):
    issue_detector = get_wikimedia_link_issue_reporter_object(language_code)
    cursor.execute("SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint FROM osm_data WHERE area_identifier = :identifier", {"identifier": internal_region_name})
    returned = cursor.fetchall()
    for entry in returned:
        rowid, object_type, object_id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint = entry
        object_description = object_type + "/" + str(object_id)
        tags = json.loads(tags)
        location = (lat, lon)
        reported = issue_detector.get_the_most_important_problem_generic(tags, location, object_type, object_description)
        if reported != None:
            link = "https://openstreetmap.org/" + object_type + "/" + str(object_id)
            data = reported.data()
            data['osm_object_url'] = link # TODO eliminate need for this
            data['tags'] = tags # TODO eliminate need for this
            data = json.dumps(data)
            cursor.execute("UPDATE osm_data SET validator_complaint = :validator_complaint WHERE rowid = :rowid", {"validator_complaint": data, "rowid": rowid})
        else:
            cursor.execute("UPDATE osm_data SET validator_complaint = :validator_complaint WHERE rowid = :rowid", {"validator_complaint": "", "rowid": rowid})

def get_wikimedia_link_issue_reporter_object(language_code):
    return wikimedia_link_issue_reporter.WikimediaLinkIssueDetector(
        forced_refresh=False,
        expected_language_code=language_code, # may be None
        languages_ordered_by_preference=[],
        additional_debug=False,
        allow_requesting_edits_outside_osm=False,
        allow_false_positives=False
        )

def generate_website_file_for_given_area(cursor, entry):
    website_main_title_part = entry['website_main_title_part']
    cursor.execute("SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NOT NULL AND validator_complaint <> ''", {"identifier": entry['internal_region_name']})
    returned = cursor.fetchall()
    reports = []
    for entry in returned:
        rowid, object_type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint = entry
        tags = json.loads(tags)
        validator_complaint = json.loads(validator_complaint)
        reports.append(validator_complaint)
    generate_webpage_with_error_output.generate_output_for_given_area(website_main_title_part, reports)

def commit_changes_in_report_directory():
    current_working_directory = os.getcwd()
    os.chdir(config.get_report_directory())
    os.system('git add index.html')
    os.system('git commit -m "automatic update of index.html"')
    os.system('git add --all')
    os.system('git commit -m "automatic update of report files"')
    os.chdir(current_working_directory)

main()