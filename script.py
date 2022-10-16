from wikibrain import wikimedia_link_issue_reporter
from wikibrain import wikipedia_knowledge
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import config
import obtain_from_overpass
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

        # magnificent speedup
        cursor.execute("""CREATE INDEX idx_osm_data_area_identifier ON osm_data (area_identifier);""")
        cursor.execute("""CREATE INDEX idx_osm_data_id_type ON osm_data (id, type);""")
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
        print()
        print()
        print(processed_entries, "/", total_entry_count)
        processed_entries += 1
        internal_region_name = entry['internal_region_name']
        print(internal_region_name)
        if "hidden" in entry:
            if entry["hidden"] == True:
                continue
        process_given_area(cursor, entry)
        connection.commit()
        generate_webpage_with_error_output.write_index_and_merged_entries(cursor) # update after each run
    connection.close()
    commit_changes_in_report_directory()


def process_given_area(cursor, entry):
    identifier_of_region_for_overpass_query=entry['identifier']
    timestamp_when_file_was_downloaded = obtain_from_overpass.download_entry(cursor, entry['internal_region_name'], identifier_of_region_for_overpass_query)

    # properly update by fetching new info about entries which were 
    # - not present in file so with outdated timestamps
    # - entries currently are carrying reports
    # (as wikipedia tag could be simply removed!)
    #
    # if we do no worry about archival data in this case it is fine to simply delete such data
    # as tag without wikidata and wikipedia tags will not be reported in wikipedia report tool
    # TODO: verify this assumption!
    cursor.execute("""SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint
    FROM osm_data
    WHERE
    area_identifier = :identifier
    AND
    download_timestamp < :timestamp_when_file_was_downloaded
    AND
    validator_complaint IS NOT NULL
    AND
    validator_complaint <> ""
    """, {"identifier": entry['internal_region_name'], "timestamp_when_file_was_downloaded": timestamp_when_file_was_downloaded})
    returned = cursor.fetchall()
    for entry in returned:
        rowid, object_type, object_id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint = entry
        print(object_type, object_id, "is outdated, not in the report so its entry is being deleted:", tags)
        cursor.execute("DELETE FROM osm_data WHERE type = :type and id = :id", {'type': object_type, 'id': object_id})

    update_validator_reports_for_given_area(cursor, entry['internal_region_name'], entry.get('language_code', None))
    generate_website_file_for_given_area(cursor, entry)

def update_validator_reports_for_given_area(cursor, internal_region_name, language_code):
    issue_detector = get_wikimedia_link_issue_reporter_object(language_code)
    # will recheck reported errors
    # will not recheck entries that previously were free of errors
    cursor.execute('SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NULL', {"identifier": internal_region_name})
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
        languages_ordered_by_preference=[language_code],
        additional_debug=False,
        allow_requesting_edits_outside_osm=False,
        allow_false_positives=False
        )

def generate_website_file_for_given_area(cursor, entry):
    reports = reports_for_given_area(cursor, entry['internal_region_name'])
    website_main_title_part = entry['website_main_title_part']
    generate_webpage_with_error_output.generate_output_for_given_area(website_main_title_part, reports)

def reports_for_given_area(cursor, internal_region_name):
    cursor.execute("SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NOT NULL AND validator_complaint <> ''", {"identifier": internal_region_name})
    returned = cursor.fetchall()
    reports = []
    for entry in returned:
        rowid, object_type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint = entry
        tags = json.loads(tags)
        validator_complaint = json.loads(validator_complaint)
        reports.append(validator_complaint)
    return reports

def commit_changes_in_report_directory():
    current_working_directory = os.getcwd()
    os.chdir(config.get_report_directory())
    os.system('git add index.html')
    os.system('git commit -m "automatic update of index.html"')
    os.system('git add --all')
    os.system('git commit -m "automatic update of report files"')
    os.chdir(current_working_directory)

main()