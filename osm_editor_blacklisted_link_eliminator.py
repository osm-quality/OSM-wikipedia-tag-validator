import os
import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer
import osm_bot_abstraction_layer.human_verification_mode as human_verification_mode
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import osm_handling_config.global_config as osm_handling_config
from osm_iterator.osm_iterator import Data
import wikimedia_link_issue_reporter
import common

def main():
    offending_objects_storage_file = common.get_file_storage_location()+"/"+'objects_with_blacklisted_links.osm'
    # run twice, initial run may pollute query by reports that some wikidata entries are fetched
    os.system('python3 generate_query_for_blacklisted_wikimedia_links.py > generated_query_for_blacklisted_entries.generated_query')
    os.system('python3 generate_query_for_blacklisted_wikimedia_links.py > generated_query_for_blacklisted_entries.generated_query')
    os.system('rm "' + offending_objects_storage_file + '"')
    os.system('ruby download.rb')

    wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())

    print(offending_objects_storage_file)

    osm = Data(offending_objects_storage_file)
    osm.iterate_over_data(cache_data)
    print(str(len(data_cache)) + " objects cached")
    osm.iterate_over_data(eliminate_blacklisted_links)

def blacklist():
    return wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().wikidata_connection_blacklist()

def try_prefixifying(data, tag, blacklist_entry):
    try:
        data['tag'][tag]
    except KeyError:
        return data
    else:
        data['tag'][blacklist_entry['prefix'] + tag] = data['tag'][tag]
        del data['tag'][tag]
        print("prefixified " + tag + " with " + blacklist_entry['prefix'])
    return data

def make_an_edit(data, link, blacklist_entry):
    data = try_prefixifying(data, 'wikidata', blacklist_entry)
    data = try_prefixifying(data, 'wikipedia', blacklist_entry)
    automatic_status = osm_bot_abstraction_layer.manually_reviewed_description()
    source = "general knowlege, checking link target"
    comment = "fixing a link to Wikipedia. In wikipedia/wikidata tags only entries about given feature should be linked. See https://wiki.openstreetmap.org/wiki/Key:wikipedia"
    discussion_url = None
    type = link.split("/")[3]

    special_expected = get_special_expected_tags(data['tag'], blacklist_entry)
    human_verification_mode.smart_print_tag_dictionary(data['tag'], special_expected)
    message = "relink to " + blacklist_entry['prefix']
    print(message + " ? [y/n]")
    additional_explanation = {}
    additional_explanation['armchair_justification'] = 'this edit relies on general knowledge ( like "Żabka (convenience store)" Wikipedia page is not describing single convenience store but chain/brand of convenience store") and is not making changes that require local survey for verification'
    additional_explanation['armchair_justification_opposite'] = 'for example adding brand tags based solely on name tag would be in my opinion example of wrong, revertable and harmful armchair editing - knowledge whatever shop named "Żabka" is part of Żabka convenience shop chain requires local knowledge'
    if human_verification_mode.is_human_confirming():
        osm_bot_abstraction_layer.make_edit(link, comment, automatic_status, discussion_url, type, data, source, 0, additional_explanation)

def initial_verification(element):
    global data_cache
    # TODO support entries without wikidata
    # TODO verify whatever wikipedia-wikidata matches
    # TODO verify whaver it is using old style wikipedia tags
    # TODO verify structural issues like this using validator
    # TODO package getting effective_wikidata into a function
    effective_wikidata = element.get_tag_value('wikidata')
    blacklist_entry = None
    try:
        blacklist_entry = blacklist()[effective_wikidata]
    except KeyError as e:
        return None

    prerequisites = {}
    for key in element.get_keys():
        prerequisites[key] = element.get_tag_value(key)

    issue_detector = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector()

    if element.get_link() in data_cache:
        return data_cache[element.get_link()]
    something_reportable = issue_detector.critical_structural_issue_report(element.get_element().tag, element.get_tag_dictionary())
    if something_reportable != None:
        print()
        print(element.get_link())
        print(something_reportable.error_message)
        return None

    old_style_links = issue_detector.get_old_style_wikipedia_keys(element.get_tag_dictionary())
    if len(old_style_links) != 0:
        raise 'should be reported already'

    data = osm_bot_abstraction_layer.get_and_verify_data(element.get_link(), prerequisites)
    if data == None:
        return None
    if data['tag'] != element.get_tag_dictionary():
        print("tag mismatch")
        return None
    data_cache[element.get_link()] = data
    return data

def get_special_expected_tags(tags, blacklist_entry):
    returned = {}
    for key, value in tags.items():
        if is_expected_tag_based_on_blacklist_entry(key, value, blacklist_entry):
            returned[key] = value
    return returned

def is_expected_tag_based_on_blacklist_entry(key, value, blacklist_entry):
    if key in blacklist_entry['expected_tags']:
        if value == blacklist_entry['expected_tags'][key]:
            return True
    if key == 'name':
        if blacklist_entry['name'] == value:
            return True

def eliminate_blacklisted_links(element):
    data = initial_verification(element)
    if data == None:
        return

    effective_wikidata = element.get_tag_value('wikidata')
    blacklist_entry = blacklist()[effective_wikidata]

    special_expected = get_special_expected_tags(data['tag'], blacklist_entry)
    human_verification_mode.smart_print_tag_dictionary(data['tag'], special_expected)

    print()
    print(element.get_link())

    for tag, expected_value in blacklist_entry['expected_tags'].items():
        present = data['tag'].get(tag)
        if expected_value != present:
            if present == None:
                present = "<missing value>"
            print("for " + tag + " " + expected_value + " was expected, got " + present)
            print("allow edit anyway? [y/n]")
            if not human_verification_mode.is_human_confirming():
                return

    wikidata_id = data['tag']['wikidata']
    make_an_edit(data, element.get_link(), blacklist_entry)

def cache_data(element):
    initial_verification(element)

data_cache = {}
main()
print("all processed - HDFC Bank is the new target")
print("all processed - new ideas are likely to be present at https://taginfo.openstreetmap.org/keys/wikipedia#values")
print("all processed - maybe try shop=supermarket and wikipedia=* on overpass?")
print("all processed - maybe try amenity=bank and wikipedia=* on overpass?")
print("all processed - maybe try amenity=fuel and wikipedia=* on overpass?")
