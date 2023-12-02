import pprint
import argparse
import os
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer
import osm_handling_config.global_config as osm_handling_config
from wikibrain import wikimedia_link_issue_reporter
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.exc import GeocoderServiceError
import sqlite3
import json
import config
import database
import time
import osm_bot_abstraction_layer.human_verification_mode as human_verification_mode
import wikibrain.wikimedia_link_issue_reporter
import datetime

def parsed_args():
    parser = argparse.ArgumentParser(description='Production of webpage about validation of wikipedia tag in osm data.')
    parser.add_argument('-file', '-f', dest='file', type=str, help='name of yaml file produced by validator')
    args = parser.parse_args()
    if not (args.file):
        parser.error('Provide yaml file generated by wikipedia validator')
    return args

def get_nominatim_country_code(lat, lon):
    try:
        # Nominatim is not cached as borders may change
        # though offline geocoder or some caching may be smart...
        # TODO
        osm_bot_abstraction_layer.sleep(3)
        geolocator = Nominatim(user_agent="Wikipedia Validator", timeout=15)
        returned = geolocator.reverse(str(lat) + ", " + str(lon)).raw
        print(returned)
    except GeocoderTimedOut:
        osm_bot_abstraction_layer.sleep(20)
        return get_nominatim_country_code(lat, lon)
    except GeocoderServiceError:
        osm_bot_abstraction_layer.sleep(200)
        return get_nominatim_country_code(lat, lon)
    if "address" not in returned:
        print(returned)
        print(link_to_point(lat, lon))
        raise "wat"
    return returned["address"]["country_code"]

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

def load_errors(cursor, processed_area):
    cursor.execute("SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint FROM osm_data WHERE validator_complaint IS NOT NULL AND validator_complaint <> '' AND area_identifier == :area_identifier", {"area_identifier": processed_area})
    returned = []
    for entry in cursor.fetchall():
        rowid, object_type, id, lat, lon, tags, area_identifier, updated, validator_complaint = entry
        tags = json.loads(tags)
        validator_complaint = json.loads(validator_complaint)
        returned.append(validator_complaint)
        validator_complaint["rowid"] = rowid
    return returned

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
    print(e)
    print(e['osm_object_url'])
    return osm_bot_abstraction_layer.get_and_verify_data(e['osm_object_url'], e['prerequisite'], prerequisite_failure_callback=note_or_fixme_review_request_indication)

def desired_wikipedia_target_from_report(e):
    desired = None
    if e['proposed_tagging_changes'] != None:
        for change in e['proposed_tagging_changes']:
            if "wikipedia" in change["to"]:
                if desired != None:
                    raise ValueError("multiple incoming replacements of the same tag")
                desired = change["to"]["wikipedia"]
    if desired == None:
        raise Exception("Expected wikipedia tag to be provided")
    return desired

def handle_follow_wikipedia_redirect_where_target_matches_wikidata_single(cursor, e, area_code, automatic_status):
    if e['error_id'] != 'wikipedia wikidata mismatch - follow wikipedia redirect':
        return
    data = get_and_verify_data(e)
    if data == None:
        return None
    if is_edit_allowed_object_based_on_location(e['osm_object_url'], data, area_code, detailed_verification_function_is_within_given_country) == False:
        announce_skipping_object_as_outside_area(e['osm_object_url']+" (handle_follow_wikipedia_redirect funtion)")
    now = data['tag']['wikipedia']
    new = desired_wikipedia_target_from_report(e)
    reason = ", as current tag is a redirect and the new page matches present wikidata"
    comment = fit_wikipedia_edit_description_within_character_limit_changed(now, new, reason)
    print()
    print(e['osm_object_url'])
    human_verification_mode.smart_print_tag_dictionary(data['tag'])
    print()
    data['tag']['wikipedia'] = new
    human_verification_mode.smart_print_tag_dictionary(data['tag'])
    if automatic_status == osm_bot_abstraction_layer.manually_reviewed_description():
        if human_verification_mode.is_human_confirming(e['osm_object_url']) == False:
            return
    discussion_urls = {
        "pl": "https://forum.openstreetmap.org/viewtopic.php?id=59649",
        "usa": "https://community.openstreetmap.org/t/bot-edit-proposal-fixing-wikipedia-tags-pointing-at-redirects-in-usa-where-it-can-be-done-reliably/101417 and https://app.slack.com/client/T029HV94T/C029HV951/thread/C029HV951-1688283468.590519",
    }
    osm_wiki_page_urls = {
        "pl": "https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/fixing_wikipedia_tags_pointing_at_redirects_in_Poland",
        "usa": "https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/fixing_wikipedia_tags_pointing_at_redirects_in_USA"
    }
    type = e['osm_object_url'].split("/")[3]
    source = "wikidata;OSM"
    osm_bot_abstraction_layer.make_edit(e['osm_object_url'], comment, automatic_status, discussion_urls[area_code], osm_wiki_page_urls[area_code], type, data, source)
    database.clear_error_and_request_update(cursor, e["rowid"])

