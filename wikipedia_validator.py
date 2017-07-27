# coding=utf-8

import urllib.request, urllib.error, urllib.parse
import argparse

import wikipedia_connection
from osm_iterator import Data

def get_problem_for_given_element(element, forced_refresh):
    link = element.get_tag_value("wikipedia")
    if link == None:
        return None
    if link.find("#") != -1:
        return "link to section:"
    language_code = wikipedia_connection.get_language_code_from_link(link)
    article_name = wikipedia_connection.get_article_name_from_link(link)
    if language_code is None or language_code.__len__() > 3:
        return "malformed wikipedia tag (" + link + ")"
    if args.expected_language_code is not None and args.expected_language_code != language_code:
        return "wikipedia page in unwanted language - " + args.expected_language_code + " was expected:"
    page = wikipedia_connection.get_wikipedia_page(language_code, article_name, forced_refresh)
    if page == None:
        return "missing article at wiki:"
    return get_geotagging_problem(page, element)


def not_a_coordinable_element(element):
    if element.get_element().tag == "relation":
        relation_type = element.get_tag_value("type")
        if relation_type == "person" or relation_type == "route":
            return True
    if element.get_tag_value("waterway") == "river":
        return True
    return False


def print_additional_pl_wikipedia_coordinates(lat, lon):
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
    pl_format = "|stopni" + lat_sign_character + " = " + lat_d
    pl_format += " |minut" + lat_sign_character + " = " + lat_m
    pl_format += " |sekund" + lat_sign_character + " = " + lat_s
    pl_format += "\n"
    pl_format += "|stopni" + lon_sign_character + " = " + lon_d
    pl_format += " |minut" + lon_sign_character + " = " + lon_m
    pl_format += " |sekund" + lon_sign_character + " = " + lon_s
    pl_format += "\n"
    print(pl_format)


def output_element(element, message):
    name = element.get_tag_value("name")
    link = element.get_tag_value("wikipedia")
    language_code = wikipedia_connection.get_language_code_from_link(link)
    article_name = wikipedia_connection.get_article_name_from_link(link)
    lat = None
    lon = None
    out_of_bounds = False
    show_out_of_bounds_elements = False
    if element.get_element().tag == "node":
        lat = float(element.get_element().attrib['lat'])
        lon = float(element.get_element().attrib['lon'])
    elif element.get_element().tag == "way" or element.get_element().tag == "relation":
        coord = element.get_coords()
        if coord is None:
            out_of_bounds = True
            if not show_out_of_bounds_elements:
                return
        else:
            lat = float(coord.lat)
            lon = float(coord.lon)
    print()
    print(message)
    print(name)
    print(element.get_link())
    if language_code is not None and article_name is not None:
        print("https://" + language_code + ".wikipedia.org/wiki/" + urllib.parse.quote(article_name))
    if out_of_bounds:
        print("Out of bounds")
    else:
        lat = "%.4f" % lat  # drop overprecision
        lon = "%.4f" % lon  # drop overprecision

        print(lat)
        print(lon)
        if language_code == "it":
            print("{{coord|" + lat + "|" + lon + "|display=title}}")
        elif language_code == "pl":
            print("{{koordynaty|" + lat + "|" + lon + "}}")
            print_additional_pl_wikipedia_coordinates(lat, lon)
        else:
            print("{{coord|" + lat + "|" + lon + "}}")


def is_wikipedia_page_geotagged(page):
    # <span class="latitude">50°04'02”N</span>&#160;<span class="longitude">19°55'03”E</span>
    index = page.find("<span class=\"latitude\">")
    inline = page.find("coordinates inline plainlinks")
    if index > inline != -1:
        index = -1  #inline coordinates are not real ones
    if index == -1:
        kml_data_str = "><span id=\"coordinates\"><b>Route map</b>: <a rel=\"nofollow\" class=\"external text\""
        if page.find(kml_data_str) == -1:  #enwiki article links to area, not point (see 'Central Park')
            return False
    return True

def get_geotagging_problem(page, element):
    if is_wikipedia_page_geotagged(page):
        if not_a_coordinable_element(element):
            return "coordinates at uncoordinable element:"
    else:
        if not not_a_coordinable_element(element):
            return "missing coordinates at wiki:"
    return None

def validate_wikipedia_link_on_element_and_print_problems(element):
    problem = get_problem_for_given_element(element, False)
    if (problem != None):
        output_element(element, problem)

def validate_wikipedia_link_on_element_and_print_problems_refresh_cache(element):
    forced_refresh = False
    if(get_problem_for_given_element(element, False) != None):
        forced_refresh = True
    validate_wikipedia_link_on_element_and_print_problems(element)


def parsed_args():
    parser = argparse.ArgumentParser(description='Validation of wikipedia tag in osm data.')
    parser.add_argument('-expected_language_code', '-l', dest='expected_language_code', type=str, help='expected language code')
    parser.add_argument('-file', '-f', dest='file', type=str, help='location of .osm file')
    parser.add_argument('-flush_cache', dest='flush_cache', help='adding this parameter will trigger flushing cache',
                        action='store_true')
    parser.add_argument('-flush_cache_for_reported_situations', dest='flush_cache_for_reported_situations',
                        help='adding this parameter will trigger flushing cache only forreported situations',
                        action='store_true')

    args = parser.parse_args()
    if not (args.file):
        parser.error('Provide .osm file')
    return args

args = parsed_args()
osm = Data(args.file)
osm.iterate_over_data(validate_wikipedia_link_on_element_and_print_problems)
