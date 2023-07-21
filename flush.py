import wikimedia_connection.wikimedia_connection as wikimedia_connection
import osm_handling_config.global_config as osm_handling_config
import os

wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())

forced_refresh = True
forced_refresh = False
wikimedia_connection.get_data_from_wikidata("en", "Manchester Street Generating Station", forced_refresh)

kill = "Q83809 Q11143416".split()
for id in kill:
    os.remove(wikimedia_connection.get_filename_with_wikidata_entity_by_id(id))
    os.remove(wikimedia_connection.get_filename_with_wikidata_by_id_response_code(id))
"""
flush.py Q49833

flushes cache of Q49833
"""