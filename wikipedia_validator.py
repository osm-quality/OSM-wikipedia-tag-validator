# coding=utf-8

import argparse
import yaml
import re

import wikimedia_connection.wikimedia_connection as wikimedia_connection
import common
from osm_iterator.osm_iterator import Data
import geopy.distance
import popular_wikidata_property_detector
import wikidata_processing
import wikipedia_knowledge

present_wikipedia_links = {}
# dictionary contains entries indexed by wikidata_id
# each entry is dictionary with entries where key is url to OSM object and value is element
present_wikidata_links = {}
# dictionary contains entries indexed by wikidata_id
# each entry is dictionary with entries where key is url to OSM object and value is element
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

# TODO replace args.expected_language_code where applicable
def get_expected_language_codes():
    returned = []
    if args.expected_language_code != None:
        returned.append(args.expected_language_code)
    return returned + wikipedia_knowledge.WikipediaKnowledge.all_wikipedia_language_codes_order_by_importance()

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

    language_code = wikimedia_connection.get_language_code_from_link(link)
    article_name = wikimedia_connection.get_article_name_from_link(link)
    wikidata_id = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name, forced_refresh)

    something_reportable = check_is_wikipedia_link_clearly_malformed(link)
    if something_reportable != None:
        return something_reportable

    something_reportable = check_is_wikipedia_page_existing(language_code, article_name, wikidata_id, forced_refresh)
    if something_reportable != None:
        return something_reportable

    #early to ensure that passing later wikidata_id of article is not going to be confusing
    something_reportable = check_for_wikipedia_wikidata_collision(present_wikidata_id, language_code, article_name, forced_refresh)
    if something_reportable != None:
        return something_reportable

    something_reportable = freely_reorderable_issue_reports(element, language_code, article_name, forced_refresh, wikidata_id, args.expected_language_code)
    if something_reportable != None:
        return something_reportable

    present_wikidata_id = element.get_tag_value("wikidata")
    if present_wikidata_id != None:
        record_wikidata_properties_present(present_wikidata_id, property_popularity)
    return None

def freely_reorderable_issue_reports(element, language_code, article_name, forced_refresh, wikidata_id, expected_language_code):
    #wikipedia tag is not malformed
    #wikipedia and wikidata tags are not conflicting
    present_wikidata_id = element.get_tag_value("wikidata")

    something_reportable = get_problem_based_on_wikidata_and_osm_element(element, wikidata_id, forced_refresh)
    if something_reportable != None:
        return something_reportable

    something_reportable = get_wikipedia_language_issues(element, language_code, article_name, forced_refresh, wikidata_id, expected_language_code)
    if something_reportable != None:
        return something_reportable

    something_reportable = check_is_wikidata_tag_is_misssing(element, present_wikidata_id, wikidata_id)
    if something_reportable != None:
        return something_reportable

    something_reportable = check_is_object_is_existing(present_wikidata_id)
    if something_reportable != None:
        return something_reportable

    something_reportable = add_data_from_wikidata(element)
    if something_reportable != None:
        return something_reportable

    return None

def check_is_wikipedia_link_clearly_malformed(link):
    if is_wikipedia_tag_clearly_broken(link):
        return ErrorReport(
                        error_id = "malformed wikipedia tag",
                        error_message = "malformed wikipedia tag (" + link + ")",
                        prerequisite = {'wikipedia': link},
                        )
    else:
        return None

def check_is_wikidata_tag_is_misssing(element, present_wikidata_id, wikidata_id):
    if present_wikidata_id == None and wikidata_id != None:
        return ErrorReport(
                        error_id = "wikidata tag may be added",
                        error_message = wikidata_id + " may be added as wikidata tag based on wikipedia tag",
                        prerequisite = {'wikipedia': element.get_tag_value("wikipedia"), 'wikidata': None}
                        )
    else:
        return None

def record_wikidata_properties_present(wikidata_id, property_popularity_counter):
    wikidata = wikimedia_connection.get_data_from_wikidata_by_id(wikidata_id)
    for property in wikidata['entities'][wikidata_id]['claims']:
        property = str(property)
        property_popularity_counter.record_property_presence(property)

def check_is_wikipedia_page_existing(language_code, article_name, wikidata_id, forced_refresh):
    page_according_to_wikidata = wikimedia_connection.get_interwiki_article_name(language_code, article_name, language_code, forced_refresh)
    if page_according_to_wikidata != None:
        # assume that wikidata is correct to save downloading page
        return None
    page = wikimedia_connection.get_wikipedia_page(language_code, article_name, forced_refresh)
    if page == None:
        return report_failed_wikipedia_page_link(language_code, article_name, wikidata_id, forced_refresh)

def get_best_interwiki_link_by_id(wikidata_id, forced_refresh):
    for potential_language_code in get_expected_language_codes():
        potential_article_name = wikimedia_connection.get_interwiki_article_name_by_id(wikidata_id, potential_language_code, forced_refresh)
        if potential_article_name != None:
            return potential_language_code + ':' + potential_article_name
    return None

