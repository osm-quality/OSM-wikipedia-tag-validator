# TODO: replace use of region_name by website_main_title_part where unique titles are needed
# remove region_name from regions processed
import common
import os
import pwd
import yaml
import generate_webpage_with_error_output
from subprocess import call
import pathlib
import datetime
import shutil
import time
from wikibrain import wikimedia_link_issue_reporter
from osm_bot_abstraction_layer.overpass_downloader import download_overpass_query
from osm_bot_abstraction_layer import overpass_query_maker

class ProcessingException(Exception):
    """TODO: documentation, not something so badly generic"""

def main():
    script_run_start_time = datetime.datetime.now()
    detect_missing_data_in_used_library()
    common.verify_folder_structure()
    delete_merged_output_files()
    pipeline_entries_from_config_file(script_run_start_time)
    make_websites_for_merged_entries()
    write_index()
    commit_changes_in_report_directory()

def detect_missing_data_in_used_library():
    # trigger what is likely to crash later,
    # rather than doing after expensive and long setup
    helper_object = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector(False, None, None, False, False, False)
    for entry in common.get_entries_to_process():
        if 'language_code' in entry:
            helper_object.wikidata_ids_of_countries_with_language(entry['language_code'])

def add_problen_reports_into_another_file(raw_reports_data_filepath, target_yaml):
    root = common.found_errors_storage_location() + "/"
    if os.path.isfile(raw_reports_data_filepath) == False:
        raise "missing file " + raw_reports_data_filepath
    system_call('cat "' + raw_reports_data_filepath +'" >> "' + root + target_yaml + '"', False)

def system_call(call, verbose=True):
    if verbose:
        print(call)
    os.system(call)

def copy_file(source, target):
    shutil.copy2(source, target)

def move_file(source, target):
    shutil.move(source, target)

def delete_filepath(filepath):
        try:
            os.remove(filepath)
        except FileNotFoundError:
            return

def delete_merged_output_files():
    for entry in common.get_entries_to_process():
        file_for_deletion = entry.get('merged_output_file', None)
        if file_for_deletion != None:
            filepath = common.output_filepath_for_raw_report_data_from_file_name(file_for_deletion)
            delete_filepath(filepath)

def pipeline(region_name, website_main_title_part, merged_output_file, language_code, identifier_of_region, script_run_start_time, silent=False):
        download_entry(region_name, identifier_of_region)
        raw_reports_data_filepath = common.output_filepath_for_raw_report_data_from_region_name(region_name)
        delete_filepath(raw_reports_data_filepath) # do it smarter to avoid data loss in case of interrupted process
        if exit_pipeline_due_to_missing_osm_data(region_name + ".osm", silent):
            return
        osm_filepath = common.downloaded_osm_data_location() + "/" + region_name + ".osm"
        make_report_file(language_code, osm_filepath, raw_reports_data_filepath)
        if not os.path.isfile(raw_reports_data_filepath):
            error = raw_reports_data_filepath + ' is not present [highly surprising]'
            print(error)
            raise ProcessingException('Unexpected failure ' + error)
        if merged_output_file != None:
            add_problen_reports_into_another_file(raw_reports_data_filepath, merged_output_file)
        make_website(raw_reports_data_filepath, website_main_title_part)
        make_query_to_reload_only_affected_objects(raw_reports_data_filepath, region_name + '.query', script_run_start_time, identifier_of_region)
        move_files_to_report_directory(website_main_title_part)

def move_files_to_report_directory(website_main_title_part):
    filenames = []
    filenames.append(website_main_title_part + '.html')
    filenames.append(website_main_title_part + ' - obvious.html')
    filenames.append(website_main_title_part + ' - test.html')
    for filename in filenames:
        try:
            move_file(filename, get_report_directory() + '/' + filename)
        except FileNotFoundError:
            print(filename + ' is not present during moving html files')

