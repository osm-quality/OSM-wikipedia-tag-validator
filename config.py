import string
import yaml
import pwd
import os


def get_entries_to_process():
    return parse_yaml_file("regions_processed.yaml")


def parse_yaml_file(filename: string):
    with open(filename, 'r') as stream:
        try:
            return yaml.full_load(stream)
        except yaml.YAMLError as exc:
            raise exc


def downloaded_osm_data_location():
    return os.environ.get('DOWNLOAD_OSM_FILE_STORAGE_LOCATION',
                          '/media/mateusz/OSM_cache/cache-for-wikipedia-validator')



def database_filepath():
    return os.environ.get('DATABASE_FILE_PATH', '/media/mateusz/OSM_cache/cache-for-wikipedia-validator/database.db')



def get_wikimedia_connection_cache_location():
    return os.environ.get('WIKIMEDIA_CONNECTION_LIBRARY_CACHE', '/media/mateusz/OSM_cache')



def user_agent():
    ("wikipedia/wikidata tag validator, operated by " +
     pwd.getpwuid(os.getuid()).pw_name + " username, written by Mateusz Konieczny (matkoniecz@gmail.com)")


def get_report_directory():
    return os.environ.get(
        'VALIDATOR_REPORT_REPOSITORY_LOCATION',
        '/media/mateusz/OSM_cache/OSM-wikipedia-tag-validator-reports'
    )
