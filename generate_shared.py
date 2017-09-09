import yaml

def load_data(yaml_report_filepath):
    with open(yaml_report_filepath, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None
    assert(False)

def get_query_header(format):
    header = ""
    if format == "maproulette":
        header+= '[out:json];'
    elif format == "josm":
        header += '[out:xml];'
    else:
        assert(False)
    header += "\n"
    header += '('
    header += "\n"
    return header

def get_query_footer(format):
    if format == "maproulette":
        return '); out body geom qt;'
    elif format == "josm":
        return '); (._;>;); out meta qt;'
    else:
        assert(False)

def get_query(filename, printed_error_ids, format):
    # accepted formats:
    # maproulette - json output, workarounds for maproulette bugs
    # josm - xml output
    returned = get_query_header(format)
    reported_errors = load_data(get_write_location()+"/"+filename)
    for e in reported_errors:
        if e['error_id'] in printed_error_ids:
            type = e['osm_object_url'].split("/")[3]
            id = e['osm_object_url'].split("/")[4]
            if type == "relation" and format == "maproulette":
                #relations skipped due to https://github.com/maproulette/maproulette2/issues/259
                continue
            returned += type+'('+id+');' + "\n"
    returned += get_query_footer(format)
    return returned

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