def exit_pipeline_due_to_missing_osm_data(osm_filename, silent):
    filepath = common.downloaded_osm_data_location() + "/" + osm_filename
    if os.path.isfile(filepath):
        return False
    if silent:
        return True
    print(filepath + ' is not present, pipeline will be exited')
    return True

def make_report_file(language_code, osm_filepath, output_yaml_filepath):
    language_code_parameter = ""
    if language_code != None:
        language_code_parameter = '-expected_language_code ' + language_code
    system_call('python3 wikipedia_validator.py ' + language_code_parameter + ' -filepath "' + osm_filepath + '"'  + ' -output_filepath "' + output_yaml_filepath + '"')

def make_query_to_reload_only_affected_objects(raw_reports_data_filepath, output_query_filename, script_run_start_time, identifier_of_region):
    input_filepath = raw_reports_data_filepath
    output_filepath = common.reload_queries_location() + "/" + output_query_filename
    if not os.path.isfile(input_filepath):
        print(input_filepath + " file not found, reload query generation is skipped")
        return
    directory_path = os.path.split(output_filepath)[0]
    pathlib.Path(directory_path).mkdir(parents=True, exist_ok=True)
    archived_filepath = output_filepath + "-archived-" + str(datetime.datetime.now()) + ".query"
    try:
        move_file(output_filepath, archived_filepath)
    except FileNotFoundError:
        pass # it is OK, it just means that we are running for the first time or cache was deleted
    with open(output_filepath, 'w') as query_file:
        all_errors = []
        for e in common.load_data(input_filepath):
            if e['error_id'] not in all_errors:
                all_errors.append(e['error_id'])
        
        date = overpass_query_maker.datetime_to_overpass_data_format(script_run_start_time)
        area_name_in_query = "searchArea"
        area_identifier = 'area.' + area_name_in_query
        area_finder_string = area_finder(identifier_of_region, area_name_in_query)
        extra_query_part = "\n" + area_finder_string + "\n"
        extra_query_part += 'nwr[wikidata](newer:"' + date + '")(' + area_identifier+ ');\n'
        extra_query_part += 'nwr[wikipedia](newer:"' + date + '")(' + area_identifier+ ');\n'
        query = common.get_query_for_loading_errors_by_category(filepath = input_filepath, printed_error_ids = all_errors, format = "josm", extra_query_part=extra_query_part)
        query_file.write(query)

def get_entry_contributing_to_merged_file(name_of_merged):
    for entry in common.get_entries_to_process():
        if entry.get('merged_output_file', None) == name_of_merged:
            return entry
    raise ProcessingException("unexpected")

def get_report_directory():
    return 'OSM-wikipedia-tag-validator-reports'

def commit_changes_in_report_directory():
    current_working_directory = os.getcwd()
    os.chdir(get_report_directory())
    system_call('git add --all')
    system_call('git commit -m "automatic update of report files"')
    os.chdir(current_working_directory)

def pipeline_entries_from_config_file(script_run_start_time):
    for entry in common.get_entries_to_process():
        pipeline(
            region_name = entry['region_name'],
            website_main_title_part = entry['website_main_title_part'],
            merged_output_file = entry.get('merged_output_file', None),
            language_code = entry.get('language_code', None),
            identifier_of_region=entry['identifier'],
            script_run_start_time = script_run_start_time,
            )


