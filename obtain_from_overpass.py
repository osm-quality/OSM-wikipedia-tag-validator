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

def download_entry(internal_region_name, identifier_data_for_overpass):
    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    downloaded_filepath = filepath_to_downloaded_osm_data(internal_region_name, "_unprocessed")
    work_filepath = filepath_to_downloaded_osm_data(internal_region_name, "_download_in_progress")
    if pathlib.Path(downloaded_filepath).is_file(): # load location from database instead, maybe? TODO
        print("full data file is downloaded already")
        cursor.execute("SELECT area_identifier, filename, download_type, download_timestamp FROM osm_data_update_log WHERE area_identifier = :area_identifier ORDER BY download_timestamp", {"area_identifier": internal_region_name})
        returned = cursor.fetchall()
        if len(returned) == 0:
            print("it is not recorded when this data was downloaded! Throwing it away and fetching new.")
            os.remove(downloaded_filepath)
            return download_entry(internal_region_name, identifier_data_for_overpass)
        print("area_identifier, filename, download_type, download_timestamp")
        latest_download_timestamp = None
        for entry in returned:
            print(entry)
            area_identifier, filename, download_type, download_timestamp = entry
            print(area_identifier, filename, download_type, download_timestamp)
            if latest_download_timestamp != None:
                raise "which timestamp is greater?" # TODO handle
            latest_download_timestamp = download_timestamp
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
        print(query)
        """
        timestamp = int(time.time())
        download_overpass_query(query, work_filepath, user_agent=config.user_agent())
        downloaded_filepath = filepath_to_downloaded_osm_data(internal_region_name, "_update_" + timestamp_formatted)
        shutil.move(work_filepath, downloaded_filepath) # this helps in cases where download was interupted and left empty file behind
        load_osm_file.load_osm_file(cursor, downloaded_filepath, internal_region_name, timestamp)
        # done AFTER data was safely loaded, committed together
        # this way we avoid problems with data downloaded and only partially loaded in database
        cursor.execute("INSERT INTO osm_data_update_log VALUES (:area_identifier, :filename, :download_type, :download_timestamp)", {"area_identifier": internal_region_name, "filename": downloaded_filepath, "download_type": "update_since_previous_download", "download_timestamp": timestamp})
        connection.commit()
        print("sleeping extra time to prevent inevitable quota exhaustion")
        time.sleep(60)
        return timestamp
        """
        return latest_download_timestamp
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
        connection.commit()
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
