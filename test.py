# coding=utf-8

import urllib2
import os.path
from lxml import etree
import string
import argparse
import decimal
import re


def get_tag_value(element, querried_tag):
    for tag in element:
        if tag.tag != "tag":
            continue
        if tag.attrib['k'] == querried_tag:
            return tag.attrib['v'].encode('utf-8')
    return ""


def not_a_coordinable_element(element):
    if element.tag == "relation":
        relation_type = get_tag_value(element, "type")
        if relation_type == "person" or relation_type == "route":
            return True
    if get_tag_value(element, "waterway") == "river":
        return True
    return False


def get_language_code_from_link(link):
    parsed_link = re.match('([^:]*):(.*)', link)
    if parsed_link is None:
        return None
    return parsed_link.group(1)


def get_article_name_from_link(link):
    parsed_link = re.match('([^:]*):(.*)', link)
    if parsed_link is None:
        return None
    return parsed_link.group(2)


def output_element(element, message):
    name = get_tag_value(element, "name")
    link = get_tag_value(element, "wikipedia")
    language_code = get_language_code_from_link(link)
    article_name = get_article_name_from_link(link)
    lat = None
    lon = None
    out_of_bounds = False
    show_out_of_bounds_elements = False
    if element.tag == "node":
        lat = float(element.attrib['lat'])
        lon = float(element.attrib['lon'])
    elif element.tag == "way" or element.tag == "relation":
        coord = get_coords_of_complex_object(element, node_database, way_database)
        if coord is None:
            out_of_bounds = True
            if not show_out_of_bounds_elements:
                return
        else:
            lat = float(coord.lat)
            lon = float(coord.lon)
    print
    print message
    print name
    print ("http://www.openstreetmap.org/" + element.tag + "/" + element.attrib['id']).encode('utf-8')
    if language_code is not None and article_name is not None:
        print "https://" + language_code + ".wikipedia.org/wiki/" + urllib2.quote(article_name)
    if out_of_bounds:
        print "Out of bounds"
    else:
        lat_sign_character = "N"
        if lat < 0:
            lat *= -1
            lat_sign_character = "S"
        lon_sign_character = "E"
        if lon < 0:
            lon *= -1
            lon_sign_character = "W"
        lat_d = int(float(lat))
        lat_m = int((float(lat) * 60) - (lat_d * 60))
        lat_s = int((float(lat) * 60 * 60) - (lat_d * 60 * 60) - (lat_m * 60))
        lat_d = str(lat_d)
        lat_m = str(lat_m)
        lat_s = str(lat_s)
        lon_d = int(float(lon))
        lon_m = int((float(lon) * 60) - (lon_d * 60))
        lon_s = int((float(lon) * 60 * 60) - (lon_d * 60 * 60) - (lon_m * 60))
        lon_d = str(lon_d)
        lon_m = str(lon_m)
        lon_s = str(lon_s)

        lat = "%.4f" % lat  # drop overprecision
        lon = "%.4f" % lon  # drop overprecision

        print lat
        print lon
        if language_code == "it":
            print "{{coord|" + lat + "|" + lon + "|display=title}}"
        else:
            print "{{coord|" + lat + "|" + lon + "}}"
        if language_code == "pl":
            pl_format = "|współrzędne = "
            pl_format += lat_d + "°" + lat_m + "'" + lat_s + '"' + lat_sign_character
            pl_format += " "
            pl_format += lon_d + "°" + lon_m + "'" + lon_s + '"' + lon_sign_character
            print pl_format


def get_form_of_link_usable_as_filename(link):
    link = link.replace("\"", "")
    link = link.replace("*", "")
    link = link.replace("\\", "")
    link = link.replace("/", "")
    link = link.replace("?", "")
    link = link.replace("<", "")
    link = link.replace(">", "")
    link = link.replace("|", "")
    return link


