import html
import yaml
import os.path
import datetime
import pprint
import json
import sqlite3

import config
import obtain_from_overpass
import database

def skip_test_cases_before_timestamp():
    return 1699101160

def generate_website_file_for_given_area(cursor, entry):
    reports = reports_for_given_area(cursor, entry['internal_region_name'])
    website_main_title_part = entry['website_main_title_part']
    timestamps = [database.get_data_download_timestamp(cursor, entry['internal_region_name'])]
    ignored_problems = entry.get('ignored_problems', [])
    generate_output_for_given_area(website_main_title_part, reports, timestamps, ignored_problems)

def reports_for_given_area(cursor, internal_region_name):
    query = "SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NOT NULL AND validator_complaint <> ''"
    query_parameters = {"identifier": internal_region_name}
    return query_to_reports_data(cursor, query, query_parameters)

def query_to_reports_data(cursor, query, query_parameters):
    try:
        cursor.execute(query, query_parameters)
        returned = cursor.fetchall()
        reports = []
        for entry in returned:
            rowid, object_type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id = entry
            tags = json.loads(tags)
            validator_complaint = json.loads(validator_complaint)
            reports.append(validator_complaint)
        return reports
    except sqlite3.DatabaseError as e:
        print(query)
        print(query_parameters)
        raise e

def generate_output_for_given_area(main_output_name_part, reports_data, timestamps_of_data, ignored_problem_codes):
    filepath = config.get_report_directory() + '/' + main_output_name_part + ".html"
    issues = for_review()
    issues_without_skipped = [i for i in issues if i not in ignored_problem_codes]
    main_report_count = generate_html_file(reports_data, filepath, issues_without_skipped, "Remember to check whether edits make sense! All reports are on this page because these tasks require human judgment to verify whether the proposed edit makes sense. Some proposed edits will be wrong, in such case they should be not done and problem reported", timestamps_of_data)

    issues = obvious_fixes()
    issues_without_skipped = [i for i in issues if i not in ignored_problem_codes]
    filepath = config.get_report_directory() + '/' + main_output_name_part + " - obvious.html"
    generate_html_file(reports_data, filepath, issues_without_skipped, "Proposed edits at this page are so obvious that automatic edit makes sense.", timestamps_of_data)

    filepath = config.get_report_directory() + '/' + main_output_name_part + " - test.html"
    generate_test_issue_listing(reports_data, timestamps_of_data, filepath, ignored_problem_codes)

    note_unused_errors(reports_data, main_output_name_part)
    return main_report_count

def generate_test_issue_listing(reports_data, timestamps_of_data, filepath, ignored_problem_codes):
    issues = for_tests()
    issues_without_skipped = [i for i in issues if i not in ignored_problem_codes]
    generate_html_file(reports_data, filepath, issues_without_skipped, "This page contains reports that are tested or are known to produce false positives. Be careful with using this data.", timestamps_of_data)

def generate_html_file(errors, output_file_name, types, information_header, timestamps_of_data):
    prefix_of_lines = "\t\t\t"
    total_error_count = 0
    added_reports = {}
    table_of_contents_text = "<ul>"
    reported_errors_text = ""
    with open( output_file_name, 'w') as file:
        file.write(object_list_header(timestamps_of_data))
        file.write(row( '<hr>', prefix_of_lines=prefix_of_lines))
        file.write(row( information_header, prefix_of_lines=prefix_of_lines ))
        file.write(row( '<hr>', prefix_of_lines=prefix_of_lines ))
        #print("LOADING ERRORS START")
        reported_errors = sorted(errors, key=lambda error: error['osm_object_url'])
        #print("LOADING ERRORS END")
        for error_type_id in types:
            #print(error_type_id)
            error_count = 0
            for e in reported_errors:
                if e['error_id'] == error_type_id:
                    error_text = error_description(e, prefix_of_lines + "\t", debug_identifier=output_file_name)
                    if error_text in added_reports:
                        #normal in merged entries
                        continue
                    if error_count == 0:
                        table_of_contents_text += '<li><a href="#' + error_type_id + '">' + error_type_id + '</a></li>'
                        reported_errors_text += row( '<a href="#' + error_type_id + '"><h2 id="' + error_type_id + '">' + error_type_id + '</h2></a>', prefix_of_lines=prefix_of_lines)
                        if e['error_general_intructions'] != None:
                            instructions = htmlify(e['error_general_intructions'])
                            reported_errors_text += row(instructions, prefix_of_lines=prefix_of_lines)
                    added_reports[error_text] = "added!"
                    error_count += 1
                    total_error_count += 1
                    reported_errors_text += error_text
            if error_count != 0:
                reported_errors_text += row( '<a href="https://overpass-turbo.eu/">overpass query</a> usable in JOSM that will load all objects where this specific error is present:', prefix_of_lines=prefix_of_lines )
                query = get_query_for_loading_errors_by_category_from_error_data(errors, printed_error_ids = [error_type_id], format = "josm")
                query_html = "<blockquote>" + escape_from_internal_python_string_to_html_ascii(query) + "</blockquote>"
                reported_errors_text += row(query_html, prefix_of_lines=prefix_of_lines)
                reported_errors_text += row( '<hr>', prefix_of_lines=prefix_of_lines )
        table_of_contents_text += "</ul>"
        file.write(table_of_contents_text)
        file.write(reported_errors_text)
        file.write(html_file_suffix())
    return total_error_count
        
