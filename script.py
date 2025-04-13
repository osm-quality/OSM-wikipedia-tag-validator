import string
import array
from sqlite3 import Cursor
from dotenv import load_dotenv
from wikibrain import wikimedia_link_issue_reporter
from wikibrain import wikipedia_knowledge
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import config
import obtain_from_overpass
import database
import json
import sqlite3
import generate_webpage_with_error_output
import os
import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer
import time
import osm_editor_bot_for_approved_tasks
import random
import datetime


def main():
    load_dotenv()
    folder = "/".join(config.database_filepath().split("/")[0:-1])
    if not os.path.isdir(folder):
        os.mkdir(folder)
    if not os.path.isdir(config.get_report_directory()):
        os.mkdir(config.get_report_directory())
    # maybe check is it ext4?
    # https://stackoverflow.com/questions/25283882/determining-the-filesystem-type-from-a-path-in-python
    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    database.create_table_if_needed(cursor)
    connection.commit()
    connection.close()

    osm_editor_bot_for_approved_tasks.main()
    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    update_validator_database_and_reports()
    update_oldest_with_no_reported_issues(cursor)
    check_database_integrity(cursor)
    connection.commit()
    connection.close()
    check_for_malformed_definitions_of_entries()


def update_oldest_with_no_reported_issues(cursor: Cursor):
    outdated_objects = oldest_entries_with_no_reported_issues(cursor)
    # what about ones not matching any still processed area?
    for outdated in outdated_objects:
        rowid, object_type, object_id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id = outdated
        print("https://www.openstreetmap.org/" + object_type + "/" + str(object_id), area_identifier, "timestamp:",
              download_timestamp)
    ignored_problems = []
    update_outdated_elements_and_reset_reports(cursor, outdated_objects, ignored_problems)


def oldest_entries_with_no_reported_issues(cursor: Cursor):
    # - entries currently are carrying reports and with outdated timestamps
    # (as wikipedia tag could be simply removed!)
    #
    # - entries without current wikidata/wikipedia tags may be outdated AND without active reports are safe
    #   - will not generate valid report
    #   - will not be false positives

    cursor.execute("""SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id
    FROM osm_data
    WHERE
    validator_complaint
    OR
    validator_complaint == ""
    ORDER BY
    download_timestamp, type, id
    ASC
    LIMIT 10
    """, {})
    return cursor.fetchall()


def check_database_integrity(cursor: Cursor):
    if random.random() < 0.1:
        print("started database integrity check (expensive, not always done - there is some random chance)")
        cursor.execute("PRAGMA integrity_check;")
        info = cursor.fetchall()
        if info != [('ok',)]:
            raise
        print("completed database integrity check")
    else:
        print("skipping expensive database integrity check (random chance)")


def update_validator_database_and_reports():
    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    connection.commit()

    # cleanup after manual tag deactivation
    cursor.execute("""UPDATE osm_data
    SET
    validator_complaint = NULL
    WHERE
    validator_complaint IS NOT NULL
    AND
    error_id IS NULL
    """)

    for entry in config.get_entries_to_process():
        if "hidden" in entry:
            if entry["hidden"] == True:
                continue
        generate_webpage_with_error_output.generate_website_file_for_given_area(cursor, entry)
    generate_webpage_with_error_output.write_index_and_merged_entries(cursor)
    commit_and_publish_changes_in_report_directory(cursor)

    wikimedia_connection.set_cache_location(config.get_wikimedia_connection_cache_location())

    entries_with_age = []
    for entry in config.get_entries_to_process():
        internal_region_name = entry['internal_region_name']
        timestamp = database.get_data_download_timestamp(cursor, internal_region_name)
        entries_with_age.append({"data": entry, "data_timestamp": timestamp})
    current_timestamp = int(time.time())
    entries_with_age = sorted(entries_with_age,
                              key=lambda entry: -(current_timestamp - entry["data_timestamp"]) * entry["data"].get(
                                  "priority_multiplier", 1))

    total_entry_count = len(config.get_entries_to_process())
    processed_entries = 0
    print()
    print()
    print()
    for selected_processing_entry in entries_with_age[::-1]:
        entry = selected_processing_entry['data']
        score = (current_timestamp - selected_processing_entry["data_timestamp"]) * entry.get("priority_multiplier", 1)
        k = str(int((score + 500) / 1000))
        # print(entry['internal_region_name'], entry.get("priority_multiplier", 1), k+"k")

    for selected_processing_entry in entries_with_age:
        if is_night():
            connection.close()
            while is_night():
                print("pausing for night, sleeping")
                time.sleep(60)
            connection = sqlite3.connect(config.database_filepath())
            cursor = connection.cursor()
        print()
        print()
        print(processed_entries, "/", total_entry_count)
        processed_entries += 1
        entry = selected_processing_entry['data']
        internal_region_name = entry['internal_region_name']
        print(internal_region_name)
        if "hidden" in entry:
            if entry["hidden"] == True:
                continue
        process_given_area(cursor, entry)
        connection.commit()
        # generate_webpage_with_error_output.write_index_and_merged_entries(cursor) # update after each run
    commit_and_publish_changes_in_report_directory(
        cursor)  # note that it is called not only here! But also at start of the function
    connection.close()


