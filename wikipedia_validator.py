# coding=utf-8

import urllib.request, urllib.error, urllib.parse
import argparse
import yaml
import re

import wikipedia_connection
import common
from osm_iterator import Data
import geopy.distance

present_wikipedia_links = {}
present_wikidata_links = {}
def record_presence(element):
    wikipedia_tag = element.get_tag_value("wikipedia")
    wikidata_tag = element.get_tag_value("wikidata")
    osm_object_url = element.get_link()
    if wikipedia_tag != None:
        if wikipedia_tag not in present_wikipedia_links:
            present_wikipedia_links[wikipedia_tag] = {}
        present_wikipedia_links[wikipedia_tag][osm_object_url] = element

    if wikidata_tag != None:
        if wikidata_tag not in present_wikidata_links:
            present_wikidata_links[wikidata_tag] = {}
        present_wikidata_links[wikidata_tag][osm_object_url] = element

properties = {}
def record_property_presence(property):
    if property not in properties:
        properties[property] = 1
    else:
        properties[property] += 1

def get_problem_for_given_element(element, forced_refresh):
    if object_should_be_deleted_not_repaired(element):
        return None

    if args.flush_cache:
        forced_refresh = True

    link = element.get_tag_value("wikipedia")
    present_wikidata_id = element.get_tag_value("wikidata")

    if link == None:
        return attempt_to_locate_wikipedia_tag(element, forced_refresh)

    #TODO - is it OK?
    #if link.find("#") != -1:
    #    return "link to section (\"only provide links to articles which are 'about the feature'\" - http://wiki.openstreetmap.org/wiki/Key:wikipedia):"

    language_code = wikipedia_connection.get_language_code_from_link(link)
    article_name = wikipedia_connection.get_article_name_from_link(link)
    wikidata_id = wikipedia_connection.get_wikidata_object_id_from_article(language_code, article_name, forced_refresh)

    if is_wikipedia_tag_clearly_broken(link):
        return ErrorReport(
                        error_id = "malformed wikipedia tag",
                        error_message = "malformed wikipedia tag (" + link + ")",
                        prerequisite = {'wikipedia': link},
                        )

    wikipedia_page_exists = check_is_wikipedia_page_existing(language_code, article_name, forced_refresh)
    if wikipedia_page_exists != None:
        return wikipedia_page_exists

    #early to ensure later that passing wikidata_id of article is not going to be confusing
    collisions = check_for_wikipedia_wikidata_collision(present_wikidata_id, language_code, article_name, forced_refresh)
    if collisions != None:
        return collisions

    #do not pass language_code, article_name
    #acquire from wikidata within function if truly necessary
    wikipedia_link_issues = get_problem_based_on_wikidata(element, language_code, article_name, wikidata_id, forced_refresh)
    if wikipedia_link_issues != None:
        return wikipedia_link_issues

    wikipedia_language_issues = get_wikipedia_language_issues(element, language_code, article_name, forced_refresh, wikidata_id)
    if wikipedia_language_issues != None:
        return wikipedia_language_issues

    if present_wikidata_id == None and wikidata_id != None:
        return ErrorReport(
                        error_id = "wikidata tag may be added",
                        error_message = wikidata_id + " may be added as wikidata tag based on wikipedia tag",
                        prerequisite = {'wikipedia': link, 'wikidata': None}
                        )

    existence_check = check_is_object_is_existing(present_wikidata_id)
    if existence_check != None:
        return existence_check

    new_data = add_data_from_wikidata(element)
    if new_data != None:
        return new_data

    if present_wikidata_id != None:
        wikidata = wikipedia_connection.get_data_from_wikidata_by_id(present_wikidata_id)
        for property in wikidata['entities'][present_wikidata_id]['claims']:
            property = str(property)
            record_property_presence(property)
    return None

def check_is_wikipedia_page_existing(language_code, article_name, forced_refresh):
    page_according_to_wikidata = get_interwiki_article_name(language_code, article_name, language_code, forced_refresh)
    if page_according_to_wikidata != None:
        # assume that wikidata is correct to save downloading page
        return None
    page = wikipedia_connection.get_wikipedia_page(language_code, article_name, forced_refresh)
    if page == None:
        return ErrorReport(
                    error_id = "wikipedia tag links to 404",
                    error_message = "missing article at wiki:",
                    prerequisite = {'wikipedia': language_code+":"+article_name}
                    )

def wikidata_data_quality_warning():
    return "REMEMBER TO VERIFY! WIKIDATA QUALITY MAY BE POOR!"