def contact_url():
    return "https://www.openstreetmap.org/message/new/Mateusz%20Konieczny"

def contact_html_prefix():
    return "<a href=\"" + contact_url() + "\">"

def contact_html_suffix():
    return "</a>"

def send_me_a_message_html():
    return contact_html_prefix() + "send me a message" + contact_html_suffix()

def feedback_header():
    return "Feedback? Ideas? Complaints? Suggestions? Request for report about other area? " + send_me_a_message_html() + "!"

def timestamp_listing(timestamps):
    if len(timestamps) == 1:
        return "This page was generated using data obtained on " + date_from_timestamp(timestamps[0]) + "."
    else:
        timestamps_string_list = []
        for timestamp in timestamps:
            timestamps_string_list.append(date_from_timestamp(timestamp))
        return "This page was generated using data obtained on various dates including " + ", ".join(list(set(timestamps_string_list))) + "."

def date_from_timestamp(timestamp):
    if timestamp == 0:
        return "-data-was-not-downloaded-for-now-"
    return str(datetime.date.fromtimestamp(timestamp))

def feedback_request(timestamps_of_data):
    returned = ""
    returned += feedback_header()
    returned += "<br />\n"
    returned += timestamp_listing(timestamps_of_data) + " Please, " + send_me_a_message_html() + " if you want it updated!"
    returned += "<br />\n"
    return returned

def html_file_header():
    returned = ""
    returned += "<html>\n"
    returned += "\t<head>\n"
    returned += '\t\t<link rel="stylesheet" href="https://mapsaregreat.com/style.css" /> <!-- GPLv3 licensed -->\n'
    returned += "\t</head>\n"
    returned += "<body>\n"
    returned += "\t<div class=\"inner\">"
    return returned

def html_file_suffix():
    returned = ""
    returned += "<h1>Other useful resources</h1>"
    returned += '<p>JOSM <a href="https://josm.openstreetmap.de/wiki/Help/Plugin/Wikipedia">Wikipedia plugin</a></p>'
    returned += "<br />\n"
    website = 'https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports'
    stored = 'https://github.com/matkoniecz/OSM-wikipedia-tag-validator-reports'
    returned += '<p class="small">Note to self: online version hosted at <a href="' + website + '">' + website + '</a>, files are stored at <a href="' + stored + '">' + stored + '</a>.'
    returned += "\t\t</div>\n"
    returned += "\t</body>\n"
    returned +=  "</html>\n"
    return returned


def object_list_header(timestamps_of_data):
    returned = ""
    returned += html_file_header()
    returned += feedback_request(timestamps_of_data)
    returned += "<br />\n"
    returned += "<br />\n"
    return returned

def link_to_osm_object(url, tags):
    name = "an affected OSM element that may be improved"
    if "name" in tags:
        name = tags["name"] + " - " + name
    return '<a href="' + url + '" target="_new">' + name + '</a>'

def format_wikipedia_link(string):
    if string == None:
        return "?"
    language_code = language_code_from_wikipedia_string(string)
    language_code = escape_from_internal_python_string_to_html_ascii(language_code)
    article_name = article_name_from_wikipedia_string(string)
    article_name = escape_from_internal_python_string_to_html_ascii(article_name)
    return '<a href="https://' + language_code + '.wikipedia.org/wiki/' + article_name + '" target="_new">' + language_code+":"+article_name + '</a>'

def article_name_from_wikipedia_string(string):
    return string[string.find(":")+1:]

def language_code_from_wikipedia_string(string):
    return string[0:string.find(":")]

def row(text, prefix_of_lines):
    returned = ""
    returned += prefix_of_lines + "</br>\n"
    returned += prefix_of_lines + text + "\n"
    return returned

    returned = ""
    returned += prefix_of_lines + "<tr>\n"
    returned += prefix_of_lines + "\t<td>\n"
    returned += prefix_of_lines + "\t\t" + text + "\n"
    returned += prefix_of_lines + "\t</td>\n"
    returned += prefix_of_lines + "</tr>\n"
    return returned

def current_wikipedia_target(e):
    current = None
    if e['proposed_tagging_changes'] != None:
        for change in e['proposed_tagging_changes']:
            if "wikipedia" in change["to"]:
                if current != None:
                    raise ValueError("multiple original replacements of the same tag (may make sense)")
                current = change["from"]["wikipedia"]
    return current

def desired_wikipedia_target(e):
    desired = None
    if e['proposed_tagging_changes'] != None:
        for change in e['proposed_tagging_changes']:
            if "wikipedia" in change["to"]:
                if desired != None:
                    raise ValueError("multiple incoming replacements of the same tag")
                desired = change["to"]["wikipedia"]
    return desired

