# coding=utf-8

import urllib.request, urllib.error, urllib.parse
import argparse
import yaml
import re

import wikipedia_connection
import common
from osm_iterator import Data
import geopy.distance

def get_problem_for_given_element(element, forced_refresh):
    if object_should_be_deleted_not_repaired(element):
        return None

    if args.flush_cache:
        forced_refresh = True

    link = element.get_tag_value("wikipedia")
    present_wikidata_id = element.get_tag_value("wikidata")

    #TODO handle also cases without wikipedia but with wikidata
    if link == None:
        return None

    #TODO - is it OK?
    #if link.find("#") != -1:
    #    return "link to section (\"only provide links to articles which are 'about the feature'\" - http://wiki.openstreetmap.org/wiki/Key:wikipedia):"

    language_code = wikipedia_connection.get_language_code_from_link(link)
    article_name = wikipedia_connection.get_article_name_from_link(link)
    wikidata_id = wikipedia_connection.get_wikidata_object_id_from_article(language_code, article_name, forced_refresh)

    if is_wikipedia_tag_clearly_broken(link):
        return ErrorReport(error_id = "malformed wikipedia tag", error_message = "malformed wikipedia tag (" + link + ")")

    page = wikipedia_connection.get_wikipedia_page(language_code, article_name, forced_refresh)

    if page == None:
        return ErrorReport(error_id = "wikipedia tag links to 404", error_message = "missing article at wiki:")

    #early to ensure later that passing wikidata_id of article is not going to be confusing
    collisions = check_for_wikipedia_wikidata_collision(present_wikidata_id, language_code, article_name, forced_refresh)
    if collisions != None:
        return collisions

    #do not pass language_code, article_name
    #aquire from wikidata within function if truly necessary
    wikipedia_link_issues = get_problem_based_on_wikidata(element, language_code, article_name, wikidata_id)
    if wikipedia_link_issues != None:
        return wikipedia_link_issues

    wikipedia_language_issues = get_wikipedia_language_issues(element, language_code, article_name, forced_refresh, wikidata_id)
    if wikipedia_language_issues != None:
        return wikipedia_language_issues

    if present_wikidata_id == None and wikidata_id != None:
        return ErrorReport(error_id = "wikidata tag may be added", error_message = wikidata_id + " may be added as wikidata tag based on wikipedia tag")

    return None

def check_for_wikipedia_wikidata_collision(present_wikidata_id, language_code, article_name, forced_refresh):
    if present_wikidata_id == None:
        return None

    article_name_with_section_stripped = article_name
    if article_name.find("#") != -1:
        article_name_with_section_stripped = re.match('([^:]*)#(.*)', article_name).group(1)

    wikidata_id_from_article = wikipedia_connection.get_wikidata_object_id_from_article(language_code, article_name_with_section_stripped, forced_refresh)
    if present_wikidata_id == wikidata_id_from_article:
        return None

    title_after_possible_redirects = wikipedia_connection.get_from_wikipedia_api(language_code, "", article_name)['title']
    if article_name != title_after_possible_redirects and article_name.find("#") == -1:
        wikidata_id_from_redirect = wikipedia_connection.get_wikidata_object_id_from_article(language_code, title_after_possible_redirects, forced_refresh)
        if present_wikidata_id == wikidata_id_from_redirect:
            message = "wikidata and wikipedia tags link to a different objects, because wikipedia page points toward redirect that should be followed (" + compare_wikidata_ids(present_wikidata_id, wikidata_id_from_article) +")"
            new_wikipedia_link = language_code+":"+title_after_possible_redirects
            return ErrorReport(
                error_id = "wikipedia wikidata mismatch - follow redirect",
                error_message = message,
                desired_wikipedia_target = new_wikipedia_link,
                prerequisite = {'wikidata': present_wikidata_id, 'wikipedia': language_code+":"+article_name},
                )
    message = "wikidata and wikipedia tags link to a different objects (" + compare_wikidata_ids(present_wikidata_id, wikidata_id_from_article) +" wikidata from article)"
    return ErrorReport(error_id = "wikipedia wikidata mismatch", error_message = message)

def compare_wikidata_ids(id1, id2):
    if id1 == None:
        id1 = "(missing)"
    if id2 == None:
        id2 = "(missing)"
    return id1 + " vs " + id2

def is_wikipedia_tag_clearly_broken(link):
    # detects missing language code
    #         unusually long language code
    #         broken language code "pl|"
    language_code = wikipedia_connection.get_language_code_from_link(link)
    if language_code is None:
        return True
    if language_code.__len__() > 3:
        return True
    if re.search("^[a-z]+\Z",language_code) == None:
        return True

