import common
import os
import yaml
from subprocess import call

def main():
    delete_output_files()
    pipeline(osm_filename = 'reloaded_Poland.osm', website_main_title_part = 'reloaded_Poland', merged_output_file = None, language_code = "pl", hide_bottable_from_public=True)
    pipeline_basic_entries()
    make_websites_for_merged_entries()
    write_index()
    make_query_to_reload_only_affected_objects('Polska.yaml', 'reload_Poland.query')
    commit_changes_in_report_directory()

def merge(source_yaml, target_yaml):
    root = common.get_file_storage_location() + "/"
    system_call('cat "' + root + source_yaml +'" >> "' + root + target_yaml + '"', False)

def system_call(call, verbose=True):
    if verbose:
        print(call)
    os.system(call)

def root():
    return common.get_file_storage_location() + "/"

def delete_output_file(filename):
        try:
            os.remove(root() + filename)
        except FileNotFoundError:
            return

def delete_output_files():
    for entry in get_entries_to_process():
        delete_output_file(entry['region_name'] + "_all.osm.yaml")
        if entry['merged_output_file'] != None:
            delete_output_file(entry['merged_output_file'] + ".yaml")

    yaml_output_files = [
        'polska_reloaded.osm.yaml',
    ]

    for filename in yaml_output_files:
        try:
            os.remove(root() + filename)
        except FileNotFoundError:
            pass

def make_website(filename_with_report, output_filename_base, hide_bottable_from_public):
    split_human_bot = ""
    if hide_bottable_from_public == True:
        split_human_bot = "-hide_bottable_from_public"
    system_call('python3 generate_webpage_with_error_output.py -file "' + filename_with_report + '" -out "' + output_filename_base + '" ' + split_human_bot)


def pipeline(osm_filename, website_main_title_part, merged_output_file, language_code, hide_bottable_from_public, silent=False):
        output_filename_errors = osm_filename + '.yaml'
        if exit_pipeline_due_to_missing_osm_data(osm_filename, silent):
            return
        make_report_file(language_code, osm_filename)
        if not os.path.isfile(root() + output_filename_errors):
            print(output_filename_errors + ' is not present [highly surprising]')
            raise 'Unexpected failure'
        if merged_output_file != None:
            merge(output_filename_errors, merged_output_file)
        make_website(output_filename_errors, website_main_title_part, hide_bottable_from_public)
        make_query_to_reload_only_affected_objects(output_filename_errors, website_main_title_part + ' new iteration.query')
        move_files_to_report_directory(website_main_title_part, hide_bottable_from_public)

def move_files_to_report_directory(website_main_title_part, hide_bottable_from_public):
    filenames = []
    filenames.append(website_main_title_part + '.html')
    if hide_bottable_from_public:
        filenames.append(website_main_title_part + ' - private.html')
    filenames.append(website_main_title_part + ' - test.html')
    for filename in filenames:
        if os.path.isfile(filename):
            system_call('mv "' + filename + '" ' + get_report_directory() + '/ -f', False)
        else:
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
    filepath = common.get_file_storage_location() + "/" + input_filename_with_reports
    if not os.path.isfile(filepath):
        print("file not found")
        return
    with open(output_query_filename, 'w') as query_file:
        all_errors = []
        for e in common.load_data(filepath):
            if e['error_id'] not in all_errors:
                all_errors.append(e['error_id'])
        query = common.get_query_for_loading_errors_by_category(filename = input_filename_with_reports, printed_error_ids = all_errors, format = "josm")
        query_file.write(query)

def get_entries_to_process():
    return common.parse_yaml_file("processed_regions.yaml")

def merged_outputs_list():
    merged_outputs = []
    for entry in get_entries_to_process():
        if entry['merged_output_file'] != None:
            merged_outputs.append(entry['merged_output_file'])
    return list(set(merged_outputs))

def get_entry_contributing_to_merged_file(name_of_merged):
    for entry in get_entries_to_process():
        if entry['merged_output_file'] == name_of_merged:
            return entry
    raise "unexpected"

def get_report_directory():
    return 'OSM-wikipedia-tag-validator-reports'

def commit_changes_in_report_directory():
    os.chdir(get_report_directory())
    system_call('git add --all')
    system_call('git commit -m "automatic update of report files"')
    system_call('git diff @~')

def pipeline_basic_entries():
    for entry in get_entries_to_process():
        pipeline(
            osm_filename = entry['region_name'] + "_all.osm",
            website_main_title_part = entry['website_main_title_part'],
            merged_output_file = entry['merged_output_file'],
            language_code = entry['language_code'],
            hide_bottable_from_public = entry['hide_bottable_from_public'],
            )

def make_websites_for_merged_entries():
    for filename in merged_outputs_list():
        if os.path.isfile(root() + filename):
            # inherit split status on bottable and nonbottable tasks
            entry = get_entry_contributing_to_merged_file(filename)
            output_filename_base = filename.replace(".yaml", "")
            make_website(filename, output_filename_base, entry['hide_bottable_from_public'])
            break
        else:
            print(root() + filename + ' is not present [highly surprising]')
            raise 'Unexpected failure'

    for filename in merged_outputs_list():
        entry = get_entry_contributing_to_merged_file(filename)
        move_files_to_report_directory(filename.replace('.yaml', ''), entry['hide_bottable_from_public'])

def write_index():
    with open('index.html', 'w') as index:
        index.write("<html><body>\n")
        for filename in merged_outputs_list():
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

    system_call('mv index.html ' + get_report_directory() + '/ -f')

if __name__ == '__main__':
    main()