def error_description(e, prefix_of_lines, debug_identifier):
    returned = ""
    if e['error_message'] == None:
        print(e)
        print("e['error_message'] is None, debug_identifier:", debug_identifier)
    else:
        returned += row(htmlify(e['error_message']), prefix_of_lines=prefix_of_lines)
    returned += row(link_to_osm_object(e['osm_object_url'], e['tags']), prefix_of_lines=prefix_of_lines)
    desired = desired_wikipedia_target(e)
    if desired != None:
        returned += describe_proposed_relinking(e, prefix_of_lines)
    returned += row( '<hr>', prefix_of_lines=prefix_of_lines)
    return returned

def describe_proposed_relinking(e, prefix_of_lines):
    returned = ""
    current = current_wikipedia_target(e)
    to = desired_wikipedia_target(e)
    if current == None or to == None:
        returned += row("failed to describe proposed relinking here (was: " + str({"current": current, "to": to}) + "), dump of raw proposed_tagging_changes: " + str(e['proposed_tagging_changes']), prefix_of_lines=prefix_of_lines)
        return returned
    if to == current:
        to = "?"
    returned += row( current + " -> " + to, prefix_of_lines=prefix_of_lines)
    if to != "?":
        article_name = article_name_from_wikipedia_string(to)
        returned += row( escape_from_internal_python_string_to_html_ascii(article_name), prefix_of_lines=prefix_of_lines)
    return returned

def note_unused_errors(reported_errors, area):
    for e in reported_errors:
        if e['error_id'] in for_review():
            continue
        if e['error_id'] in obvious_fixes():
            continue
        if e['error_id'] in for_tests():
            continue
        if e['error_id'] in ignored():
            continue
        print('"' + e['error_id'] + '" is not appearing in any generated webpage - in', area)

def for_review():
    returned = [
        'wikipedia tag links to 404',
        'wikidata tag links to 404',
    ]
    for from_tags in [
        "wikipedia and wikidata",
        "wikipedia",
        "wikidata",
    ]:
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a gene")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a violation of law")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a sermon")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a battle")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a transport accident")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a crime")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a disaster")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a television series")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a saying")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a website")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a given name")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a coat of arms")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an object that exists outside physical reality")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an animal or plant (and not an individual one)")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a human")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a vehicle model or class")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a weapon model or class")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a brand")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a sport")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a restaurant chain")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a chain store")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a robbery")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a terrorist organisation")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a historical event")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a software")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a social issue")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an aspect in a geographic region")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a television program")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a podcast")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a protest")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a stampede")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a military operation")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a fictional entity")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a type of structure")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a train category")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an electronic device model series")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a heraldic animal")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a bicycle sharing system")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a history of a geographic region")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a branch of military service")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a type of world view")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an explosion")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a sports competition")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a public transport network")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a recurring sports event")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a religious denomination")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a profession")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a conflict")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a film")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a multinational corporation")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a mental process")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an electric utility")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a shooting")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a cuisine")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a food")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a legal action")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a meeting")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a travel")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a road type")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an overview article")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an electric vehicle charging network")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a postal service")
    returned += [
        "link to a disambiguation page",
        'wikipedia wikidata mismatch',
        'tag may be added based on wikidata',
        'tag may be added based on wikidata - teryt',
        'invalid old-style wikipedia tag',
        'malformed wikidata tag',
        'malformed wikipedia tag',
        "malformed wikipedia tag - nonexisting language code",
        'information board with wikipedia tag, not subject:wikipedia',
        'information board with wikidata tag, not subject:wikidata',
        'blacklisted connection with known replacement',
        'mismatching teryt:simc codes in wikidata and in osm element',
        'wikipedia tag in outdated form and there is mismatch between links',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not',
        'wikipedia/wikidata type tag that is incorrect according to not:* tag',
        "wikipedia tag needs to be removed based on wikidata code and teryt:simc identifier",
        'malformed secondary wikidata tag',

        'secondary wikidata tag links to 404',

        'malformed wikipedia tag - for brand prefixed tags',
        'malformed wikipedia tag - for operator prefixed tags',
        'malformed wikipedia tag - for subject prefixed tags',
        'malformed wikipedia tag - for network prefixed tags',
        'malformed wikipedia tag - for taxon prefixed tags',
        'malformed wikipedia tag - for genus prefixed tags',
        'malformed wikipedia tag - for species prefixed tags',
        'malformed wikipedia tag - for parish prefixed tags',
        'malformed wikipedia tag - for flag prefixed tags',
        'malformed wikipedia tag - for buried prefixed tags',
        'malformed wikipedia tag - for artist prefixed tags',
        'malformed wikipedia tag - for name prefixed tags',
        'malformed wikipedia tag - for name:etymology prefixed tags',
        'malformed wikipedia tag - for old_name:etymology prefixed tags',
        'malformed wikipedia tag - for architect prefixed tags',
        'malformed wikipedia tag - for on_the_list prefixed tags',
        'malformed wikipedia tag - for model prefixed tags',
        'malformed wikipedia tag - for manufacturer prefixed tags',
        'malformed wikipedia tag - for royal_cypher prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for brand prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for operator prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for subject prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for network prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for taxon prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for genus prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for species prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for parish prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for buried prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for artist prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for flag prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for name prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for name:etymology prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for old_name:etymology prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for architect prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for on_the_list prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for model prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for manufacturer prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for royal_cypher prefixed tags',
        'wikipedia wikidata mismatch - for brand prefixed tags',
        'wikipedia wikidata mismatch - for operator prefixed tags',
        'wikipedia wikidata mismatch - for subject prefixed tags',
        'wikipedia wikidata mismatch - for network prefixed tags',
        'wikipedia wikidata mismatch - for taxon prefixed tags',
        'wikipedia wikidata mismatch - for genus prefixed tags',
        'wikipedia wikidata mismatch - for species prefixed tags',
        'wikipedia wikidata mismatch - for parish prefixed tags',
        'wikipedia wikidata mismatch - for buried prefixed tags',
        'wikipedia wikidata mismatch - for artist prefixed tags',
        'wikipedia wikidata mismatch - for flag prefixed tags',
        'wikipedia wikidata mismatch - for name prefixed tags',
        'wikipedia wikidata mismatch - for name:etymology prefixed tags',
        'wikipedia wikidata mismatch - for old_name:etymology prefixed tags',
        'wikipedia wikidata mismatch - for architect prefixed tags',
        'wikipedia wikidata mismatch - for on_the_list prefixed tags',
        'wikipedia wikidata mismatch - for model prefixed tags',
        'wikipedia wikidata mismatch - for manufacturer prefixed tags',
        'wikipedia wikidata mismatch - for royal_cypher prefixed tags',

        "species secondary tag links something that is not species according to wikidata (checking P105)",
        "bridge:wikipedia - move to bridge outline",
        "bridge:wikidata - move to bridge outline",
        "bridge:wikipedia and bridge:wikidata - move to bridge outline",

        'wikipedia tag links bot wikipedia',
        "genus secondary tag links something that is not genus according to wikidata (checking P105)",

        'malformed secondary wikidata tag - for brand prefixed tags',
        'malformed secondary wikidata tag - for operator prefixed tags',
        'malformed secondary wikidata tag - for subject prefixed tags',
        'malformed secondary wikidata tag - for network prefixed tags',
        'malformed secondary wikidata tag - for taxon prefixed tags',
        'malformed secondary wikidata tag - for genus prefixed tags',
        'malformed secondary wikidata tag - for species prefixed tags',
        'malformed secondary wikidata tag - for parish prefixed tags',
        'malformed secondary wikidata tag - for flag prefixed tags',
        'malformed secondary wikidata tag - for buried prefixed tags',
        'malformed secondary wikidata tag - for artist prefixed tags',
        'malformed secondary wikidata tag - for name prefixed tags',
        'malformed secondary wikidata tag - for name:etymology prefixed tags',
        'malformed secondary wikidata tag - for old_name:etymology prefixed tags',
        'malformed secondary wikidata tag - for architect prefixed tags',
        'malformed secondary wikidata tag - for on_the_list prefixed tags',
        'malformed secondary wikidata tag - for model prefixed tags',
        'malformed secondary wikidata tag - for manufacturer prefixed tags',
        'malformed secondary wikidata tag - for royal_cypher prefixed tags',
        "malformed secondary wikidata tag - for owner prefixed tags",
        "malformed secondary wikidata tag - for artist_name prefixed tags",
    ]
    return returned

