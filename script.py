import common
import os
import yaml
import generate_webpage_with_error_output
from subprocess import call
import pathlib
import datetime
import shutil

class ProcessingException(Exception):
    """TODO: documentation, not something so badly generic"""

def main():
    download_data()
    delete_output_files()
    pipeline(osm_filename = 'reloaded_Poland.osm', website_main_title_part = 'reloaded_Poland', merged_output_file = None, language_code = "pl")
    pipeline_entries_from_config_file()
    make_websites_for_merged_entries()
    write_index()
    make_query_to_reload_only_affected_objects('Polska.yaml', 'Polska.query')
    commit_changes_in_report_directory()
    #pipeline_graticule_entries()

def download_data():
    os.system("ruby download.rb")

def merge(source_yaml, target_yaml):
    root = common.get_file_storage_location() + "/"
    system_call('cat "' + root + source_yaml +'" >> "' + root + target_yaml + '"', False)

def system_call(call, verbose=True):
    if verbose:
        print(call)
    os.system(call)

def root():
    return common.get_file_storage_location() + "/"

def copy_file(source, target):
    shutil.copy2(source, target)

def move_file(source, target):
    shutil.move(source, target)

def delete_in_storage_folder(filename):
        try:
            os.remove(root() + filename)
        except FileNotFoundError:
            return

def delete_output_files():
    for region_name in get_graticule_region_names():
        file_for_deletion = region_name + ".osm.yaml"
        delete_in_storage_folder(file_for_deletion)

    for entry in get_entries_to_process():
        delete_in_storage_folder(entry['region_name'] + ".osm.yaml")
        file = entry.get('merged_output_file', None)
        if file != None:
            delete_in_storage_folder(file)

    yaml_output_files = [
        'polska_reloaded.osm.yaml',
    ]

    for filename in yaml_output_files:
        try:
            os.remove(root() + filename)
        except FileNotFoundError:
            pass

def make_website(filename_with_report, output_filename_base):
    split_human_bot = ""
    system_call('python3 generate_webpage_with_error_output.py -file "' + filename_with_report + '" -out "' + output_filename_base + '" ' + split_human_bot, False)


def pipeline(osm_filename, website_main_title_part, merged_output_file, language_code, silent=False):
        output_filename_errors = osm_filename + '.yaml'
        if exit_pipeline_due_to_missing_osm_data(osm_filename, silent):
            return
        make_report_file(language_code, osm_filename)
        filepath = root() + output_filename_errors
        if not os.path.isfile(filepath):
            print(filepath + ' is not present [highly surprising]')
            raise ProcessingException('Unexpected failure')
        if merged_output_file != None:
            merge(output_filename_errors, merged_output_file)
        make_website(output_filename_errors, website_main_title_part)
        make_query_to_reload_only_affected_objects(output_filename_errors, website_main_title_part + '.query')
        move_files_to_report_directory(website_main_title_part)

def move_files_to_report_directory(website_main_title_part):
    filenames = []
    filenames.append(website_main_title_part + '.html')
    filenames.append(website_main_title_part + ' - obvious.html')
    filenames.append(website_main_title_part + ' - test.html')
    filenames.append(website_main_title_part + ' - boring.html')
    for filename in filenames:
        try:
            move_file(filename, get_report_directory() + '/' + filename)
        except FileNotFoundError:
            print(filename + ' is not present')

def exit_pipeline_due_to_missing_osm_data(osm_filename, silent):
    if os.path.isfile(root() + osm_filename):
        return False
    if silent:
        return True
    print(osm_filename + ' is not present')
    return True

def make_report_file(language_code, osm_filename):
    language_code_parameter = ""
    if language_code != None:
        language_code_parameter = '-expected_language_code ' + language_code
    system_call('python3 wikipedia_validator.py ' + language_code_parameter + ' -file "' + osm_filename + '"')

def make_query_to_reload_only_affected_objects(input_filename_with_reports, output_query_filename):
    input_filepath = common.get_file_storage_location() + "/" + input_filename_with_reports
    output_filepath = root() + 'reload_querries/' + output_query_filename
    if not os.path.isfile(input_filepath):
        print("file not found")
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
        query = common.get_query_for_loading_errors_by_category(filename = input_filename_with_reports, printed_error_ids = all_errors, format = "josm")
        query_file.write(query)

def get_entries_to_process():
    return common.parse_yaml_file("regions_processed.yaml")

def merged_outputs_list():
    merged_outputs = []
    for entry in get_entries_to_process():
        if entry.get('merged_output_file', None) != None:
            merged_outputs.append(entry['merged_output_file'])
    return list(set(merged_outputs))

def get_entry_contributing_to_merged_file(name_of_merged):
    for entry in get_entries_to_process():
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

def pipeline_entries_from_config_file():
    for entry in get_entries_to_process():
        pipeline(
            osm_filename = entry['region_name'] + ".osm",
            website_main_title_part = entry['website_main_title_part'],
            merged_output_file = entry.get('merged_output_file', None),
            language_code = entry.get('language_code', None),
            )

def get_graticule_region_names():
    returned = []
    for lat in range(-180, 180+1):
        for lon in range(-180, 180+1):
            region_name = str(lat) + ", " + str(lon)
            returned.append(region_name)
    return returned

def pipeline_graticule_entries():
    for region_name in get_graticule_region_names():
        pipeline(
            osm_filename = region_name + ".osm",
            website_main_title_part = region_name,
            merged_output_file = None,
            language_code = None,
            silent = True,
            )

def make_websites_for_merged_entries():
    for filename in merged_outputs_list():
        filepath = root() + filename
        if os.path.isfile(filepath):
            # inherit split status on bottable and nonbottable tasks
            entry = get_entry_contributing_to_merged_file(filename)
            output_filename_base = filename.replace(".yaml", "")
            make_website(filename, output_filename_base)
        else:
            print(filepath + ' is not present [highly surprising]')
            raise ProcessingException('Unexpected failure')

    for filename in merged_outputs_list():
        entry = get_entry_contributing_to_merged_file(filename)
        move_files_to_report_directory(filename.replace('.yaml', ''))

def write_index():
    with open('index.html', 'w') as index:
        index.write("<html><body>\n")
        index.write(generate_webpage_with_error_output.feedback_request())
        index.write("</br>\n")
        index.write("</br>\n")
        for filename in sorted(merged_outputs_list()):
            name = filename.replace('.yaml', '')
            index.write("<a href = " + common.htmlify(name) + ".html>" + common.htmlify(name) + "</a></br>\n")
        for entry in get_entries_to_process():
            website_main_title_part = entry['website_main_title_part']
            filename = website_main_title_part + '.html'
            potential_filepath = get_report_directory() + '/' + filename
            if os.path.isfile(potential_filepath):
                index.write('<a href = "' + common.htmlify(filename) + '">' + common.htmlify(website_main_title_part) + "</a></br>\n")
            else:
                print(potential_filepath + ' is not present')
        index.write("</html></body>\n")

    move_file('index.html', get_report_directory() + '/' + 'index.html')

if __name__ == '__main__':
    main()
