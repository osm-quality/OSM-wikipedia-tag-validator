import argparse
import yaml

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

def print_html_header():
    print("<html>")
    print("<body>")
    print("<table>")

def link_to_osm_object(url):
    return '<a href="' + url + '" target="_new">OSM element with broken tag that should be fixed</a>'

def article_name_from_wikipedia_string(string):
    return string[string.find(":")+1:]

def language_code_from_wikipedia_string(string):
    return string[0:string.find(":")]

def escape_from_internal_python_string_to_html_ascii(string):
    return str(string).encode('ascii', 'xmlcharrefreplace').decode()

def format_wikipedia_link(string):
    if string == None:
        return "?"
    language_code = language_code_from_wikipedia_string(string)
    article_name = article_name_from_wikipedia_string(string)
    article_name = escape_from_internal_python_string_to_html_ascii(article_name)
    return '<a href="https://' + language_code + '.wikipedia.org/wiki/' + article_name + '" target="_new">' + language_code+":"+article_name + '</a>'

def print_table_row(text):
    print("<tr>")
    print("<td>")
    print(text)
    print("</td>")
    print("</tr>")

def parsed_args():
    parser = argparse.ArgumentParser(description='Production of webpage about validation of wikipedia tag in osm data.')
    parser.add_argument('-file', '-f', dest='file', type=str, help='name of yaml file produced by validator')
    args = parser.parse_args()
    if not (args.file):
        parser.error('Provide .osm file')
    return args

def htmlify(string):
    return escape_from_internal_python_string_to_html_ascii(string).replace("\n", "<br />")

def main():
    args = parsed_args()
    print_html_header()
    filename = args.file
    reported_errors = load_data(get_write_location()+"/"+filename)
    for e in reported_errors:
        if e['error_id'] == 'wikipedia tag links to 404':
            print_table_row(htmlify(e['error_message']))
            print_table_row(link_to_osm_object(e['osm_object_url']))
            current = format_wikipedia_link(e['current_wikipedia_target'])
            to = format_wikipedia_link(e['desired_wikipedia_target'])
            if to == current:
                to = "?"
            print_table_row( current + " -> " + to)
            if to != "?":
                print_table_row( escape_from_internal_python_string_to_html_ascii(article_name_from_wikipedia_string(e['desired_wikipedia_target'])))
            print_table_row( '-------' )
    for e in reported_errors:
        if e['error_id'] == 'wikipedia tag relinking necessary':
            print_table_row(htmlify(e['error_message']))
            print_table_row(link_to_osm_object(e['osm_object_url']))
            current = format_wikipedia_link(e['current_wikipedia_target'])
            to = format_wikipedia_link(e['desired_wikipedia_target'])
            if to == current:
                to = "?"
            print_table_row( current + " -> " + to)
            if to != "?":
                print_table_row( escape_from_internal_python_string_to_html_ascii(article_name_from_wikipedia_string(e['desired_wikipedia_target'])))
            print_table_row( '-------' )
    for e in reported_errors:
        if e['error_id'] == 'link to disambig':
            print_table_row(htmlify(e['error_message']))
            print_table_row(link_to_osm_object(e['osm_object_url']))
            current = format_wikipedia_link(e['current_wikipedia_target'])
            to = format_wikipedia_link(e['desired_wikipedia_target'])
            if to == current:
                to = "?"
            print_table_row( current + " -> " + to)
            if to != "?":
                print_table_row( escape_from_internal_python_string_to_html_ascii(article_name_from_wikipedia_string(e['desired_wikipedia_target'])))
            print_table_row( '-------' )

    print("</table>")
    print("</body>")
    print("</html>")

main()
