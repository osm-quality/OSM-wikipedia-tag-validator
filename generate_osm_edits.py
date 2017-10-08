import osmapi
import time
import argparse
import common
import os
import wikipedia_connection
# docs: http://osmapi.metaodi.ch/

def bot_username():
    return "Mateusz Konieczny - bot account"

def manual_username():
    return "Mateusz Konieczny"

def fully_automated_description():
    return "yes"

def manually_reviewed_description():
    return "no, it is a manually reviewed edit"

def get_api(username):
    return osmapi.OsmApi(username = username, passwordfile = "password.secret")

def character_limit_of_description():
    return 255

class ChangesetBuilder:
    def __init__(self, affected_objects_description, comment, automatic_status, discussion_url, source):
        self.affected_objects_description = affected_objects_description
        self.comment = comment
        self.automatic_status = automatic_status
        self.discussion_url = discussion_url
        self.source = source

    def create_changeset(self, api):
        comment = output_full_comment_get_comment_within_limit(self.affected_objects_description, self.comment)
        changeset_description = {
            "comment": comment,
            "automatic": self.automatic_status,
            "source_code": "https://github.com/matkoniecz/OSM-wikipedia-tag-validator.git",
            "source": self.source,
            "cases_where_human_help_is_required": 'https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports/',
            }
        if self.discussion_url != None:
            changeset_description["discussion_before_edits"] = self.discussion_url
        api.ChangesetCreate(changeset_description)

def parsed_args():
    parser = argparse.ArgumentParser(description='Production of webpage about validation of wikipedia tag in osm data.')
    parser.add_argument('-file', '-f', dest='file', type=str, help='name of yaml file produced by validator')
    args = parser.parse_args()
    if not (args.file):
        parser.error('Provide yaml file generated by wikipedia validator')
    return args

def get_data(id, type):
    api = get_api(manual_username())
    try:
        if type == 'node':
            return api.NodeGet(id)
        if type == 'way':
            return api.WayGet(id)
        if type == 'relation':
            return api.RelationGet(id)
    except osmapi.ElementDeletedApiError:
        return None
    assert(False)

def update_element(api, type, data):
    if type == 'node':
        return api.NodeUpdate(data)
    if type == 'way':
        return api.WayUpdate(data)
    if type == 'relation':
        return api.RelationUpdate(data)
    assert False, str(type) + " type as not recognised"

def is_text_field_mentioning_wikipedia_or_wikidata(text):
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

def prerequisite_failure_reason(e, data):
    advice = note_or_fixme_review_request_indication(data)
    if advice != None:
        return advice + " was present for " + e['osm_object_url']

    for key in e['prerequisite'].keys():
        if e['prerequisite'][key] == None:
            if key in data['tag']:
                return("failed " + key + " prerequisite, as key " + key + " was present for " + e['osm_object_url'])
        elif key not in data['tag']:
            return("failed " + key + " prerequisite, as key " + key + " was missing for " + e['osm_object_url'])
        elif e['prerequisite'][key] != data['tag'][key]:
            return("failed " + key + " prerequisite for " + e['osm_object_url'])
    return None

def load_errors():
    args = parsed_args()
    filepath = common.get_file_storage_location()+"/"+args.file
    if not os.path.isfile(filepath):
        print(filepath + " is not a file, provide an existing file")
        return
    return common.load_data(filepath)

def sleep(time_in_s):
    print("Sleeping")
    time.sleep(time_in_s)

def get_correct_api(automatic_status, discussion_url):
    if automatic_status == manually_reviewed_description():
        return get_api(manual_username())
    elif automatic_status == fully_automated_description():
        assert(discussion_url != None)
        return get_api(bot_username())
    else:
        assert(False)

def output_full_comment_get_comment_within_limit(affected_objects_description, comment):
    full_comment = affected_objects_description + " " + comment
    if(len(comment) > character_limit_of_description()):
        raise "comment too long"
    if(len(full_comment) <= character_limit_of_description()):
        comment = full_comment
    print(full_comment)
    return comment

def make_edit(affected_objects_description, comment, automatic_status, discussion_url, type, data, source):
    api = get_correct_api(automatic_status, discussion_url)
    builder = ChangesetBuilder(affected_objects_description, comment, automatic_status, discussion_url, source)
    builder.create_changeset(api)
    update_element(api, type, data)
    api.ChangesetClose()
    sleep(60)

def fit_wikipedia_edit_description_within_character_limit_new(new, reason):
    comment = "adding [wikipedia=" + new + "]" + reason
    if(len(comment)) > character_limit_of_description():
        comment = "adding wikipedia tag " + reason
    if(len(comment)) > character_limit_of_description():
        raise("comment too long")
    return comment

def fit_wikipedia_edit_description_within_character_limit_changed(now, new, reason):
    comment = "[wikipedia=" + now + "] to [wikipedia=" + new + "]" + reason
    if(len(comment)) > character_limit_of_description():
        comment = "changing wikipedia tag to <" + new + ">" + reason
    if(len(comment)) > character_limit_of_description():
        comment = "changing wikipedia tag " + reason
    if(len(comment)) > character_limit_of_description():
        raise("comment too long")
    return comment

def get_and_verify_data(e):
    type = e['osm_object_url'].split("/")[3]
    id = e['osm_object_url'].split("/")[4]
    data = get_data(id, type)
    if data == None:
        return None
    failure = prerequisite_failure_reason(e, data)
    if failure != None:
        print(failure)
        return None
    return data

