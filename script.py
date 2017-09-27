import common
import os
import yaml
from subprocess import call

def merge(source_yaml, target_yaml):
    root = common.get_file_storage_location() + "/"
    system_call('cat "' + root + source_yaml +'" >> "' + root + target_yaml + '"')

def system_call(call):
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
        move_files_to_report_directory(website_main_title_part)

def move_files_to_report_directory(website_main_title_part):
    filenames = []
    filenames.append(website_main_title_part + '.html')
    filenames.append(website_main_title_part + ' - private.html')
    filenames.append(website_main_title_part + ' - test.html')
    for filename in filenames:
        if os.path.isfile(filename):
            system_call('mv "' + filename + '" OSM-wikipedia-tag-validator-reports/ -f')
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
        language_code_parameter = '-expected_language_code pl'
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
    returned = None
    with open("processed_regions.yaml", 'r') as stream:
        try:
            returned = yaml.load(stream)
        except yaml.YAMLError as exc:
            raise(exc)
    return returned

def merged_outputs_list():
    merged_outputs = []
    for entry in get_entries_to_process():
        if entry['merged_output_file'] != None:
            merged_outputs.append(entry['merged_output_file'])
    return list(set(merged_outputs))

def main():
    delete_output_files()
    for entry in get_entries_to_process():
        pipeline(
            osm_filename = entry['region_name'] + "_all.osm",
            website_main_title_part = entry['website_main_title_part'],
            merged_output_file = entry['merged_output_file'],
            language_code = entry['language_code'],
            hide_bottable_from_public = entry['hide_bottable_from_public'],
            )
    
    pipeline(osm_filename = 'reloaded_Poland.osm', website_main_title_part = 'reloaded_Poland', merged_output_file = None, language_code = "pl", hide_bottable_from_public=True)

    for name in merged_outputs_list():
        filename = name + '.yaml'
        if os.path.isfile(root() + filename):
            for entry in get_entries_to_process():
                if entry['merged_output_file'] == name:
                    # inherit split status on bottable and nonbottable tasks
                    make_website(filename, name, entry['hide_bottable_from_public'])
                    break
        else:
            print(filename + ' is not present [highly surprising]')
            raise 'Unexpected failure'

    with open('index.html', 'w') as index:
        index.write("<html><body>\n")
        for name in merged_outputs_list():
            index.write("<a href = " + name + ".html>" + name + "</a></br>\n")
        for entry in get_entries_to_process():
            website_main_title_part = entry['website_main_title_part']
            filename = website_main_title_part + '.html'
            if os.path.isfile(filename):
                index.write('<a href = "' + filename + '">' + website_main_title_part + "</a></br>\n")
            else:
                print(filename + ' is not present')
        index.write("</html></body>\n")

    system_call('mv index.html OSM-wikipedia-tag-validator-reports/ -f')
    main_name_parts_of_reports = []
    for name in merged_outputs_list():
        move_files_to_report_directory(name)

    make_query_to_reload_only_affected_objects('Polska.yaml', 'reload_Poland.query')

    os.chdir('OSM-wikipedia-tag-validator-reports')
    system_call('git add --all')
    system_call('git commit -m "automatic update of report files"')
    system_call('git diff @~')

if __name__ == '__main__':
    main()
