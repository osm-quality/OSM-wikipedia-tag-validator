import html
import yaml
import os.path
import datetime
import pprint
import json
import sqlite3

import config
import obtain_from_overpass

def generate_website_file_for_given_area(cursor, entry):
    reports = reports_for_given_area(cursor, entry['internal_region_name'])
    website_main_title_part = entry['website_main_title_part']
    timestamps = [obtain_from_overpass.get_data_timestamp(cursor, entry['internal_region_name'])]
    ignored_problems = entry.get('ignored_problems', [])
    generate_output_for_given_area(website_main_title_part, reports, timestamps, ignored_problems)

def reports_for_given_area(cursor, internal_region_name):
    query = "SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NOT NULL AND validator_complaint <> ''"
    query_parameters = {"identifier": internal_region_name}
    return query_to_reports_data(cursor, query, query_parameters)

def query_to_reports_data(cursor, query, query_parameters):
    try:
        cursor.execute(query, query_parameters)
        returned = cursor.fetchall()
        reports = []
        for entry in returned:
            rowid, object_type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint = entry
            tags = json.loads(tags)
            validator_complaint = json.loads(validator_complaint)
            reports.append(validator_complaint)
        return reports
    except sqlite3.DatabaseError as e:
        print(internal_region_name)
        raise e

def generate_output_for_given_area(main_output_name_part, reports_data, timestamps_of_data, ignored_problem_codes):
    filepath = config.get_report_directory() + '/' + main_output_name_part + ".html"
    issues = for_review()
    issues_without_skipped = [i for i in issues if i not in ignored_problem_codes]
    main_report_count = generate_html_file(reports_data, filepath, issues_without_skipped, "Remember to check whatever edit makes sense! All reports are at this page because this tasks require human judgment to verify whatever proposed edit makes sense.", timestamps_of_data)

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
                    error_text = error_description(e, prefix_of_lines + "\t")
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

def error_description(e, prefix_of_lines):
    returned = ""
    returned += row(htmlify(e['error_message']), prefix_of_lines=prefix_of_lines)
    returned += row(link_to_osm_object(e['osm_object_url'], e['tags']), prefix_of_lines=prefix_of_lines)
    desired_deprecated_form = e['desired_wikipedia_target'] #TODO - eliminate use of deprecated form, starting from bot
    current_deprecated_form = e['current_wikipedia_target'] #TODO - eliminate use of deprecated form, starting from bot
    desired = None
    current = None
    if e['proposed_tagging_changes'] != None:
        for change in e['proposed_tagging_changes']:
            if "wikipedia" in change["to"]:
                if desired != None:
                    raise ValueError("multiple incoming replacements of the same tag")
                if current != None:
                    raise ValueError("multiple original replacements of the same tag (may make sense)")
                desired = change["to"]["wikipedia"]
                current = change["from"]["wikipedia"]
    if desired_deprecated_form != None:
        if desired_deprecated_form != desired:
            for _ in range(30):
                print("+++++++++++++++++ MISMATCH on desired ++++++++++++++++++++++")
            pprint.pprint(e['proposed_tagging_changes'])
            pprint.pprint(e['desired_wikipedia_target'])
            pprint.pprint(e)
            raise
    if current_deprecated_form != None:
        if current_deprecated_form != current:
            for _ in range(30):
                print("++++++++++++++ MISMATCH on current +++++++++++++++++++++++++")
            pprint.pprint(e['proposed_tagging_changes'])
            pprint.pprint(e['current_wikipedia_target'])
            pprint.pprint(e)
            raise
        for _ in range(30):
            print("++++++++++++++ deprecated current form exists at all, why? +++++++++++++++++++++++++")
        pprint.pprint(e['proposed_tagging_changes'])
        pprint.pprint(e['current_wikipedia_target'])
        pprint.pprint(e)

    if e['desired_wikipedia_target'] != None:
        returned += describe_proposed_relinking(e, prefix_of_lines)
    returned += row( '<hr>', prefix_of_lines=prefix_of_lines)
    return returned