def get_wikipedia_language_issues(element, language_code, article_name, forced_refresh, wikidata_id):
    if args.expected_language_code is None:
        return None
    if args.expected_language_code == language_code:
        return None
    reason = why_object_is_allowed_to_have_foreign_language_label(element, wikidata_id)
    if reason != None:
        if args.additional_debug:
            print(describe_osm_object(element) + " is allowed to have foreign wikipedia link, because " + reason)
        return None
    correct_article = get_interwiki(language_code, article_name, args.expected_language_code, forced_refresh)
    if correct_article != None:
        error_message = "wikipedia page in unexpected language - " + args.expected_language_code + " was expected:"
        good_link = args.expected_language_code + ":" + correct_article
        prerequisite = {'wikipedia': language_code+":"+article_name}
        return ErrorReport(
            error_id = "wikipedia tag unexpected language",
            error_message = error_message,
            desired_wikipedia_target = good_link,
            prerequisite = prerequisite,
            )
    else:
        if args.only_osm_edits:
            return None
        if args.allow_false_positives == False:
            return None
        error_message = "wikipedia page in unexpected language - " + args.expected_language_code + " was expected, no page in that language was found:"
        return ErrorReport(error_id = "wikipedia tag unexpected language, article missing", error_message = error_message)
    assert(False)

def should_use_subject_message(type, base_type_id):
    return "article linked in wikipedia tag is about """ + type + \
    ", so it is very unlikely to be correct \
    (subject:wikipedia=* tag would be probably better - \
    in case of change remember to remove wikidata tag if it is present) \
    [base_type_id: " + base_type_id + "]"

def get_should_use_subject_error(type, base_type_id):
    return ErrorReport(error_id = "should use wikipedia:subject", error_message = should_use_subject_message(type, base_type_id))

def get_list_of_links_from_disambig(element, language_code, article_name):
    returned = []
    links_from_disambig_page = wikipedia_connection.get_from_wikipedia_api(language_code, "&prop=links", article_name)['links']
    for link in links_from_disambig_page:
        if link['ns'] == 0:
            returned.append(link['title'])
    return returned

def get_list_of_disambig_fixes(element, language_code, article_name):
    returned = ""
    links_from_disambig_page = wikipedia_connection.get_from_wikipedia_api(language_code, "&prop=links", article_name)['links']
    for title in get_list_of_links_from_disambig(element, language_code, article_name):
        wikidata_id = wikipedia_connection.get_wikidata_object_id_from_article(language_code, title)
        location = (None, None)
        if wikidata_id != None:
            location = wikipedia_connection.get_location_from_wikidata(wikidata_id)
        distance_description = ""
        if location == (None, None):
            distance_description = " <no location data on wikidata>"
        elif get_location_of_element(element) == (None, None):
            distance_description = " <no location data for OSM element>"
        else:
            coords_1 = (location[0], location[1])
            coords_2 = (get_location_of_element(element)[0], get_location_of_element(element)[1])
            # recommended by https://stackoverflow.com/a/43211266/4130619
            distance = geopy.distance.vincenty(coords_1, coords_2).km
            if distance > 3:
                distance = str(int(distance)) + " km"
            else:
                distance = str(int(distance*1000)) + " m"
            distance_description = ' is ' + distance + " away"
        returned += title + distance_description + "\n"
    return returned