def download_entry(area_name, identifier_of_region):
    suffix = "_reloaded"
    # todo: avoid destructive downloads,
    # at the same time avoid overloading disk
    downloaded_filename = downloaded_file_with_osm_data(area_name, suffix)
    query_filepath = get_query_filename_for_reload_of_file(area_name)
    if pathlib.Path(query_filepath).is_file():
        with open(query_filepath, 'r') as query_file:
            query = query_file.read()
            print("downloading reload query for", area_name)
            download_overpass_query(query, downloaded_filename, timeout=timeout(), user_agent=user_agent())
            print("copying to", downloaded_file_with_osm_data(area_name, ""))
            copy_file(source=downloaded_filename, target=downloaded_file_with_osm_data(area_name, ""))
            return
    suffix = "_unprocessed"
    downloaded_filename = downloaded_file_with_osm_data(area_name, suffix)
    if pathlib.Path(downloaded_filename).is_file():
        print("full data file is downloaded already")
    else:
        print("there is no reload query for ", area_name, "full data needs to be obtained")
        area_name_in_query = "searchArea"
        area_finder_string = area_finder(identifier_of_region, area_name_in_query)
        query = query_text(area_finder_string, area_name_in_query)
        download_overpass_query(query, downloaded_filename, timeout=timeout(), user_agent=user_agent())
    print("copying to", downloaded_file_with_osm_data(area_name, ""))
    copy_file(source=downloaded_filename, target=downloaded_file_with_osm_data(area_name, ""))

def area_finder(identifier_tag_dictionary, name_of_area):
    for key in identifier_tag_dictionary.keys():
        if "'" in key:
            raise "escaping not implemented for ' character"
        if "'" in identifier_tag_dictionary[key]:
            raise "escaping not implemented for ' character"
    if len(identifier_tag_dictionary) == 0:
        raise "unexpectedly empty"
    returned = "area"
    for key in identifier_tag_dictionary.keys():
        value = identifier_tag_dictionary[key]
        returned += "['" + key + "'='" + value + "']"
    returned += "->." + name_of_area + ";\n"
    return returned

def query_text(area_finder_string, area_name):
    area_identifier = 'area.' + area_name

    query = "[timeout:" + str(timeout()) + "];\n"
    query += "(\n"
    query += area_finder_string 
    query += "node['wikipedia'](" + area_identifier+ ");\n"
    query += "way['wikipedia'](" + area_identifier+ ");\n"
    query += "relation['wikipedia'](" + area_identifier+ ");\n"
    query += "node['wikidata'](" + area_identifier+ ");\n"
    query += "way['wikidata'](" + area_identifier+ ");\n"
    query += "relation['wikidata'](" + area_identifier+ ");\n"

    query += "node[~'wikipedia:.*'~'.*'](" + area_identifier+ ");\n"
    query += "way[~'wikipedia:.*'~'.*'](" + area_identifier+ ");\n"
    query += "relation[~'wikipedia:.*'~'.*'](" + area_identifier+ ");\n"

    query += ');\n'
    query += "out body;\n"
    query += ">;\n" # expanding
    query += 'out skel qt;'
    return query

def user_agent():
  "wikipedia/wikidata tag validator, operated by " + pwd.getpwuid(os.getuid()).pw_name + " username, written by Mateusz Konieczny (matkoniecz@gmail.com)"

def timeout():
  return 2550


# TODO: synchronize with make_query_to_reload_only_affected_objects calls
# to ensure name synchronization
def get_query_filename_for_reload_of_file(area_name):
  return common.reload_queries_location() + "/" + area_name + ".query"

def downloaded_file_with_osm_data(name, suffix):
  filename = name
  filename += suffix + ".osm"
  return common.downloaded_osm_data_location() + "/" + filename

def make_website(raw_reports_data_filepath, output_filename_base):
    main_error_count = generate_webpage_with_error_output.generate_output_for_given_area(raw_reports_data_filepath, output_filename_base)
    return main_error_count

def make_websites_for_merged_entries():
    for filename in common.merged_outputs_filenames_list():
        filepath_to_file_listing_mistakes = common.found_errors_storage_location() + "/" + filename
        if os.path.isfile(filepath_to_file_listing_mistakes):
            # inherit split status on bottable and nonbottable tasks
            entry = get_entry_contributing_to_merged_file(filename)
            output_filename_base = filename.replace(".yaml", "")
            filepath_to_report = common.found_errors_storage_location() + "/" + filename
            make_website(filepath_to_report, output_filename_base)
        else:
            print(filepath_to_file_listing_mistakes + ' file is not present during making website for merged entries [highly surprising]')
            raise ProcessingException('Unexpected failure')

    for filename in common.merged_outputs_filenames_list():
        entry = get_entry_contributing_to_merged_file(filename)
        move_files_to_report_directory(filename.replace('.yaml', ''))