def check_is_object_is_existing(present_wikidata_id):
    if present_wikidata_id == None:
        return None
    no_longer_existing = wikipedia_connection.get_property_from_wikidata(present_wikidata_id, 'P576')
    if no_longer_existing != None:
        return ErrorReport(
                        error_id = "no longer existing object",
                        error_message ="Wikidata claims that this object no longer exists. Historical, no longer existing object must not be mapped in OSM - so it means that it is mistake or OSM is outdated." + " " + wikidata_data_quality_warning(),
                        prerequisite = {'wikidata': present_wikidata_id}
                        )

def decapsulate_wikidata_value(from_wikidata):
    # https://www.mediawiki.org/wiki/Wikibase/DataModel/JSON#Claims_and_Statements
    # todo fix flow by random exception
    try:
        from_wikidata = from_wikidata[0]['datavalue']['value']
    except KeyError:
        pass
    try:
        from_wikidata = from_wikidata[0]['mainsnak']['datavalue']['value']
    except KeyError:
        pass
    try:
        # for wikidata values formed like
        # {'entity-type': 'item', 'id': 'Q43399', 'numeric-id': 43399}
        if isinstance(from_wikidata, dict):
            if from_wikidata['entity-type'] == 'item':
                from_wikidata = from_wikidata['id']
    except KeyError:
        pass
    return from_wikidata

def tag_from_wikidata(present_wikidata_id, osm_key, wikidata_property, element, id_suffix="", message_suffix = ""):
    from_wikidata = wikipedia_connection.get_property_from_wikidata(present_wikidata_id, wikidata_property)
    if from_wikidata == None:
        return None
    from_wikidata = decapsulate_wikidata_value(from_wikidata)
    if element.get_tag_value(osm_key) == None:
            return ErrorReport(
                        error_id = "tag may be added based on wikidata" + id_suffix,
                        error_message = str(from_wikidata) + " may be added as " + osm_key + " tag based on wikidata entry" + message_suffix + " " + wikidata_data_quality_warning(),
                        prerequisite = {'wikidata': present_wikidata_id, osm_key: None}
                        )
    elif element.get_tag_value(osm_key) != from_wikidata:
            return ErrorReport(
                        error_id = "tag conflict with wikidata value" + id_suffix,
                        error_message = str(from_wikidata) + " conflicts with " + element.get_tag_value(osm_key) + " for " + osm_key + " tag based on wikidata entry" + " " + wikidata_data_quality_warning(),
                        prerequisite = {'wikidata': present_wikidata_id, osm_key: element.get_tag_value(osm_key)}
                        )

def add_data_from_wikidata(element):
    present_wikidata_id = element.get_tag_value("wikidata")
    if present_wikidata_id == None:
        return None
    if len(present_wikidata_links[present_wikidata_id].keys()) != 1:
        return None
    iata = tag_from_wikidata(present_wikidata_id, 'iata', 'P238', element)
    if iata != None:
        return iata
    simc = tag_from_wikidata(present_wikidata_id, 'teryt:simc', 'P4046', element, '', ' do weryfikacji przydaje się http://eteryt.stat.gov.pl/eTeryt/rejestr_teryt/udostepnianie_danych/baza_teryt/uzytkownicy_indywidualni/wyszukiwanie/wyszukiwanie.aspx?contrast=default ')
    if simc != None:
        return simc
    #moving P138 to name:wikidata tag makes no sense, just use wikidata instead
    website = tag_from_wikidata(present_wikidata_id, 'website', 'P856', element, " - boring")
    if website != None and website.error_message.find('web.archive.org') != -1:
        return website
    operator = tag_from_wikidata(present_wikidata_id, 'operator', 'P126', element, " - testing")
    if operator != None:
        return operator
    if element.get_tag_value('historic') == None:
        from_wikidata = wikipedia_connection.get_property_from_wikidata(present_wikidata_id, 'P1435')
        if from_wikidata == None:
            return None
        return ErrorReport(
            error_id = "tag conflict with wikidata value",
            error_message = "without historic tag and has heritage designation according to wikidata" + wikidata_data_quality_warning(),
            prerequisite = {'wikidata': present_wikidata_id, 'historic': None}
            )

    if element.get_tag_value('ele') != None:
        from_wikidata = wikipedia_connection.get_property_from_wikidata(present_wikidata_id, 'P2044')
        if from_wikidata == None:
            return None
        from_wikidata = decapsulate_wikidata_value(from_wikidata)
        if from_wikidata != element.get_tag_value('ele'):
            return ErrorReport(
                error_id = "tag conflict with wikidata value",
                error_message = "elevation in OSM vs elevation in Wikidata" + wikidata_data_quality_warning(),
                prerequisite = {'wikidata': present_wikidata_id, 'ele': element.get_tag_value('ele')}
                )

    if element.get_tag_value('ele') == None:
        if element.get_tag_value('natural') == 'peak':
            from_wikidata = wikipedia_connection.get_property_from_wikidata(present_wikidata_id, 'P2044')
            if from_wikidata == None:
                return None
            from_wikidata = decapsulate_wikidata_value(from_wikidata)
            return ErrorReport(
                        error_id = "tag may be added based on wikidata",
                        error_message = str(from_wikidata) + " may be added as ele tag based on wikidata entry" + " " + wikidata_data_quality_warning(),
                        prerequisite = {'wikidata': present_wikidata_id, 'ele': None}
                        )
    #TODO - match wikidata by teryt:simc (P4046)
    #2 minutes wasted on matching https://www.openstreetmap.org/node/3009664303

    #TODO  P1653 is also teryt property
    #P395 license plate code
    #geometry - waterway structure graph (inflow [P974], outflow [P403], tributary [P974]) - see http://tinyurl.com/y9h7ym7g
    #P571 - should be easy to process - lakes on river
    #P814 protected area
    #P2043 length
    #P36 capital of something
    #P140 religion
    return None

