from osm_iterator.osm_iterator import Data
import csv
import wikimedia_connection.wikimedia_connection as wikimedia_connection
import common
import generate_osm_edits
import geopy.distance

# IDEA
# entries for import may be obtained by running query in following link:
# http://88.99.164.208/wikidata/#SELECT%20%3Fitem%20%3Fteryt%20%3FitemLabel%20WHERE%20{%0A%20%3Fitem%20wdt%3AP31%2Fwdt%3AP279*%20wd%3AQ486972%20.%0A%20%3Fitem%20wdt%3AP4046%20%3Fteryt%20.%0A%20FILTER%20NOT%20EXISTS%20{%20%3Fosm1%20osmt%3Awikidata%20%3Fitem%20.%20}%0A%20%0A%20SERVICE%20wikibase%3Alabel%20{%20bd%3AserviceParam%20wikibase%3Alanguage%20"pl%2C[AUTO_LANGUAGE]%2Cen"%20}%0A}
# and downloading data into teryt_wikidata.csv file located at folder specified by cache_location.config file
# later also everything with teryt (see https://www.wikidata.org/wiki/Q30910912 )
# https://wiki.openstreetmap.org/wiki/User_talk:Yurik
# 2 minutes wasted on matching https://www.openstreetmap.org/node/3009664303
# for fixing wikidata data: https://query.wikidata.org/#SELECT %3Fitem %3FitemLabel %3Fvalue %3Fresult (STRLEN(STR(%3Fvalue)) AS %3Fstringlength) %3Fsnak %3Frank%0AWHERE%0A{%0A%09{%0A%09%09SELECT %3Fitem %3Fvalue %3Fresult %3Fsnak %3Frank%0A%09%09WHERE%0A%09%09{%0A%09%09%09{%0A%09%09%09%09%3Fitem p%3AP4046 [ ps%3AP4046 %3Fvalue%3B wikibase%3Arank %3Frank ] .%0A%09%09%09%09BIND("mainsnak" AS %3Fsnak) .%0A%09%09%09} UNION {%0A%09%09%09%09%3Fstatement1 pq%3AP4046 %3Fvalue%3B%0A%09%09%09%09%09wikibase%3Arank %3Frank .%0A%09%09%09%09%3Fitem %3Fp1 %3Fstatement1 .%0A%09%09%09%09BIND("qualifier" AS %3Fsnak) .%0A%09%09%09} UNION {%0A%09%09%09%09%3Fref pr%3AP4046 %3Fvalue .%0A%09%09%09%09%3Fstatement2 prov%3AwasDerivedFrom %3Fref%3B%0A%09%09%09%09%09wikibase%3Arank %3Frank .%0A%09%09%09%09%3Fitem %3Fp2 %3Fstatement2 .%0A%09%09%09%09BIND("reference" AS %3Fsnak) .%0A%09%09%09} .%0A%09%09%09BIND( REGEX( STR( %3Fvalue )%2C "^(\\d{7})%24" ) AS %3Fregexresult ) .%0A%09%09%09FILTER( %3Fregexresult %3D false ) .%0A%09%09%09BIND( IF( %3Fregexresult %3D true%2C "pass"%2C "fail" ) AS %3Fresult ) .%0A%09%09%09FILTER( %3Fitem NOT IN ( wd%3AQ4115189%2C wd%3AQ13406268%2C wd%3AQ15397819 ) ) .%0A%09%09} %0A%09%09LIMIT 100%0A%09} .%0A%09SERVICE wikibase%3Alabel { bd%3AserviceParam wikibase%3Alanguage "en" } .%0A}%0A%23ORDER BY %3Frank %3Fsnak %3Fvalue%0A%23PLEASE NOTE%3A This is experimental and may only work for simple patterns.%0A%23Tests may fail due to%3A%0A%23(1) differences in regex format between SPARQL (https%3A%2F%2Fwww.w3.org%2FTR%2Fxpath-functions%2F%23regex-syntax) and PCRE (used by constraint reports). Don't change the regex to work with SPARQL!%0A%23(2) some bug in the link that brought you here%0A%23Known to fail%3A P227 (multiple curly braces)%2C P274%2C P281

teryt_simc_in_OSM = {}

def is_valid_teryt_code(teryt):
    return len(teryt) == 7

