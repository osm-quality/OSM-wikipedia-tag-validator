# Wikidata processing, not strictly specific to wikipedia validator tasks,
# but also not direct fetching of data like wikimedia_connection

import wikimedia_connection.wikimedia_connection as wikimedia_connection

def get_all_types_describing_wikidata_object(wikidata_id):
    base_type_ids = get_wikidata_type_ids_of_entry(wikidata_id)
    if base_type_ids == None:
        return []
    return get_recursive_all_subclass_of_list(base_type_ids)

def get_recursive_all_subclass_of_list(base_type_ids):
    all_types = []
    for type in base_type_ids:
        all_types += get_recursive_all_subclass_of(type)
    return all_types

def get_wikidata_type_ids_of_entry(wikidata_id):
    if wikidata_id == None:
        return None
    types = None
    try:
        forced_refresh = False
        wikidata_entry = wikimedia_connection.get_data_from_wikidata_by_id(wikidata_id, forced_refresh)
        wikidata_entry = wikidata_entry['entities']
        object_id = list(wikidata_entry)[0]
        types = wikidata_entry[object_id]['claims']['P31']
    except KeyError:
        return None
    return [type['mainsnak']['datavalue']['value']['id'] for type in types]

def wikidata_entries_for_abstract_or_very_broad_concepts():
    return ['Q1801244', 'Q28732711', 'Q223557', 'Q488383', 'Q16686448',
    'Q151885', 'Q35120', 'Q37260', 'Q246672', 'Q5127848', 'Q16889133',
    'Q386724', 'Q17008256', 'Q11348', 'Q11028', 'Q1260632', 'Q1209283',
    'Q673661', 'Q23008351', 'Q1914636', 'Q17334923', 'Q2221906',
    'Q2324993', 'Q58778', 'Q18340964', 'Q1544281', 'Q2101636',
    'Q30060700', 'Q3778211',
    ]

def get_recursive_all_subclass_of(wikidata_id, banned_parents = wikidata_entries_for_abstract_or_very_broad_concepts(), debug = False):
    processed = []
    to_process = [{"id": wikidata_id, "depth": 0}]
    while to_process != []:
        process = to_process.pop()
        process_id = process["id"]
        depth = process["depth"]
        if debug:
            print(" "*depth + wikidata_description(process_id))
        processed.append(process_id)
        new_ids = get_useful_direct_parents(process_id, processed + to_process + banned_parents)
        for parent_id in new_ids:
            to_process.append({"id": parent_id, "depth": depth+1})
    return processed

def wikidata_description(wikidata_id):
    en_docs = get_wikidata_description(wikidata_id, 'en')
    if en_docs != None:
        return en_docs
    pl_docs = get_wikidata_description(wikidata_id, 'pl')
    if pl_docs != None:
        return pl_docs
    return("Unexpected type " + wikidata_id + " undocumented format")

def get_wikidata_label(wikidata_id, language):
    if wikidata_id == None:
        return None
    try:
        data = wikimedia_connection.get_data_from_wikidata_by_id(wikidata_id)['entities'][wikidata_id]
        return data['labels']['en']['value']
    except KeyError:
        return None

def get_wikidata_explanation(wikidata_id, language):
    if wikidata_id == None:
        return None
    try:
        data = wikimedia_connection.get_data_from_wikidata_by_id(wikidata_id)['entities'][wikidata_id]
        return data['descriptions'][language]['value']
    except KeyError:
        return None

def get_wikidata_description(wikidata_id, language):
    if wikidata_id == None:
        return None
    docs = wikimedia_connection.get_data_from_wikidata_by_id(wikidata_id)
    returned = ""
    label = get_wikidata_label(wikidata_id, language)
    explanation = get_wikidata_explanation(wikidata_id, language)

    if label == None and explanation == None:
        return None

    if explanation != None:
        explanation = ' (' + explanation +')'
    else:
        explanation = ''

    return(language + ": " + label + explanation + ' [' + wikidata_id + "]")

def get_useful_direct_parents(wikidata_id, forbidden):
    more_general_list = wikimedia_connection.get_property_from_wikidata(wikidata_id, 'P279') #subclass of
    if more_general_list == None:
        return []
    returned = []
    for more_general in more_general_list:
        more_general_id = more_general['mainsnak']['datavalue']['value']['id']
        if more_general_id not in forbidden:
            returned.append(more_general_id)
    return returned

def decapsulate_wikidata_value(from_wikidata):
    # https://www.mediawiki.org/wiki/Wikibase/DataModel/JSON#Claims_and_Statements
    # todo fix flow by random exception
    try:
        from_wikidata = from_wikidata[0]['datavalue']['value']
    except KeyError:
        pass
    try:
        from_wikidata = from_wikidata[0]['mainsnak']['datavalue']['value']
    except KeyError:
        pass
    try:
        # for wikidata values formed like
        # {'entity-type': 'item', 'id': 'Q43399', 'numeric-id': 43399}
        if isinstance(from_wikidata, dict):
            if from_wikidata['entity-type'] == 'item':
                from_wikidata = from_wikidata['id']
    except KeyError:
        pass
    return from_wikidata

def describe_unexpected_wikidata_type(type_id):
    # print entire inheritance set
    for parent_category in get_recursive_all_subclass_of(type_id, wikidata_entries_for_abstract_or_very_broad_concepts(), True):
        print("if type_id == '" + parent_category + "':")
        print(wikidata_description(parent_category))

def dump_base_types_of_object_in_stdout(wikidata_id, description_of_source):
    print("----------------")
    print(wikidata_id)
    for type_id in get_wikidata_type_ids_of_entry(wikidata_id):
        print("------")
        print(description_of_source)
        print("type " + type_id)
        describe_unexpected_wikidata_type(type_id)