def get_problem_based_on_wikidata(element, language_code, article_name, wikidata_id):
    if wikidata_id == None:
        return ErrorReport(error_id = "wikidata entry missing", error_message = describe_osm_object(element) + " has no matching wikidata entry")

    base_type_id = get_wikidata_type_id_of_entry(wikidata_id)
    if base_type_id == None:
        if args.only_osm_edits:
            return None
        # instance data not present in wikidata
        # not reporting as error as import from OSM to Wikidata is not feasible
        # also, this problem is easy to find on Wikidata itself so it is not useful to report it
        return None
    all_types = get_recursive_all_subclass_of(base_type_id)
    for type_id in all_types:
        if type_id == 'Q4167410':
            #TODO note that pageprops may be a better source that should be used - it does not require wikidata entry
            #https://pl.wikipedia.org/w/api.php?action=query&format=json&prop=pageprops&redirects=&titles=Java%20(ujednoznacznienie)
            list = get_list_of_disambig_fixes(element, language_code, article_name)
            error_message = wikipedia_url(language_code, article_name) + " is a disambig page - not a proper wikipedia link\n\n" + list
            return ErrorReport(error_id = "link to disambig", error_message = error_message)
        if type_id == 'Q5':
            return get_should_use_subject_error('a human', base_type_id)
        if type_id == 'Q18786396' or type_id == 'Q16521':
            return get_should_use_subject_error('an animal', base_type_id)
        #valid for example for museums, parishes
        #if type_id == 'Q43229':
        #    return get_should_use_subject_error('organization', base_type_id)
        if type_id == 'Q1344':
            return get_should_use_subject_error('an opera', base_type_id)
        if type_id == 'Q35127':
            return get_should_use_subject_error('a website', base_type_id)
        if type_id == 'Q1190554':
            return get_should_use_subject_error('an event', base_type_id)
        if type_id == 'Q5398426':
            return get_should_use_subject_error('a television series', base_type_id)
        if type_id == 'Q3026787':
            return get_should_use_subject_error('a saying', base_type_id)
        if type_id == 'Q13406463':
            error_message = "article linked in wikipedia tag is a list, so it is very unlikely to be correct"
            return ErrorReport(error_id = "link to list", error_message = "")
    for type_id in all_types:
        if is_wikidata_type_id_recognised_as_OK(type_id):
            return None

    if args.additional_debug:
        print("------------")
        print(describe_osm_object(element))
        print("unexpected type " + base_type_id)
        describe_unexpected_wikidata_type(base_type_id)
    return None

def is_wikidata_type_id_recognised_as_OK(type_id):
    if type_id == 'Q486972':
        #"human settlement"
        return True
    if type_id == 'Q811979':
        #"designed structure"
        return True
    if type_id == 'Q46831':
        # mountain range - "geographic area containing numerous geologically related mountains"
        return True
    if type_id == 'Q11776944':
        # Megaregion
        return True
    if type_id == 'Q31855':
        #instytut badawczy
        return True
    if type_id == 'Q34442':
        #road
        return True
    if type_id == 'Q2143825':
        #walking path 'path for hiking in a natural environment'
        return True
    if type_id == 'Q11634':
        #'art of sculpture'
        return True
    if type_id == 'Q56061':
        #'administrative territorial entity' - 'territorial entity for administration purposes, with or without its own local government'
        return True
    if type_id == 'Q473972':
        #'protected area'
        return True
    if type_id == 'Q4022':
        #river
        return True
    if type_id == 'Q22698':
        #park
        return True
    if type_id == 'Q11446':
        #ship
        return True
    if type_id == 'Q12876':
        #tank
        return True
    if type_id == 'Q57607':
        #christmas market
        return True
    if type_id == 'Q8502':
        #mountain
        return True
    if type_id == 'Q10862618':
        #mountain saddle
        return True
    if type_id == 'Q35509':
        #cave
        return True
    if type_id == 'Q23397':
        #lake
        return True
    if type_id == 'Q39816':
        #valley
        return True
    if type_id == 'Q179700':
        #statue
        return True
    #quite generic ones:
    if type_id == 'Q271669':
        #landform
        return True
    if type_id == 'Q376799':
        #transport infrastructure
        return True
    if type_id == 'Q15324':
        #body of water
        return True
    if type_id == 'Q975783':
        #land estate
        return True
    if type_id == 'Q8205328':
        #equipment (human-made physical object with a useful purpose)
        return True
    if type_id == 'Q618123':
        #geographical object
        return True
    return False

def wikidata_entries_for_abstract_or_very_broad_concepts():
    return ['Q1801244', 'Q28732711', 'Q223557', 'Q488383', 'Q16686448',
    'Q151885', 'Q35120', 'Q37260', 'Q246672', 'Q5127848', 'Q16889133',
    'Q386724', 'Q17008256', 'Q11348', 'Q11028', 'Q1260632', 'Q1209283',
    'Q673661', 'Q23008351', 'Q1914636', 'Q17334923', 'Q2221906',
    'Q2324993', 'Q58778', 'Q18340964', 'Q1544281', 'Q2101636',
    'Q30060700', 'Q3778211',
    ]

