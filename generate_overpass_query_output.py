import argparse
import yaml

def get_write_location():
    cache_location_config_filepath = 'cache_location.config'
    cache_location_file = open(cache_location_config_filepath, 'r')
    returned = cache_location_file.read()
    cache_location_file.close()
    return returned

def load_data(yaml_report_filepath):
    with open(yaml_report_filepath, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None
    assert(False)

def parsed_args():
    parser = argparse.ArgumentParser(description='Production of webpage about validation of wikipedia tag in osm data.')
    parser.add_argument('-file', '-f', dest='file', type=str, help='name of yaml file produced by validator')
    args = parser.parse_args()
    if not (args.file):
        parser.error('Provide .osm file')
    return args

def print_query_header():
    print('[out:json];')
    print('(')

def print_query_footer():
    print('); out body geom qt;')

def main():
    args = parsed_args()
    print_query_header()
    filename = args.file
    reported_errors = load_data(get_write_location()+"/"+filename)
    for e in reported_errors:
        if e['error_id'] == 'wikipedia tag links to 404':
            type = e['osm_object_url'].split("/")[3]
            id = e['osm_object_url'].split("/")[4]
            if type == "relation":
                #relations skipped due to https://github.com/maproulette/maproulette2/issues/259
                continue
            print(type+'('+id+');')
    print_query_footer()

main()
