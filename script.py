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
                    (type text, id number, lat float, lon float, tags text, area_identifier text, osm_data_updated date, validator_complaint text)''')


def main():
    issue_detector = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector(
        forced_refresh=False,
        expected_language_code=None,
        languages_ordered_by_preference=[],
        additional_debug=False,
        allow_requesting_edits_outside_osm=False,
        allow_false_positives=False
        )

    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    create_table_if_needed(cursor)
    wikimedia_connection.set_cache_location(config.get_wikimedia_connection_cache_location())

    for entry in config.get_entries_to_process():
        internal_region_name = entry['internal_region_name']
        print(internal_region_name)
        if "hidden" in entry:
            if entry["hidden"] == True:
                continue
        website_main_title_part = entry['website_main_title_part']
        merged_output_file = entry.get('merged_output_file', None)
        language_code = entry.get('language_code', None)
        identifier_of_region_for_overpass_query=entry['identifier']
        downloaded_filepath = download.download_entry(internal_region_name, identifier_of_region_for_overpass_query)
        load_osm_file.load_osm_file(downloaded_filepath, internal_region_name)

        cursor = connection.cursor()
        cursor.execute("SELECT rowid, type, id, lat, lon, tags, area_identifier, osm_data_updated, validator_complaint FROM osm_data WHERE area_identifier = :identifier", {"identifier": internal_region_name})
        returned = cursor.fetchall()
        for entry in returned:
            rowid, object_type, object_id, lat, lon, tags, area_identifier, osm_data_updated, validator_complaint = entry
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
        connection.commit()

        cursor.execute("SELECT rowid, type, id, lat, lon, tags, area_identifier, osm_data_updated, validator_complaint FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NOT NULL AND validator_complaint <> ''", {"identifier": internal_region_name})
        returned = cursor.fetchall()
        reports = []
        for entry in returned:
            rowid, object_type, id, lat, lon, tags, area_identifier, osm_data_updated, validator_complaint = entry
            tags = json.loads(tags)
            validator_complaint = json.loads(validator_complaint)
            reports.append(validator_complaint)
        generate_webpage_with_error_output.generate_output_for_given_area(website_main_title_part, reports)
    generate_webpage_with_error_output.write_index(cursor)
    connection.close()
    commit_changes_in_report_directory()

def commit_changes_in_report_directory():
    current_working_directory = os.getcwd()
    os.chdir(config.get_report_directory())
    os.system('git add index.html')
    os.system('git commit -m "automatic update of index.html"')
    os.system('git add --all')
    os.system('git commit -m "automatic update of report files"')
    os.chdir(current_working_directory)

main()