def is_night():
    return datetime.datetime.now().hour >= 19 or datetime.datetime.now().hour < 4


def check_for_malformed_definitions_of_entries():
    for entry in config.get_entries_to_process():
        if "/" in entry['internal_region_name']:
            raise Exception("/ in " + entry['internal_region_name'])
        if "/" in entry['website_main_title_part']:
            raise Exception("/ in " + entry['website_main_title_part'])


def process_given_area(cursor: Cursor, entry: array):
    ignored_problems = entry.get('ignored_problems', [])
    identifier_of_region_for_overpass_query = entry['identifier']
    internal_region_name = entry['internal_region_name']
    timestamp_when_file_was_downloaded = obtain_from_overpass.download_entry(cursor, internal_region_name,
                                                                             identifier_of_region_for_overpass_query)
    outdated_objects = outdated_entries_in_area_that_must_be_updated(cursor, internal_region_name,
                                                                     timestamp_when_file_was_downloaded)
    update_outdated_elements_and_reset_reports(cursor, outdated_objects, ignored_problems)
    update_validator_reports_for_given_area(cursor, internal_region_name, entry.get('language_code', None),
                                            ignored_problems)
    generate_webpage_with_error_output.generate_website_file_for_given_area(cursor, entry)


def update_outdated_elements_and_reset_reports(cursor: Cursor, outdated_objects: array, ignored_problems: array):
    # properly update by fetching new info about entries which also must be updated and could be missed
    for outdated in outdated_objects:
        rowid, object_type, object_id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id = outdated
        if validator_complaint != None and validator_complaint != "":
            validator_complaint = json.loads(validator_complaint)
            if validator_complaint['error_id'] in ignored_problems:
                continue
            else:
                print(validator_complaint['error_id'], "IS NOT AMONG", ignored_problems)
        data = osm_bot_abstraction_layer.get_data(object_id, object_type)
        timestamp = int(time.time())
        # print(json.dumps(returned, default=str, indent=3))
        new_tags = "was deleted"
        cursor.execute("""
        DELETE FROM osm_data
        WHERE
        type = :type AND id = :id
        """, {"type": object_type, "id": object_id})
        print("deleting", object_type, object_id)
        if data != None:  # None means that it was deleted
            new_tags = json.dumps(data["tag"], indent=3)  # pretty format also in database for easier debugging
            new_lat = lat
            new_lon = lon
            if object_type == "node":
                new_lat = data["lat"]
                new_lon = data["lon"]
                # what about ways and relations?
            # print(data)
            cursor.execute(
                "INSERT INTO osm_data VALUES (:type, :id, :lat, :lon, :tags, :area_identifier, :download_timestamp, :validator_complaint, :error_id)",
                {'type': object_type, 'id': object_id, 'lat': new_lat, 'lon': new_lon, "tags": new_tags,
                 "area_identifier": area_identifier, "download_timestamp": timestamp, "validator_complaint": None,
                 'error_id': None})
        complaint = "<no reported error>"
        if validator_complaint != None and validator_complaint != "":
            complaint = validator_complaint['error_id']
        print(object_type, object_id, "is outdated, not in the report so its entry needs to be updated for", complaint,
              "in", area_identifier)


def outdated_entries_in_area_that_must_be_updated(
        cursor: Cursor,
        internal_region_name: string,
        timestamp_when_file_was_downloaded: int
):
    # - entries currently are carrying reports and with outdated timestamps
    # (as wikipedia tag could be simply removed!)
    #
    # - entries without current wikidata/wikipedia tags may be outdated AND without active reports are safe
    #   - will not generate valid report
    #   - will not be false positives

    cursor.execute("""SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id
    FROM osm_data
    WHERE
    area_identifier = :identifier
    AND
    download_timestamp < :timestamp_when_file_was_downloaded
    AND
    validator_complaint IS NOT NULL
    AND
    validator_complaint <> ""
    """, {"identifier": internal_region_name, "timestamp_when_file_was_downloaded": timestamp_when_file_was_downloaded})
    return cursor.fetchall()