def describe_proposed_relinking(e, prefix_of_lines):
    returned = ""
    current = format_wikipedia_link(e['current_wikipedia_target'])
    to = format_wikipedia_link(e['desired_wikipedia_target'])
    if to == current:
        to = "?"
    returned += row( current + " -> " + to, prefix_of_lines=prefix_of_lines)
    if to != "?":
        article_name = article_name_from_wikipedia_string(e['desired_wikipedia_target'])
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
    return [
        'wikipedia tag links to 404',
        'wikidata tag links to 404',
        'should use a secondary wikipedia tag - linking to a gene',
        'should use a secondary wikipedia tag - linking to a violation of law',
        'should use a secondary wikipedia tag - linking to a sermon',
        'link to an unlinkable article',
        'wikipedia wikidata mismatch',
        'should use a secondary wikipedia tag - linking to a battle',
        "should use a secondary wikipedia tag - linking to a transport accident",
        "should use a secondary wikipedia tag - linking to a crime",
        "should use a secondary wikipedia tag - linking to a film",
        "should use a secondary wikipedia tag - linking to a disaster",
        'should use a secondary wikipedia tag - linking to a website',
        'should use a secondary wikipedia tag - linking to a television series',
        'should use a secondary wikipedia tag - linking to a saying',
        'should use a secondary wikipedia tag - linking to a website',
        'should use a secondary wikipedia tag - linking to a given name',
        'should use a secondary wikipedia tag - linking to a coat of arms',
        'tag may be added based on wikidata',
        'tag may be added based on wikidata - teryt',
        'invalid old-style wikipedia tag',
        'malformed wikidata tag',
        'malformed wikipedia tag',
        "malformed wikipedia tag - nonexisting language code",
        'information board with wikipedia tag, not subject:wikipedia',
        'information board with wikidata tag, not subject:wikidata',
        'should use a secondary wikipedia tag - linking to a human',
        'should use a secondary wikipedia tag - linking to an animal or plant (and not an individual one)',
        'should use a secondary wikipedia tag - linking to a vehicle model or class',
        'should use a secondary wikipedia tag - linking to a weapon model or class',
        "should use a secondary wikipedia tag - linking to a brand",
        'should use a secondary wikipedia tag - linking to a restaurant chain',
        'should use a secondary wikipedia tag - linking to a chain store',
        'blacklisted connection with known replacement',
        'should use a secondary wikipedia tag - linking to a robbery',
        'should use a secondary wikipedia tag - linking to a terrorist organisation',
        'should use a secondary wikipedia tag - linking to a historical event',
        'mismatching teryt:simc codes in wikidata and in osm element',
        'wikipedia tag in outdated form and there is mismatch between links',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not',
        'wikipedia/wikidata type tag that is incorrect according to not:* tag',
        "wikipedia tag needs to be removed based on wikidata code and teryt:simc identifier",
        'should use a secondary wikipedia tag - linking to a social issue',
        'should use a secondary wikipedia tag - linking to a social movement',
        'should use a secondary wikipedia tag - linking to an aspect in a geographic region',
        'should use a secondary wikipedia tag - linking to a television program',
        'should use a secondary wikipedia tag - linking to a podcast',
        'should use a secondary wikipedia tag - linking to a protest',
        'should use a secondary wikipedia tag - linking to a stampede',
        'should use a secondary wikipedia tag - linking to a festival',
        'should use a secondary wikipedia tag - linking to a fictional entity',
        'should use a secondary wikipedia tag - linking to a type of structure',
        'should use a secondary wikipedia tag - linking to a train category',
        'should use a secondary wikipedia tag - linking to an electronic device model series',
        'should use a secondary wikipedia tag - linking to a physical process',
        'malformed secondary wikidata tag',
    ]

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
    ]

def for_tests():
    return [
        'should use a secondary wikipedia tag - linking to a branch of military service',
        'should use a secondary wikipedia tag - linking to a history of a geographic region',
        # TODO detect when directly linked entry has https://www.wikidata.org/wiki/Property:P1282 set
        # TODO take down https://taginfo.openstreetmap.org/keys/related%3Awikipedia#chronology before it lays eggs

        # TODO: detect image=* that should be wikimedia_commons=*
        # TODO: check above for 404 erorrs
        # TODO: check wikimedia_commons=* for invalid syntax and 404 errors
        'secondary wikidata tag links to 404',
        'no longer existing object',
        'tag conflict with wikidata value',
        'tag conflict with wikidata value - testing',
        'wikipedia tag unexpected language, article missing',
        'tag conflict with wikidata value - boring',
        'tag may be added based on wikidata - website', # dubious copyright
        'should use a secondary wikipedia tag - linking to a public transport network',
        'should use a secondary wikipedia tag - linking to a bicycle sharing system',
    ]