def attempt_to_locate_wikipedia_tag(element, forced_refresh):
    present_wikidata_id = element.get_tag_value("wikidata")
    wikipedia_type_keys = []
    for key in element.get_keys():
        if key.find("wikipedia:") != -1:
            wikipedia_type_keys.append(key)

    if present_wikidata_id != None and wikipedia_type_keys == []:
        return attempt_to_locate_wikipedia_tag_using_wikidata_id(present_wikidata_id, forced_refresh)

    if present_wikidata_id == None and wikipedia_type_keys != []:
        return attempt_to_locate_wikipedia_tag_using_old_style_wikipedia_keys(element, wikipedia_type_keys, forced_refresh)

    if present_wikidata_id != None and wikipedia_type_keys != []:
        return attempt_to_locate_wikipedia_tag_using_old_style_wikipedia_keys_and_wikidata(element, wikipedia_type_keys, present_wikidata_id, forced_refresh)
    return None

def attempt_to_locate_wikipedia_tag_using_old_style_wikipedia_keys_and_wikidata(element, wikipedia_type_keys, wikidata_id, forced_refresh):
    assert(wikidata_id != None)

    links = wikipedia_candidates_based_on_old_style_wikipedia_keys(element, wikipedia_type_keys, forced_refresh)

    prerequisite = {'wikidata': wikidata_id}
    for key in wikipedia_type_keys:
        prerequisite[key] = element.get_tag_value(key)

    conflict = False
    for link in links:
        language_code = wikipedia_connection.get_language_code_from_link(link)
        article_name = wikipedia_connection.get_article_name_from_link(link)
        id_from_link = wikipedia_connection.get_wikidata_object_id_from_article(language_code, article_name, forced_refresh)
        if wikidata_id != id_from_link:
            conflict = True

    if conflict:
        return ErrorReport(
            error_id = "wikipedia tag in outdated form and wikidata - mismatch",
            error_message = "wikipedia tag in outdated form (" + str(wikipedia_type_keys) + "), without wikipedia but with wikidata tag present. Mismatch happened and requires human judgment to solve.",
            prerequisite = prerequisite,
            )
    else:
        language_code = args.expected_language_code
        article_name = get_interwiki_article_name_by_id(wikidata_id, language_code, forced_refresh)
        return ErrorReport(
            error_id = "wikipedia tag from wikipedia tag in outdated form and wikidata",
            error_message = "wikipedia tag in outdated form (" + str(wikipedia_type_keys) + "), without wikipedia but with wikidata tag present",
            prerequisite = prerequisite,
            desired_wikipedia_target = language_code + ":" + article_name,
            )


def attempt_to_locate_wikipedia_tag_using_wikidata_id(present_wikidata_id, forced_refresh):
    article = get_interwiki_article_name_by_id(present_wikidata_id, args.expected_language_code, forced_refresh)
    if article == None:
        return None
    language_code = args.expected_language_code
    # TODO - if not available allow English or other languages
    return ErrorReport(
        error_id = "wikipedia from wikidata tag",
        error_message = "without wikipedia tag, without wikipedia:language tags, with wikidata tag present that provides article [target was not checked for disambigs etc - TODO, fix that]",
        desired_wikipedia_target = language_code + ":" + article,
        prerequisite = {'wikipedia': None, 'wikidata': present_wikidata_id},
        )

