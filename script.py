import common
import os
from subprocess import call

def merge(source_yaml, target_yaml):
    root = common.get_file_storage_location() + "/"
    system_call('cat "' + root + source_yaml +'" >> "' + root + target_yaml + '"')

def system_call(call):
    print(call)
    os.system(call)

def voivoddeships_of_poland():
    voivoddeships = ["małopolskie", "podkarpackie", "lubelskie",
      "świętokrzyskie", "mazowieckie", "podlaskie",
      "warmińsko-mazurskie", "pomorskie", "kujawsko-pomorskie",
      "zachodniopomorskie", "lubuskie", "wielkopolskie", "dolnośląskie",
      "opolskie", "śląskie", "łódzkie"]
    return ["województwo " + name for name in voivoddeships]

def root():
    return common.get_file_storage_location() + "/"

def delete_output_files():
    yaml_output_files = [
        'Bremen_all.osm.yaml',
        'Berlin_nodes_without_geometry.osm.yaml',
        'Stendal_all.osm.yaml',
        'Kraków_all.osm.yaml',
        'Deutschland.yaml',
        'Polska.yaml',
    ]

    for index, voivoddeship in enumerate(voivoddeships_of_poland()):
        yaml_output_files.append(voivoddeship + "_all.osm.yaml")

    for filename in yaml_output_files:
        try:
            os.remove(root() + filename)
        except FileNotFoundError:
            pass

def make_website(filename_with_report, output_filename_base):
    system_call('python3 generate_webpage_with_error_output.py -file "' + filename_with_report + '" -out "' + output_filename_base + '"')


def pipeline(osm_filename, website_main_title_part, merged_output_file):
        output_filename_errors = osm_filename + '.yaml'
        if not os.path.isfile(root() + osm_filename):
            print(osm_filename + ' is not present')
            return
        system_call('python3 wikipedia_validator.py -expected_language_code pl -file "' + osm_filename + '"')
        if not os.path.isfile(root() + output_filename_errors):
            print(output_filename_errors + ' is not present [highly surprising]')
            raise 'Unexpected failure'
        if merged_output_file != None:
            merge(output_filename_errors, merged_output_file)
        make_website(output_filename_errors, website_main_title_part)
        make_query_to_reload_only_affected_objects(output_filename_errors, website_main_title_part + ' new iteration.query')

def germany():
    input_filenames = [
        'Bremen_all.osm',
        #'Berlin_nodes_without_geometry.osm',
        'Stendal_all.osm',
    ]
    for filename in input_filenames:
        if not os.path.isfile(root() + filename):
            print(filename + ' is not present')
        else:
            call(['python3', 'wikipedia_validator.py', '-expected_language_code', 'de', '-file', filename])
            merge(filename + '.yaml', 'Deutschland.yaml')

    make_website('Deutschland.yaml', 'Deutschland')
    make_website('Bremen_all.osm.yaml', 'Bremen')

def krakow():
    system_call('python3 wikipedia_validator.py -expected_language_code pl -file "Kraków_all.osm" -allow_requesting_edits_outside_osm -additional_debug -allow_false_positives')
    make_website('Kraków_all.osm.yaml', 'Kraków')

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

def main():
    delete_output_files()

    germany()
    krakow()

    # Poland
    for name in voivoddeships_of_poland():
        pipeline(
                osm_filename = name + '_all.osm',
                website_main_title_part = name,
                merged_output_file = 'Polska.yaml'
                )

    filename = 'Polska.yaml'
    if os.path.isfile(root() + filename):
        make_website(filename, 'Polska')
    else:
        print(filename + ' is not present [highly surprising]')
        raise 'Unexpected failure'

    try:
        os.remove("index.html")
    except FileNotFoundError:
        pass

    with open('index.html', 'w') as index:
        index.write("<html><body>\n")
        index.write("<a href = Polska.html>Polska</a></br>\n")
        index.write("<a href = Krak&oacute;w.html>Krak&oacute;w</a></br>\n")
        index.write("<a href = Deutschland.html>Deutschland</a></br>\n")
        index.write("<a href = Bremen.html>Bremen</a></br>\n")
        for voivoddeship in voivoddeships_of_poland():
            name = common.htmlify(voivoddeship)
            filename = voivoddeship + '.html'
            if os.path.isfile(filename):
                index.write('<a href = "' + name + '.html">' + name + "</a></br>\n")
            else:
                print(filename + ' is not present')
        index.write("</html></body>\n")

    system_call('mv index.html OSM-wikipedia-tag-validator-reports/ -f')
    main_name_parts_of_reports = []
    main_name_parts_of_reports.append('Polska')
    main_name_parts_of_reports.append('Kraków')
    main_name_parts_of_reports.append('Deutschland')
    main_name_parts_of_reports.append('Bremen')
    for voivoddeship in voivoddeships_of_poland():
        main_name_parts_of_reports.append(voivoddeship)

    for name in main_name_parts_of_reports:
        filenames = []
        filenames.append(name + '.html')
        filenames.append(name + ' - private.html')
        filenames.append(name + ' - test.html')
        for filename in filenames:
            if os.path.isfile(filename):
                system_call('mv "' + filename + '" OSM-wikipedia-tag-validator-reports/ -f')
            else:
                print(filename + ' is not present')

    make_query_to_reload_only_affected_objects('Polska.yaml', 'reload_Poland.query')

    os.chdir('OSM-wikipedia-tag-validator-reports')
    system_call('git add --all')
    system_call('git commit -m "automatic update of report files"')
    system_call('git diff @~')

if __name__ == '__main__':
    main()