def update_validator_reports_for_given_area(
        cursor: Cursor,
        internal_region_name: string,
        language_code: string,
        ignored_problems: array
):
    detect_problems_using_cache_for_wikimedia_data(cursor, internal_region_name, language_code)
    print("SKIPPING CACHE REFRESH OF WIKIDATA DATA")  # TODO reestablish it in a proper way
    # print("NOW CHECKING WHAT WAS REPORTED WITHOUT USING CACHE!")
    # verify_that_problem_exist_without_using_cache_for_wikimedia_data(cursor, internal_region_name, language_code, ignored_problems)


def detect_problems_using_cache_for_wikimedia_data(cursor: Cursor, internal_region_name: string, language_code: string):
    issue_detector = get_wikimedia_link_issue_reporter_object(language_code)
    # will recheck reported errors
    # will not recheck entries that previously were free of errors
    cursor.execute(
        'SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NULL',
        {"identifier": internal_region_name})
    entries = cursor.fetchall()
    update_problem_for_all_this_entries(issue_detector, cursor, entries, [])


def verify_that_problem_exist_without_using_cache_for_wikimedia_data(
        cursor: Cursor,
        internal_region_name: string,
        language_code: string,
        ignored_problems: array
):
    issue_detector_refreshing_cache = get_wikimedia_link_issue_reporter_object(language_code, forced_refresh=True)
    # recheck reported with request to fetch cache
    # done separately to avoid refetching over and over again where everything is fine
    # (say, tags on a road/river)
    cursor.execute(
        'SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NOT NULL AND validator_complaint <> ""',
        {"identifier": internal_region_name})
    entries = cursor.fetchall()
    update_problem_for_all_this_entries(issue_detector_refreshing_cache, cursor, entries, ignored_problems)


def update_problem_for_all_this_entries(
        issue_detector: array,
        cursor: Cursor,
        entries: array,
        ignored_problems: array
):
    for entry in entries:
        rowid, object_type, object_id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id = entry
        tags = json.loads(tags)
        location = (lat, lon)
        object_description = object_type + "/" + str(object_id)
        if validator_complaint != None:
            if len(ignored_problems) > 0:
                validator_complaint = json.loads(validator_complaint)
                if validator_complaint['error_id'] in ignored_problems:
                    continue
        update_problem_for_entry(issue_detector, cursor, tags, location, object_type, object_id, object_description,
                                 rowid)


def update_problem_for_entry(
        issue_detector: array,
        cursor: Cursor,
        tags: object,
        location: string,
        object_type: string,
        object_id: int,
        object_description: string,
        rowid: int
):
    object_description = object_type + "/" + str(object_id)
    reported = issue_detector.get_the_most_important_problem_generic(tags, location, object_type, object_description)
    if reported is not None:
        link = "https://openstreetmap.org/" + object_type + "/" + str(object_id)
        data = reported.data()
        data['osm_object_url'] = link  # TODO eliminate need for this
        data['tags'] = tags  # TODO eliminate need for this
        error_id = data['error_id']
        data = json.dumps(data)
        cursor.execute("""UPDATE osm_data 
            SET validator_complaint = :validator_complaint,
                error_id = :error_id
            WHERE rowid = :rowid""",
                       {"validator_complaint": data, "error_id": error_id, "rowid": rowid})
    else:
        cursor.execute("""UPDATE osm_data
            SET validator_complaint = :validator_complaint,
                error_id = :error_id
            WHERE rowid = :rowid""",
                       {"validator_complaint": "", "error_id": "", "rowid": rowid})


def get_wikimedia_link_issue_reporter_object(language_code: string, forced_refresh: bool = False):
    return wikimedia_link_issue_reporter.WikimediaLinkIssueDetector(
        forced_refresh=forced_refresh,
        expected_language_code=language_code,  # may be None
        languages_ordered_by_preference=[language_code],
        additional_debug=False,
        allow_requesting_edits_outside_osm=False,
        allow_false_positives=False
    )


def commit_and_publish_changes_in_report_directory(cursor: Cursor):
    missing = 0
    for entry in config.get_entries_to_process():
        if database.get_data_download_timestamp(cursor, entry['internal_region_name']) == 0:
            missing += 1
    if missing > 0:
        print(missing, "entries miss data altogether")
        return
    current_working_directory = os.getcwd()
    os.chdir(config.get_report_directory())
    os.system('git add index.html')
    os.system('git commit -m "automatic update of index.html"')
    os.system('git add --all')
    os.system('git commit -m "automatic update of report files"')
    os.system('git push')
    os.chdir(current_working_directory)


if __name__ == '__main__':
    main()