def obvious_fixes():
    return [
        'wikipedia tag unexpected language',
        'wikipedia tag from wikipedia tag in an outdated form',
        'wikipedia wikidata mismatch - follow wikipedia redirect',
        'wikipedia from wikidata tag',
        'wikipedia from wikidata tag, unexpected language',
        'wikidata from wikipedia tag',
        'wikipedia tag in an outdated form for removal',
        'wikipedia tag from wikipedia tag in an outdated form and wikidata',
        'wikipedia wikidata mismatch - follow wikidata redirect',
        "wikipedia tag using redirecting language code",
        "wikipedia needs to be updated based on wikidata code and teryt:simc identifier",

        'wikipedia wikidata mismatch - follow wikidata redirect - for brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for operator prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for subject prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for network prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for taxon prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for genus prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for species prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for parish prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for buried prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for artist prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for flag prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for name prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for name:etymology prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for old_name:etymology prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for architect prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for on_the_list prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for model prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for manufacturer prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for tank:model prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for network:2 prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for operator prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for subject prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for network prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for taxon prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for genus prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for species prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for parish prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for buried prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for artist prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for flag prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for name prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for name:etymology prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for old_name:etymology prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for architect prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for on_the_list prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for model prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for manufacturer prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for tank:model prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for network:2 prefixed tags',
    ]