def get_linkable_OSM_element(teryt, potential_wikidata_id):
    if not is_valid_teryt_code(teryt):
        return None
    elif teryt not in list(teryt_simc_in_OSM.keys()):
        #print("teryt <" + teryt + "> not found in OSM http://www.wikidata.org/entity/" + potential_wikidata_id)
        return None
    elif len(teryt_simc_in_OSM[teryt]) > 1:
        error = "repeated teryt: " + str(len(teryt_simc_in_OSM[teryt])) + " "
        for element in teryt_simc_in_OSM[teryt]:
            error += element.get_link()
        #print(error)
        return None
    elif len(teryt_simc_in_OSM[teryt]) == 1:
        osm_element = teryt_simc_in_OSM[teryt][0]
        if osm_element.get_tag_value('wikidata') == None:
            #everything is OK and ready for edit
            #print()
            #print("# " + teryt + " is the same for http://www.wikidata.org/entity/" + potential_wikidata_id + " and " + teryt_simc_in_OSM[teryt][0].get_link())
            return osm_element
        if osm_element.get_tag_value('wikidata') != potential_wikidata_id:
            print()
            print("# " + teryt + " is the same for http://www.wikidata.org/entity/" + potential_wikidata_id + " and " + teryt_simc_in_OSM[teryt][0].get_link() + " but there is already a different wikidata value")
            lang = 'pl'
            article = wikimedia_connection.get_interwiki_article_name_by_id(potential_wikidata_id, lang)
            print("#: Expected article: " + common.wikipedia_url(lang, article))
            article = wikimedia_connection.get_interwiki_article_name_by_id(osm_element.get_tag_value('wikidata'), lang)
            print("#: Currently linked article: " + common.wikipedia_url(lang, article))
            if osm_element.get_tag_value('place') != None:
                print("#: place=" + osm_element.get_tag_value('place'))
            else:
                print("#: place tag not present")
        return None
    else:
        assert(False)

def get_wikidata_OSM_pairs():
    returned = []
    with open(common.get_file_storage_location() + "/" + 'teryt_wikidata.csv', 'r') as csvfile:
        print(common.get_file_storage_location() + "/" + 'teryt_wikidata.csv')
        reader = csv.reader(csvfile)
        for row in reader:
            wikidata_id = row[0].replace("http://www.wikidata.org/entity/", "")
            teryt = row[1]
            element = get_linkable_OSM_element(teryt, wikidata_id)
            if element == None:
                continue
            returned.append({'osm_element': element, 'wikidata_id': wikidata_id})
    return returned

def get_changeset_builder():
    affected_objects_description = ""
    comment = "adding wikipedia and wikidata tags based on teryt simc code in OSM (teryt:simc tag) and Wikidata (P4046 property)"
    automatic_status = generate_osm_edits.fully_automated_description()
    discussion_url = 'https://forum.openstreetmap.org/viewtopic.php?id=59926'
    source = "wikidata, OSM"
    return generate_osm_edits.ChangesetBuilder(affected_objects_description, comment, automatic_status, discussion_url, source)

def load_data():
    wikimedia_connection.set_cache_location(common.get_wikimedia_connection_cache_location())
    file = "teryt_simc.osm"
    osm = Data(common.get_file_storage_location() + "/" + file)
    osm.iterate_over_data(record_presence)
    return get_wikidata_OSM_pairs()

def generate_edit(osm_element):
    edit = {}
    edit['osm_object_url'] = osm_element.get_link()
    edit['prerequisite'] = {'wikidata': None, 'wikipedia': None, "teryt:simc": osm_element.get_tag_value("teryt:simc")}
    return edit

def get_location_of_element(element):
    coord = element.get_coords()
    if coord is None:
        return None, None
    else:
        return float(coord.lat), float(coord.lon)
    assert(False)

def get_api():
    return generate_osm_edits.get_correct_api(get_changeset_builder().automatic_status, get_changeset_builder().discussion_url)

def process_pairs(pairs):
    api = get_api()
    unprocessed = []
    center_location = None
    count = 0
    changeset_opened = False
    for pair in pairs:
        location = get_location_of_element(pair['osm_element'])
        if geopy.distance.vincenty(center_location, location).km > 80 and center_location != None:
            unprocessed.append(pair)
            continue

        edit = generate_edit(pair['osm_element'])
        data = generate_osm_edits.get_and_verify_data(edit)

        if data == None:
            continue

        if(center_location == None):
            get_changeset_builder().create_changeset(api)
            changeset_opened = True
            center_location = location

        data['tag']['wikidata'] = pair['wikidata_id']
        wikipedia_in_pl = wikimedia_connection.get_interwiki_article_name_by_id(pair['wikidata_id'], 'pl')
        if wikipedia_in_pl == None:
            continue
        data['tag']['wikipedia'] = "pl:" + wikipedia_in_pl
        type = edit['osm_object_url'].split("/")[3]

        print(edit['osm_object_url'] + ' ' + data['tag']['name'] + ' - adding wikidata=' + data['tag']['wikidata'] + ' wikipedia=' + data['tag']['wikipedia'])

        count += 1
        generate_osm_edits.update_element(api, type, data)

        if count >= 500:
            print("closing changeset after reaching limit of 500 items")
            api.ChangesetClose()
            changeset_opened = False
            center_location = None
            count = 0
            generate_osm_edits.sleep(60)
    if changeset_opened:
        api.ChangesetClose()
        generate_osm_edits.sleep(60)
    return unprocessed

def main():
    pairs = load_data()
    for pair in pairs:
        wikipedia_in_pl = wikimedia_connection.get_interwiki_article_name_by_id(pair['wikidata_id'], 'pl')
        if wikipedia_in_pl == None:
            print(pair['osm_element'].get_link() + " has no matching entry in pl wikipedia")
    while True:
        pairs = process_pairs(pairs)
        if pairs == []:
            break


def record_presence(element):
    teryt = element.get_tag_value("teryt:simc")
    if teryt not in teryt_simc_in_OSM:
        teryt_simc_in_OSM[teryt] = []
    teryt_simc_in_OSM[teryt].append(element)

main()