def attempt_to_locate_wikipedia_tag_using_old_style_wikipedia_keys(element, wikipedia_type_keys, forced_refresh):
    prerequisite = {'wikipedia': None, 'wikidata': None}
    links = wikipedia_candidates_based_on_old_style_wikipedia_keys(element, wikipedia_type_keys, forced_refresh)
    for key in wikipedia_type_keys:
        prerequisite[key] = element.get_tag_value(key)
    if len(links) == 1 and None not in links:
        return ErrorReport(
            error_id = "wikipedia from wikipedia tag in outdated form",
            error_message = "wikipedia tag in outdated form (" + str(wikipedia_type_keys) + "), without wikipedia tag, without wikidata tag [target was not checked for disambigs etc - TODO, fix that]",
            desired_wikipedia_target = links[0],
            prerequisite = prerequisite,
            )
    else:
        return ErrorReport(
            error_id = "wikipedia from wikipedia tag in outdated form - mismatch",
            error_message = "wikipedia tag in outdated form (" + str(wikipedia_type_keys) + "), without wikipedia tag, without wikidata tag, human judgement required [target was not checked for disambigs etc - TODO, fix that]",
            prerequisite = prerequisite,
            )

def wikipedia_candidates_based_on_old_style_wikipedia_keys(element, wikipedia_type_keys, forced_refresh):
    links = []
    for key in wikipedia_type_keys:
        language_code = wikipedia_connection.get_text_after_first_colon(key)
        article_name = element.get_tag_value(key)
        article = get_interwiki_article_name(language_code, article_name, args.expected_language_code, forced_refresh)
        if article == None:
            if key not in links:
                links.append(key)
        elif article not in links:
            links.append(args.expected_language_code + ":" + article)
    return links

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
    return ErrorReport(
        error_id = "wikipedia wikidata mismatch",
        error_message = message,
        prerequisite = {'wikidata': present_wikidata_id, 'wikipedia': language_code+":"+article_name},
        )

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
    prerequisite = {'wikipedia': language_code+":"+article_name}
    reason = why_object_is_allowed_to_have_foreign_language_label(element, wikidata_id)
    if reason != None:
        if args.additional_debug:
            print(describe_osm_object(element) + " is allowed to have foreign wikipedia link, because " + reason)
        return None
    correct_article = get_interwiki_article_name(language_code, article_name, args.expected_language_code, forced_refresh)
    if correct_article != None:
        error_message = "wikipedia page in unexpected language - " + args.expected_language_code + " was expected:"
        good_link = args.expected_language_code + ":" + correct_article
        return ErrorReport(
            error_id = "wikipedia tag unexpected language",
            error_message = error_message,
            desired_wikipedia_target = good_link,
            prerequisite = prerequisite,
            )
    else:
        if not args.allow_requesting_edits_outside_osm:
            return None
        if not args.allow_false_positives:
            return None
        error_message = "wikipedia page in unexpected language - " + args.expected_language_code + " was expected, no page in that language was found:"
        return ErrorReport(
            error_id = "wikipedia tag unexpected language, article missing",
            error_message = error_message,
            prerequisite = prerequisite,
            )
    assert(False)

def should_use_subject_message(type, special_prefix):
    special_prefix_text = ""
    if special_prefix != None:
        special_prefix_text = "or " + special_prefix + "wikipedia"
    message = "article linked in wikipedia tag is about """ + type + \
    ", so it is very unlikely to be correct \
    (subject:wikipedia=* " + special_prefix_text + " tag would be probably better \
    (see https://wiki.openstreetmap.org/wiki/Key:wikipedia#Secondary_Wikipedia_links ) - \
    in case of change remember to remove wikidata tag if it is present) \
    (object categorised by Wikidata - wrong classification may be caused by wrong data on Wikidata"
    return message

def get_should_use_subject_error(type, special_prefix, wikidata_id):
    return ErrorReport(
        error_id = "should use wikipedia:subject",
        error_message = should_use_subject_message(type, special_prefix),
        prerequisite = {'wikidata': wikidata_id},
        )

def get_list_of_links_from_disambig(wikidata_id, forced_refresh):
    language_code = "en"
    if args.expected_language_code != None:
        language_code = args.expected_language_code
    article_name = get_interwiki_article_name_by_id(wikidata_id, language_code, forced_refresh)
    returned = []
    links_from_disambig_page = wikipedia_connection.get_from_wikipedia_api(language_code, "&prop=links", article_name)['links']
    for link in links_from_disambig_page:
        if link['ns'] == 0:
            returned.append({'title': link['title'], 'language_code': language_code})
    return returned

def distance_in_km_to_string(distance_in_km):
    if distance_in_km > 3:
        return str(int(distance_in_km)) + " km"
    else:
        return str(int(distance_in_km*1000)) + " m"

def distance_in_km_of_wikidata_object_from_location(coords_given, wikidata_id):
    if wikidata_id == None:
        return None
    location_from_wikidata = wikipedia_connection.get_location_from_wikidata(wikidata_id)
    # recommended by https://stackoverflow.com/a/43211266/4130619
    return geopy.distance.vincenty(coords_given, location_from_wikidata).km