def report_failed_wikipedia_page_link(language_code, article_name, wikidata_id, forced_refresh):
    message = "Wikipedia article linked from OSM object using wikipedia tag is missing. Typically article was moved and wikipedia tag should be edited to point to the new one. Sometimes article was deleted and no longer exists so wikipedia tag should be deleted."
    proposed_new_target = get_best_interwiki_link_by_id(wikidata_id, forced_refresh)
    if proposed_new_target != None:
        message += " wikidata tag present on element points to an existing article"
    return ErrorReport(
                error_id = "wikipedia tag links to 404",
                error_message = message,
                prerequisite = {'wikipedia': language_code+":"+article_name},
                desired_wikipedia_target = proposed_new_target,
                )

def wikidata_data_quality_warning():
    return "REMEMBER TO VERIFY! WIKIDATA QUALITY MAY BE POOR!"

def check_is_object_is_existing(present_wikidata_id):
    if present_wikidata_id == None:
        return None
    no_longer_existing = wikimedia_connection.get_property_from_wikidata(present_wikidata_id, 'P576')
    if no_longer_existing != None:
        return ErrorReport(
                        error_id = "no longer existing object",
                        error_message ="Wikidata claims that this object no longer exists. Historical, no longer existing object must not be mapped in OSM - so it means that it is mistake or OSM is outdated." + " " + wikidata_data_quality_warning(),
                        prerequisite = {'wikidata': present_wikidata_id}
                        )

def tag_from_wikidata(present_wikidata_id, wikidata_property):
    from_wikidata = wikimedia_connection.get_property_from_wikidata(present_wikidata_id, wikidata_property)
    if from_wikidata == None:
        return None
    return wikidata_processing.decapsulate_wikidata_value(from_wikidata)

def generate_error_report_for_tag_from_wikidata(from_wikidata, present_wikidata_id, osm_key, element, id_suffix="", message_suffix = ""):
    if element.get_tag_value(osm_key) == None:
            return ErrorReport(
                        error_id = "tag may be added based on wikidata" + id_suffix,
                        error_message = str(from_wikidata) + " may be added as " + osm_key + " tag based on wikidata entry" + message_suffix + " " + wikidata_data_quality_warning(),
                        prerequisite = {'wikidata': present_wikidata_id, osm_key: None}
                        )
    elif element.get_tag_value(osm_key) != from_wikidata:
            if not args.allow_requesting_edits_outside_osm:
                # typically Wikidata is wrong, not OSM
                return None
            return ErrorReport(
                        error_id = "tag conflict with wikidata value" + id_suffix,
                        error_message = str(from_wikidata) + " conflicts with " + element.get_tag_value(osm_key) + " for " + osm_key + " tag based on wikidata entry - note that OSM value may be OK and Wikidata entry is wrong, in that case one may either ignore this error or fix Wikidata entry" + message_suffix + " " + wikidata_data_quality_warning(),
                        prerequisite = {'wikidata': present_wikidata_id, osm_key: element.get_tag_value(osm_key)}
                        )

def tag_from_wikidata_error_report(present_wikidata_id, osm_key, wikidata_property, element, id_suffix="", message_suffix = ""):
    from_wikidata = tag_from_wikidata(present_wikidata_id, wikidata_property)
    if from_wikidata == None:
        return None
    return generate_error_report_for_tag_from_wikidata(from_wikidata, present_wikidata_id, osm_key, element, id_suffix, message_suffix)

def teryt_code_from_wikidata(element):
    present_wikidata_id = element.get_tag_value("wikidata")
    from_wikidata = tag_from_wikidata(present_wikidata_id, 'P4046')
    if from_wikidata == None:
        return None
    from_wikidata = from_wikidata.replace("{{r|Dz.U. 29/2013}}", "") # popular Wikidata problem
    return generate_error_report_for_tag_from_wikidata(from_wikidata, present_wikidata_id, 'teryt:simc', element, ' - teryt', ' do weryfikacji przydaje się \nhttp://eteryt.stat.gov.pl/eTeryt/rejestr_teryt/udostepnianie_danych/baza_teryt/uzytkownicy_indywidualni/wyszukiwanie/wyszukiwanie.aspx?contrast=default\n ')

def add_name_from_wikidata(element):
    present_wikidata_id = element.get_tag_value("wikidata")
    # IDEA - skip former official names ( https://www.wikidata.org/wiki/Q387396 ), skip official_name equal to name

    official_name_wikidata = tag_from_wikidata(present_wikidata_id, 'P1448')
    name_wikidata = tag_from_wikidata(present_wikidata_id, 'P1705')
    keys_with_names_from_OSM = ["name", "official_name", "loc_name"]
    names_in_wikidata = []
    if official_name_wikidata != None:
        names_in_wikidata.append(official_name_wikidata['text'])
    if name_wikidata != None:
        names_in_wikidata.append(name_wikidata['text'])

    names_in_OSM = []
    prerequisite = {'wikidata': present_wikidata_id}
    for key in keys_with_names_from_OSM:
        if element.get_tag_value(key) != None:
            names_in_OSM.append(element.get_tag_value(key))
            prerequisite[key] = element.get_tag_value(key)
    for_import = list(set(names_in_wikidata) - set(names_in_OSM))
    if for_import == []:
        return None
    return ErrorReport(
                error_id = "tag may be added based on wikidata - testing",
                error_message = str(for_import) + " may be added as names (name, loc_name, offivial_name tags...) based on wikidata entry - note that even slight variations are useful " + wikidata_data_quality_warning(),
                prerequisite = prerequisite,
                )