def change_to_local_language_single(cursor, e, area_code, automatic_status):
    if automatic_status == None:
        automatic_status = osm_bot_abstraction_layer.manually_reviewed_description()
        raise NotImplementedError
    else:
        raise NotImplementedError
    if e['error_id'] != 'wikipedia tag unexpected language':
        return
    data = get_and_verify_data(e)
    if data == None:
        return None
    if is_edit_allowed_object_based_on_location(e['osm_object_url'], data, area_code, very_rough_verification_function_is_within_given_country_prefers_false_negatives) == False:
        print("Skipping object", e['osm_object_url'], "- apparently not within catchment area")
        print("ONLY EXTREMELY ROUGH CHECK WAS MADE! FALSE POSITIVES EXPECTED!")
        print("---------------------------------")
        print()
        print()
        #announce_skipping_object_as_outside_area(e['osm_object_url'])
        # TODO: what about objects exactly on borders? This could result in a slow moving edit wars...
        # Nominatim-based checking will not work reliably here...

        # TODO What about objects between "absolutely certain core" and borders?
        # right now I skip them...
        return

    # run validator check again to prevent editing based on stale data
    # ask to run check without using cached data
    # done only for objects scheduled to be deleted so some Wikimedia API is fine
    print(data['tag'])
    object_description = e['osm_object_url']
    wikipedia = data['tag']['wikipedia'] # must be present given that error is about bad Wikipedia in the first place
    wikidata = data['tag']['wikidata'] # there may be need to get it somehow
    new_report = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector(forced_refresh=True).get_wikipedia_language_issues(object_description, tags, wikipedia, wikidata_id)
    if desired_wikipedia_target_from_report(e) != desired_wikipedia_target_from_report(new_report):
        print(e)
        print(new_report)
        print(desired_wikipedia_target_from_report(e))
        print(desired_wikipedia_target_from_report(new_report))
        raise Exception("report seems outdated")
    now = data['tag']['wikipedia']
    new = desired_wikipedia_target_from_report(e)
    reason = ", as wikipedia page in the local language should be preferred"
    comment = fit_wikipedia_edit_description_within_character_limit_changed(now, new, reason)
    data['tag']['wikipedia'] = new
    discussion_url = None
    #osm_wiki_documentation_page = 
    type = e['osm_object_url'].split("/")[3]
    source = "wikidata, OSM"
    osm_bot_abstraction_layer.make_edit(e['osm_object_url'], comment, automatic_status, discussion_url, osm_wiki_documentation_page, type, data, source)
    database.clear_error_and_request_update(cursor, e["rowid"])

def filter_reported_errors(reported_errors, matching_error_ids):
    errors_for_removal = []
    for e in reported_errors:
        if e['error_id'] in matching_error_ids:
            errors_for_removal.append(e)
    return errors_for_removal

