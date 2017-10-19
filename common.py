import html
import yaml
import os
import urllib.parse

def wikidata_url(wikidata_id):
    return "https://www.wikidata.org/wiki/" + wikidata_id

def wikipedia_url(language_code, article_name):
    return "https://" + language_code + ".wikipedia.org/wiki/" + urllib.parse.quote(article_name)

def parse_yaml_file(filename):
    with open(filename, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            raise(exc)

def get_file_storage_location():
    cache_location_config_filepath = 'cache_location.config'
    if not os.path.isfile(cache_location_config_filepath):
        raise "failed to locate " + cache_location_config_filepath
    cache_location_file = open(cache_location_config_filepath, 'r')
    returned = cache_location_file.read()
    cache_location_file.close()
    return returned

def escape_from_internal_python_string_to_html_ascii(string):
    return str(string).encode('ascii', 'xmlcharrefreplace').decode()

def htmlify(string):
    escaped = html.escape(string)
    escaped_ascii = escape_from_internal_python_string_to_html_ascii(escaped)
    return escaped_ascii.replace("\n", "<br />")

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
        header+= '[out:json]'
    elif format == "josm":
        header += '[out:xml]'
    else:
        assert(False)
    header += "[timeout:3600]"
    header += ";"
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

def escape_for_overpass(text):
    text = text.replace("\\", "\\\\")
    return text.replace("'", "\\'")

def get_prerequisite_in_overpass_query_format(error):
    try:
        return tag_dict_to_overpass_query_format(error['prerequisite'])
    except KeyError:
        return ""

def tag_dict_to_overpass_query_format(tags):
    returned = ""
    for key in tags.keys():
        escaped_key = escape_for_overpass(key)
        if tags[key] == None:
            returned += "['" + escaped_key + "'!~'.*']"
        else:
            escaped_value = escape_for_overpass(tags[key])
            returned += "['" + escaped_key + "'='" + escaped_value + "']"
    return returned

def get_query_for_loading_errors_by_category(filename, printed_error_ids, format):
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
            returned += type+'('+id+')' + get_prerequisite_in_overpass_query_format(e) + ';' + "\n"
    returned += get_query_footer(format) + "//" + str(printed_error_ids)
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
