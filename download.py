import config
from osm_bot_abstraction_layer.overpass_downloader import download_overpass_query
import pathlib
import shutil
import time
import sqlite3

def filepath_to_downloaded_osm_data(name, suffix):
  filename = name
  filename += suffix + ".osm"
  return config.downloaded_osm_data_location() + "/" + filename

def timeout():
  return 2550

def download_entry(internal_region_name, identifier_of_region):
    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    downloaded_filepath = filepath_to_downloaded_osm_data(internal_region_name, "_unprocessed")
    work_filepath = filepath_to_downloaded_osm_data(internal_region_name, "_download_in_progress")
    if pathlib.Path(downloaded_filepath).is_file():
        print("full data file is downloaded already")
        cursor.execute("SELECT area_identifier, filename, download_type, download_timestamp FROM osm_data_update_log WHERE area_identifier = :area_identifier ORDER BY download_timestamp", {"area_identifier": internal_region_name})
        returned = cursor.fetchall()
        if len(returned) == 0:
            print("it is not recorded when this data was downloaded!")
        for entry in returned:
            print(entry)
            area_identifier, filename, download_type, download_timestamp = entry
            print(area_identifier, filename, download_type, download_timestamp)
    else:
        timestamp = int(time.time())
        area_name_in_query = "searchArea"
        area_finder_string = area_finder(identifier_of_region, area_name_in_query)
        query = download_query_text(area_finder_string, area_name_in_query)
        download_overpass_query(query, work_filepath, user_agent=config.user_agent())
        shutil.move(work_filepath, downloaded_filepath) # this helps in cases where download was interupted and left empty file behind
        cursor.execute("INSERT INTO osm_data_update_log VALUES (:area_identifier, :filename, :download_type, :download_timestamp)", {"area_identifier": internal_region_name, "filename": downloaded_filepath, "download_type": "initial_full_data", "download_timestamp": timestamp})
        connection.commit()
        print("sleeping extra time to prevent inevitable quota exhaustion")
        time.sleep(60)
    return downloaded_filepath

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

def download_query_text(area_finder_string, area_name):
    area_identifier = 'area.' + area_name

    query = "[timeout:" + str(timeout()) + "];\n"
    query += "(\n"
    query += area_finder_string 
    query += "node['wikipedia'](" + area_identifier+ ");\n"
    query += "way['wikipedia'](" + area_identifier+ ");\n"
    query += "relation['wikipedia'](" + area_identifier+ ");\n"
    query += "node['wikidata'](" + area_identifier+ ");\n"
    query += "way['wikidata'](" + area_identifier+ ");\n"
    query += "relation['wikidata'](" + area_identifier+ ");\n"

    query += 'node[~"wikipedia:.*"~".*"](' + area_identifier+ ");\n"
    query += 'way[~"wikipedia:.*"~".*"](' + area_identifier+ ");\n"
    query += 'relation[~"wikipedia:.*"~".*"](' + area_identifier+ ");\n"

    query += ');\n'
    query += "out center;"
    return query
