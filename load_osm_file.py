from osm_iterator.osm_iterator import Data
import sqlite3
import json

def load_osm_data(element):
    global cursor
    global identifier

    tags = element.get_tag_dictionary()
    object_type = element.get_type()
    object_number = element.get_id()
    lat = element.get_coords().lat
    lon = element.get_coords().lon
    object_description = element.get_link()
    
    if tags == {}:
        return

    relevant = False
    for key in tags.keys():
        if "wikidata" in key or "wikipedia" in key:
            relevant = True
    
    if relevant:
        cursor.execute("INSERT INTO osm_data VALUES (:type, :id, :lat, :lon, :tags, :area_identifier, :osm_data_updated, :validator_complaint)", {'type': object_type, 'id': object_number, 'lat': lat, 'lon': lon, "tags": json.dumps(tags), "area_identifier": identifier, "osm_data_updated": "2022-12-01", "validator_complaint": None})


def load_osm_file(osm_file_filepath, identifier_of_region):
    global cursor
    global identifier
    identifier = identifier_of_region

    connection = sqlite3.connect('test.db')
    cursor = connection.cursor()

    osm = Data(osm_file_filepath)
    osm.iterate_over_data(load_osm_data)
    connection.commit()
    connection.close()