def for_tests():
    returned = []
    for from_tags in [
        "wikipedia and wikidata",
        "wikipedia",
        "wikidata",
    ]:
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a general industry")

        # free flight mess
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a physical process")

        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a belief")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an economic sector")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an academic discipline")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a research")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an award")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an insurance")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a police operation")
    returned += [

        # TODO detect when directly linked entry has https://www.wikidata.org/wiki/Property:P1282 set ("OpenStreetMap tag or key")
        # TODO take down https://taginfo.openstreetmap.org/keys/related%3Awikipedia#chronology before it lays eggs - initial attempts at https://www.openstreetmap.org/changeset/63434500 https://www.openstreetmap.org/changeset/131746422
        # TODO: detect image=* that should be wikimedia_commons=*
        # TODO: check above for 404 erorrs
        # TODO: check wikimedia_commons=* for invalid syntax and 404 errors

        # enable after flushing this error classes from the database as some were processed
        # and after at least attemped processing of OSM-specific issues
        # Note that processing this helps Wikidata more than anything else
        "genus secondary tag links something that is not species according to wikidata",
        "species secondary tag links something that is not species according to wikidata",

        "taxon secondary tag links something that is not taxon according to wikidata (checking regular ontology)",

        "malformed secondary wikidata tag - for post_office:service_provider prefixed tags",
        "malformed secondary wikidata tag - for delivery:partner prefixed tags",
        "malformed secondary wikidata tag - for post_office:brand prefixed tags",

        'malformed wikipedia tag - for artist_name prefixed tags',
        'wikipedia wikidata mismatch - for artist_name prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for artist_name prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for artist_name prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for artist_name prefixed tags',

        "no longer existing brand (according to Wikidata) - and marked as active shop in OSM, with tagging referring to defunct one",

        "malformed secondary wikidata tag - for official_name prefixed tags", # TODO what it even means?
    ]
    return returned