def ignored():
    return [
        # add TOC and roll out new edits first
        #
        # some things are fixed in Wikidata and my cache is wrong
        # growing number of miscaches
        #
        # multiple test cases created
        # enable it after Wikidata community runs out of what I reported
        # AND all tests in wikibrain are passing
        #
        # or when I confirmed that I can clear
        # /media/mateusz/OSM_cache/wikimedia-connection-cache
        # and reuse database to avoid redownloading entries for
        # entries not reported as broken now (or bite bullet and redownload everything
        # or switch to Wikipedia/Wikidata dumps instead of API)
        #
        # or reenable redownloading cached data on reports being generated
        # (needs "delete cache if older than X" in upstream repo) 
        'should use a secondary wikipedia tag - linking to an art genre',
        'should use a secondary wikipedia tag - linking to an event',
        'should use a secondary wikipedia tag - linking to a behavior',

        # enable after running out of art genre stuff and fixing reports after ferries
        'should use a secondary wikipedia tag - linking to a general industry',

        # tricky with office=goverment, postpone handling untill less tricky stuff is dealt with
        # (including on Wikidata side)
        'should use a secondary wikipedia tag - linking to a government program',

        # too often problem is on Wikidata side - generate list and show it to Wikidata community?
        'should use a secondary wikipedia tag - linking to an uncoordinable generic object',

        # too many mistakes. TODO: just remove it (or maybe keep as a reminder?)
        'should use a secondary wikipedia tag - linking to a company that has multiple locations',

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
    ]

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
        all_timestamps.append(obtain_from_overpass.get_data_timestamp(cursor, entry['internal_region_name']))
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

def write_index_and_merged_entries(cursor):
    all_timestamps = all_timestamps_for_index_page(cursor)
    website_html = html_header_for_index_page(all_timestamps)

    completed = ""
    merged_outputs = list_of_processed_entries_for_each_merged_group()

    for merged_code in merged_outputs.keys():
        timestamps_of_data = []
        merged_reports = []
        primary_report_count = 0
        for component in merged_outputs[merged_code]:
            if "hidden" in component:
                if component["hidden"] == True:
                    continue
            cursor.execute("SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NOT NULL AND validator_complaint <> ''", {"identifier": component['internal_region_name']})
            returned = cursor.fetchall()
            for entry in returned:
                rowid, object_type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint = entry
                tags = json.loads(tags)
                validator_complaint = json.loads(validator_complaint)
                if validator_complaint['error_id'] not in component.get('ignored_problems', []):
                    merged_reports.append(validator_complaint)
                    if validator_complaint['error_id'] in for_review():
                        primary_report_count += 1
            timestamps_of_data.append(obtain_from_overpass.get_data_timestamp(cursor, component['internal_region_name']))
        generate_output_for_given_area(merged_code, merged_reports, timestamps_of_data, component.get('ignored_problems', []))
        
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
        if obtain_from_overpass.get_data_timestamp(cursor, entry['internal_region_name']) == 0:
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
    query = "SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint FROM osm_data WHERE validator_complaint IS NOT NULL AND validator_complaint <> ''"
    query_parameters = {}
    reports_data = query_to_reports_data(cursor, query, query_parameters)
    filepath = config.get_report_directory() + '/' + "all merged - test.html"
    ignored_problem_codes = []
    generate_test_issue_listing(reports_data, all_timestamps, filepath, ignored_problem_codes)

def human_review_problem_count_for_given_internal_region_name(cursor, internal_region_name):
    cursor.execute("SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint FROM osm_data WHERE area_identifier = :identifier AND validator_complaint IS NOT NULL AND validator_complaint <> ''", {"identifier": internal_region_name})
    returned = cursor.fetchall()
    report_count = 0
    for entry in returned:
        rowid, object_type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint = entry
        validator_complaint = json.loads(validator_complaint)
        if(validator_complaint['error_id'] in for_review()):
            report_count += 1
    return report_count

def problem_count_string(report_count):
    if report_count == 1:
        return '(found ' + str(report_count) + ' problem)</br>'
    return '(found ' + str(report_count) + ' problems)</br>'

if __name__ == "__main__":
    raise "unsupported, expected to be used as a library"
