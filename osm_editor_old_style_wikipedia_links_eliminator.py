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

class EditData():
    def __init__(self, is_automatic, file_with_data, file_with_expanded_data, discussion_url):
        self.is_automatic = is_automatic
        self.file_with_data = file_with_data
        self.file_with_expanded_data = file_with_expanded_data
        self.discussion_url = discussion_url

        if self.is_automatic:
            self.max_items_in_group = 500
            self.sleep = 60
            self.automatic_status_description = osm_bot_abstraction_layer.fully_automated_description()
        else:
            self.max_items_in_group = 5
            self.sleep = 0.1
            self.automatic_status_description = osm_bot_abstraction_layer.manually_reviewed_description()

def cache_data(element):
    global data_cache
    prerequisites = {}
    data = osm_bot_abstraction_layer.get_and_verify_data(element.get_link(), prerequisites)
    data_cache[element.get_link()] = data

def remember_available(element):
    global list_of_elements_within_range
    list_of_elements_within_range.append(element.get_link())

def splitter(element):
    global list_of_elements
    global list_of_elements_within_range
    if element.get_link() in list_of_elements_within_range:
        list_of_elements.append(element)

def get_tags_for_removal(tags):
    issue_checker = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector()
    old_style_links = issue_checker.get_old_style_wikipedia_keys(tags)
    if len(old_style_links) == 0:
        return
    if len(old_style_links) > 1:
        #allowing more requires checking whatever links are conflicting
        #in case of missing wikipedia tag - also deciding which language should be linked
        if tags.get('wikipedia') == None:
            print("more than one old style link, no wikipedia tag - language would need to be selected")
            return None
        if tags.get('wikipedia') != None:
            print("more than one old style link - tags should be checked for conflicts")
            return None

    old_style_link = old_style_links[0]

    language_code = wikimedia_connection.get_text_after_first_colon(old_style_link)
    article_name = tags.get(old_style_link)

    if issue_checker.check_is_wikipedia_link_clearly_malformed(language_code+":"+article_name):
        print("page linked in " + old_style_link + " has malformed link")
        return None

    if issue_checker.check_is_wikipedia_page_existing(language_code, article_name) != None:
        print("page linked in " + old_style_link + " is not existing")
        return None

    wikidata_from_old_style_link = wikipedia_page_to_wikidata_id(language_code, article_name)
    if wikidata_from_old_style_link == None:
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

def wikipedia_page_to_wikidata_id(language_code, article_name):
    issue_checker = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector()
    wikidata_from_old_style_link = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name)
    if wikidata_from_old_style_link == None:
        print("no wikidata issued for Wikipedia article (" + article_name + " in " + language_code + "wiki ) linked in this element, it may be a redirect")
        article_name = issue_checker.get_article_name_after_redirect(language_code, article_name)
        wikidata_after_redirect = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name)
        if wikidata_after_redirect == None:
            print("checking for redirects changed nothing")
            return None
        else:
            print("redirects to " + article_name)
            return None
    return wikidata_from_old_style_link

def build_changeset(config):
    comment = "changing old-style wikipedia tagging (wikipedia:lang=article) to current style (wikipedia=lang:article), to make tagging more useful and consistent See https://wiki.openstreetmap.org/wiki/Key:wikipedia"
    source = None
    api = osm_bot_abstraction_layer.get_correct_api(config.automatic_status_description, config.discussion_url)
    affected_objects_description = ""
    builder = osm_bot_abstraction_layer.ChangesetBuilder(
        affected_objects_description,
        comment,
        config.automatic_status_description,
        config.discussion_url,
        source)
    builder.create_changeset(api)
    return api

def eliminate_old_style_links(package, config):
    api = build_changeset(config)
    something_was_changed = False
    for element in package.list:
        prerequisites = {}
        data = osm_bot_abstraction_layer.get_and_verify_data(element.get_link(), prerequisites)
        tags = data['tag']

        if tags == {}:
            continue
        for_removal = get_tags_for_removal(tags)
        if for_removal == None:
            print(element.get_link())
            print()
            continue

        if len(for_removal) != 1:
            continue

        old_style_link = for_removal[0]
        language_code = wikimedia_connection.get_text_after_first_colon(old_style_link)
        article_name = tags.get(old_style_link)

        special_expected = {}
        expected_wikipedia = language_code + ":" + article_name
        delete_only_complete_duplicates = False
        if delete_only_complete_duplicates:
            if data['tag'].get('wikipedia') != None and data['tag'].get('wikipedia') != expected_wikipedia:
                print(element.get_link())
                print(data['tag'].get('wikipedia'))
                print(expected_wikipedia)
                print("mismatch with wikipedia")
                continue
        human_verification_mode.smart_print_tag_dictionary(data['tag'], special_expected)
        print()
        print(old_style_link + "=" + tags.get(old_style_link) + " for removal")
        print()
        if data['tag'].get('wikipedia') == None:
            data['tag']['wikipedia'] = expected_wikipedia
        del data['tag'][old_style_link]
        print()
        human_verification_mode.smart_print_tag_dictionary(data['tag'], special_expected)
        if config.is_automatic or human_verification_mode.is_human_confirming():
            print("editing:")
            osm_bot_abstraction_layer.update_element(api, element.element.tag, data)
            something_was_changed = True
        print()
        print()
    api.ChangesetClose()
    if something_was_changed:
        time.sleep(config.sleep)

def main():
    poland_bot = EditData(
        True,
        'old_style_wikipedia_links_for_bot_elimination_Polska_v2.osm',
        'old_style_wikipedia_links_for_bot_elimination_Polska_v2.expanded.osm',
        "https://forum.openstreetmap.org/viewtopic.php?pid=698244")
    world_manual = EditData(
        False,
        'old_style_wikipedia_links_for_elimination.osm',
        'old_style_wikipedia_links_for_elimination.expanded.osm',
        None)
    config = poland_bot

    offending_objects_storage_file = common.get_file_storage_location()+"/"+config.file_with_data
    offending_objects_storage_expanded_file = common.get_file_storage_location()+"/"+config.file_with_expanded_data
    print(offending_objects_storage_file)
    print(offending_objects_storage_expanded_file)
    os.system('rm "' + offending_objects_storage_file + '"')
    os.system('rm "' + offending_objects_storage_expanded_file + '"')
    os.system('ruby download.rb')
    wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())

    global list_of_elements
    list_of_elements = []

    global list_of_elements_within_range
    list_of_elements_within_range = []

    data_within_bot_range = Data(offending_objects_storage_file)
    data_within_bot_range.iterate_over_data(remember_available)

    osm = Data(offending_objects_storage_expanded_file)
    #osm.iterate_over_data(cache_data)
    osm.iterate_over_data(splitter)
    print(len(list_of_elements))
    #list_of_elements = list_of_elements[:8000]
    print(len(list_of_elements))
    max_count = config.max_items_in_group
    returned = Package.split_into_packages(list_of_elements, max_count)
    #print(returned)
    print(len(returned))
    for package in returned:
        for element in package.list:
            print(element.get_link())
        eliminate_old_style_links(package, config)
        print()
        print()
main()
