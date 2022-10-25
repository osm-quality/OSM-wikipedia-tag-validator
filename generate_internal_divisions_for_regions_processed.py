import osm_bot_abstraction_layer.world_data as world_data
import yaml
import json

def main():
    returned = ""
    # for code "ISO3166-1", "ISO3166-1:alpha2", "ISO3166-2" tags can be used
    processed = [
        { # Germany https://www.openstreetmap.org/relation/51477
        'code': 'DE',
        'group_name': ["Deutschland (Germany - Niemcy)"],
        'extra_part_of_name': "Deutschland (Germany)",
        'extra_part_of_internal_name': "Niemcy",
        'language_code': 'de',
        'requested_by': 'https://www.openstreetmap.org/messages/1060670',
        'admin_level': 4,
        'generated_commented_out': True,
        },
        { # China https://www.openstreetmap.org/relation/270056
        'code': 'CN',
        'group_name': ["中国 (China - Chiny)"],
        'extra_part_of_name': "中国 (China)",
        'extra_part_of_internal_name': "Chiny",
        'language_code': None, # not touching this quagmire
        'requested_by': 'https://github.com/matkoniecz/OSM-wikipedia-tag-validator-reports/issues/1',
        'admin_level': 4,
        'generated_commented_out': True,
        },
        {
        'code': 'AU',
        'group_name': ["Australia"],
        'extra_part_of_name': "Australia",
        'extra_part_of_internal_name': "Australia",
        'language_code': None, # not touching this quagmire
        'requested_by': 'https://discord.com/channels/413070382636072960/413070502580453387/1031511358694502470',
        'admin_level': 4,
        },
    ]
    done_already = [
        {
        'code': 'JP',
        'group_name': ["日本 (Japan - Japonia)"],
        'extra_part_of_name': "日本 (Japan - Japonia)",
        'extra_part_of_internal_name': "Japonia",
        'language_code': "ja",
        'requested_by': 'https://www.openstreetmap.org/messages/1054938 Bman',
        'admin_level': 4,
        },
        {
        'code': 'US-TX',
        'group_name': ["USA", "Texas"],
        'extra_part_of_name': "Texas",
        'extra_part_of_internal_name': "Texas",
        'language_code': "en",
        'requested_by': 'skquinn via PM in https://www.openstreetmap.org/messages/924460 and Bman via PM in https://www.openstreetmap.org/messages/1054938',
        'admin_level': 6,
        }
    ]
    for source in processed:
        returned += generate_subregion_list(source, source['admin_level'])
    print(returned)

def generate_subregion_list(source, admin_level):
    returned = ""
    returned += "\n"
    returned += "\n"
    ISO3166 = source['code']
    data = world_data.list_of_area_divisions_data(ISO3166, admin_level, ["name", "wikidata", "name:pl", "name:en"], '/tmp/boundary_data.osm')
    for osm_data in data:
        returned += generate_entry_for_specific_subregion(source, osm_data)
        returned += "\n"
    print(returned)
    return returned

def generate_entry_for_specific_subregion(source, osm_data):
    print(source)
    print(osm_data)
    internal_name = None
    for key in ["name:pl", "name:en", "name"]:
        if key in osm_data and osm_data[key] != None:
            internal_name = osm_data[key]
            break
        else:
            print(osm_data["name"], "/", osm_data["name:en"], " has no", key, "tag")
    extra_names = [osm_data.get("name:en"), osm_data.get("name:pl")]
    shown_extra_names = []
    blocked_names = [None, osm_data["name"]]
    for name in extra_names:
        if name not in blocked_names:
            shown_extra_names.append(name)
    website_main_title_part = osm_data["name"]
    if len(shown_extra_names) > 0:
        website_main_title_part += " (" + ", ".join(shown_extra_names) + ")"
    if "extra_part_of_name" in source:
        internal_name = source["extra_part_of_internal_name"] + ": " + internal_name
        website_main_title_part = source["extra_part_of_name"] + ": " + website_main_title_part

    region_data = {
        "internal_region_name": internal_name,
        "website_main_title_part": website_main_title_part,
        "merged_into": source["group_name"],
        "identifier": {'wikidata': osm_data["wikidata"]},
        "requested_by": source['requested_by'],
        }
    if "generated_commented_out" in source:
        region_data["generated_commented_out"] = source["generated_commented_out"],
    if source['language_code'] != None:
        region_data['language_code'] = source['language_code']
    return generate_yaml_row_text(region_data)

def generate_yaml_row_text(region_data):
    language_code_section = ""
    if 'language_code' in region_data:
        language_code_section = "language_code: '" + region_data['language_code'] + "', "
    dumped = region_data.copy()
    dumped.pop("generated_commented_out", None)
    raw_yaml = "-" + yaml.dump(dumped)
    manual = "- {internal_region_name: '" + region_data['internal_region_name'] + "', website_main_title_part: '" + region_data['website_main_title_part'] + "', merged_into: " + str(json.dumps(region_data["merged_into"])) + ", identifier: {'wikidata': '" + region_data["identifier"]["wikidata"] + "'}, " + language_code_section + "requested_by: '" + region_data["requested_by"] + "'}"
    print(raw_yaml)
    print(manual)
    returned = manual
    if region_data["generated_commented_out"]:
        returned = "#" + returned
    return returned

main()
