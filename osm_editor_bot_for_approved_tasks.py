import argparse
import common
import os
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer
import osm_handling_config.global_config as osm_handling_config
from wikibrain import wikimedia_link_issue_reporter

def parsed_args():
    parser = argparse.ArgumentParser(description='Production of webpage about validation of wikipedia tag in osm data.')
    parser.add_argument('-file', '-f', dest='file', type=str, help='name of yaml file produced by validator')
    args = parser.parse_args()
    if not (args.file):
        parser.error('Provide yaml file generated by wikipedia validator')
    return args

def is_text_field_mentioning_wikipedia_or_wikidata(text):
    text = text.replace("http://wiki-de.genealogy.net/GOV:", "")
    if text.find("wikipedia") != -1:
        return True
    if text.find("wikidata") != -1:
        return True
    if text.find("wiki") != -1:
        return True
    return False

def note_or_fixme_review_request_indication(data):
    fixme = ""
    note = ""
    if 'fixme' in data['tag']:
        fixme = data['tag']['fixme']
    if 'note' in data['tag']:
        note = data['tag']['note']
    text_dump = "fixme=<" + fixme + "> note=<" + note + ">"
    if is_text_field_mentioning_wikipedia_or_wikidata(fixme):
        return text_dump
    if is_text_field_mentioning_wikipedia_or_wikidata(note):
        return text_dump
    return None

def load_errors():
    args = parsed_args()
    filepath = common.get_file_storage_location()+"/"+args.file
    if not os.path.isfile(filepath):
        print(filepath + " is not a file, provide an existing file")
        return
    return common.load_data(filepath)

def fit_wikipedia_edit_description_within_character_limit_new(new, reason):
    comment = "adding [wikipedia=" + new + "]" + reason
    if(len(comment)) > osm_bot_abstraction_layer.character_limit_of_description():
        comment = "adding wikipedia tag " + reason
    if(len(comment)) > osm_bot_abstraction_layer.character_limit_of_description():
        raise("comment too long")
    return comment

def fit_wikipedia_edit_description_within_character_limit_changed(now, new, reason):
    comment = "[wikipedia=" + now + "] to [wikipedia=" + new + "]" + reason
    if(len(comment)) > osm_bot_abstraction_layer.character_limit_of_description():
        comment = "changing wikipedia tag to <" + new + ">" + reason
    if(len(comment)) > osm_bot_abstraction_layer.character_limit_of_description():
        comment = "changing wikipedia tag " + reason
    if(len(comment)) > osm_bot_abstraction_layer.character_limit_of_description():
        raise("comment too long")
    return comment

def get_and_verify_data(e):
    return osm_bot_abstraction_layer.get_and_verify_data(e['osm_object_url'], e['prerequisite'], note_or_fixme_review_request_indication)

def handle_follow_wikipedia_redirect(e):
    if e['error_id'] != 'wikipedia wikidata mismatch - follow wikipedia redirect':
        return
    language_code = wikimedia_connection.get_language_code_from_link(e['prerequisite']['wikipedia'])
    if language_code != "pl":
        print(e['prerequisite']['wikipedia'] + " is not in the expected language code!")
        return
    data = get_and_verify_data(e)
    if data == None:
        return None
    now = data['tag']['wikipedia']
    new = e['desired_wikipedia_target']
    reason = ", as current tag is a redirect and the new page matches present wikidata"
    comment = fit_wikipedia_edit_description_within_character_limit_changed(now, new, reason)
    data['tag']['wikipedia'] = e['desired_wikipedia_target']
    discussion_url = "https://forum.openstreetmap.org/viewtopic.php?id=59649"
    osm_wiki_documentation_page = "https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/fixing_wikipedia_tags_pointing_at_redirects_in_Poland"
    automatic_status = osm_bot_abstraction_layer.fully_automated_description()
    type = e['osm_object_url'].split("/")[3]
    source = "wikidata, OSM"
    osm_bot_abstraction_layer.make_edit(e['osm_object_url'], comment, automatic_status, discussion_url, osm_wiki_documentation_page, type, data, source)

def change_to_local_language(e):
    if e['error_id'] != 'wikipedia tag unexpected language':
        return
    language_code = wikimedia_connection.get_language_code_from_link(e['prerequisite']['wikipedia'])
    if language_code != "pl":
        print(e['prerequisite']['wikipedia'] + " is not in the expected language code!")
        return
    data = get_and_verify_data(e)
    if data == None:
        return None
    now = data['tag']['wikipedia']
    new = e['desired_wikipedia_target']
    reason = ", as wikipedia page in the local language should be preferred"
    comment = fit_wikipedia_edit_description_within_character_limit_changed(now, new, reason)
    data['tag']['wikipedia'] = e['desired_wikipedia_target']
    discussion_url = None
    #osm_wiki_documentation_page = 
    automatic_status = osm_bot_abstraction_layer.manually_reviewed_description()
    type = e['osm_object_url'].split("/")[3]
    source = "wikidata, OSM"
    osm_bot_abstraction_layer.make_edit(e['osm_object_url'], comment, automatic_status, discussion_url, osm_wiki_documentation_page, type, data, source)

def filter_reported_errors(reported_errors, matching_error_ids):
    errors_for_removal = []
    for e in reported_errors:
        if e['error_id'] in matching_error_ids:
            errors_for_removal.append(e)
    return errors_for_removal

def is_edit_allowed_object_based_on_location(object_data, target_country):
    if target_country != "pl":
        raise "unimplemented"
    print(object_data)

