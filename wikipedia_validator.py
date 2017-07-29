# coding=utf-8

import urllib.request, urllib.error, urllib.parse
import argparse

import wikipedia_connection
from osm_iterator import Data

def get_problem_for_given_element(element, forced_refresh):
    if args.flush_cache:
        forced_refresh = True
    link = element.get_tag_value("wikipedia")
    if link == None:
        return None
    if link.find("#") != -1:
        return "link to section (\"only provide links to articles which are 'about the feature'\" - http://wiki.openstreetmap.org/wiki/Key:wikipedia):"
    language_code = wikipedia_connection.get_language_code_from_link(link)
    article_name = wikipedia_connection.get_article_name_from_link(link)
    wikidata_id = wikipedia_connection.get_wikidata_object_id_from_article(language_code, article_name, forced_refresh)

    if language_code is None or language_code.__len__() > 3:
        return "malformed wikipedia tag (" + link + ")"

    if is_object_outside_language_area(wikidata_id):
        return None

    page = wikipedia_connection.get_wikipedia_page(language_code, article_name, forced_refresh)

    if page == None:
        return "missing article at wiki:"

    wikipedia_link_issues = get_problem_based_on_wikidata(element, page, language_code, article_name, wikidata_id)
    if wikipedia_link_issues != None:
        return wikipedia_link_issues

    if args.expected_language_code is not None and args.expected_language_code != language_code:
        correct_article = get_interwiki(language_code, article_name, args.expected_language_code, forced_refresh)
        if correct_article != None:
            return "wikipedia page in unwanted language - " + args.expected_language_code + " was expected:"
        if correct_article == None and args.only_osm_edits == False and args.allow_false_positives:
            return "wikipedia page in unwanted language - " + args.expected_language_code + " was expected, no page in that language was found:"
    if args.only_osm_edits == False:
        return get_geotagging_problem(page, element, wikidata_id)
    return None

def get_problem_based_on_wikidata(element, page, language_code, article_name, wikidata_id):
    if not element_can_be_reduced_to_position_at_single_location(element):
        return None
    if is_wikipedia_page_geotagged(page) or wikipedia_connection.get_location_from_wikidata(wikidata_id) != (None, None):
        return None
    type_id = get_wikidata_type_id_from_article(language_code, article_name)
    if type_id == None:
        if args.only_osm_edits:
            return None
        return "instance data not present in wikidata for " + wikidata_url(language_code, article_name) + ". unable to verify type of object:"
    if type_id == 'Q4167410':
        return wikipedia_url(language_code, article_name) + " is a disambig page - not a proper wikipedia link"
    if type_id == 'Q811979':
        #"designed structure"
        return None
    if type_id == 'Q46831':
        # mountain range - "geographic area containing numerous geologically related mountains"
        return None
    if type_id == 'Q11776944':
        # Megaregion
        return None
    if type_id == 'Q31855':
        #instytut badawczy
        return None
    if type_id == 'Q34442':
        #road
        return None
    if type_id == 'Q5':
        return "article linked in wikipedia tag is about human, so it is very unlikely to be correct (subject:wikipedia=* tag would be probably better - in case of change remember to remove wikidata tag if it is present)"
    if get_wikidata_entry_description(type_id, 'en') != None:
        print("if type_id == '" + get_wikidata_entry_description(type_id, 'en'))
    elif get_wikidata_entry_description(type_id, args.expected_language_code) != None:
        print("if type_id == '" + get_wikidata_entry_description(type_id, args.expected_language_code))
    else:
        print("Unexpected type " + type_id + " undocumented format")
    return None

def get_wikidata_entry_description(wikidata_id, language):
    docs = wikipedia_connection.get_data_from_wikidata_by_id(wikidata_id)
    returned = ""
    try:
        label = docs['entities'][wikidata_id]['labels'][language]['value']
        returned = wikidata_id + " described as " + label
    except KeyError:
        return None

    try:
        explanation = docs['entities'][wikidata_id]['descriptions'][language]['value']
        returned = returned + " \"" + explanation + "\""
    except KeyError:
        return returned

def get_wikidata_type_id_from_article(language_code, article_name):
    try:
        forced_refresh = False
        wikidata_entry = wikipedia_connection.get_data_from_wikidata(language_code, article_name, forced_refresh)
        wikidata_entry = wikidata_entry['entities']
        object_id = list(wikidata_entry)[0]
        return wikidata_entry[object_id]['claims']['P31'][0]['mainsnak']['datavalue']['value']['id']
    except KeyError:
        return None

def is_object_outside_language_area(wikidata_id):
    if args.expected_language_code != None:
        return False

    if args.expected_language_code == "pl":
        target = 'Q36' #TODO, make it more general
    else:
        assert(False)

    countries = wikipedia_connection.get_property_from_wikidata(wikidata_id, 'P17')
    if countries == None:
        return False
    for country in countries:
        country = country['mainsnak']['datavalue']['value']['id']
        if country == target:
            return False
    if not matched:
        #not in the wanted country
        return True

def element_can_be_reduced_to_position_at_single_location(element):
    if element.get_element().tag == "relation":
        relation_type = element.get_tag_value("type")
        if relation_type == "person" or relation_type == "route":
            return False
    if element.get_tag_value("waterway") == "river":
        return False
    return True