def get_distance_description_between_location_and_wikidata_id(location, wikidata_id):
    if location == (None, None):
        return " <no location data>"
    distance = distance_in_km_of_wikidata_object_from_location(location, wikidata_id)
    if distance == None:
        return " <no location data on wikidata>"
    return ' is ' + distance_in_km_to_string(distance) + " away"

def get_list_of_disambig_fixes(location, element_wikidata_id, forced_refresh):
    #TODO open all pages, merge duplicates using wikidata and list them as currently
    returned = ""
    links = get_list_of_links_from_disambig(element_wikidata_id, forced_refresh)
    if element_wikidata_id == None:
        return "page without wikidata element, unable to load link data. Please, create wikidata element (TODO: explain how it can be done)"
    if links == None:
        return "TODO improve language handling on foreign disambigs"
    for link in links:
        link_wikidata_id = wikipedia_connection.get_wikidata_object_id_from_article(link['language_code'], link['title'])
        distance_description = get_distance_description_between_location_and_wikidata_id(location, link_wikidata_id)
        returned += link['title'] + distance_description + "\n"
    return returned

def get_error_report_if_secondary_wikipedia_tag_should_be_used(wikidata_id):
    # contains ideas based partially on constraints in https://www.wikidata.org/wiki/Property:P625
    class_error = get_error_report_if_type_unlinkable_as_primary(wikidata_id)
    if class_error != None:
        return class_error

    property_error = get_error_report_if_property_indicates_that_it_is_unlinkable_as_primary(wikidata_id)
    if property_error != None:
        return property_error

def get_error_report_if_property_indicates_that_it_is_unlinkable_as_primary(wikidata_id):
    if wikipedia_connection.get_property_from_wikidata(wikidata_id, 'P247') != None:
        return get_should_use_subject_error('a spacecraft', 'name:', wikidata_id)
    if wikipedia_connection.get_property_from_wikidata(wikidata_id, 'P279') != None:
        return get_should_use_subject_error('an uncoordinable generic object', 'name:', wikidata_id)

def get_all_types_describing_wikidata_object(wikidata_id):
    base_type_ids = get_wikidata_type_ids_of_entry(wikidata_id)
    if base_type_ids == None:
        return []
    return get_recursive_all_subclass_of_list(base_type_ids)

def get_recursive_all_subclass_of_list(base_type_ids):
    all_types = []
    for type in base_type_ids:
        all_types += get_recursive_all_subclass_of(type)
    return all_types

def get_error_report_if_type_unlinkable_as_primary(wikidata_id):
    for type_id in get_all_types_describing_wikidata_object(wikidata_id):
        if type_id == 'Q5':
            return get_should_use_subject_error('a human', 'name:', wikidata_id)
        if type_id == 'Q18786396' or type_id == 'Q16521':
            return get_should_use_subject_error('an animal or plant', None, wikidata_id)
        #valid for example for museums, parishes
        #if type_id == 'Q43229':
        #    return get_should_use_subject_error('organization', None)
        if type_id == 'Q1344':
            return get_should_use_subject_error('an opera', None, wikidata_id)
        if type_id == 'Q35127':
            return get_should_use_subject_error('a website', None, wikidata_id)
        if type_id == 'Q1190554':
            return get_should_use_subject_error('an event', None, wikidata_id)
        if type_id == 'Q5398426':
            return get_should_use_subject_error('a television series', None, wikidata_id)
        if type_id == 'Q3026787':
            return get_should_use_subject_error('a saying', None, wikidata_id)
        if type_id == 'Q18534542':
            return get_should_use_subject_error('a restaurant chain', 'brand:', wikidata_id)
        if type_id == 'Q22687':
            return get_should_use_subject_error('a bank', 'brand:', wikidata_id)
        if type_id == 'Q507619':
            return get_should_use_subject_error('a chain store', 'brand:', wikidata_id)
        # appears in constraints of coordinate property in Wikidata but not applicable to OSM
        # pl:ArcelorMittal Poland Oddział w Krakowie may be linked
        #if type_id == 'Q4830453':
        #    return get_should_use_subject_error('a business enterprise', 'brand:', wikidata_id)
        if type_id == 'Q202444':
            return get_should_use_subject_error('a given name', 'name:', wikidata_id)
        if type_id == 'Q21502408':
            return get_should_use_subject_error('a mandatory constraint', None, wikidata_id)
    return None