def get_elevation_data_from_wikidata_report(element):
    present_wikidata_id = element.get_tag_value("wikidata")
    ele_from_tag = element.get_tag_value('ele')
    from_wikidata = tag_from_wikidata(present_wikidata_id, 'P2044')
    if from_wikidata == None:
        return None
    unit_from_wikidata = from_wikidata['unit']
    amount_from_wikidata = from_wikidata['amount']

    try:
        amount_from_wikidata = float(amount_from_wikidata)
    except ValueError:
        print("failed conversion to float: " + from_wikidata['amount'] + " in " + present_wikidata_id + " for " + element.get_link())
        return None

    if unit_from_wikidata == 'http://www.wikidata.org/entity/Q3710':
        # feets
        unit_from_wikidata = "http://www.wikidata.org/entity/Q11573"
        amount_from_wikidata = 0.3048006 * amount_from_wikidata

    if unit_from_wikidata != "http://www.wikidata.org/entity/Q11573":
        print("unexpected height unit in Wikidata: " + unit_from_wikidata + " in " + present_wikidata_id + " for " + element.get_link())
        return None

    if ele_from_tag != None:
        try:
            ele_from_tag = float(ele_from_tag)
        except ValueError:
            print("failed conversion to float: ele=" +element.get_tag_value('ele') + " in " + element.get_link())
            return None

    if ele_from_tag != None:
        if amount_from_wikidata != ele_from_tag:
            if(abs(amount_from_wikidata - ele_from_tag) > 1):
                if not args.allow_requesting_edits_outside_osm:
                    return None
                if not args.allow_false_positives:
                    return None
                return ErrorReport(
                    error_id = "tag conflict with wikidata value - testing",
                    error_message = "elevation in OSM (" + str(ele_from_tag) + ") vs elevation in Wikidata (" + str(amount_from_wikidata) + ")" + " " + wikidata_data_quality_warning(),
                    prerequisite = {'wikidata': present_wikidata_id, 'ele': element.get_tag_value('ele')}
                    )

    if element.get_tag_value('ele') == None:
        if element.get_tag_value('natural') == 'peak':
            return ErrorReport(
                        error_id = "tag may be added based on wikidata - testing",
                        error_message = str(amount_from_wikidata) + " may be added as ele tag based on wikidata entry" + " " + wikidata_data_quality_warning(),
                        prerequisite = {'wikidata': present_wikidata_id, 'ele': None}
                        )

def guess_value_of_historic_tag_from_element(element):
    if element.get_tag_value('building') == "church":
        return "church"
    if element.get_tag_value('amenity') == 'place_of_worship' and element.get_tag_value('religion') == 'christian':
        return "church"
    if element.get_tag_value('man_made') == "lighthouse":
        return "lighthouse"
    if element.get_tag_value('building') == "yes":
        return "building"
    if element.get_tag_value('leisure') == "park":
        return "park"
    return None

def get_heritage_data_from_wikidata_report(element):
    if element.get_tag_value("boundary") == "national_park":
        # so are tagged on wikidata as P1435
        return None

    present_wikidata_id = element.get_tag_value("wikidata")
    from_wikidata = tag_from_wikidata(present_wikidata_id, 'P1435')
    if from_wikidata == None:
        return None
    if element.get_tag_value('historic') == None and element.get_tag_value('heritage') == None:
        specific_tag = guess_value_of_historic_tag_from_element(element)
        if specific_tag != None:
            specific_tag = "historic="+specific_tag
        else:
            specific_tag = "historic"
        return ErrorReport(
            error_id = "tag may be added based on wikidata - " + specific_tag,
            error_message = "without heritage tag, without " + specific_tag + " tag (see http://wiki.openstreetmap.org/wiki/Key:historic ) and has heritage designation according to wikidata " + wikidata_data_quality_warning(),
            prerequisite = {'wikidata': present_wikidata_id, 'historic': None, 'heritage': None}
            )
    return None

def website_from_wikidata_error_report(element):
    present_wikidata_id = element.get_tag_value("wikidata")
    website = tag_from_wikidata_error_report(present_wikidata_id, 'website', 'P856', element, " - website")
    if website != None and website.error_message.find('web.archive.org') == -1:
        if element.get_tag_value('contact:website') == None:
            return website