def print_wikipedia_location_data(lat, lon, language_code):
    lat = "%.4f" % lat  # drop overprecision
    lon = "%.4f" % lon  # drop overprecision

    print(lat)
    print(lon)
    if language_code == "it":
        print("{{coord|" + lat + "|" + lon + "|display=title}}")
    elif language_code == "pl":
        print("{{współrzędne|" + lat + " " + lon + "|umieść=na górze}}")
        print("")
        print(lat + " " + lon)
        print("")
        print_pl_wikipedia_coordinates_for_infobox_old_style(float(lat), float(lon))
    else:
        print("{{coord|" + lat + "|" + lon + "}}")

def print_pl_wikipedia_coordinates_for_infobox_old_style(lat, lon):
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


def wikidata_url(language_code, article_name):
    return "https://www.wikidata.org/wiki/" + wikipedia_connection.get_wikidata_object_id_from_article(language_code, article_name)

def wikipedia_url(language_code, article_name):
    return "https://" + language_code + ".wikipedia.org/wiki/" + urllib.parse.quote(article_name)

def get_interwiki(source_language_code, source_article_name, target_language, forced_refresh):
    try:
        wikidata_entry = wikipedia_connection.get_data_from_wikidata(source_language_code, source_article_name, forced_refresh)
        wikidata_entry = wikidata_entry['entities']
        id = list(wikidata_entry)[0]
        return wikidata_entry[id]['sitelinks'][target_language+'wiki']['title']
    except KeyError:
        return None

def output_element(element, message):
    name = element.get_tag_value("name")
    link = element.get_tag_value("wikipedia")
    language_code = wikipedia_connection.get_language_code_from_link(link)
    article_name = wikipedia_connection.get_article_name_from_link(link)
    lat = None
    lon = None
    out_of_bounds = False
    if element.get_element().tag == "node":
        lat = float(element.get_element().attrib['lat'])
        lon = float(element.get_element().attrib['lon'])
    elif element.get_element().tag == "way" or element.get_element().tag == "relation":
        coord = element.get_coords()
        if coord is None:
            out_of_bounds = True
        else:
            lat = float(coord.lat)
            lon = float(coord.lon)
    print()
    print(message)
    print(name)
    print(element.get_link())
    print_interwiki_situation_if_relevant(language_code, article_name)
    if out_of_bounds:
        print("Location data missing")
    else:
        if args.only_osm_edits == False:
            print_wikipedia_location_data(lat, lon, language_code)

def print_interwiki_situation_if_relevant(language_code, article_name):
    if language_code is not None and article_name is not None:
        print(wikipedia_url(language_code, article_name))
        print(article_name)
        article_name_in_intended = get_interwiki(language_code, article_name, args.expected_language_code, False)
        if article_name_in_intended == None:
            print("no article in " + args.expected_language_code + "wiki")
        else:
            print(args.expected_language_code + ":" + article_name_in_intended)

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

def get_geotagging_problem(page, element, wikidata_id):
    if is_wikipedia_page_geotagged(page) or wikipedia_connection.get_location_from_wikidata(wikidata_id) != (None, None):
        return None
    if element_can_be_reduced_to_position_at_single_location(element):
        return "missing coordinates at wiki or wikipedia tag should be replaced by something like operator:wikipedia=en:McDonald's or subject:wikipedia=*:"
    return None

def validate_wikipedia_link_on_element_and_print_problems(element):
    problem = get_problem_for_given_element(element, False)
    if (problem != None):
        output_element(element, problem)

def validate_wikipedia_link_on_element_and_print_problems_refresh_cache_for_reported(element):
    if(get_problem_for_given_element(element, False) != None):
        get_problem_for_given_element(element, True)
    validate_wikipedia_link_on_element_and_print_problems(element)


def parsed_args():
    parser = argparse.ArgumentParser(description='Validation of wikipedia tag in osm data.')
    parser.add_argument('-expected_language_code', '-l', dest='expected_language_code', type=str, help='expected language code')
    parser.add_argument('-file', '-f', dest='file', type=str, help='location of .osm file')
    parser.add_argument('-flush_cache', dest='flush_cache', help='adding this parameter will trigger flushing cache',
                        action='store_true')
    parser.add_argument('-flush_cache_for_reported_situations', dest='flush_cache_for_reported_situations',
                        help='adding this parameter will trigger flushing cache only for reported situations \
                        (redownloads wikipedia data for cases where errors are reported, \
                        so removes false positives where wikipedia is already fixed)',
                        action='store_true')
    parser.add_argument('-only_osm_edits', dest='only_osm_edits', help='adding this parameter will remove reporting of problems that may require editing wikipedia',
                        action='store_true')
    parser.add_argument('-allow_false_positives', dest='allow_false_positives', help='enables validator rules that may report false positives')
    args = parser.parse_args()
    if not (args.file):
        parser.error('Provide .osm file')
    return args

cache_location_config_filepath = 'cache_location.config'
cache_location_file = open(cache_location_config_filepath, 'r')
wikipedia_connection.set_cache_location(cache_location_file.read())
cache_location_file.close()

args = parsed_args()
osm = Data(args.file)
if args.flush_cache_for_reported_situations:
    osm.iterate_over_data(validate_wikipedia_link_on_element_and_print_problems_refresh_cache_for_reported)
else:
    osm.iterate_over_data(validate_wikipedia_link_on_element_and_print_problems)