def get_error_report_if_wikipedia_target_is_of_unusable_type(location, wikidata_id, forced_refresh):
    for type_id in get_all_types_describing_wikidata_object(wikidata_id):
        if type_id == 'Q4167410':
            # TODO note that pageprops may be a better source that should be used
            # it does not require wikidata entry
            # wikidata entry may be wrong
            # https://pl.wikipedia.org/w/api.php?action=query&format=json&prop=pageprops&redirects=&titles=Java%20(ujednoznacznienie)
            list = get_list_of_disambig_fixes(location, wikidata_id, forced_refresh)
            error_message = "link leads to a disambig page - not a proper wikipedia link (according to Wikidata - if target is not a disambig check Wikidata entry whatever it is correct)\n\n" + list
            return ErrorReport(
                error_id = "link to unlinkable article",
                error_message = error_message,
                prerequisite = {'wikidata': wikidata_id},
                )
        if type_id == 'Q13406463':
            error_message = "article linked in wikipedia tag is a list, so it is very unlikely to be correct"
            return ErrorReport(
                error_id = "link to unlinkable article",
                error_message = error_message,
                prerequisite = {'wikidata': wikidata_id},
                )
        if type_id == 'Q20136634':
            error_message = "article linked in wikipedia tag is an overview aerticle, so it is very unlikely to be correct"
            return ErrorReport(
                error_id = "link to unlinkable article",
                error_message = error_message,
                prerequisite = {'wikidata': wikidata_id},
                )

def get_problem_based_on_wikidata(element, language_code, article_name, wikidata_id, forced_refresh):
    if wikidata_id == None:
        return None

    base_type_ids = get_wikidata_type_ids_of_entry(wikidata_id)
    if base_type_ids == None:
        # instance data not present in wikidata
        # not fixable easily as imports from OSM to Wikidata are against rules
        # as OSM data is protected by ODBL, and Wikidata is on CC0 license
        # also, this problem is easy to find on Wikidata itself so it is not useful to report it
        return None
    location = get_location_of_element(element)
    base_type_problem = get_problem_based_on_wikidata_base_types(location, wikidata_id, forced_refresh)
    if base_type_problem != None:
        return base_type_problem

    if args.additional_debug:
        complain_in_stdout_if_wikidata_entry_not_of_known_safe_type(wikidata_id, describe_osm_object(element))

def get_problem_based_on_wikidata_base_types(location, wikidata_id, forced_refresh):
    unusable_wikipedia_article = get_error_report_if_wikipedia_target_is_of_unusable_type(location, wikidata_id, forced_refresh)
    if unusable_wikipedia_article != None:
        return unusable_wikipedia_article

    secondary_tag_error = get_error_report_if_secondary_wikipedia_tag_should_be_used(wikidata_id)
    if secondary_tag_error != None:
        return secondary_tag_error
    return None

def complain_in_stdout_if_wikidata_entry_not_of_known_safe_type(wikidata_id, description_of_source):
    for type_id in get_all_types_describing_wikidata_object(wikidata_id):
        if is_wikidata_type_id_recognised_as_OK(type_id):
            return None

    print("----------------")
    print(wikidata_id)
    for type_id in get_wikidata_type_ids_of_entry(wikidata_id):
        print("------")
        print(description_of_source)
        print("unexpected type " + type_id)
        describe_unexpected_wikidata_type(type_id)

def is_wikidata_type_id_recognised_as_OK(type_id):
    objects_mappable_in_OSM = [
        {'wikidata': 'Q486972', 'label': 'human settlement'},
        {'wikidata': 'Q811979', 'label': 'designed structure'},
        {'wikidata': 'Q46831', 'label': 'mountain range - geographic area containing numerous geologically related mountains'},
        {'wikidata': 'Q11776944', 'label': 'Megaregion'},
        {'wikidata': 'Q31855', 'label': 'instytut badawczy'},
        {'wikidata': 'Q34442', 'label': 'road'},
        {'wikidata': 'Q2143825', 'label': 'walking path path for hiking in a natural environment'},
        {'wikidata': 'Q11634', 'label': 'art of sculpture'},
        {'wikidata': 'Q56061', 'label': 'administrative territorial entity - territorial entity for administration purposes, with or without its own local government'},
        {'wikidata': 'Q473972', 'label': 'protected area'},
        {'wikidata': 'Q4022', 'label': 'river'},
        {'wikidata': 'Q22698', 'label': 'park'},
        {'wikidata': 'Q11446', 'label': 'ship'},
        {'wikidata': 'Q12876', 'label': 'tank'},
        {'wikidata': 'Q57607', 'label': 'christmas market'},
        {'wikidata': 'Q8502', 'label': 'mountain'},
        {'wikidata': 'Q10862618', 'label': 'mountain saddle'},
        {'wikidata': 'Q35509', 'label': 'cave'},
        {'wikidata': 'Q23397', 'label': 'lake'},
        {'wikidata': 'Q39816', 'label': 'valley'},
        {'wikidata': 'Q179700', 'label': 'statue'},
        # Quite generic ones
        {'wikidata': 'Q271669', 'label': 'landform'},
        {'wikidata': 'Q376799', 'label': 'transport infrastructure'},
        {'wikidata': 'Q15324', 'label': 'body of water'},
        {'wikidata': 'Q975783', 'label': 'land estate'},
        {'wikidata': 'Q8205328', 'label': 'equipment (human-made physical object with a useful purpose)'},
        {'wikidata': 'Q618123', 'label': 'geographical object'},
        {'wikidata': 'Q43229', 'label': 'organization'},
    ]
    for mappable_type in objects_mappable_in_OSM:
        if type_id == mappable_type['wikidata']:
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
    if en_docs != None:
        return en_docs
    pl_docs = get_wikidata_description(wikidata_id, 'pl')
    if pl_docs != None:
        return pl_docs
    return("Unexpected type " + wikidata_id + " undocumented format")