def get_filename_with_article(language_code, article_link):
    return os.path.join('cache', language_code, get_form_of_link_usable_as_filename(article_link) + ".txt")


def get_filename_with_code(language_code, article_link):
    return os.path.join('cache', language_code, get_form_of_link_usable_as_filename(article_link) + ".code.txt")


class UrlResponse:
    def __init__(self, content, code):
        self.content = content
        self.code = code


def fetch(url):
    while True:
        try:
            f = urllib2.urlopen(url)
            return UrlResponse(f.read(), f.getcode())
        except urllib2.HTTPError as e:
            return UrlResponse("", e.getcode())
        except urllib2.URLError as e:
            print "no response from server for url " + url
            print e
            continue


def fetch_data_from_wikipedia(language_code, article_link):
    path = os.path.join('cache', language_code)
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
    print "fetching from " + language_code + "wiki: " + article_link
    article_file = open(get_filename_with_article(language_code, article_link), 'w')
    code_file = open(get_filename_with_code(language_code, article_link), 'w')
    url = "https://" + language_code + ".wikipedia.org/wiki/" + urllib2.quote(article_link)
    result = fetch(url)
    article_file.write(str(result.content))
    code_file.write(str(result.code))
    article_file.close()
    code_file.close()


def it_is_necessary_to_reload_files(language_code, article_link):
    article_filename = get_filename_with_article(language_code, article_link)
    code_filename = get_filename_with_code(language_code, article_link)
    files_need_reloading = args.flush_cache

    if not os.path.isfile(article_filename) or not os.path.isfile(code_filename):
        files_need_reloading = True
    else:
        code_file = open(code_filename, 'r')
        if code_file.read() == "":
            files_need_reloading = True
        code_file.close()
    return files_need_reloading


def process_element(element, forced_refresh=False):
    link = get_tag_value(element, "wikipedia")
    if link == "":
        return False
    elif string.find(link, "#") != -1:
        output_element(element, "link to section:")
        return True
    else:
        language_code = get_language_code_from_link(link)
        article_name = get_article_name_from_link(link)
        if args.expected_language_code is not None and args.expected_language_code != language_code:
            output_element(element, "missing " + args.expected_language_code + ":")
            return True
        if language_code is None or language_code.__len__() > 2:
            output_element(element, "malformed wikipedia tag (" + link + ")")
            return True
        if it_is_necessary_to_reload_files(language_code, article_name) or forced_refresh:
            fetch_data_from_wikipedia(language_code, article_name)
        article_file = open(get_filename_with_article(language_code, article_name), 'r')
        page = article_file.read()
        article_file.close()
        code_file = open(get_filename_with_code(language_code, article_name), 'r')
        code = int(code_file.read())
        code_file.close()
        # <span class="latitude">50°04'02”N</span>&#160;<span class="longitude">19°55'03”E</span>
        index = string.find(page, "<span class=\"latitude\">")
        inline = string.find(page, "coordinates inline plainlinks")
        if index > inline != -1:
            index = -1  #inline coordinates are not real ones
        if index == -1:
            if code != 200:
                output_element(element, "missing article at wiki:")
                return True
            else:
                kml_data_str = "><span id=\"coordinates\"><b>Route map</b>: <a rel=\"nofollow\" class=\"external text\""
                if string.find(page, kml_data_str) == -1:  #enwiki article links to area, not point (see 'Central Park')
                    if not not_a_coordinable_element(element):
                        output_element(element, "missing coordinates at " + language_code + "wiki:")
                        return True
        else:
            if not_a_coordinable_element(element):
                output_element(element, "coordinates at uncoordinable element:")
                return True
    return False