def ignored():
    returned = [
        # TODO - source:species should not be validated...
        'malformed secondary wikidata tag - for source:species prefixed tags',
        "malformed secondary wikidata tag - for image:license prefixed tags",


        # see https://www.wikidata.org/wiki/User:Mateusz_Konieczny/failing_testcases
        # also, I slowly create notes for Sprint cases
        # reactivate only of wikidata issues will be processed or when I run out of notes to create (hahaha)
        "no longer existing brand (according to Wikidata) - and marked as active shop in OSM",

        # see
        # https://www.openstreetmap.org/note/3965037
        # https://www.openstreetmap.org/note/3965039
        # https://www.openstreetmap.org/note/3965033
        # https://www.openstreetmap.org/note/3965031
        "no longer existing brand (according to Wikidata) - and tag processing has not worked well",

        'no longer existing object (according to Wikidata)', # many false positives, for example airport where runway remains may be mapped in OSM while not in Wikidata
        # TODO: redo this, but skip cases where OSM has disused: abandoned: etc
        # for example https://www.openstreetmap.org/node/1042007056 should be disused: prefixed or Wikidata is wrong
    ]
    for from_tags in [
        "wikipedia and wikidata",
        "wikipedia",
        "wikidata",
    ]:
        # mostly wikidata bugs were found - is it really priority? Enabling MR, bot edits for wikidata redirects
        # and wider: OSM bot edits
        # and wider: OSMF activities
        # and wider: see my TODO list....
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an event")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a behavior")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a human behavior")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an intentional human activity")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a human activity")

        # many protestant churches appear here, figure it out as low priority
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a tradition")

        # how we should link it then?
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a religious denomination")

        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a signage")

        # many find problem on Wikidata, though some are actual tagging issues in OSM
        # review again after some time, when I run out of more interesting ones
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an art genre")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a genre")

        # extremely likely to be wikidata issue, dig it out after restoring other ones (then advertise to wikidata people, or just generate listing of such cases blindly)
        # reports problem on Wikidata, useful for fixing Wikidata - not OSM
        # once many collect maybe reporting then in one big group may make sense as they can still hide
        # things from my hidden gem processor
        # or implement skipping this errors also there? Wikidata bug category? 
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a church architecture")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a religious sculpture (genre)")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a spheroidal weathering")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a surface mining")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a construction (as economic activity)")

        # tricky with office=goverment, postpone handling untill less tricky stuff is dealt with
        # (including on Wikidata side)
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a government program")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a research project")

        # lets ignore it for now
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a geodetic control network")

        # horribly tricky mess due to denominations (and I deleted MR task without renaming it what makes things worse - and requires some special handling)
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a social movement")

        # some people claim that it is linkable like office=company
        # lets keep it here for now
        # TODO
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a radio station")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a broadcaster")

        # not sure is it even invalid to map...
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a music festival")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to an annual event")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a festival")
        returned.append("should use a secondary wikipedia tag - linking from " + from_tags + " tag to a film festival")


    returned += [
        # TODO
        # should it even exist?
        # add detection of them in get_the_most_important_problem_generic in wikibrain
        # before any validity checking
        'malformed wikipedia tag - for razed:brand prefixed tags',
        'wikipedia wikidata mismatch - for razed:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for razed:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for razed:brand prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for razed:brand prefixed tags',
        'malformed wikipedia tag - for removed:brand prefixed tags',
        'wikipedia wikidata mismatch - for removed:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for removed:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for removed:brand prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for removed:brand prefixed tags',
        'malformed wikipedia tag - for was:brand prefixed tags',
        'wikipedia wikidata mismatch - for was:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for was:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for was:brand prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for was:brand prefixed tags',
        'malformed wikipedia tag - for disused:brand prefixed tags',
        'wikipedia wikidata mismatch - for disused:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for disused:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for disused:brand prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for disused:brand prefixed tags',
        'malformed wikipedia tag - for construction:brand prefixed tags',
        'wikipedia wikidata mismatch - for construction:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for construction:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for construction:brand prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for construction:brand prefixed tags',
        'malformed wikipedia tag - for abandoned:brand prefixed tags',
        'wikipedia wikidata mismatch - for abandoned:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for abandoned:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for abandoned:brand prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for abandoned:brand prefixed tags',
        'malformed wikipedia tag - for abandoned:operator prefixed tags',
        'wikipedia wikidata mismatch - for abandoned:operator prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for abandoned:operator prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for abandoned:operator prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for abandoned:operator prefixed tags',

        # related:wikipedia should not exist in the first place, maybe it should be reported as a problem on its own?
        # https://taginfo.openstreetmap.org/keys/related%3Awikipedia#chronology
        'malformed wikipedia tag - for related prefixed tags',
        'wikipedia wikidata mismatch - for related prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for related prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for related prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for related prefixed tags',

        # being turned into model prefix - report for change?
        'malformed wikipedia tag - for vehicle prefixed tags',
        'wikipedia wikidata mismatch - for vehicle prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for vehicle prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for vehicle prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for vehicle prefixed tags',

        # what is this? Investigate
        # almost certainly should be moved to man_made=bridge area
        # https://taginfo.openstreetmap.org/keys/bridge%3Awikipedia#overview
        'malformed wikipedia tag - for bridge prefixed tags',
        "malformed secondary wikidata tag - for bridge prefixed tags",
        'wikipedia wikidata mismatch - for bridge prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for bridge prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for bridge prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for bridge prefixed tags',

        # investigate terribleness after 15:00
        # https://taginfo.openstreetmap.org/keys/tunnel%3Awikipedia#overview
        # note that following started to be reported recently:
        # bridge:wikipedia and bridge:wikidata - move to bridge outline
        # bridge:wikipedia - move to bridge outline
        # bridge:wikidata - move to bridge outline
        'malformed wikipedia tag - for tunnel prefixed tags',
        'wikipedia wikidata mismatch - for tunnel prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for tunnel prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for tunnel prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for tunnel prefixed tags',

        # investigate terribleness after 15:00
        'malformed wikipedia tag - for old_wikidata prefixed tags',
        'wikipedia wikidata mismatch - for old_wikidata prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for old_wikidata prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for old_wikidata prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for old_wikidata prefixed tags',

        # what is this? Investigate after 15:00
        #TODO remove from databse and clear this entries
        'malformed wikipedia tag - for object prefixed tags',
        'wikipedia wikidata mismatch - for object prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for object prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for object prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for object prefixed tags',

        # what is this? Investigate after 15:00
        'malformed wikipedia tag - for post_office:brand prefixed tags',
        'wikipedia wikidata mismatch - for post_office:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for post_office:brand prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for post_office:brand prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for post_office:brand prefixed tags',

        'malformed wikipedia tag - for post_office:service_provider prefixed tags',
        'wikipedia wikidata mismatch - for post_office:service_provider prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for post_office:service_provider prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for post_office:service_provider prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for post_office:bservice_provider and prefixed tags',

        'malformed wikipedia tag - for branch prefixed tags',
        'wikipedia wikidata mismatch - for branch prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for branch prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for branch prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for branch prefixed tags',

        # not really justified, may be tricky to convince community about this
        'malformed wikipedia tag - for was prefixed tags',
        'wikipedia wikidata mismatch - for was prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for was prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for was prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for was prefixed tags',

        'malformed wikipedia tag - for abandoned prefixed tags',
        'wikipedia wikidata mismatch - for abandoned prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for abandoned prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for abandoned prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for abandoned prefixed tags',

        'malformed wikipedia tag - for disused prefixed tags',
        'wikipedia wikidata mismatch - for disused prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for disused prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for disused prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for disused prefixed tags',

        'malformed wikipedia tag - for razed prefixed tags',
        'wikipedia wikidata mismatch - for razed prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for razed prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for razed prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for razed prefixed tags',

        'malformed wikipedia tag - for removed prefixed tags',
        'wikipedia wikidata mismatch - for removed prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for removed prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for removed prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for removed prefixed tags',


        # skip as not really important?
        'malformed wikipedia tag - for not prefixed tags',
        'wikipedia wikidata mismatch - for not prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for not prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for not prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for not prefixed tags',

        # skip as not really important?
        'malformed wikipedia tag - for supervisor_district prefixed tags',
        'wikipedia wikidata mismatch - for supervisor_district prefixed tags',
        'wikipedia wikidata mismatch - follow wikipedia redirect - for supervisor_district prefixed tags',
        'wikipedia wikidata mismatch - follow wikidata redirect - for supervisor_district prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for supervisor_district prefixed tags',


        # how say https://www.openstreetmap.org/node/1968342133 should be tagged?
        'should use a secondary wikipedia tag - linking to a geodetic control network',

        # is https://www.openstreetmap.org/way/234792502
        # really wrong?
        'should use a secondary wikipedia tag - linking to a music festival',

        # too often problem is on Wikidata side - generate list and show it to Wikidata community?
        'should use a secondary wikipedia tag - linking from wikipedia tag to an uncoordinable generic object',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to an uncoordinable generic object',
        'should use a secondary wikipedia tag - linking from wikidata tag to an uncoordinable generic object',

        # too many mistakes. TODO: just remove it (or maybe keep as a reminder?)
        'should use a secondary wikipedia tag - linking from wikidata tag to a company that has multiple locations',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a company that has multiple locations',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a company that has multiple locations',

        # I am not so interested in Wikidata, and want to be less interested
        #
        # Wikidata community is also not strongly interested, but there is an occasional person that can be feed
        # start from processing known reports in the wikidata structure test cases
        #
        # https://www.wikidata.org/wiki/Wikidata_talk:WikiProject_Ontology
        # https://www.wikidata.org/wiki/Wikidata:Project_chat/Archive/2022/08#Subclass_trees
        # https://wiki.openstreetmap.org/wiki/Talk:Data_items#Broken_Wikidata_ontology

        # inherently Wikidata issue, lets advertise it after Wikidata Ontology is promoted and 
        # has entirely fixed deep structural issues (AKA never)
        # this reports cases where name:etymology:wikidata:missing tag is present what claims
        # that Wikidata is missing entries
        # See also https://www.wikidata.org/w/index.php?title=Wikidata:Project_chat&oldid=1800873697#Is_someone_who_is_a_patron_of_a_street_always_notable_enough_for_Wikidata_identifier?
        'name:etymology:wikidata:missing',

        'link to a list', # even I am not really convinced it is a problem

        #'no longer existing object', 'no longer existing brand', # renamed, should be removed once database updates or is forced to update # now flooded with errors anyway

    ]
    return returned

