# coding=utf-8

import os.path
import re
import json
import urllib.request, urllib.error, urllib.parse
from lxml import etree


class UrlResponse:
    def __init__(self, content, code):
        self.content = content
        self.code = code


def fetch(url):
    while True:
        try:
            print("fetching " + url)
            f = urllib.request.urlopen(url)
            return UrlResponse(f.read(), f.getcode())
        except urllib.error.HTTPError as e:
            return UrlResponse("", e.getcode())
        except urllib.error.URLError as e:
            print(("no response from server for url " + url))
            print(e)
            continue

def fetch_from_wikipedia_api(language_code, what, article_link):
    url = "https://" + language_code + ".wikipedia.org/w/api.php?action=query&format=json"+what+"&redirects=&titles=" + urllib.parse.quote(article_link)
    parsed_json = json.loads(fetch(url).content)
    id = list(parsed_json['query']['pages'])[0]
    data = parsed_json['query']['pages'][id]
    return data

def fetch_from_wikidata_api(language_code, article_link):
    url = "https://www.wikidata.org/w/api.php?action=wbgetentities&sites=" + language_code + "wiki&titles=" + urllib.parse.quote(article_link) + "&format=json"
    parsed_json = json.loads(str(fetch(url).content.decode()))
    return parsed_json

def fetch_from_wikidata_api_by_id(wikidata_id):
    url = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids=" + wikidata_id + "&format=json"
    parsed_json = json.loads(str(fetch(url).content.decode()))
    return parsed_json

def get_intro_from_wikipedia(language_code, article_link, requested_length=None):
    request = "&prop=extracts&exintro=&explaintext"
    if requested_length != None:
        request += "&exchars=" + str(requested_length)

    data = fetch_from_wikipedia_api(language_code, request, article_link)
    try:
        return data['extract'].encode('utf-8')
    except KeyError:
        print(("Failed extract extraction for " + article_link + " on " + language_code)) 
        return None
    raise("unexpected")

def turn_title_into_url_form(filename):
    return "File:"+urllib.parse.quote(filename[5:])
    return title.replace(" ", "%20") #TODO DELETE - most likely too limoted

def get_url_from_commons_image(filename, max_size=None):
    url = "https://tools.wmflabs.org/magnus-toolserver/commonsapi.php?image=" + turn_title_into_url_form(filename)
    tag_match = "file"
    if max_size != None:
        width, height = max_size
        url += "&thumbwidth=" + str(width) + "&thumbheight=" + str(height)
        tag_match = "thumbnail"
    data_about_image = fetch(url).content
    data = etree.ElementTree(etree.fromstring(data_about_image))
    for element in data.getiterator():
        if element.tag == tag_match and element.text != None:
            return element.text
    return None

def get_pageprops(language_code, article_link):
    data = fetch_from_wikipedia_api(language_code, "&prop=pageprops", article_link)
    try:
        return data['pageprops']
    except KeyError:
        print(("Failed pageprops extraction for " + article_link + " on " + language_code)) 
        return None
    raise("unexpected")

def get_image_from_wikipedia_article(language_code, article_link):
    page = get_pageprops(language_code, article_link)
    if page == None:
        return None
    filename_via_page_image =  None
    try:
        filename_via_page_image = "File:" + page['page_image'].encode('utf-8')
    except KeyError:
        print(("Failed image extraction via page image for " + article_link + " on " + language_code)) 
        return None
    return filename_via_page_image

def get_wikidata_id(language_code, article_link):
    page = get_pageprops(language_code, article_link)
    if page == None:
        return None
    wikidata_id = None
    try:
        wikidata_id = page['wikibase_item'].encode('utf-8')
    except KeyError:
        print(("Failed wikidata id extraction " + article_link + " on " + language_code))
        return None
    if wikidata_id == None:
        raise ValueError("wat")
    return wikidata_id

def get_data_from_wikidata(wikidata_id):
    url = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids="+wikidata_id+"&format=json"
    return json.loads(fetch(url).content)

def get_property_from_wikidata(wikidata_id, property):
    wikidata = get_data_from_wikidata(wikidata_id)
    try:
        return wikidata['entities'][wikidata_id]['claims'][property]
    except KeyError:
        return None

def get_interwiki_link(language_code, article_link, target_language_code):
    wikidata_id = get_wikidata_id(language_code, article_link)
    if wikidata_id == None:
        return None
    wikidata = get_data_from_wikidata(wikidata_id)
    try:
        return wikidata['entities'][wikidata_id]['sitelinks'][target_language_code+"wiki"]['title'].encode('utf-8')
    except KeyError:
        return None