def add_data_from_wikidata(element):
    present_wikidata_id = element.get_tag_value("wikidata")
    if present_wikidata_id == None:
        return None
    if len(present_wikidata_links[present_wikidata_id].keys()) != 1:
        return None
    tag = add_name_from_wikidata(element)
    if tag != None:
        return None
    tag = teryt_code_from_wikidata(element)
    if tag != None:
        return None
    iata = tag_from_wikidata_error_report(present_wikidata_id, 'iata', 'P238', element)
    if iata != None:
        return iata
    # importing directly from GUS is probably a better idea
    #population = tag_from_wikidata_error_report(present_wikidata_id, 'population', 'P1082', element, " - testing")
    #if population != None:
    #    return population
    tag = tag_from_wikidata_error_report(present_wikidata_id, 'postal_code', 'P281', element, ' - postal_code')
    if tag != None:
        return tag

    tag = website_from_wikidata_error_report(element)
    if tag != None:
        return tag
    #moving P138 to name:wikidata tag makes no sense, just use wikidata instead
    #IDEA
    #handle multiple operators - https://www.wikidata.org/wiki/Q429672
    #handle conversion from wikidata_id to text
    #operator = tag_from_wikidata_error_report(present_wikidata_id, 'operator', 'P126', element, " - testing")
    #if operator != None:
    #    return operator
    #also, P127 is for owner

    tag = get_elevation_data_from_wikidata_report(element)
    if tag != None:
        return tag

    tag = get_heritage_data_from_wikidata_report(element)
    if tag != None:
        return tag

    #IDEA  P1653 is also teryt property
    #P395 license plate code
    #geometry - waterway structure graph (inflow [P974], outflow [P403], tributary [P974]) - see http://tinyurl.com/y9h7ym7g
    #P571 - should be easy to process - lakes on river
    #P814 protected area
    #P2043 length
    #P36 capital of something
    #P140 religion
    #P150 - list of subareas
    #P2046 - area of feature
    #P402 - id of OSM relation
    #P4080 - house count
    #P1427 - start point (for routes)
    #P1064 track gauge
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
        if link == None:
            conflict = True
            continue
        language_code = wikimedia_connection.get_language_code_from_link(link)
        article_name = wikimedia_connection.get_article_name_from_link(link)
        id_from_link = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name, forced_refresh)
        if wikidata_id != id_from_link:
            conflict = True

    if conflict:
        return ErrorReport(
            error_id = "wikipedia tag in outdated form and wikidata - mismatch",
            error_message = "wikipedia tag in outdated form (" + str(wikipedia_type_keys) + "), without wikipedia but with wikidata tag present. Mismatch happened and requires human judgment to solve.",
            prerequisite = prerequisite,
            )
    else:
        return ErrorReport(
            error_id = "wikipedia tag from wikipedia tag in an outdated form and wikidata",
            error_message = "wikipedia tag in outdated form (" + str(wikipedia_type_keys) + "), without wikipedia but with wikidata tag present",
            prerequisite = prerequisite,
            desired_wikipedia_target = get_best_interwiki_link_by_id(wikidata_id, forced_refresh),
            )


def attempt_to_locate_wikipedia_tag_using_wikidata_id(present_wikidata_id, forced_refresh):
    location = (None, None)
    description = "object with wikidata=" + present_wikidata_id
    problem_indicated_by_wikidata = get_problem_based_on_wikidata(present_wikidata_id, description, location, forced_refresh)
    if problem_indicated_by_wikidata:
        return problem_indicated_by_wikidata

    link = get_best_interwiki_link_by_id(present_wikidata_id, forced_refresh)
    if link == None:
        return None
    language_code = wikimedia_connection.get_language_code_from_link(link)
    if language_code in get_expected_language_codes():
        return ErrorReport(
            error_id = "wikipedia from wikidata tag",
            error_message = "without wikipedia tag, without wikipedia:language tags, with wikidata tag present that provides article, article language is not surprising",
            desired_wikipedia_target = link,
            prerequisite = {'wikipedia': None, 'wikidata': present_wikidata_id},
            )
    else:
        return ErrorReport(
            error_id = "wikipedia from wikidata tag, unexpected language",
            error_message = "without wikipedia tag, without wikipedia:language tags, with wikidata tag present that provides article",
            desired_wikipedia_target = link,
            prerequisite = {'wikipedia': None, 'wikidata': present_wikidata_id},
            )

def attempt_to_locate_wikipedia_tag_using_old_style_wikipedia_keys(element, wikipedia_type_keys, forced_refresh):
    prerequisite = {'wikipedia': None, 'wikidata': None}
    links = wikipedia_candidates_based_on_old_style_wikipedia_keys(element, wikipedia_type_keys, forced_refresh)
    for key in wikipedia_type_keys:
        prerequisite[key] = element.get_tag_value(key)
    if len(links) != 1 or None in links:
        return ErrorReport(
            error_id = "wikipedia from wikipedia tag in outdated form - mismatch",
            error_message = "wikipedia tag in outdated form (" + str(wikipedia_type_keys) + "), without wikipedia tag, without wikidata tag, human judgement required as algorithm failed to find certain match",
            prerequisite = prerequisite,
            )
    wikipedia_link = links[0]
    lang = wikimedia_connection.get_language_code_from_link(wikipedia_link)
    article = wikimedia_connection.get_article_name_from_link(wikipedia_link)
    wikidata_id = wikimedia_connection.get_wikidata_object_id_from_article(lang, article)
    # if wikidata_id is None - some checks will not be done
    # it is considered acceptable as it will not introduce new error in OSM
    # though it skips situation where human maybe would notice it
    description = "object with " + str(wikipedia_type_keys)
    location = (None, None)
    problem_indicated_by_wikidata = get_problem_based_on_wikidata(wikidata_id, description, location, forced_refresh)
    if problem_indicated_by_wikidata:
        return problem_indicated_by_wikidata
    return ErrorReport(
        error_id = "wikipedia tag from wikipedia tag in an outdated form",
        error_message = "wikipedia tag in outdated form (" + str(wikipedia_type_keys) + "), without wikipedia tag, without wikidata tag",
        desired_wikipedia_target = wikipedia_link,
        prerequisite = prerequisite,
        )

