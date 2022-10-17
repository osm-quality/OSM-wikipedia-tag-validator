import config
from osm_bot_abstraction_layer.overpass_downloader import download_overpass_query
from osm_bot_abstraction_layer import overpass_query_maker
import pathlib
import shutil
import time
import sqlite3
import load_osm_file
from datetime import datetime
import osm_bot_abstraction_layer
import os

def filepath_to_downloaded_osm_data(name, suffix):
  filename = name
  filename += suffix + ".osm"
  return config.downloaded_osm_data_location() + "/" + filename

def timeout():
  return 2550

def get_data_timestamp(cursor, internal_region_name):
    downloaded_filepath = filepath_to_downloaded_osm_data(internal_region_name, "_unprocessed") # load location from database instead, maybe? TODO
    if pathlib.Path(downloaded_filepath).is_file():
        print("full data file is downloaded already")
        cursor.execute("SELECT download_timestamp FROM osm_data_update_log WHERE area_identifier = :area_identifier ORDER BY download_timestamp DESC LIMIT 1", {"area_identifier": internal_region_name})
        returned = cursor.fetchall()
        if len(returned) == 0:
            return 0
        else:
            return returned[0][0]
    return 0

def download_entry(cursor, internal_region_name, identifier_data_for_overpass):
    downloaded_filepath = filepath_to_downloaded_osm_data(internal_region_name, "_unprocessed") # load location from database instead, maybe? TODO
    work_filepath = filepath_to_downloaded_osm_data(internal_region_name, "_download_in_progress")
    if pathlib.Path(downloaded_filepath).is_file():
        print("full data file is downloaded already")
        latest_download_timestamp = get_data_timestamp(cursor, internal_region_name)
        if latest_download_timestamp == 0:
            print("it is not recorded when this data was downloaded! Throwing it away and fetching new.")
            os.remove(downloaded_filepath)
            # there could be old entries which are no longer valid and not present anymore in fetched data
            # because elements are deleted or without wikidata/wikipedia tags
            # so lets delete all of them
            cursor.execute("""DELETE FROM osm_data WHERE area_identifier = :identifier""", {"identifier": internal_region_name})
            return download_entry(cursor, internal_region_name, identifier_data_for_overpass)
        print("area_identifier, filename, download_type, download_timestamp")
        current_timestamp = int(time.time())
        age_of_data_in_seconds = current_timestamp - latest_download_timestamp
        age_of_data_in_hours = age_of_data_in_seconds/60/60
        print("age_of_data_in_seconds", age_of_data_in_seconds, "age_of_data_in_hours", int(age_of_data_in_hours + 0.5))
        if age_of_data_in_hours < 24:
            print("not old enough, this data is fine")
            return latest_download_timestamp
        print("at this point update should be run")
        print("https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_API_by_Example#Users_and_old_data")
        print("osm_bot_abstraction_layer.datetime_to_overpass_data_format")
        dt_object = datetime.fromtimestamp(latest_download_timestamp)
        timestamp_formatted = overpass_query_maker.datetime_to_overpass_data_format(dt_object)
        area_name_in_query = "searchArea"
        area_finder_string = area_finder(identifier_data_for_overpass, area_name_in_query)
        query = download_update_query_text(area_finder_string, area_name_in_query, latest_download_timestamp)
        timestamp = int(time.time())
        download_overpass_query(query, work_filepath, user_agent=config.user_agent())
        downloaded_filepath = filepath_to_downloaded_osm_data(internal_region_name, "_update_" + timestamp_formatted)
        shutil.move(work_filepath, downloaded_filepath) # this helps in cases where download was interupted and left empty file behind
        load_osm_file.load_osm_file(cursor, downloaded_filepath, internal_region_name, timestamp)
        # done AFTER data was safely loaded, committed together
        # this way we avoid problems with data downloaded and only partially loaded in database
        cursor.execute("INSERT INTO osm_data_update_log VALUES (:area_identifier, :filename, :download_type, :download_timestamp)", {"area_identifier": internal_region_name, "filename": downloaded_filepath, "download_type": "update_since_previous_download", "download_timestamp": timestamp})
        print("sleeping extra time to prevent inevitable quota exhaustion")
        time.sleep(60)
        return timestamp
    else:
        timestamp = int(time.time())
        area_name_in_query = "searchArea"
        area_finder_string = area_finder(identifier_data_for_overpass, area_name_in_query)
        query = download_query_text(area_finder_string, area_name_in_query)
        download_overpass_query(query, work_filepath, user_agent=config.user_agent())
        shutil.move(work_filepath, downloaded_filepath) # this helps in cases where download was interupted and left empty file behind

        load_osm_file.load_osm_file(cursor, downloaded_filepath, internal_region_name, timestamp)

        # done AFTER data was safely loaded, committed together
        # this way we avoid problems with data downloaded and only partially loaded in database
        cursor.execute("INSERT INTO osm_data_update_log VALUES (:area_identifier, :filename, :download_type, :download_timestamp)", {"area_identifier": internal_region_name, "filename": downloaded_filepath, "download_type": "initial_full_data", "download_timestamp": timestamp})
        print("sleeping extra time to prevent inevitable quota exhaustion")
        time.sleep(60)
    return timestamp

def area_finder(identifier_tag_dictionary, name_of_area):
    for key in identifier_tag_dictionary.keys():
        if "'" in key:
            raise NotImplementedError("escaping not implemented for ' character")
        if "'" in identifier_tag_dictionary[key]:
            raise NotImplementedError("escaping not implemented for ' character")
    if len(identifier_tag_dictionary) == 0:
        raise Exception("unexpectedly empty")
    returned = "area"
    for key in identifier_tag_dictionary.keys():
        value = identifier_tag_dictionary[key]
        returned += "['" + key + "'='" + value + "']"
    returned += "->." + name_of_area + ";\n"
    return returned

def download_update_query_text(area_finder_string, area_name, timestamp):
    dt_object = datetime.fromtimestamp(timestamp)
    timestamp_formatted = overpass_query_maker.datetime_to_overpass_data_format(dt_object)
    area_identifier = 'area.' + area_name

    query = "[timeout:" + str(timeout()) + "];\n"
    query += area_finder_string 
    query += "(\n"
    query += 'nwr[~"wikipedia.*"~".*"](' + area_identifier+ ')(newer:"' + timestamp_formatted + '");\n'
    query += ');\n'
    query += "out center;"
    return query

def download_query_text(area_finder_string, area_name):
    area_identifier = 'area.' + area_name

    query = "[timeout:" + str(timeout()) + "];\n"
    query += area_finder_string 
    query += "(\n"
    query += 'nwr[~"wikipedia.*"~".*"](' + area_identifier+ ");\n"
    query += ');\n'
    query += "out center;"
    return query
