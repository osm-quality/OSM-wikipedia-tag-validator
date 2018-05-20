from termcolor import colored
import os
import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer
import osm_bot_abstraction_layer.human_verification_mode as human_verification_mode
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import osm_handling_config.global_config as osm_handling_config
from osm_iterator.osm_iterator import Data
from osm_bot_abstraction_layer.split_into_packages import Package
import wikimedia_link_issue_reporter
import common
from termcolor import colored
import time

def cache_data(element):
    global data_cache
    prerequisites = {}
    data = osm_bot_abstraction_layer.get_and_verify_data(element.get_link(), prerequisites)
    data_cache[element.get_link()] = data

def splitter(element):
    global list_of_elements
    list_of_elements.append(element)

def get_tags_for_removal(tags):
    issue_checker = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector()
    old_style_links = issue_checker.get_old_style_wikipedia_keys(tags)
    if len(old_style_links) != 1:
        #allowing more requires checking whatever links are conflicting
        #in case of missing wikipedia tag - also deciding which language should be linked
        return None

    old_style_link = old_style_links[0]
    language_code = wikimedia_connection.get_text_after_first_colon(old_style_link)
    article_name = tags.get(old_style_link)

    wikidata_from_old_style_link = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name)
    if wikidata_from_old_style_link == None:
        print("no wikidata issued for Wikipedia article linked in this element")
        return None
    if tags.get('wikipedia') != None:
        language_code = wikimedia_connection.get_language_code_from_link(tags.get('wikipedia'))
        article_name = wikimedia_connection.get_article_name_from_link(tags.get('wikipedia'))
        id_from_wikipedia_tag = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name)
        if id_from_wikipedia_tag != wikidata_from_old_style_link:
            print("old-style tags, wikipedia tag mismatch")
            return None
    if tags.get('wikidata') != None:
        if tags.get('wikidata') != wikidata_from_old_style_link:
            print("old-style tags, wikidata tag mismatch")
            return None

    return [old_style_link]

def build_changeset():
    automatic_status = osm_bot_abstraction_layer.manually_reviewed_description()
    comment = "changing old-style wikipedia tag to current style, to prevent doubletagging by iD users, make tag more useful and harmonize tagging See https://wiki.openstreetmap.org/wiki/Key:wikipedia"
    discussion_url = None
    source = None
    api = osm_bot_abstraction_layer.get_correct_api(automatic_status, discussion_url)
    affected_objects_description = ""
    builder = osm_bot_abstraction_layer.ChangesetBuilder(affected_objects_description, comment, automatic_status, discussion_url, source)
    builder.create_changeset(api)
    return api

def eliminate_old_style_links(package):
    api = build_changeset()
    for element in package.list:
        prerequisites = {}
        data = osm_bot_abstraction_layer.get_and_verify_data(element.get_link(), prerequisites)
        tags = data['tag']

        for_removal = get_tags_for_removal(tags)
        if for_removal == None:
            continue

        if len(for_removal) != 1:
            continue

        old_style_link = for_removal[0]
        language_code = wikimedia_connection.get_text_after_first_colon(old_style_link)
        article_name = tags.get(old_style_link)

        print()
        print()
        print(old_style_link + "=" + tags.get(old_style_link) + " for removal")
        print()

        special_expected = {}
        expected_wikipedia = language_code + ":" + article_name
        if data['tag'].get('wikipedia') != None and data['tag'].get('wikipedia') != expected_wikipedia:
            print("mismatch with wikipedia")
            continue
        data['tag']['wikipedia'] = expected_wikipedia
        del data['tag'][old_style_link]
        human_verification_mode.smart_print_tag_dictionary(data['tag'], special_expected)
        if human_verification_mode.is_human_confirming():
            osm_bot_abstraction_layer.update_element(api, element.element.tag, data)
        print()
        print()
    api.ChangesetClose()
    time.sleep(0.1)

def main():
    filename = 'old_style_wikipedia_links_for_elimination.osm'
    filename = 'old_style_wikipedia_links_for_bot_elimination_Polska.osm'
    offending_objects_storage_file = common.get_file_storage_location()+"/"+filename
    print(offending_objects_storage_file)
    os.system('rm "' + offending_objects_storage_file + '"')
    os.system('ruby download.rb')
    wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())

    global list_of_elements
    list_of_elements = []

    osm = Data(offending_objects_storage_file)
    #osm.iterate_over_data(cache_data)
    osm.iterate_over_data(splitter)
    print(len(list_of_elements))
    list_of_elements = list_of_elements[:2000]
    print(len(list_of_elements))
    max_count = 5
    returned = Package.split_into_packages(list_of_elements, max_count)
    #print(returned)
    print(len(returned))
    for package in returned:
        print(len(package.list))
    filtered = [p for p in returned if len(p.list) > max_count/3]
    print(len(filtered))
    for package in filtered:
        for element in package.list:
            print(element.get_link())
        eliminate_old_style_links(package)
        print()
        print()
main()