def main_report_count_in_report_file(reports_filepath):
    reports_data = common.load_data(reports_filepath)
    if reports_data == None:
        print(reports_filepath + " has no data")
        raise ValueError(reports_filepath + " has no data")
    count = 0
    for error_type_id in generate_webpage_with_error_output.for_review():
        for e in reports_data:
                if e['error_id'] == error_type_id:
                    count += 1
    return count

def problem_count_string(reports_filepath):
    report_count = main_report_count_in_report_file(reports_filepath)
    if report_count == 1:
        return '(found ' + str(report_count) + ' problem)</br>'
    return '(found ' + str(report_count) + ' problems)</br>'

def write_index():
    website_html = ""
    website_html += generate_webpage_with_error_output.html_file_header() + "\n"
    website_html += '<p>This page lists OpenStreetMap objects that have <a href="https://wiki.openstreetmap.org/wiki/Key:wikipedia">wikipedia</a> / <a href="https://wiki.openstreetmap.org/wiki/Key:wikipedia">wikidata</a> tags with some problems.</p>'
    website_html += '<p>For example, it allows to detect cases where <a href="https://www.openstreetmap.org/way/693854629/history">incorrect object was linked</a> or where link leads to deleted page or there is some other issue.</p>\n'
    website_html += '<p>This tool is an <a href="https://github.com/matkoniecz/OSM-wikipedia-tag-validator#story-behing-this-tool">unexpected result</a> of creating a detector of interesting places based on OSM Data and Wikipedia. It turned out to require a filter to avoid invalid links. As detected links can be often fixed and it is better to remove invalid rather than keep them, I am sharing this tool.</p>\n'
    website_html += "</hr>\n"
    website_html += "</br>\n"
    website_html += generate_webpage_with_error_output.feedback_request() + "\n"
    website_html += "</br>\n"
    website_html += "</hr>\n"
    """
    website_html += '<p></p>\n'
    """
    website_html += "</br>\n"

    completed = ""

    for filename in sorted(common.merged_outputs_filenames_list()):
        name = filename.replace('.yaml', '')
        reports_filepath = common.found_errors_storage_location() + "/" + filename
        website_html += '<a href = "' + common.htmlify(name) + '.html">' + common.htmlify(name) + '</a> ' + problem_count_string(reports_filepath) + '\n'
    for entry in common.get_entries_to_process():
        if "hidden" in entry:
            if entry["hidden"] == True:
                continue
        website_main_title_part = entry['website_main_title_part']


        reports_filepath = common.output_filepath_for_raw_report_data_from_region_name(entry['region_name'])
        report_count = main_report_count_in_report_file(reports_filepath)
        report_count_string = problem_count_string(reports_filepath)

        filename = website_main_title_part + '.html'
        potential_filepath = get_report_directory() + '/' + filename
        if os.path.isfile(potential_filepath):
            line = '<a href = "' + common.htmlify(filename) + '">' + common.htmlify(website_main_title_part) + '</a> ' + report_count_string + '\n'
            if report_count != 0:
                website_html += line
            else:
                completed += line
        else:
            print(potential_filepath + ' is not present during write_index')
    website_html += "<br>\n"
    website_html += "<h1>Finished, congratulations :)</h1>\n"
    if completed == "":
        completed = "<p>nothing for now :(<p>\n"
    website_html += completed
    website_html += generate_webpage_with_error_output.html_file_suffix()
    with open('index.html', 'w') as index:
        index.write(website_html)
    move_file('index.html', get_report_directory() + '/' + 'index.html')

if __name__ == '__main__':
    main()