def get_recursive_all_subclass_of(wikidata_id, banned_parents = wikidata_entries_for_abstract_or_very_broad_concepts(), debug = False):
    processed = []
    to_process = [{"id": wikidata_id, "depth": 0}]
    while to_process != []:
        process = to_process.pop()
        process_id = process["id"]
        depth = process["depth"]
        if debug:
            print(" "*depth + wikidata_description(process_id))
        processed.append(process_id)
        new_ids = get_useful_direct_parents(process_id, processed + to_process + banned_parents)
        for parent_id in new_ids:
            to_process.append({"id": parent_id, "depth": depth+1})
    return processed

def get_useful_direct_parents(wikidata_id, forbidden):
    more_general_list = wikipedia_connection.get_property_from_wikidata(wikidata_id, 'P279') #subclass of
    if more_general_list == None:
        return []
    returned = []
    for more_general in more_general_list:
        more_general_id = more_general['mainsnak']['datavalue']['value']['id']
        if more_general_id not in forbidden:
            returned.append(more_general_id)
    return returned

def describe_unexpected_wikidata_type(type_id):
    # print entire inheritance set
    for parent_category in get_recursive_all_subclass_of(type_id):
        print("if type_id == '" + parent_category + "':")
        print(wikidata_description(parent_category))

def wikidata_description(wikidata_id):
    en_docs = get_wikidata_description(wikidata_id, 'en')
    local_docs = get_wikidata_description(wikidata_id, args.expected_language_code)
    if en_docs != None:
        return en_docs
    if local_docs != None:
        return local_docs
    return("Unexpected type " + wikidata_id + " undocumented format")

def get_wikidata_label(wikidata_id, language):
    try:
        data = wikipedia_connection.get_data_from_wikidata_by_id(wikidata_id)['entities'][wikidata_id]
        return data['labels']['en']['value']
    except KeyError:
        return None

def get_wikidata_explanation(wikidata_id, language):
    try:
        data = wikipedia_connection.get_data_from_wikidata_by_id(wikidata_id)['entities'][wikidata_id]
        return data['descriptions'][language]['value']
    except KeyError:
        return None

def get_wikidata_description(wikidata_id, language):
    docs = wikipedia_connection.get_data_from_wikidata_by_id(wikidata_id)
    returned = ""
    label = get_wikidata_label(wikidata_id, language)
    explanation = get_wikidata_explanation(wikidata_id, language)

    if label == None and explanation == None:
        return None

    if explanation != None:
        explanation = ' (' + explanation +')'
    else:
        explanation = ''

    return(language + ": " + label + explanation + ' [' + wikidata_id + "]")

def get_wikidata_type_id_of_entry(wikidata_id):
    try:
        forced_refresh = False
        wikidata_entry = wikipedia_connection.get_data_from_wikidata_by_id(wikidata_id, forced_refresh)
        wikidata_entry = wikidata_entry['entities']
        object_id = list(wikidata_entry)[0]
        return wikidata_entry[object_id]['claims']['P31'][0]['mainsnak']['datavalue']['value']['id']
    except KeyError:
        return None

# unknown data, known to be completely inside -> not allowed, returns None
# known to be outside or on border -> allowed, returns reason
def why_object_is_allowed_to_have_foreign_language_label(element, wikidata_id):
    if args.expected_language_code == None:
        return "no expected language is defined"

    if args.expected_language_code == "pl":
        target = 'Q36' #TODO, make it more general
    elif args.expected_language_code == "de":
        target = 'Q183'
    else:
        assert(False)

    countries = wikipedia_connection.get_property_from_wikidata(wikidata_id, 'P17')
    if countries == None:
        # TODO locate based on coordinates...
        return None
    for country in countries:
        country_id = country['mainsnak']['datavalue']['value']['id']
        if country_id != target:
            # we need to check whatever locations still belongs to a given country
            # it is necessary to avoid gems like
            # "Płock is allowed to have foreign wikipedia link, because it is at least partially in Nazi Germany"
            # P582 indicates the time an item ceases to exist or a statement stops being valid
            try:
                country['qualifiers']['P582']
            except KeyError:
                country_name = get_wikidata_label(country_id, 'en')
                #P582 is missing, therefore it is no longer valid
                if country_name == None:
                    return "it is at least partially in country without known name on Wikidata (country_id=" + country_id + ")"
                if country_id == 'Q7318':
                    print(describe_osm_object(element) + " is tagged on wikidata as location in no longer existing " + country_name)
                    return None
                return "it is at least partially in " + country_name
    return None

def element_can_be_reduced_to_position_at_single_location(element):
    if element.get_element().tag == "relation":
        relation_type = element.get_tag_value("type")
        if relation_type == "person" or relation_type == "route":
            return False
    if element.get_tag_value("waterway") == "river":
        return False
    return True

