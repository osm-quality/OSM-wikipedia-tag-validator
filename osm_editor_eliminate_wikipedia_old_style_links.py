from termcolor import colored
import os
import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer
import osm_bot_abstraction_layer.human_verification_mode as human_verification_mode
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import osm_handling_config.global_config as osm_handling_config
from osm_iterator.osm_iterator import Data
import wikimedia_link_issue_reporter
import common
from termcolor import colored

def cache_data(element):
    global data_cache
    prerequisites = {}
    data = osm_bot_abstraction_layer.get_and_verify_data(element.get_link(), prerequisites)
    data_cache[element.get_link()] = data

def eliminate_old_style_links(element):
    prerequisites = {}
    data = osm_bot_abstraction_layer.get_and_verify_data(element.get_link(), prerequisites)
    tags = data['tag']
    old_style_links = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().get_old_style_wikipedia_keys(tags)
    if len(old_style_links) != 1:
        #allowing more requires checking whatever links are conflicting
        #in case of missing wikipedia tag - also deciding which language should be linked
        return
    old_style_link = old_style_links[0]
    language_code = wikimedia_connection.get_text_after_first_colon(old_style_link)
    article_name = tags.get(old_style_link)

    wikidata_from_old_style_link = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name)
    if wikidata_from_old_style_link == None:
        print("no wikidata issued")
        return
    if tags.get('wikipedia') != None:
        language_code = wikimedia_connection.get_language_code_from_link(tags.get('wikipedia'))
        article_name = wikimedia_connection.get_article_name_from_link(tags.get('wikipedia'))
        id_from_wikipedia_tag = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name)
        if id_from_wikipedia_tag != wikidata_from_old_style_link:
            print("old-style tags, wikipedia tag mismatch")
            return
    if tags.get('wikidata') != None:
        if tags.get('wikidata') != wikidata_from_old_style_link:
            print("old-style tags, wikidata tag mismatch")
            return
    print()
    print()
    print(old_style_link + "=" + tags.get(old_style_link) + " for removal")
    print()
    issue_checker = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector()
    missing_page_report = issue_checker.check_is_wikipedia_page_existing(language_code, article_name)
    if missing_page_report != None:
        return
    
    special_expected = {}
    data['tag']['wikipedia'] = language_code + ":" + article_name
    del data['tag'][old_style_link]
    human_verification_mode.smart_print_tag_dictionary(data['tag'], special_expected)
    if human_verification_mode.is_human_confirming():
        make_an_edit(data, element.get_link())
    print()
    print()

def make_an_edit(data, link):
    automatic_status = osm_bot_abstraction_layer.manually_reviewed_description()
    comment = "changing old-style wikipedia tag to current style, to prevent doubletagging by iD users, make tag more useful and harmonize tagging See https://wiki.openstreetmap.org/wiki/Key:wikipedia"
    discussion_url = None
    source = None
    type = link.split("/")[3]
    sleep_time = 0
    osm_bot_abstraction_layer.make_edit(link, comment, automatic_status, discussion_url, type, data, source, sleep_time)

def main():
    filename = 'old_style_wikipedia_links_for_elimination.osm'
    filename = 'old_style_wikipedia_links_for_bot_elimination_Polska.osm'
    offending_objects_storage_file = common.get_file_storage_location()+"/"+filename
    print(offending_objects_storage_file)
    os.system('rm "' + offending_objects_storage_file + '"')
    os.system('ruby download.rb')
    wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())

    osm = Data(offending_objects_storage_file)
    #osm.iterate_over_data(cache_data)
    osm.iterate_over_data(eliminate_old_style_links)
main()