def is_edit_allowed_object_has_set_wikipedia(object_data, target_country):
    if target_country != "pl":
        raise "unimplemented"

    wikipedia_tag = object_data['tag']['wikipedia']
    language_code = wikimedia_connection.get_language_code_from_link(wikipedia_tag)
    article_name = wikimedia_connection.get_article_name_from_link(wikipedia_tag)
    wikidata_id = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name)

    if wikipedia_tag in ["ru:Шешупе", "lt:Šešupė", "lt:Vyžaina", "be:Калонка", "be:Пчолка", "lt:Ingelis", "lt:Gilbietis (ežeras)"]: # workaround for failed country detection
        return False

    if language_code == "pl":
        return True # addumes that Polish Wikipedia code is use only in Poland
        
    countries_tagged_in_wikidata = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().get_country_location_from_wikidata_id(wikidata_id)

    if(len(countries_tagged_in_wikidata) > 1):
        print("SKIPPED BECAUSE IN MORE THAN ONE COUNTRY " + e['osm_object_url'])
        return False

    if(countries_tagged_in_wikidata == [target_country]):
        return True

    if language_code != "pl" and wikipedia_tag not in ["de:Rastenburger Kleinbahnen"]:
        print("UNEXPECTED LANGUAGE CODE for Wikipedia tag in " + e['osm_object_url'])
        raise "UNEXPECTED LANGUAGE CODE for Wikipedia tag in " + e['osm_object_url']
        return False

    return False

def add_wikidata_tag_from_wikipedia_tag(reported_errors):
    errors_for_removal = filter_reported_errors(reported_errors, ['wikidata from wikipedia tag'])
    if errors_for_removal == []:
        return
    automatic_status = osm_bot_abstraction_layer.fully_automated_description()
    affected_objects_description = ""
    comment = "add wikidata tag based on wikipedia tag"
    discussion_url = 'https://forum.openstreetmap.org/viewtopic.php?id=59925'
    osm_wiki_page_url = 'https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/adding_wikidata_tags_based_on_wikipedia_tags_in_Poland'
    api = osm_bot_abstraction_layer.get_correct_api(automatic_status, discussion_url)
    source = "wikidata, OSM"
    builder = osm_bot_abstraction_layer.ChangesetBuilder(affected_objects_description, comment, automatic_status, discussion_url, osm_wiki_page_url, source)
    builder.create_changeset(api)

    for e in errors_for_removal:
        data = get_and_verify_data(e)
        if data == None:
            continue

        if is_edit_allowed_object_has_set_wikipedia(data, "pl") == False and is_edit_allowed_object_based_on_location(data, "pl") == False:
            continue

        wikipedia_tag = data['tag']['wikipedia']
        language_code = wikimedia_connection.get_language_code_from_link(wikipedia_tag)
        article_name = wikimedia_connection.get_article_name_from_link(wikipedia_tag)
        wikidata_id = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name)

        print(e['osm_object_url'])
        print(wikidata_id)
        reason = ", as wikidata tag may be added based on wikipedia tag"
        change_description = e['osm_object_url'] + " " + str(e['prerequisite']) + " to " + wikidata_id + reason
        print(change_description)
        osm_bot_abstraction_layer.sleep(2)
        data['tag']['wikidata'] = wikidata_id
        type = e['osm_object_url'].split("/")[3]
        osm_bot_abstraction_layer.update_element(api, type, data)

    api.ChangesetClose()
    osm_bot_abstraction_layer.sleep(60)

def add_wikipedia_tag_from_wikidata_tag(reported_errors):
    errors_for_removal = filter_reported_errors(reported_errors, ['wikipedia from wikidata tag'])
    if errors_for_removal == []:
        return
    #TODO check location - checking language of desired article is not helpful as Polish articles exist for objects outside Poland...
    #language_code = wikimedia_connection.get_language_code_from_link(e['desired_wikipedia_target'])
    #if language_code != "pl":
    #    return
    automatic_status = osm_bot_abstraction_layer.fully_automated_description()
    affected_objects_description = ""
    comment = "add wikipedia tag based on wikidata tag"
    discussion_url = 'https://forum.openstreetmap.org/viewtopic.php?id=59888'
    osm_wiki_page_url = 'https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/adding_wikipedia_tags_based_on_wikidata_tags_in_Poland'
    api = osm_bot_abstraction_layer.get_correct_api(automatic_status, discussion_url)
    source = "wikidata, OSM"
    builder = osm_bot_abstraction_layer.ChangesetBuilder(affected_objects_description, comment, automatic_status, discussion_url, osm_wiki_page_url, source)
    builder.create_changeset(api)

    for e in errors_for_removal:
        data = get_and_verify_data(e)
        if data == None:
            continue
        new = e['desired_wikipedia_target']
        reason = ", as wikipedia tag may be added based on wikidata"
        change_description = e['osm_object_url'] + " " + str(e['prerequisite']) + " to " + new + reason
        print(change_description)
        data['tag']['wikipedia'] = e['desired_wikipedia_target']
        type = e['osm_object_url'].split("/")[3]
        osm_bot_abstraction_layer.update_element(api, type, data)

    api.ChangesetClose()
    osm_bot_abstraction_layer.sleep(60)

def main():
    wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())
    # for testing: api="https://api06.dev.openstreetmap.org", 
    # website at https://master.apis.dev.openstreetmap.org/
    reported_errors = load_errors()
    #requires manual checking is it operating in Poland #add_wikipedia_tag_from_wikidata_tag(reported_errors)
    add_wikidata_tag_from_wikipedia_tag(reported_errors) #self-checking location based on Wikipedia language code
    for e in reported_errors:
        handle_follow_wikipedia_redirect(e) #self-checking location based on Wikipedia language code [pl required]
        #change_to_local_language(e) - discussion missing
        pass

if __name__ == '__main__':
    main()