def is_edit_allowed_object_based_on_location(osm_object_url, object_data, target_country, verification_function_is_within_given_country):
    print()
    for node_id in osm_bot_abstraction_layer.get_all_nodes_of_an_object(osm_object_url):
        node_data = osm_bot_abstraction_layer.get_data(node_id, "node")
        if verification_function_is_within_given_country(osm_object_url, node_data["lat"], node_data["lon"], target_country) == False:
            return False
    print()
    print(object_data)
    return True

def detailed_verification_function_is_within_given_country(root_osm_object_url, lat, lon, target_country):
    if is_location_clearly_outside_territory(lat, lon, target_country):
        return False
    if is_location_possibly_outside_territory(lat, lon, target_country):
        return check_with_nominatim_is_within_given_country(root_osm_object_url, lat, lon, target_country, debug=True)
    return True

def very_rough_verification_function_is_within_given_country_prefers_false_negatives(root_osm_object_url, lat, lon, target_country):
    if is_location_clearly_inside_territory(lat, lon, target_country) == True:
        return True
    return False

def check_with_nominatim_is_within_given_country(root_osm_object_url, lat, lon, target_country, debug):
    if debug:
        print(lat, lon, "- part of", root_osm_object_url, "was classified as possibly outside based on heuristic - running nominatim to check fully", target_country)
    if get_nominatim_country_code(lat, lon) == target_country:
        return True
    else:
        if debug:
            print(lat, lon, "- part of", root_osm_object_url, "was classified as outside", target_country)
            print(link_to_point(lat, lon))
        return False

def is_location_clearly_outside_territory(lat, lon, target_country):
    if target_country == "pl":
        if lat < 48.166:
            return True
        if lat > 55.678:
            return True
        if lon < 12.480:
            return True
        if lon > 25.137:
            return True
        return False
    elif target_country == "usa":
        if is_inside_bboxfinder_link("http://bboxfinder.com/#23.885838,-168.925781,71.856229,-63.984375", lon, lat):
            return False
        return True
    else:
        raise "unimplemented"
    raise

def is_inside_bboxfinder_link(link, lon, lat):
        # http://bboxfinder.com/#32.990236,-122.921906,48.995537,-95.405273
        coords = link.split("#")[1].split(",")
        min_lat = float(coords[0])
        min_lon = float(coords[1])
        max_lat = float(coords[2])
        max_lon = float(coords[3])
        if lon >= min_lon:
            if lon <= max_lon:
                if lat >= min_lat:
                    if lat <= max_lat:
                        return True

def is_location_clearly_inside_territory(lat, lon, target_country):
    if target_country == "pl":
        if lat >= 48.166:
            return False
        if lat <= 55.678:
            return False
        if lon >= 12.480:
            return False
        if lon <= 25.137:
            return False
        return True
    elif target_country == "usa":
        # http://bboxfinder.com/#32.990236,-122.921906,48.995537,-95.405273
        tested = is_inside_bboxfinder_link("http://bboxfinder.com/#32.990236,-122.921906,48.995537,-95.405273", lon, lat)
        if lon >= -122.921906:
            if lon <= -95.405273:
                if lat >= 32.990236:
                    if lat <= 48.995537:
                        if tested != True:
                            print(tested, lat, lon, is_inside_bboxfinder_link("http://bboxfinder.com/#32.990236,-122.921906,48.995537,-95.405273", lon, lat))
                            raise "wat"
                        return True
        if tested == True:
            print(tested, lat, lon, is_inside_bboxfinder_link("http://bboxfinder.com/#32.990236,-122.921906,48.995537,-95.405273", lon, lat))
            raise "wat"
        print("is_location_clearly_inside_territory should be smarter for USA")
        return False
    else:
        raise "unimplemented"
    raise

def is_location_possibly_outside_territory(lat, lon, target_country):
    if target_country == "pl":
        if lat < 53.943:
            if lat > 51.069:
                if lon < 22.643:
                    if lon > 15.128:
                        return False 
    elif target_country == "usa":
        return False 
        print("is_location_possibly_outside_territory should be smarter for USA")
    else:
        raise "unimplemented"
    return True