def wikipedia_candidates_based_on_old_style_wikipedia_keys(element, wikipedia_type_keys, forced_refresh):
    links = []
    for key in wikipedia_type_keys:
        language_code = wikimedia_connection.get_text_after_first_colon(key)
        article_name = element.get_tag_value(key)

        wikidata_id = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name)
        if wikidata_id == None:
            links.append(language_code + ":" + article_name)
            continue

        link = get_best_interwiki_link_by_id(wikidata_id, forced_refresh)
        if link == None:
            links.append(language_code + ":" + article_name)
            continue

        links.append(link)
    return list(set(links))

def get_wikidata_id_after_redirect(wikidata_id):
    return wikimedia_connection.get_data_from_wikidata_by_id(wikidata_id)['entities'][wikidata_id]['id']

def get_article_name_after_redirect(language_code, article_name):
    return wikimedia_connection.get_from_wikipedia_api(language_code, "", article_name)['title']

def check_for_wikipedia_wikidata_collision(present_wikidata_id, language_code, article_name, forced_refresh):
    if present_wikidata_id == None:
        return None

    article_name_with_section_stripped = article_name
    if article_name.find("#") != -1:
        article_name_with_section_stripped = re.match('([^:]*)#(.*)', article_name).group(1)

    wikidata_id_from_article = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name_with_section_stripped, forced_refresh)
    if present_wikidata_id == wikidata_id_from_article:
        return None

    base_message = "wikidata and wikipedia tags link to a different objects"
    message = base_message + ", because wikidata tag points to a redirect that should be followed (" + compare_wikidata_ids(present_wikidata_id, wikidata_id_from_article) +")"
    maybe_redirected_wikidata_id = get_wikidata_id_after_redirect(present_wikidata_id)
    if maybe_redirected_wikidata_id != present_wikidata_id:
        if maybe_redirected_wikidata_id == wikidata_id_from_article:
            return ErrorReport(
                error_id = "wikipedia wikidata mismatch - follow wikidata redirect",
                error_message = message,
                prerequisite = {'wikidata': present_wikidata_id, 'wikipedia': language_code+":"+article_name},
                )

    title_after_possible_redirects = get_article_name_after_redirect(language_code, article_name)
    is_article_redirected = (article_name != title_after_possible_redirects and article_name.find("#") == -1)
    if is_article_redirected:
        wikidata_id_from_redirect = wikimedia_connection.get_wikidata_object_id_from_article(language_code, title_after_possible_redirects, forced_refresh)
        if present_wikidata_id == wikidata_id_from_redirect:
            message = base_message + ", because wikidata tag points to a redirect that should be followed (" + compare_wikidata_ids(present_wikidata_id, wikidata_id_from_article) +")"
            new_wikipedia_link = language_code+":"+title_after_possible_redirects
            return ErrorReport(
                error_id = "wikipedia wikidata mismatch - follow wikipedia redirect",
                error_message = message,
                desired_wikipedia_target = new_wikipedia_link,
                prerequisite = {'wikidata': present_wikidata_id, 'wikipedia': language_code+":"+article_name},
                )
    message = base_message + " (" + compare_wikidata_ids(present_wikidata_id, wikidata_id_from_article) +" wikidata from article)"
    if maybe_redirected_wikidata_id != present_wikidata_id:
        message += " Note that this OSM object has wikidata tag links a redirect (" + present_wikidata_id  + " to " + maybe_redirected_wikidata_id + ")."
    if is_article_redirected:
        message += " Note that this OSM object has wikipedia tag that links redirect ('" + article_name  + "' to '" + title_after_possible_redirects + "')."
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
    language_code = wikimedia_connection.get_language_code_from_link(link)
    if language_code is None:
        return True
    if language_code.__len__() > 3:
        return True
    if re.search("^[a-z]+\Z",language_code) == None:
        return True