def get_image_from_wikidata(wikidata_id):
    data = get_property_from_wikidata(wikidata_id, 'P18')
    if data == None:
        return None
    data = data[0]['mainsnak']
    if data['datatype'] != 'commonsMedia':
        print(("unexpected datatype for " + wikidata_id + " - " + datatype))
        return None
    return "File:"+data['datavalue']['value'].encode('utf-8').replace(" ", "_")

def get_location_from_wikidata(wikidata_id):
    data = get_property_from_wikidata(wikidata_id, 'P625')
    if data == None:
        return (None, None)
    data = data[0]['mainsnak']
    if data == None:
        return (None, None)
    data = data['datavalue']['value']
    return data['latitude'], data['longitude']

def get_page_image(link, max_size=None):
    language_code = get_language_code_from_link(link)
    article_link = get_article_name_from_link(link)
    filename_via_page_image = get_image_from_wikipedia_article(language_code, article_link)
    wikidata_id = get_wikidata_id(language_code, article_link)
    filename_via_wikidata = None 
    if wikidata_id != None:
        filename_via_wikidata = get_image_from_wikidata(wikidata_id)

    filename = filename_via_wikidata
    if filename == None:
        filename = filename_via_page_image
    if filename == None:
        return None
    return get_url_from_commons_image(filename, max_size)

def get_language_code_from_link(link):
    parsed_link = re.match('([^:]*):(.*)', link)
    if parsed_link is None:
        return None
    return parsed_link.group(1)


def get_article_name_from_link(link):
    parsed_link = re.match('([^:]*):(.*)', link)
    if parsed_link is None:
        return None
    return parsed_link.group(2)


def get_form_of_link_usable_as_filename(link):
    link = link.replace("\"", "")
    link = link.replace("*", "")
    link = link.replace("\\", "")
    link = link.replace("/", "")
    link = link.replace("?", "")
    link = link.replace("<", "")
    link = link.replace(">", "")
    link = link.replace("|", "")
    return link


def get_filename_with_wikidata_entity(language_code, article_link):
    return os.path.join('cache', language_code, get_form_of_link_usable_as_filename(article_link) + ".wikidata_entitytxt")

def get_filename_with_article(language_code, article_link):
    return os.path.join('cache', language_code, get_form_of_link_usable_as_filename(article_link) + ".txt")

def get_filename_with_code(language_code, article_link):
    return os.path.join('cache', language_code, get_form_of_link_usable_as_filename(article_link) + ".code.txt")

def write_to_file(filename, content):
    specified_file = open(filename, 'w')
    specified_file.write(content)
    specified_file.close()

def get_data_from_wikipedia(language_code, article_link):
    path = os.path.join('cache', language_code)
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
    print(("fetching from " + language_code + "wiki: " + article_link))
    article_filename = get_filename_with_article(language_code, article_link)
    code_filename = get_filename_with_code(language_code, article_link)
    url = "https://" + language_code + ".wikipedia.org/wiki/" + urllib.parse.quote(article_link)
    result = fetch(url)
    write_to_file(article_filename, str(result.content))
    write_to_file(code_filename, str(result.code))


def it_is_necessary_to_reload_files(language_code, article_link):
    article_filename = get_filename_with_article(language_code, article_link)
    code_filename = get_filename_with_code(language_code, article_link)

    if not os.path.isfile(article_filename) or not os.path.isfile(code_filename):
        return True
    else:
        files_need_reloading = False
        code_file = open(code_filename, 'r')
        if code_file.read() == "":
            files_need_reloading = True
        code_file.close()
        return files_need_reloading
    return False

def get_wikipedia_page(language_code, article_name, forced_refresh):
    if it_is_necessary_to_reload_files(language_code, article_name) or forced_refresh:
        get_data_from_wikipedia(language_code, article_name)
    wikipedia_article_cache_filepath = get_filename_with_article(language_code, article_name)
    if not os.path.isfile(wikipedia_article_cache_filepath):
        print(it_is_necessary_to_reload_files(language_code, article_name))
        print(wikipedia_article_cache_filepath)
        assert False
    article_file = open(wikipedia_article_cache_filepath, 'r')
    page = article_file.read()
    article_file.close()
    code_file = open(get_filename_with_code(language_code, article_name), 'r')
    code = int(code_file.read())
    code_file.close()
    if code != 200:
        return None
    return page