def announce_skipping_object_as_outside_area(osm_object_url):
    print("Skipping object", osm_object_url, "- apparently not within catchment area")
    print("---------------------------------")
    print()
    print()

def handle_wikidata_redirect(cursor, reported_errors, area_code, automatic_status):
    errors_for_removal = filter_reported_errors(reported_errors, ['wikipedia wikidata mismatch - follow wikidata redirect'])
    if errors_for_removal == []:
        return
    comment = "handle unstable wikidata ids - apply redirects"
    discussion_urls = {
        'pl': 'https://community.openstreetmap.org/t/propozycja-automatycznej-edycji-tagi-wikidata-co-sa-przekierowaniami/7727',
        'usa': 'https://community.openstreetmap.org/t/bot-edit-proposal-update-wikidata-tag-redirects/106588 and https://osmus.slack.com/archives/C029HV951/p1698760768541059',
    }
    osm_wiki_page_urls = {
        'pl': "https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/fixing_wikidata_tags_pointing_at_redirects_in_Poland",
        'usa': None,
    }

    api = osm_bot_abstraction_layer.get_correct_api(automatic_status, discussion_urls[area_code], osm_wiki_page_urls[area_code])
    source = "wikidata"
    builder = osm_bot_abstraction_layer.ChangesetBuilder("", comment, automatic_status, discussion_urls[area_code], osm_wiki_page_urls[area_code], source)
    started_changeset = False


    detector = wikibrain.wikimedia_link_issue_reporter.WikimediaLinkIssueDetector()

    for e in errors_for_removal:
        data = get_and_verify_data(e)
        if data == None:
            continue
        if is_edit_allowed_object_based_on_location(e['osm_object_url'], data, area_code, detailed_verification_function_is_within_given_country) == False:
            announce_skipping_object_as_outside_area(e['osm_object_url'] + " (handle_wikidata_redirect function)")
            continue
        redirected = detector.get_wikidata_id_after_redirect(data['tag']['wikidata'], forced_refresh=True)
        print()
        if redirected != data['tag']['wikidata']:
            data['tag']['wikidata'] = redirected
        type = e['osm_object_url'].split("/")[3]
        if started_changeset == False:
            started_changeset = True
            builder.create_changeset(api)
        print("handle_wikidata_redirect EDITS",e['osm_object_url'])
        osm_bot_abstraction_layer.update_element(api, type, data)
        database.clear_error_and_request_update(cursor, e["rowid"])

def add_wikidata_tag_from_wikipedia_tag(cursor, reported_errors, area_code, automatic_status):
    errors_for_removal = filter_reported_errors(reported_errors, ['wikidata from wikipedia tag'])
    if errors_for_removal == []:
        return
    if automatic_status == osm_bot_abstraction_layer.manually_reviewed_description():
        raise NotImplementedError
    affected_objects_description = ""
    comment = "add wikidata tag based on wikipedia tag"
    discussion_urls = {
        'pl': 'https://forum.openstreetmap.org/viewtopic.php?id=59925'
    }
    osm_wiki_page_urls = {
        "pl": 'https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/adding_wikidata_tags_based_on_wikipedia_tags_in_Poland'
    }
    api = osm_bot_abstraction_layer.get_correct_api(automatic_status, discussion_urls[area_code], osm_wiki_page_urls[area_code])
    source = "wikidata;OSM"
    builder = osm_bot_abstraction_layer.ChangesetBuilder(affected_objects_description, comment, automatic_status, discussion_urls[area_code], osm_wiki_page_urls[area_code], source)
    started_changeset = False

    for e in errors_for_removal:
        data = get_and_verify_data(e)
        if data == None:
            continue
        if is_edit_allowed_object_based_on_location(e['osm_object_url'], data, area_code, detailed_verification_function_is_within_given_country) == False:
            announce_skipping_object_as_outside_area(e['osm_object_url'] + " (add_wikidata_tag_from_wikipedia_tag function)")
            continue

        wikipedia_tag = data['tag']['wikipedia']
        language_code = wikimedia_connection.get_language_code_from_link(wikipedia_tag)
        article_name = wikimedia_connection.get_article_name_from_link(wikipedia_tag)
        wikidata_id = wikimedia_connection.get_wikidata_object_id_from_article(language_code, article_name)

        reason = ", as wikidata tag may be added based on wikipedia tag"
        change_description = e['osm_object_url'] + " " + str(e['prerequisite']) + " to " + wikidata_id + reason
        print(change_description)
        osm_bot_abstraction_layer.sleep(2)
        data['tag']['wikidata'] = wikidata_id
        type = e['osm_object_url'].split("/")[3]
        if started_changeset == False:
            started_changeset = True
            builder.create_changeset(api)
        print("add_wikidata_tag_from_wikipedia_tag EDITS",e['osm_object_url'])
        osm_bot_abstraction_layer.update_element(api, type, data)
        database.clear_error_and_request_update(cursor, e["rowid"])

    if started_changeset:
        api.ChangesetClose()
        if automatic_status == osm_bot_abstraction_layer.fully_automated_description():
            osm_bot_abstraction_layer.sleep(60)