def get_wikipedia_language_issues(element, language_code, article_name, forced_refresh, wikidata_id, expected_language_code):
    # complains when Wikipedia page is not in the preferred language,
    # in cases when it is possible
    if expected_language_code is None:
        return None
    if expected_language_code == language_code:
        return None
    prerequisite = {'wikipedia': language_code+":"+article_name}
    reason = why_object_is_allowed_to_have_foreign_language_label(element, wikidata_id, expected_language_code)
    if reason != None:
        if args.additional_debug:
            print(describe_osm_object(element) + " is allowed to have foreign wikipedia link, because " + reason)
        return None
    correct_article = wikimedia_connection.get_interwiki_article_name(language_code, article_name, expected_language_code, forced_refresh)
    if correct_article != None:
        error_message = "wikipedia page in unexpected language - " + expected_language_code + " was expected:"
        good_link = expected_language_code + ":" + correct_article
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
        error_message = "wikipedia page in unexpected language - " + expected_language_code + " was expected, no page in that language was found:"
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
    ", so it is very unlikely to be correct \n\
    subject:wikipedia=* " + special_prefix_text + " tag would be probably better \
    (see https://wiki.openstreetmap.org/wiki/Key:wikipedia#Secondary_Wikipedia_links ) \n\
    in case of change remember to remove wikidata tag if it is present \n\
    object categorised by Wikidata - wrong classification may be caused by wrong data on Wikidata"
    return message

def get_should_use_subject_error(type, special_prefix, wikidata_id):
    return ErrorReport(
        error_id = "should use a secondary wikipedia tag",
        error_message = should_use_subject_message(type, special_prefix),
        prerequisite = {'wikidata': wikidata_id},
        )

def get_list_of_links_from_disambig(wikidata_id, forced_refresh):
    link = get_best_interwiki_link_by_id(wikidata_id, forced_refresh)
    if link == None:
        print("ops, no language code matched for " + wikidata_id)
        return []
    article_name = wikimedia_connection.get_article_name_from_link(link)
    language_code = wikimedia_connection.get_language_code_from_link(link)
    links_from_disambig_page = wikimedia_connection.get_from_wikipedia_api(language_code, "&prop=links", article_name)['links']
    returned = []
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
    location_from_wikidata = wikimedia_connection.get_location_from_wikidata(wikidata_id)
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
        link_wikidata_id = wikimedia_connection.get_wikidata_object_id_from_article(link['language_code'], link['title'])
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
    if wikimedia_connection.get_property_from_wikidata(wikidata_id, 'P247') != None:
        return get_should_use_subject_error('a spacecraft', 'name:', wikidata_id)
    if wikimedia_connection.get_property_from_wikidata(wikidata_id, 'P279') != None:
        return get_should_use_subject_error('an uncoordinable generic object', 'name:', wikidata_id)

def get_error_report_if_type_unlinkable_as_primary(wikidata_id):
    for type_id in wikidata_processing.get_all_types_describing_wikidata_object(wikidata_id):
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
    for type_id in wikidata_processing.get_all_types_describing_wikidata_object(wikidata_id):
        if type_id == 'Q4167410':
            # TODO note that pageprops may be a better source that should be used
            # it does not require wikidata entry
            # wikidata entry may be wrong
            # https://pl.wikipedia.org/w/api.php?action=query&format=json&prop=pageprops&redirects=&titles=Java%20(ujednoznacznienie)
            list = get_list_of_disambig_fixes(location, wikidata_id, forced_refresh)
            error_message = "link leads to a disambig page - not a proper wikipedia link (according to Wikidata - if target is not a disambig check Wikidata entry whether it is correct)\n\n" + list
            return ErrorReport(
                error_id = "link to an unlinkable article",
                error_message = error_message,
                prerequisite = {'wikidata': wikidata_id},
                )
        if type_id == 'Q13406463':
            error_message = "article linked in wikipedia tag is a list, so it is very unlikely to be correct"
            return ErrorReport(
                error_id = "link to an unlinkable article",
                error_message = error_message,
                prerequisite = {'wikidata': wikidata_id},
                )
        if type_id == 'Q20136634':
            error_message = "article linked in wikipedia tag is an overview article, so it is very unlikely to be correct"
            return ErrorReport(
                error_id = "link to an unlinkable article",
                error_message = error_message,
                prerequisite = {'wikidata': wikidata_id},
                )

def get_problem_based_on_wikidata_and_osm_element(element, wikidata_id, forced_refresh):
    if wikidata_id == None:
        # instance data not present in wikidata
        # not fixable easily as imports from OSM to Wikidata are against rules
        # as OSM data is protected by ODBL, and Wikidata is on CC0 license
        # also, this problem is easy to find on Wikidata itself so it is not useful to report it
        return None

    description = describe_osm_object(element)
    location = get_location_of_element(element)
    return get_problem_based_on_wikidata(wikidata_id, description, location, forced_refresh)

def get_problem_based_on_wikidata(wikidata_id, description, location, forced_refresh):
    return get_problem_based_on_base_types(wikidata_id, description, location, forced_refresh)

def get_problem_based_on_base_types(wikidata_id, description, location, forced_refresh):
    base_type_ids = wikidata_processing.get_wikidata_type_ids_of_entry(wikidata_id)
    if base_type_ids == None:
        return None

    base_type_problem = get_problem_based_on_wikidata_base_types(location, wikidata_id, forced_refresh)
    if base_type_problem != None:
        return base_type_problem

    if args.additional_debug:
        complain_in_stdout_if_wikidata_entry_not_of_known_safe_type(wikidata_id, description)


