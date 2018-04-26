# coding=utf-8

import argparse
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import common
from osm_iterator.osm_iterator import Data
import popular_wikidata_property_detector
import wikipedia_knowledge
import osm_handling_config.global_config as osm_handling_config
import wikimedia_link_issue_reporter

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

def get_problem_for_given_element_and_record_stats(element, forced_refresh):
    if args.flush_cache:
        forced_refresh = True
    helper_object = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector(
        forced_refresh, args.expected_language_code, get_expected_language_codes(), args.additional_debug,
        args.allow_requesting_edits_outside_osm, args.allow_false_positives)
    problems = helper_object.get_problem_for_given_element(element)
    if problems != None:
        return problems

    present_wikidata_id = element.get_tag_value("wikidata")
    if present_wikidata_id != None:
        record_wikidata_properties_present(present_wikidata_id, property_popularity)

def record_wikidata_properties_present(wikidata_id, property_popularity_counter):
    wikidata = wikimedia_connection.get_data_from_wikidata_by_id(wikidata_id)
    try:
        for property in wikidata['entities'][wikidata_id]['claims']:
            property = str(property)
            property_popularity_counter.record_property_presence(property)
    except KeyError as e:
        print(wikidata_id, " errored with ", e)

# TODO replace args.expected_language_code where applicable
def get_expected_language_codes():
    returned = []
    if args.expected_language_code != None:
        returned.append(args.expected_language_code)
    return returned + wikipedia_knowledge.WikipediaKnowledge.all_wikipedia_language_codes_order_by_importance()

def output_element(element, error_report):
    error_report.bind_to_element(element)
    link = element.get_tag_value("wikipedia")
    language_code = None
    article_name = None
    if link != None:
        language_code = wikimedia_connection.get_language_code_from_link(link)
        article_name = wikimedia_connection.get_article_name_from_link(link)
    position = element.get_coords()

    if position.lat == None or position.lon == None:
        error_report.debug_log = "Location data missing"

    error_report.yaml_output(yaml_report_filepath())

def yaml_report_filepath():
    return common.get_file_storage_location()+"/" + args.file + ".yaml"

def validate_wikipedia_link_on_element_and_print_problems(element):
    problem = get_problem_for_given_element_and_record_stats(element, False)
    if (problem != None):
        output_element(element, problem)

def validate_wikipedia_link_on_element_and_print_problems_refresh_cache_for_reported(element):
    if(get_problem_for_given_element_and_record_stats(element, False) != None):
        get_problem_for_given_element_and_record_stats(element, True)
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
    problem = wikimedia_link_issue_reporter.ErrorReport(
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
    wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())
    if not (args.file):
        parser.error('Provide .osm file')
    osm = Data(common.get_file_storage_location() + "/" + args.file)
    osm.iterate_over_data(record_presence)
    if args.flush_cache_for_reported_situations:
        osm.iterate_over_data(validate_wikipedia_link_on_element_and_print_problems_refresh_cache_for_reported)
    else:
        osm.iterate_over_data(validate_wikipedia_link_on_element_and_print_problems)

    process_repeated_appearances()

    property_popularity.print_popular_properties()

global args #TODO remove global
args = parsed_args()
property_popularity = popular_wikidata_property_detector.PopularWikidataPropertiesDetector()

if __name__ == "__main__":
    main()

# TODO - search for IDEA note