def add_wikipedia_tag_from_wikidata_tag(cursor, reported_errors, area_code, automatic_status=None):
    errors_for_removal = filter_reported_errors(reported_errors, ['wikipedia from wikidata tag'])
    if errors_for_removal == []:
        return
    if automatic_status == osm_bot_abstraction_layer.manually_reviewed_description():
        raise NotImplementedError
    # osm_bot_abstraction_layer.manually_reviewed_description()
    affected_objects_description = ""
    comment = "add wikipedia tag based on wikidata tag"
    discussion_urls = {
        "pl": 'https://forum.openstreetmap.org/viewtopic.php?id=59888',
    }
    osm_wiki_page_urls = {
        "pl": 'https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/adding_wikipedia_tags_based_on_wikidata_tags_in_Poland'
    }
    api = osm_bot_abstraction_layer.get_correct_api(automatic_status, discussion_urls[area_code], osm_wiki_page_urls[area_code])
    source = "wikidata;OSM"
    builder = osm_bot_abstraction_layer.ChangesetBuilder(affected_objects_description, comment, automatic_status, discussion_urls[area_code], osm_wiki_page_urls[area_code], source)
    started_changeset = False

    for e in errors_for_removal:
        data = get_and_verify_data(e)
        if data == None:
            continue

        if is_edit_allowed_object_based_on_location(e['osm_object_url'], data, area_code, detailed_verification_function_is_within_given_country) == False:
            announce_skipping_object_as_outside_area(e['osm_object_url'] + " (add_wikipedia_tag_from_wikidata_tag function)")
            continue

        new = desired_wikipedia_target_from_report(e)
        reason = ", as wikipedia tag may be added based on wikidata"
        change_description = e['osm_object_url'] + " " + str(e['prerequisite']) + " to " + new + reason
        print(change_description)
        data['tag']['wikipedia'] = new
        type = e['osm_object_url'].split("/")[3]
        if started_changeset == False:
            started_changeset = True
            builder.create_changeset(api)
        osm_bot_abstraction_layer.update_element(api, type, data)
        database.clear_error_and_request_update(cursor, e["rowid"])

    if started_changeset:
        api.ChangesetClose()
        if automatic_status == osm_bot_abstraction_layer.fully_automated_description():
            osm_bot_abstraction_layer.sleep(60)

def link_to_point(lat, lon):
    return "https://www.openstreetmap.org/?mlat=" + str(lat) + "&mlon=" + str(lon) + "#map=10/" + str(lat) + "/" + str(lon)