def get_wikidata_label(wikidata_id, language):
    if wikidata_id == None:
        return None
    try:
        data = wikipedia_connection.get_data_from_wikidata_by_id(wikidata_id)['entities'][wikidata_id]
        return data['labels']['en']['value']
    except KeyError:
        return None

def get_wikidata_explanation(wikidata_id, language):
    if wikidata_id == None:
        return None
    try:
        data = wikipedia_connection.get_data_from_wikidata_by_id(wikidata_id)['entities'][wikidata_id]
        return data['descriptions'][language]['value']
    except KeyError:
        return None

def get_wikidata_description(wikidata_id, language):
    if wikidata_id == None:
        return None
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

def get_wikidata_type_ids_of_entry(wikidata_id):
    if wikidata_id == None:
        return None
    types = None
    try:
        forced_refresh = False
        wikidata_entry = wikipedia_connection.get_data_from_wikidata_by_id(wikidata_id, forced_refresh)
        wikidata_entry = wikidata_entry['entities']
        object_id = list(wikidata_entry)[0]
        types = wikidata_entry[object_id]['claims']['P31']
    except KeyError:
        return None
    return [type['mainsnak']['datavalue']['value']['id'] for type in types]

# unknown data, known to be completely inside -> not allowed, returns None
# known to be outside or on border -> allowed, returns reason
def why_object_is_allowed_to_have_foreign_language_label(element, wikidata_id):
    if wikidata_id == None:
        return "no wikidata entry exists"

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

def get_interwiki_article_name_by_id(wikidata_id, target_language, forced_refresh):
    if wikidata_id == None:
        return None
    wikidata_entry = wikipedia_connection.get_data_from_wikidata_by_id(wikidata_id, forced_refresh)
    return get_interwiki_article_name_from_wikidata_data(wikidata_entry, target_language)

def get_interwiki_article_name(source_language_code, source_article_name, target_language, forced_refresh):
    wikidata_entry = wikipedia_connection.get_data_from_wikidata(source_language_code, source_article_name, forced_refresh)
    return get_interwiki_article_name_from_wikidata_data(wikidata_entry, target_language)

def get_interwiki_article_name_from_wikidata_data(wikidata_entry, target_language):
    try:
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
    language_code = None
    article_name = None
    if link != None:
        language_code = wikipedia_connection.get_language_code_from_link(link)
        article_name = wikipedia_connection.get_article_name_from_link(link)
    lat, lon = get_location_of_element(element)

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
    parser.add_argument('-expected_language_code', '-l',
                        dest='expected_language_code',
                        type=str,
                        help='expected language code (short form of parameter: -l)')
    parser.add_argument('-file', '-f',
                        dest='file',
                        type=str,
                        help='location of .osm file (short form of parameter: -f')
    parser.add_argument('-flush_cache',
                        dest='flush_cache',
                        help='adding this parameter will trigger flushing cache',
                        action='store_true')
    parser.add_argument('-flush_cache_for_reported_situations',
                        dest='flush_cache_for_reported_situations',
                        help='adding this parameter will trigger flushing cache only for reported situations \
                        (redownloads wikipedia data for cases where errors are reported, \
                        so removes false positives where wikipedia is already fixed)',
                        action='store_true')
    parser.add_argument('-allow_requesting_edits_outside_osm',
                        dest='allow_requesting_edits_outside_osm',
                        help='enables reporting of problems that may require editing wikipedia or wikidata',
                        action='store_true')
    parser.add_argument('-additional_debug',
                        dest='additional_debug',
                        help='additional debug - shows when wikidata types are no recognized, list locations allowed to have a foreign language label',
                        action='store_true')
    parser.add_argument('-allow_false_positives',
                        dest='allow_false_positives',
                        help='enables validator rules that may report false positives',
                        action='store_true')
    args = parser.parse_args()
    return args

def output_message_about_duplication(complaint, wikidata_id, link, entries):
    query = "[out:xml](\n\
            node[wikidata='" + wikidata_id + "];\n\
            way[wikidata=" + wikidata_id + "];\n\
            relation[wikidata=" + wikidata_id + "];\n\
            );\n\
            out meta;>;out meta qt;"
    message = link + complaint + str(entries) + "\n\n\n" + query
    example_element = list(present_wikipedia_links[link].values())[0]
    problem = ErrorReport(
                        error_id = "duplicated link",
                        error_message = message,
                        prerequisite = {'wikidata': wikidata_id},
                        )
    output_element(example_element, problem)

