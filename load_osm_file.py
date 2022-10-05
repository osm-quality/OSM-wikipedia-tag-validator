import xml_stream
import sqlite3
import json
import config

def load_osm_file(osm_file_filepath, identifier_of_region):
    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()

    # based on https://github.com/sopherapps/xml_stream/issues/6 and osm_iterator
    nodes_iter = xml_stream.read_xml_file(osm_file_filepath, records_tag="node")
    ways_iter = xml_stream.read_xml_file(osm_file_filepath, records_tag="way")
    relations_iter = xml_stream.read_xml_file(osm_file_filepath, records_tag="relation")


    for complex_set in [relations_iter, ways_iter]:
        for v in complex_set:
            osm_tags = {}
            for tag in v:
                if tag.tag != "tag":
                    continue
                key = tag.attrib['k']
                value = tag.attrib['v']
                osm_tags[key] = value
            if len(osm_tags) > 0:
                osm_type = v.tag
                osm_id = v.attrib['id']
                for tag in v:
                    if tag.tag != "center":
                        continue
                    lat = float(tag.attrib['lat'])
                    lon = float(tag.attrib['lon'])
                    record(cursor, osm_type, osm_id, lat, lon, osm_tags, identifier_of_region)
    for v in nodes_iter:
        osm_tags = {}
        for tag in v:
            if tag.tag != "tag":
                continue
            key = tag.attrib['k']
            value = tag.attrib['v']
            osm_tags[key] = value
        if len(osm_tags) > 0:
            osm_type = v.tag
            osm_id = v.attrib['id']
            lat = float(v.attrib['lat'])
            lon = float(v.attrib['lon'])
            record(cursor, osm_type, osm_id, lat, lon, osm_tags, identifier_of_region)
    connection.commit()
    connection.close()


def record(cursor, object_type, object_number, lat, lon, tags, identifier_of_region):
    if tags == {}:
        return

    relevant = False
    for key in tags.keys():
        if "wikidata" in key or "wikipedia" in key:
            relevant = True
    if relevant:
        cursor.execute("INSERT INTO osm_data VALUES (:type, :id, :lat, :lon, :tags, :area_identifier, :osm_data_updated, :validator_complaint)", {'type': object_type, 'id': object_number, 'lat': lat, 'lon': lon, "tags": json.dumps(tags), "area_identifier": identifier_of_region, "osm_data_updated": "2022-12-01", "validator_complaint": None})