def object_should_be_deleted_not_repaired(element):
    if element.get_element().tag == "relation":
        relation_type = element.get_tag_value("type")
        if relation_type == "person":
            return True
    if element.get_tag_value("historic") == "battlefield":
        return True

def wikidata_url(wikidata_id):
    return "https://www.wikidata.org/wiki/" + wikidata_id

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

class ErrorReport:
    def __init__(self, error_message=None, element=None, desired_wikipedia_target=None, debug_log=None, error_id=None, prerequisite=None):
        self.error_id = error_id
        self.error_message = error_message
        self.debug_log = debug_log
        self.element = element
        self.desired_wikipedia_target = desired_wikipedia_target
        self.prerequisite = prerequisite

    def yaml_output(self, filepath):
        data = dict(
            error_id = self.error_id,
            error_message = self.error_message,
            debug_log = self.debug_log,
            osm_object_description = describe_osm_object(self.element),
            osm_object_url = self.element.get_link(),
            current_wikipedia_target = self.element.get_tag_value("wikipedia"),
            desired_wikipedia_target = self.desired_wikipedia_target,
            prerequisite = self.prerequisite,
        )
        with open(filepath, 'a') as outfile:
            yaml.dump([data], outfile, default_flow_style=False)

    def stdout_output(self):
        print()
        print(self.error_message)
        print(describe_osm_object(self.element))
        print(self.element.get_link())
        print(self.debug_log)
        print(self.prerequisite)
        if self.desired_wikipedia_target != None:
            print("wikipedia tag should probably be relinked to " + self.desired_wikipedia_target)

def describe_osm_object(element):
    name = element.get_tag_value("name")
    if name == None:
        name = ""
    return name + " " + element.get_link()

def output_element(element, error_report):
    error_report.element = element
    link = element.get_tag_value("wikipedia")
    language_code = wikipedia_connection.get_language_code_from_link(link)
    article_name = wikipedia_connection.get_article_name_from_link(link)
    lat, lon = get_location_of_element(element)

    debug_log = None

    if (lat, lon) == (None, None):
        error_report.debug_log = "Location data missing"

    error_report.yaml_output(yaml_report_filepath())

def yaml_report_filepath():
    return common.get_file_storage_location()+"/" + args.file + ".yaml"

def get_location_of_element(element):
    lat = None
    lon = None
    if element.get_element().tag == "node":
        lat = float(element.get_element().attrib['lat'])
        lon = float(element.get_element().attrib['lon'])
        return lat, lon
    elif element.get_element().tag == "way" or element.get_element().tag == "relation":
        coord = element.get_coords()
        if coord is None:
            return None, None
        else:
            return float(coord.lat), float(coord.lon)
    assert(False)

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
    parser.add_argument('-additional_debug', dest='additional_debug', help='additional debug - shows when wikidata types are no recognized, list locations allowed to have a foreign language label',
                        action='store_true')
    parser.add_argument('-allow_false_positives', dest='allow_false_positives', help='enables validator rules that may report false positives')
    args = parser.parse_args()
    if not (args.file):
        parser.error('Provide .osm file')
    return args

wikipedia_connection.set_cache_location(common.get_file_storage_location())

args = parsed_args()
osm = Data(args.file)
if args.flush_cache_for_reported_situations:
    osm.iterate_over_data(validate_wikipedia_link_on_element_and_print_problems_refresh_cache_for_reported)
else:
    osm.iterate_over_data(validate_wikipedia_link_on_element_and_print_problems)

#TODO detect mismatched wikipedia and wikidata tags
#TODO detect wikidata tag matching subject:wikipedia or operator:wikipedia
#TODO detect repeated links
#TODO find links to no longer existing objects https://www.wikidata.org/wiki/Property:P576

print("https://osm.wikidata.link/candidates/relation/2768922 (Kraków)")
print("https://osm.wikidata.link/candidates/relation/2654452 (powiat krakowski)")
print("https://osm.wikidata.link/candidates/relation/2907540 (Warszawa)")
print("https://osm.wikidata.link/filtered/Poland")
#https://osm.wikidata.link/candidates/relation/2675559 mazury
#https://osm.wikidata.link/candidates/relation/2675566 mazury
#https://osm.wikidata.link/candidates/relation/2675509 mazury
#https://osm.wikidata.link/candidates/relation/2675563 mazury

#links from buildings to parish are wrong - but from religious admin are OK https://www.wikidata.org/wiki/Q11808149
