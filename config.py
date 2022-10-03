import yaml
import pwd
import os

def get_entries_to_process():
    return parse_yaml_file("regions_processed.yaml")

def parse_yaml_file(filename):
    with open(filename, 'r') as stream:
        try:
            return yaml.full_load(stream)
        except yaml.YAMLError as exc:
            raise(exc)

def downloaded_osm_data_location():
    return parse_yaml_file("cache_config.yaml")["downloaded_osm_file_storage_location"]

def get_wikimedia_connection_cache_location():
    return parse_yaml_file("cache_config.yaml")['wikimedia_connection_library_cache']

def user_agent():
  "wikipedia/wikidata tag validator, operated by " + pwd.getpwuid(os.getuid()).pw_name + " username, written by Mateusz Konieczny (matkoniecz@gmail.com)"