def get_problem_based_on_wikidata_base_types(location, wikidata_id, forced_refresh):
    unusable_wikipedia_article = get_error_report_if_wikipedia_target_is_of_unusable_type(location, wikidata_id, forced_refresh)
    if unusable_wikipedia_article != None:
        return unusable_wikipedia_article

    secondary_tag_error = get_error_report_if_secondary_wikipedia_tag_should_be_used(wikidata_id)
    if secondary_tag_error != None:
        return secondary_tag_error

    secondary_tag_error = headquaters_location_indicate_invalid_connection(location, wikidata_id)
    if secondary_tag_error != None:
        return secondary_tag_error

def get_location_of_this_headquaters(headquarters):
    try:
        position = headquarters['qualifiers']['P625'][0]['datavalue']['value']
        position = (position['latitude'], position['longitude'])
        return position
    except KeyError:
        pass
    try:
        id_of_location = headquarters['mainsnak']['datavalue']['value']['id']
        return wikimedia_connection.get_location_from_wikidata(id_of_location)
    except KeyError:
        pass
    return (None, None)

def headquaters_location_indicate_invalid_connection(location, wikidata_id):
    if location == (None, None):
        return None
    headquarters_location_data = wikimedia_connection.get_property_from_wikidata(wikidata_id, 'P159')
    if headquarters_location_data == None:
        return None
    for option in headquarters_location_data:
        location_from_wikidata = get_location_of_this_headquaters(option)
        if location_from_wikidata != (None, None):
            if geopy.distance.vincenty(location, location_from_wikidata).km > 20:
                return get_should_use_subject_error('a company that is not linkable from a single location', 'brand:', wikidata_id)

    return None

def complain_in_stdout_if_wikidata_entry_not_of_known_safe_type(wikidata_id, description_of_source):
    for type_id in wikidata_processing.get_all_types_describing_wikidata_object(wikidata_id):
        if is_wikidata_type_id_recognised_as_OK(type_id):
            return None
    wikidata_processing.dump_base_types_of_object_in_stdout(wikidata_id, description_of_source)


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

def wikidata_ids_of_countries_with_language(language_code):
    if language_code == "pl":
        return ['Q36']
    if language_code == "de":
        return ['Q183']
    if language_code == "cz":
        return ['Q213']
    if language_code == "en":
        new_zealand = 'Q664'
        usa = 'Q30'
        uk = 'Q145'
        australia = 'Q408'
        canada = 'Q16'
        ireland = 'Q22890'
        # IDEA - add other areas from https://en.wikipedia.org/wiki/English_language
        return [uk, usa, new_zealand, australia, canada, ireland]
    assert False, "language code <" + language_code + "> without hardcoded list of matching countries"

# unknown data, known to be completely inside -> not allowed, returns None
# known to be outside or on border -> allowed, returns reason
def why_object_is_allowed_to_have_foreign_language_label(element, wikidata_id, expected_language_code):
    if wikidata_id == None:
        return "no wikidata entry exists"

    if expected_language_code == None:
        return "no expected language is defined"

    country_ids_where_expected_language_will_be_enforced = wikidata_ids_of_countries_with_language(expected_language_code)

    countries = get_current_countries_by_id(wikidata_id)
    if countries == None:
        # TODO locate based on coordinates...
        return None
    for country_id in countries:
        if country_id in country_ids_where_expected_language_will_be_enforced:
            continue
        country_name = wikidata_processing.get_wikidata_label(country_id, 'en')
        if country_name == None:
            return "it is at least partially in country without known name on Wikidata (country_id=" + country_id + ")"
        if country_id == 'Q7318':
            print(describe_osm_object(element) + " is tagged on wikidata as location in no longer existing " + country_name)
            return None
        return "it is at least partially in " + country_name
    return None

def get_current_countries_by_id(wikidata_id):
    countries = wikimedia_connection.get_property_from_wikidata(wikidata_id, 'P17')
    if countries == None:
        return None
    returned = []
    for country in countries:
        country_id = country['mainsnak']['datavalue']['value']['id']
        # we need to check whether locations still belongs to a given country
        # it is necessary to avoid gems like
        # "Płock is allowed to have foreign wikipedia link, because it is at least partially in Nazi Germany"
        # P582 indicates the time an item ceases to exist or a statement stops being valid
        try:
            country['qualifiers']['P582']
        except KeyError:
                #P582 is missing, therefore it is not a statement aplying to the past
                returned.append(country_id)
    return returned

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

