import osm_bot_abstraction_layer.world_data as world_data

for ISO3166_1 in ['JP', 'IR', 'PL']:
    print(world_data.list_of_area_divisions_data(ISO3166_1, 4, ["name", "wikidata"], '/tmp/boundary_data.osm'))