def parsed_args():
    parser = argparse.ArgumentParser(description='Validation of wikipedia tag in osm data.')
    parser.add_argument('-expected_language_code', '-l', dest='expected_language_code', type=str, help='expected language code')
    parser.add_argument('-file', '-f', dest='file', type=str, help='location of osm file')
    parser.add_argument('-lat', '-latitude', dest='lat', type=float,
                        help='location of area, OSM data will be fetched (in deegres)')
    parser.add_argument('-lon', '-longitude', dest='lon', type=float,
                        help='location of area, OSM data will be fetched (in deegres)')
    parser.add_argument('-delta', '-d', dest='delta', type=float,
                        help='size of area, OSM data will be fetched (in deegres)')
    parser.add_argument('-flush_cache', dest='flush_cache', help='adding this parameter will trigger flushing cache',
                        action='store_true')
    parser.add_argument('-flush_cache_for_reported_situations', dest='flush_cache_for_reported_situations',
                        help='adding this parameter will trigger flushing cache only forreported situations',
                        action='store_true')

    args = parser.parse_args()
    if not (args.file or (args.lat and args.lon)):
        parser.error('Provide file with OSM data or location')
    if args.file and (args.lat and args.lon):
        parser.error('Provide file with OSM data or location, not both. For programmers and lawyers: data XOR location')
    return args


def fetch_osm_data(lat, lon, delta, filename):
    osm_file = open(filename, 'w')
    url = "http://overpass-api.de/api/interpreter?data=(node("
    url += str(lat - delta) + "," + str(lon - delta) + "," + str(lat + delta) + "," + str(lon + delta)
    url += ");<;);out%20meta;"
    response = fetch(url)
    osm_file.write(response.content)
    osm_file.close()


def get_coords_of_complex_object(element, node_database, way_database):
    min_lat = 180
    max_lat = -180
    min_lon = 180
    max_lon = -180
    if element.tag != "way" and element.tag != "relation":
        raise ValueError("Not a proper element passed to get_coords_of_complex_object")
    for tag in element:
        if (tag.tag == "nd") or (tag.tag == "member" and tag.attrib['type'] == "node"):
            node_id = int(tag.attrib['ref'])
            try:
                if node_database[node_id] is None:
                    raise KeyError
            except KeyError:
                return None  # node outside of downloaded map
            lat = node_database[node_id].lat
            lon = node_database[node_id].lon
        elif tag.tag == "member" and tag.attrib['type'] == "way":
            way_id = int(tag.attrib['ref'])
            try:
                if way_database[way_id] is None:
                    raise KeyError
            except KeyError:
                return None  # way outside of downloaded map
            lat = way_database[way_id].lat
            lon = way_database[way_id].lon
        else:
            continue
        min_lat = min([min_lat, lat])
        max_lat = max([max_lat, lat])
        min_lon = min([min_lon, lon])
        max_lon = max([max_lon, lon])
    return Coord((min_lat + max_lat) / 2, (min_lon + max_lon) / 2)


class Coord:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon


args = parsed_args()
if args.lat and args.lon:
    delta = 0.02
    if args.delta is not None:
        delta = args.delta
    args.file = str(args.lat) + "-" + str(args.lon) + "#" + str(delta) + ".osm"
    if not os.path.isfile(args.file) or args.flush_cache or args.flush_cache_for_reported_situations:
        fetch_osm_data(args.lat, args.lon, delta, args.file)
data = etree.parse(args.file)
node_database = {}
way_database = {}
for element in data.getiterator():
    if element.tag != "node" and element.tag != "way" and element.tag != "relation":
        continue
    if element.tag == "node":
        lat = decimal.Decimal(element.attrib['lat'].encode('utf-8'))
        lon = decimal.Decimal(element.attrib['lon'].encode('utf-8'))
        osm_id = int(element.attrib['id'])
        node_database[osm_id] = Coord(lat, lon)
    if element.tag == "way":
        coords = get_coords_of_complex_object(element, node_database, way_database)
        osm_id = int(element.attrib['id'])
        way_database[osm_id] = coords
    if process_element(element):
        if args.flush_cache_for_reported_situations:
            process_element(element, forced_refresh=True)