class ErrorReport:
    def __init__(self, error_message=None, desired_wikipedia_target=None, debug_log=None, error_id=None, prerequisite=None):
        self.error_id = error_id
        self.error_message = error_message
        self.debug_log = debug_log
        self.current_wikipedia_target = None
        self.desired_wikipedia_target = desired_wikipedia_target
        self.prerequisite = prerequisite

    def bind_to_element(self, element):
        self.current_wikipedia_target = element.get_tag_value("wikipedia") # TODO - save all tags #TODO - how to handle multiple?
        self.osm_object_url = element.get_link()
        self.location = get_location_of_element(element)

    def yaml_output(self, filepath):
        data = dict(
            error_id = self.error_id,
            error_message = self.error_message,
            debug_log = self.debug_log,
            osm_object_url = self.osm_object_url,
            current_wikipedia_target = self.current_wikipedia_target, #TODO - make it generic
            desired_wikipedia_target = self.desired_wikipedia_target, #TODO - make it generic
            prerequisite = self.prerequisite,
            location = self.location,
        )
        with open(filepath, 'a') as outfile:
            yaml.dump([data], outfile, default_flow_style=False)

def describe_osm_object(element):
    name = element.get_tag_value("name")
    if name == None:
        name = ""
    return name + " " + element.get_link()

def output_element(element, error_report):
    error_report.bind_to_element(element)
    link = element.get_tag_value("wikipedia")
    language_code = None
    article_name = None
    if link != None:
        language_code = wikimedia_connection.get_language_code_from_link(link)
        article_name = wikimedia_connection.get_article_name_from_link(link)
    lat, lon = get_location_of_element(element)

    if (lat, lon) == (None, None):
        error_report.debug_log = "Location data missing"

    error_report.yaml_output(yaml_report_filepath())

def yaml_report_filepath():
    return common.get_file_storage_location()+"/" + args.file + ".yaml"

def get_location_of_element(element):
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


def output_message_about_duplication_of_wikidata_id(example_element, wikidata_id, complaint, osm_links_of_affected, id_suffix=""):
    query = "[out:xml](\n\
            node[wikidata='" + wikidata_id + "];\n\
            way[wikidata=" + wikidata_id + "];\n\
            relation[wikidata=" + wikidata_id + "];\n\
            );\n\
            out meta;>;out meta qt;"
    message = wikidata_id + complaint + str(osm_links_of_affected) + "\n\n\n" + query
    problem = ErrorReport(
                        error_id = "duplicated link" + id_suffix,
                        error_message = message,
                        prerequisite = {'wikidata': wikidata_id},
                        )
    output_element(example_element, problem)

def process_repeated_appearances_for_this_wikidata_id(wikidata_id, entries):
    example_element = list(entries.values())[0]
    complaint = None
    category = None
    if example_element.get_tag_value('waterway') != None:
        complaint = " is repeated, should be replaced by wikipedia/wikidata tags on a waterway relation "
        category = " - waterway"
    elif example_element.get_tag_value('highway') != None and example_element.get_tag_value('area') == None:
        return # road may be tagged multiple times and it is OK
    elif len(entries) > 2:
        is_about_place = False
        for element in list(entries.values()):
            if element.get_tag_value("place") != None:
                is_about_place = True
        if is_about_place:
            if len(entries) <= 10:
                # place is commonly duplicated on areas and nodes
                # sometimes there are even multiple relations for the same are
                # for example city and county having the same area
                return None
            complaint = " is repeated, it probably means that some wikidata/wikipedia tags are incorrect or object is duplicated "
            category = " - place"
        else:
            complaint = " is repeated, it probably means that some wikidata/wikipedia tags are incorrect or object is duplicated "
            category = " - generic"
    else:
        return
    output_message_about_duplication_of_wikidata_id(example_element, wikidata_id, complaint, list(entries.keys()), category)

def process_repeated_appearances():
    # TODO share between runs
    repeated_wikidata_warned_already = []
    for wikipedia_link in present_wikipedia_links:
        pass # IDEA - consider complaining

    for wikidata_id in present_wikidata_links:
        if len(present_wikidata_links[wikidata_id].keys()) == 1:
            continue
        if wikidata_id not in repeated_wikidata_warned_already:
            process_repeated_appearances_for_this_wikidata_id(wikidata_id, present_wikidata_links[wikidata_id])
            repeated_wikidata_warned_already.append(wikidata_id)

def main():
    wikimedia_connection.set_cache_location(common.get_wikimedia_connection_cache_location())
    if not (args.file):
        parser.error('Provide .osm file')
    osm = Data(common.get_file_storage_location() + "/" + args.file)
    osm.iterate_over_data(record_presence)
    if args.flush_cache_for_reported_situations:
        osm.iterate_over_data(validate_wikipedia_link_on_element_and_print_problems_refresh_cache_for_reported)
    else:
        osm.iterate_over_data(validate_wikipedia_link_on_element_and_print_problems)

    process_repeated_appearances()

    # idea links from buildings to parish are wrong - but from religious admin are OK https://www.wikidata.org/wiki/Q11808149

    property_popularity.print_popular_properties()

global args #TODO remove global
args = parsed_args()
property_popularity = popular_wikidata_property_detector.PopularWikidataPropertiesDetector()

if __name__ == "__main__":
    main()

# TODO - search for IDEA note
# IDEA detect wikidata tag matching subject:wikipedia or operator:wikipedia

# IDEA import name:pl - for example for https://www.wikidata.org/wiki/Q1952
# IDEA make maproulette and post on https://forum.openstreetmap.org/viewtopic.php?id=59430
