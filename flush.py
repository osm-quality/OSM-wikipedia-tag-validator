import wikimedia_connection.wikimedia_connection as wikimedia_connection
import osm_handling_config.global_config as osm_handling_config
import os

from dotenv import load_dotenv

def flush_data_for_wikipedia_article(link):
    forced_refresh = True
    wikimedia_connection.get_data_from_wikidata(link.split(":")[0], link.split(":")[1], forced_refresh)

def flush_data_for_wikidata_entry(id):
    os.remove(wikimedia_connection.get_filename_with_wikidata_entity_by_id(id))
    os.remove(wikimedia_connection.get_filename_with_wikidata_by_id_response_code(id))

def flush_mediawiki_data_for_tags(tags):
    wikidata = live_osm_data['tag'].get('wikidata')
    wikipedia = live_osm_data['tag'].get('wikipedia')
    if wikipedia != None:
        flush_data_for_wikipedia_article(wikipedia)
    if wikidata != None:
        flush_data_for_wikidata_entry(wikidata)

def main():
    load_dotenv()
    wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())

    flush_data_for_wikipedia_article("tr:Perinthos")

    kill = "".split()
    for id in kill:
        flush_data_for_wikidata_entry(id)
    """
    flush.py Q49833

    flushes cache of Q49833
    """

if __name__ == "__main__":
    main()