def htmlify(string):
    escaped = html.escape(string)
    escaped_ascii = escape_from_internal_python_string_to_html_ascii(escaped)
    return escaped_ascii.replace("\n", "<br />")

def escape_from_internal_python_string_to_html_ascii(string):
    return str(string).encode('ascii', 'xmlcharrefreplace').decode()

def get_query_for_loading_errors_by_category_from_error_data(reported_errors, printed_error_ids, format, extra_query_part=""):
    returned = get_query_header(format)
    for e in sorted(reported_errors, key=lambda error: error['osm_object_url'] ):
        if e['error_id'] in printed_error_ids:
            type = e['osm_object_url'].split("/")[3]
            id = e['osm_object_url'].split("/")[4]
            if type == "relation" and format == "maproulette":
                #relations skipped due to https://github.com/maproulette/maproulette2/issues/259
                continue
            returned += type+'('+id+')' + get_prerequisite_in_overpass_query_format(e) + ';' + "\n"
    returned += extra_query_part
    returned += get_query_footer(format) + "//" + str(printed_error_ids)
    return returned

def get_query_header(format):
    header = ""
    if format == "maproulette":
        header+= '[out:json]'
    elif format == "josm":
        header += '[out:xml]'
    else:
        assert(False)
    header += "[timeout:3600]"
    header += ";"
    header += "\n"
    header += '('
    header += "\n"
    return header

def get_query_footer(format):
    if format == "maproulette":
        return '); out body geom qt;'
    elif format == "josm":
        return '); (._;>;); out meta qt;'
    else:
        assert(False)

def escape_for_overpass(text):
    text = text.replace("\\", "\\\\")
    return text.replace("'", "\\'")

def get_prerequisite_in_overpass_query_format(error):
    try:
        return tag_dict_to_overpass_query_format(error['prerequisite'])
    except KeyError:
        return ""

def tag_dict_to_overpass_query_format(tags):
    returned = ""
    for key in ordered_keys(tags):
        escaped_key = escape_for_overpass(key)
        if tags[key] == None:
            returned += "['" + escaped_key + "'!~'.*']"
        else:
            escaped_value = escape_for_overpass(tags[key])
            returned += "['" + escaped_key + "'='" + escaped_value + "']"
    return returned

def ordered_keys(dictionary):
    keys = list(dictionary.keys())
    return sorted(keys)

def index_page_description():
    website_html = ""
    website_html += '<p>This page lists OpenStreetMap objects that have <a href="https://wiki.openstreetmap.org/wiki/Key:wikipedia">wikipedia</a> / <a href="https://wiki.openstreetmap.org/wiki/Key:wikipedia">wikidata</a> tags with some problems.</p>'
    website_html += '<p>For example, it allows to detect cases where <a href="https://www.openstreetmap.org/way/693854629/history">an incorrect object was linked</a>, a link leads to a deleted page or there is some other issue.</p>\n'
    website_html += '<p>This tool is an <a href="https://github.com/matkoniecz/OSM-wikipedia-tag-validator#story-behing-this-tool">unexpected result</a> of creating a detector of interesting places based on OSM Data and Wikipedia. It turned out to require a filter to avoid invalid links. As detected links can be often fixed and it is better to remove invalid rather than keep them, I am sharing this tool.</p>\n'
    website_html += "</hr>\n"
    website_html += "</br>\n"
    return website_html