def handle_follow_redirect(e):
    if e['error_id'] != 'wikipedia wikidata mismatch - follow wikipedia redirect':
        return
    language_code = wikipedia_connection.get_language_code_from_link(e['prerequisite']['wikipedia'])
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
    automatic_status = fully_automated_description()
    type = e['osm_object_url'].split("/")[3]
    source = "wikidata, OSM"
    make_edit(e['osm_object_url'], comment, automatic_status, discussion_url, type, data, source)

def change_to_local_language(e):
    if e['error_id'] != 'wikipedia tag unexpected language':
        return
    #language_code = wikipedia_connection.get_language_code_from_link(e['prerequisite']['wikipedia'])
    #if language_code != "pl":
    #    return
    data = get_and_verify_data(e)
    if data == None:
        return None
    now = data['tag']['wikipedia']
    new = e['desired_wikipedia_target']
    reason = ", as wikipedia page in the local language should be preferred"
    comment = fit_wikipedia_edit_description_within_character_limit_changed(now, new, reason)
    data['tag']['wikipedia'] = e['desired_wikipedia_target']
    discussion_url = None
    automatic_status = manually_reviewed_description()
    type = e['osm_object_url'].split("/")[3]
    source = "wikidata, OSM"
    make_edit(e['osm_object_url'], comment, automatic_status, discussion_url, type, data, source)

def filter_reported_errors(reported_errors, matching_error_ids):
    errors_for_removal = []
    for e in reported_errors:
        if e['error_id'] in matching_error_ids:
            errors_for_removal.append(e)
    return errors_for_removal

def add_wikipedia_tag_from_wikidata_tag(reported_errors):
    errors_for_removal = filter_reported_errors(reported_errors, ['wikipedia from wikidata tag'])
    if errors_for_removal == []:
        return
    #TODO check location - checking language of desired article is not helpful as Polish articles exist for objects outside Poland...
    #language_code = wikipedia_connection.get_language_code_from_link(e['desired_wikipedia_target'])
    #if language_code != "pl":
    #    return
    automatic_status = fully_automated_description()
    affected_objects_description = ""
    comment = "add wikipedia tag based on wikidata tag"
    discussion_url = 'https://forum.openstreetmap.org/viewtopic.php?id=59888'
    api = get_correct_api(automatic_status, discussion_url)
    source = "wikidata, OSM"
    builder = ChangesetBuilder(affected_objects_description, comment, automatic_status, discussion_url, source)
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
        update_element(api, type, data)

    api.ChangesetClose()
    sleep(60)

def add_wikipedia_links_basing_on_old_style_wikipedia_tags(reported_errors):
    matching_error_ids = [
                'wikipedia tag from wikipedia tag in an outdated form and wikidata',
                'wikipedia tag from wikipedia tag in an outdated form',
                ]
    errors_for_removal = filter_reported_errors(reported_errors, matching_error_ids)
    if errors_for_removal == []:
        return
    #TODO check location - checking language of desired article is not helpful as Polish articles exist for objects outside Poland...
    #language_code = wikipedia_connection.get_language_code_from_link(e['desired_wikipedia_target'])
    #if language_code != "pl":
    #    return

    automatic_status = fully_automated_description()
    affected_objects_description = ""
    comment = "adding wikipedia and wikidata tags based on old style wikipedia tags"
    discussion_url = 'https://forum.openstreetmap.org/viewtopic.php?id=59665'
    api = get_correct_api(automatic_status, discussion_url)
    source = "wikidata, OSM"
    builder = ChangesetBuilder(affected_objects_description, comment, automatic_status, discussion_url, source)
    builder.create_changeset(api)

    for e in errors_for_removal:
        data = get_and_verify_data(e)
        if data == None:
            continue
        new = e['desired_wikipedia_target']
        data['tag']['wikipedia'] = new
        reason = ", as standard wikipedia tag is better than old style wikipedia tags"
        change_description = e['osm_object_url'] + " " + str(e['prerequisite']) + " to " + new + reason
        if e['error_id'] == 'wikipedia tag from wikipedia tag in an outdated form':
            language_code = wikipedia_connection.get_language_code_from_link(e['desired_wikipedia_target'])
            article_name = wikipedia_connection.get_article_name_from_link(e['desired_wikipedia_target'])
            wikidata_id = wikipedia_connection.get_wikidata_object_id_from_article(language_code, article_name)
            assert(wikidata_id != None)
            data['tag']['wikidata'] = wikidata_id
            change_description += " +adding wikidata=" + wikidata_id
        print(change_description)
        type = e['osm_object_url'].split("/")[3]
        update_element(api, type, data)

    api.ChangesetClose()
    sleep(60)

def main():
    wikipedia_connection.set_cache_location(common.get_file_storage_location())
    # for testing: api="https://api06.dev.openstreetmap.org", 
    # website at https://master.apis.dev.openstreetmap.org/
    reported_errors = load_errors()
    #requires manual checking is it operating in Poland #add_wikipedia_links_basing_on_old_style_wikipedia_tags(reported_errors)
    #requires manual checking is it operating in Poland #add_wikipedia_tag_from_wikidata_tag(reported_errors)
    for e in reported_errors:
        #handle_follow_redirect(e)
        #change_to_local_language(e)
        pass

if __name__ == '__main__':
    main()