def has_bot_edit_been_done_on_this_data(cursor, internal_region_name, bot_edit_type):
    data_download_timestamp = database.get_data_download_timestamp(cursor, internal_region_name)
    bot_edit_timestamp = database.get_bot_edit_timestamp(cursor, internal_region_name, bot_edit_type)
    if bot_edit_timestamp < data_download_timestamp:
        return False
    else:
        #print("no need to rerun bot edit, data was not yet updated")
        return True

def handle_follow_wikipedia_redirect_where_target_matches_wikidata(cursor, reported_errors, area_code, automatic_status):
    for e in reported_errors:
        handle_follow_wikipedia_redirect_where_target_matches_wikidata_single(cursor, e, area_code, automatic_status)

def change_to_local_language(cursor, reported_errors, area_code, automatic_status):
    for e in reported_errors:
        change_to_local_language_single(cursor, e, area_code, automatic_status)

def run_bot_edit_if_not_run_and_record_that_it_was_run(cursor, connection, internal_region_name, area_code, fix_function, automatic_status):
    bot_edit_type = fix_function.__name__
    if has_bot_edit_been_done_on_this_data(cursor, internal_region_name, bot_edit_type) == False:
        reported_errors = load_errors(cursor, internal_region_name)
        timestamp = int(time.time())
        fix_function(cursor, reported_errors, area_code, automatic_status)
        database.record_bot_edit_timestamp(cursor, internal_region_name, bot_edit_type, timestamp)
        connection.commit()

def main():
    wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())
    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    # for testing: api="https://api06.dev.openstreetmap.org", 
    # website at https://master.apis.dev.openstreetmap.org/
    print("proper usa bbox checker add")

    for entry in config.get_entries_to_process():
        internal_region_name = entry["internal_region_name"]
        if 'USA' in entry.get('merged_into', []):
            area_code = "usa"
            automated = osm_bot_abstraction_layer.fully_automated_description()
            manual = osm_bot_abstraction_layer.manually_reviewed_description()
            run_bot_edit_if_not_run_and_record_that_it_was_run(cursor, connection, internal_region_name, area_code, handle_follow_wikipedia_redirect_where_target_matches_wikidata, automated)
            #run_bot_edit_if_not_run_and_record_that_it_was_run(cursor, connection, internal_region_name, area_code, handle_wikidata_redirect, manual)
            if datetime.datetime.now() > datetime.datetime(2013, 12, 13):
                print("https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/fixing_wikidata_tags_pointing_at_redirects_in_Poland apply to USA")
                print("https://community.openstreetmap.org/t/bot-edit-proposal-update-wikidata-tag-redirects-where-updated-value-would-match-present-wikipedia-tag/106588")
                print()
                print("https://osmus.slack.com/archives/C029HV951/p1701369028374809 - wikipedia tag unexpected language")

    for entry in config.get_entries_to_process():
        internal_region_name = entry["internal_region_name"]
        if entry.get('language_code', None) == "pl":
            area_code = "pl"
            #print(internal_region_name, "botting")
            automatic_status = osm_bot_abstraction_layer.fully_automated_description()
            run_bot_edit_if_not_run_and_record_that_it_was_run(cursor, connection, internal_region_name, area_code, add_wikipedia_tag_from_wikidata_tag, automatic_status)
            run_bot_edit_if_not_run_and_record_that_it_was_run(cursor, connection, internal_region_name, area_code, add_wikidata_tag_from_wikipedia_tag, automatic_status)
            run_bot_edit_if_not_run_and_record_that_it_was_run(cursor, connection, internal_region_name, area_code, handle_wikidata_redirect, automatic_status)
            run_bot_edit_if_not_run_and_record_that_it_was_run(cursor, connection, internal_region_name, area_code, handle_follow_wikipedia_redirect_where_target_matches_wikidata, automatic_status)
            
            # what is the bot permission status here, actually?
            #run_bot_edit_if_not_run_and_record_that_it_was_run(cursor, connection, reported_errors, internal_region_name, area_code, change_to_local_language)
    connection.commit()
    connection.close()



if __name__ == '__main__':
    main()
