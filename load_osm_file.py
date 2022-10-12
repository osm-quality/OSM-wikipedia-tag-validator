import xml_stream
import sqlite3
import json
import config

def load_osm_file(cursor, osm_file_filepath, identifier_of_region, timestamp_when_file_was_downloaded):
    for entry in xml_streaming_of_osm_file(osm_file_filepath):
        record(cursor, entry, identifier_of_region, timestamp_when_file_was_downloaded)

def record(cursor, entry, identifier_of_region, timestamp):
    if entry["osm_tags"] == {}:
        return

    relevant = False
    for key in entry["osm_tags"].keys():
        if "wikidata" in key or "wikipedia" in key:
            relevant = True
    if relevant:
        cursor.execute("SELECT download_timestamp FROM osm_data WHERE type = :type and id = :id", {'type': entry["osm_type"], 'id': entry["osm_id"]})
        data = cursor.fetchall()
        if len(data) > 1:
            raise "unexpected" # TODO store old data in osm_data or move it to somewhere else to record statistics
        if len(data) == 1:
            present_already_timestamp = data[0][0]
            print("currently stored data has timestamp", present_already_timestamp, "our is", timestamp, (timestamp-present_already_timestamp), "seconds later")
            # TODO do not always delete, only when needed
            cursor.execute("DELETE FROM osm_data WHERE type = :type and id = :id", {'type': entry["osm_type"], 'id': entry["osm_id"]})

        cursor.execute("INSERT INTO osm_data VALUES (:type, :id, :lat, :lon, :tags, :area_identifier, :download_timestamp, :validator_complaint)", {'type': entry["osm_type"], 'id': entry["osm_id"], 'lat': entry["lat"], 'lon': entry["lon"], "tags": json.dumps(entry["osm_tags"]), "area_identifier": identifier_of_region, "download_timestamp": timestamp, "validator_complaint": None})

def xml_streaming_of_osm_file(osm_file_filepath):
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
                    yield({"osm_type": osm_type, "osm_id": osm_id, "lat": lat, "lon": lon, "osm_tags": osm_tags})
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
            yield({"osm_type": osm_type, "osm_id": osm_id, "lat": lat, "lon": lon, "osm_tags": osm_tags})