def process_repeated_appearances_for_this_wikidata_id(wikidata_id, link, entries):
    if 'Q4022' in get_all_types_describing_wikidata_object(wikidata_id):
        complaint = " is repeated, should be replaced by wikipedia/wikidata tags on a waterway relation "
        output_message_about_duplication(complaint, wikidata_id, link, entries)

def process_repeated_appearances():
    # TODO share between runs
    # TODO warn about all, not just rivers (what about node + relation duplicates?)
    repeated_wikidata_warned_already = []
    for link in present_wikipedia_links:
        entries = present_wikipedia_links[link].keys()
        if len(entries) == 1:
            continue
        language_code = wikipedia_connection.get_language_code_from_link(link)
        article_name = wikipedia_connection.get_article_name_from_link(link)
        wikidata_id = wikipedia_connection.get_wikidata_object_id_from_article(language_code, article_name)
        if wikidata_id == None:
            continue
        if wikidata_id not in repeated_wikidata_warned_already:
            process_repeated_appearances_for_this_wikidata_id(wikidata_id, link, entries)
            repeated_wikidata_warned_already.append(wikidata_id)

    for link in present_wikidata_links:
        entries = present_wikidata_links[link].keys()
        if len(entries) == 1:
            continue
        if wikidata_id not in repeated_wikidata_warned_already:
            process_repeated_appearances_for_this_wikidata_id(wikidata_id, link, entries)
            repeated_wikidata_warned_already.append(wikidata_id)

def skip_property(property_name):
    known = ['P18','P1566','P31','P646','P421','P910','P94','P131','P373',
    'P625','P17', 'P856', 'P1376', 'P935', 'P1435', 'P2044', 'P4046', 'P1464',
    'P206', 'P41', 'P1200', 'P884', 'P2225', 'P227', 'P30', 'P1792', 'P361',
    'P1343', 'P706', 'P949', 'P242', 'P14', 'P214', 'P197', 'P126', 'P708',
    'P2053', 'P974', 'P1653', 'P268', 'P201', 'P395', 'P571', 'P84', 'P403',
    'P47', 'P2043', 'P138', 'P36', 'P140', 'P356', 'P1889', 'P1082', 'P190',
    'P998', 'P948', 'P159', 'P443', 'P3417']
    if property_name in known:
        return True
    types = get_all_types_describing_wikidata_object(property_name)
    if "Q18608871" in types:
        # Wikidata property for items about people
        return True
    return False

def print_popular_properties():
    limit = 100
    iata_code_property = 'P238'
    if iata_code_property in properties:
        limit = properties[iata_code_property] * 5 + 50
    for property in properties.keys():
        if properties[property] > limit:
            if not skip_property(property):
                print("https://www.wikidata.org/wiki/Property:" + str(property))
    for property in properties.keys():
        if properties[property] > limit:
            if not skip_property(property):
                print("'" + str(property) + "',")

def main():
    wikipedia_connection.set_cache_location(common.get_file_storage_location())
    if not (args.file):
        parser.error('Provide .osm file')
    osm = Data(common.get_file_storage_location() + "/" + args.file)
    osm.iterate_over_data(record_presence)
    if args.flush_cache_for_reported_situations:
        osm.iterate_over_data(validate_wikipedia_link_on_element_and_print_problems_refresh_cache_for_reported)
    else:
        osm.iterate_over_data(validate_wikipedia_link_on_element_and_print_problems)

    process_repeated_appearances()

    #TODO detect wikidata tag matching subject:wikipedia or operator:wikipedia

    print("https://osm.wikidata.link/candidates/relation/2768922 (Kraków)")
    print("https://osm.wikidata.link/candidates/relation/2654452 (powiat krakowski)")
    print("https://osm.wikidata.link/candidates/relation/2907540 (Warszawa)")
    print("https://osm.wikidata.link/filtered/Poland")
    #https://osm.wikidata.link/candidates/relation/2675559 mazury
    #https://osm.wikidata.link/candidates/relation/2675566 mazury
    #https://osm.wikidata.link/candidates/relation/2675509 mazury
    #https://osm.wikidata.link/candidates/relation/2675563 mazury

    #links from buildings to parish are wrong - but from religious admin are OK https://www.wikidata.org/wiki/Q11808149
    # https://wiki.openstreetmap.org/wiki/User_talk:Yurik - wait for answers

    print_popular_properties()

global args #TODO remove global
args = parsed_args()

if __name__ == "__main__":
    main()