def all_timestamps_for_index_page(cursor):
    all_timestamps = []
    for entry in config.get_entries_to_process():
        if "hidden" in entry:
            if entry["hidden"] == True:
                continue
        all_timestamps.append(database.get_data_download_timestamp(cursor, entry['internal_region_name']))
    return all_timestamps

def html_header_for_index_page(all_timestamps):
    index_header = ""
    index_header += html_file_header() + "\n" + index_page_description()
    index_header += feedback_request(all_timestamps) + "\n"
    index_header += "</br>\n"
    index_header += "</hr>\n"
    index_header += "</br>\n"
    return index_header

def list_of_processed_entries_for_each_merged_group():
    merged_outputs = {}
    for entry in config.get_entries_to_process():
        if entry.get('merged_into', None) != None:
            for parent in entry['merged_into']:
                if parent not in merged_outputs:
                    merged_outputs[parent] = []
                merged_outputs[parent].append(entry)
    return merged_outputs

def all_error_reports_of_area(cursor, internal_region_name):
    cursor.execute("SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NOT NULL AND validator_complaint <> ''", {"identifier": internal_region_name})
    return cursor.fetchall()

def write_index_and_merged_entries(cursor):
    all_timestamps = all_timestamps_for_index_page(cursor)
    website_html = html_header_for_index_page(all_timestamps)

    completed = ""
    merged_outputs = list_of_processed_entries_for_each_merged_group()

    for merged_code in merged_outputs.keys():
        timestamps_of_data = []
        merged_primary_reports = []
        merged_secondary_reports = []
        for component in merged_outputs[merged_code]:
            ignored_problems = component.get('ignored_problems', [])
            if "hidden" in component:
                if component["hidden"] == True:
                    continue
            for entry in all_error_reports_of_area(cursor, component['internal_region_name']):
                rowid, object_type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id = entry
                #tags = json.loads(tags) - unused
                validator_complaint = json.loads(validator_complaint)
                if error_id not in ignored_problems:
                    if error_id in for_review():
                        merged_primary_reports.append(validator_complaint)
                    else:
                        merged_secondary_reports.append(validator_complaint)
            timestamps_of_data.append(database.get_data_download_timestamp(cursor, component['internal_region_name']))

        # ignored reports were used to filter out reports for each component
        generate_output_for_given_area(merged_code, merged_primary_reports + merged_secondary_reports, timestamps_of_data, [])
        
        primary_report_count = len(merged_primary_reports)
        if(list(set(timestamps_of_data)) == [0]):
            print(merged_code, "has no collected data at all, skipping")
        else:
            line = '<a href = "./' + htmlify(merged_code) + '.html">' + htmlify(merged_code) + '</a> ' + problem_count_string(primary_report_count) + '\n'
            if primary_report_count > 0:
                website_html += line
            else:
                completed += line

    for entry in config.get_entries_to_process():
        if "hidden" in entry:
            if entry["hidden"] == True:
                continue
        website_main_title_part = entry['website_main_title_part']
        filename = website_main_title_part + '.html'
        report_count = human_review_problem_count_for_given_internal_region_name(cursor, entry['internal_region_name'])
        report_count_string = problem_count_string(report_count)
        line = '<a href = "./' + htmlify(filename) + '">' + htmlify(website_main_title_part) + '</a> ' + report_count_string + '\n'
        if database.get_data_download_timestamp(cursor, entry['internal_region_name']) == 0:
            print(entry['internal_region_name'], "has no collected data at all, skipping")
        else:
            if report_count != 0:
                website_html += line
            else:
                completed += line
    website_html += "<br>\n"
    website_html += "<h1>Finished, congratulations :)</h1>\n"
    if completed == "":
        completed = "<p>nothing for now :(<p>\n"
    website_html += completed
    website_html += html_file_suffix()
    with open(config.get_report_directory() + '/' + 'index.html', 'w') as index:
        index.write(website_html)
    generate_shared_test_results_page(cursor, all_timestamps)

def generate_shared_test_results_page(cursor, all_timestamps):
    query = "SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id FROM osm_data WHERE validator_complaint IS NOT NULL AND validator_complaint <> '' AND download_timestamp > :timestamp"
    query_parameters = {"timestamp": str(skip_test_cases_before_timestamp())}
    reports_data = query_to_reports_data(cursor, query, query_parameters)
    filepath = config.get_report_directory() + '/' + "all merged - test.html"
    ignored_problem_codes = []
    generate_test_issue_listing(reports_data, all_timestamps, filepath, ignored_problem_codes)

def human_review_problem_count_for_given_internal_region_name(cursor, internal_region_name):
    # TODO smart COUNT() may be better
    cursor.execute("SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NOT NULL AND validator_complaint <> ''", {"identifier": internal_region_name})
    returned = cursor.fetchall()
    report_count = 0
    for entry in returned:
        rowid, object_type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id = entry
        #validator_complaint = json.loads(validator_complaint) - unused
        if(error_id in for_review()):
            report_count += 1
    return report_count

def problem_count_string(report_count):
    if report_count == 1:
        return '(found ' + str(report_count) + ' problem)</br>'
    return '(found ' + str(report_count) + ' problems)</br>'

if __name__ == "__main__":
    raise "unsupported, expected to be used as a library"
