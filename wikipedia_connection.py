# coding=utf-8
# download prefix in functions means that the function will inevitably attempt to download
# get prefix means that it will try to use cache before downloading

import os.path
import re
import json
import urllib.request, urllib.error, urllib.parse
import hashlib

class UrlResponse:
    def __init__(self, content, code):
        self.content = content
        self.code = code


def download(url):
    while True:
        try:
            print("downloading " + url)
            f = urllib.request.urlopen(url)
            return UrlResponse(f.read(), f.getcode())
        except urllib.error.HTTPError as e:
            return UrlResponse("", e.getcode())
        except urllib.error.URLError as e:
            print(("no response from server for url " + url))
            print(e)
            continue

def get_from_wikipedia_api(language_code, what, article_name):
    language_code = urllib.parse.quote(language_code)
    article_name = urllib.parse.quote(article_name)
    url = "https://" + language_code + ".wikipedia.org/w/api.php?action=query&format=json"+what+"&redirects=&titles=" + article_name
    parsed_json = json.loads(get_from_generic_url(url))
    id = list(parsed_json['query']['pages'])[0]
    data = parsed_json['query']['pages'][id]
    return data

def get_intro_from_wikipedia(language_code, article_name, requested_length=None):
    request = "&prop=extracts&exintro=&explaintext"
    if requested_length != None:
        request += "&exchars=" + str(requested_length)

    data = get_from_wikipedia_api(language_code, request, article_name)
    try:
        return data['extract']
    except KeyError:
        print(("Failed extract extraction for " + article_name + " on " + language_code))
        return None
    raise("unexpected")

def get_pageprops(language_code, article_name):
    data = get_from_wikipedia_api(language_code, "&prop=pageprops", article_name)
    try:
        return data['pageprops']
    except KeyError:
        print(("Failed pageprops extraction for " + article_name + " on " + language_code))
        return None
    raise("unexpected")

def get_image_from_wikipedia_article(language_code, article_name):
    page = get_pageprops(language_code, article_name)
    if page == None:
        return None
    filename_via_page_image =  None
    try:
        filename_via_page_image = "File:" + page['page_image']
    except KeyError:
        return None
    return filename_via_page_image

def get_wikidata_object_id_from_article(language_code, article_name, forced_refresh = False):
    try:
        wikidata_entry = get_data_from_wikidata(language_code, article_name, forced_refresh)['entities']
        id = list(wikidata_entry)[0]
        if id == "-1":
            return None
        return id
    except KeyError:
        return None

def get_property_from_wikidata(wikidata_id, property, forced_refresh = False):
    wikidata = get_data_from_wikidata_by_id(wikidata_id, forced_refresh)
    try:
        return wikidata['entities'][wikidata_id]['claims'][property]
    except KeyError:
        return None

def get_interwiki_link(language_code, article_name, target_language_code, forced_refresh = False):
    wikidata_id = get_wikidata_object_id_from_article(language_code, article_name)
    if wikidata_id == None:
        return None
    wikidata = get_data_from_wikidata_by_id(wikidata_id, forced_refresh)
    try:
        return wikidata['entities'][wikidata_id]['sitelinks'][target_language_code+"wiki"]['title']
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
    return "File:"+data['datavalue']['value'].replace(" ", "_")

def get_location_from_wikidata(wikidata_id):
    data = get_property_from_wikidata(wikidata_id, 'P625')
    if data == None:
        return (None, None)
    data = data[0]['mainsnak']
    if data == None:
        return (None, None)
    data = data['datavalue']['value']
    return data['latitude'], data['longitude']

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

def get_form_of_link_usable_as_filename_without_data_loss(link):
    #TODO - on cache purge replace get_form_of_link_usable_as_filename by this
    #to ensure that extension (especially .code.txt) are going to work - othewise url ending on .code would cause problems
    link = link.replace(".", ".d.")

    link = link.replace("\"", ".q.")
    link = link.replace("*", ".st.")
    link = link.replace("\\", ".b.")
    link = link.replace("/", ".s.")
    link = link.replace("?", ".qe.")
    link = link.replace("<", ".l.")
    link = link.replace(">", ".g.")
    link = link.replace("|", ".p.")
    return link

def url_to_hash(url):
    return hashlib.sha256(url.encode('utf-8')).hexdigest()

def set_cache_location(path):
    global cache_location_store
    cache_location_store = path

def cache_location():
    assert(cache_location_store != None)
    return cache_location_store

def wikidata_language_placeholder():
    return 'wikidata_by_id'

def get_filename_with_wikidata_entity_by_id(id):
    return os.path.join(cache_location(), 'cache', wikidata_language_placeholder(), get_form_of_link_usable_as_filename(id) + ".wikidata_entity.txt")

def get_filename_with_wikidata_by_id_response_code(id):
    return os.path.join(cache_location(), 'cache', wikidata_language_placeholder(), get_form_of_link_usable_as_filename(id) + ".wikidata_entity.code.txt")

def get_filename_with_wikidata_entity(language_code, article_name):
    return os.path.join(cache_location(), 'cache', language_code, get_form_of_link_usable_as_filename(article_name) + ".wikidata_entity.txt")

def get_filename_with_wikidata_response_code(language_code, article_name):
    return os.path.join(cache_location(), 'cache', language_code, get_form_of_link_usable_as_filename(article_name) + ".wikidata_entity.code.txt")

def get_filename_with_article(language_code, article_name):
    return os.path.join(cache_location(), 'cache', language_code, get_form_of_link_usable_as_filename(article_name) + ".txt")

def get_filename_with_wikipedia_response_code(language_code, article_name):
    return os.path.join(cache_location(), 'cache', language_code, get_form_of_link_usable_as_filename(article_name) + ".code.txt")

def write_to_file(filename, content):
    specified_file = open(filename, 'w')
    specified_file.write(content)
    specified_file.close()

def write_to_binary_file(filename, content):
    specified_file = open(filename, 'wb')
    specified_file.write(content)
    specified_file.close()

def ensure_that_cache_folder_exists(language_code):
    path = os.path.join(cache_location(), 'cache', language_code)
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

def is_it_necessary_to_reload_files(content_filename, response_code_filename):
    if not os.path.isfile(content_filename) or not os.path.isfile(response_code_filename):
        return True
    else:
        files_need_reloading = False
        code_file = open(response_code_filename, 'r')
        if code_file.read() == "":
            files_need_reloading = True
        code_file.close()
        return files_need_reloading
    return False

def get_data_from_cache_files(response_filename, response_code_filename):
    response_file = open(response_filename, 'r')
    response = response_file.read()
    response_file.close()
    code_file = open(response_code_filename, 'r')
    code = int(code_file.read())
    code_file.close()
    if code != 200:
        return None
    return response

def download_data_from_wikipedia(language_code, article_name):
    ensure_that_cache_folder_exists(language_code)
    response_filename = get_filename_with_article(language_code, article_name)
    code_filename = get_filename_with_wikipedia_response_code(language_code, article_name)
    url = "https://" + urllib.parse.quote(language_code) + ".wikipedia.org/wiki/" + urllib.parse.quote(article_name)
    result = download(url)
    write_to_file(response_filename, str(result.content))
    write_to_file(code_filename, str(result.code))

def download_data_from_wikidata_by_id(wikidata_id):
    ensure_that_cache_folder_exists(wikidata_language_placeholder())
    response_filename = get_filename_with_wikidata_entity_by_id(wikidata_id)
    code_filename = get_filename_with_wikidata_by_id_response_code(wikidata_id)

    url = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids=" + urllib.parse.quote(wikidata_id) + "&format=json"
    result = download(url)
    content = str(result.content.decode())
    write_to_file(response_filename, content)
    write_to_file(code_filename, str(result.code))

def get_data_from_wikidata_by_id(wikidata_id, forced_refresh=False):
    if it_is_necessary_to_reload_wikidata_by_id_files(wikidata_id) or forced_refresh:
        download_data_from_wikidata_by_id(wikidata_id)
    response_filename = get_filename_with_wikidata_entity_by_id(wikidata_id)
    response_code_filename = get_filename_with_wikidata_by_id_response_code(wikidata_id)
    if not os.path.isfile(response_filename):
        print(it_is_necessary_to_reload_wikidata_by_id_files(wikidata_id))
        print(response_filename)
        assert False
    response = get_data_from_cache_files(response_filename, response_code_filename)
    if response == None:
        return response
    return json.loads(response)

def it_is_necessary_to_reload_wikidata_by_id_files(wikidata_id):
    content_filename = get_filename_with_wikidata_entity_by_id(wikidata_id)
    response_code_filename = get_filename_with_wikidata_by_id_response_code(wikidata_id)
    return is_it_necessary_to_reload_files(content_filename, response_code_filename)

def download_data_from_wikidata(language_code, article_name):
    ensure_that_cache_folder_exists(language_code)
    response_filename = get_filename_with_wikidata_entity(language_code, article_name)
    code_filename = get_filename_with_wikidata_response_code(language_code, article_name)

    url = "https://www.wikidata.org/w/api.php?action=wbgetentities&sites=" + urllib.parse.quote(language_code) + "wiki&titles=" + urllib.parse.quote(article_name) + "&format=json"
    result = download(url)
    content = str(result.content.decode())
    write_to_file(response_filename, content)
    write_to_file(code_filename, str(result.code))

def get_data_from_wikidata(language_code, article_name, forced_refresh):
    if it_is_necessary_to_reload_wikidata_files(language_code, article_name) or forced_refresh:
        download_data_from_wikidata(language_code, article_name)
    response_filename = get_filename_with_wikidata_entity(language_code, article_name)
    response_code_filename = get_filename_with_wikidata_response_code(language_code, article_name)
    if not os.path.isfile(response_filename):
        print(it_is_necessary_to_reload_wikidata_files(language_code, article_name))
        print(response_filename)
        assert False
    response = get_data_from_cache_files(response_filename, response_code_filename)
    if response == None:
        return response
    return json.loads(response)


def it_is_necessary_to_reload_wikidata_files(language_code, article_name):
    content_filename = get_filename_with_wikidata_entity(language_code, article_name)
    response_code_filename = get_filename_with_wikidata_response_code(language_code, article_name)
    return is_it_necessary_to_reload_files(content_filename, response_code_filename)

def it_is_necessary_to_reload_wikipedia_files(language_code, article_name):
    content_filename = get_filename_with_article(language_code, article_name)
    response_code_filename = get_filename_with_wikipedia_response_code(language_code, article_name)
    return is_it_necessary_to_reload_files(content_filename, response_code_filename)

def get_wikipedia_page(language_code, article_name, forced_refresh):
    if it_is_necessary_to_reload_wikipedia_files(language_code, article_name) or forced_refresh:
        download_data_from_wikipedia(language_code, article_name)
    response_filename = get_filename_with_article(language_code, article_name)
    response_code_filename = get_filename_with_wikipedia_response_code(language_code, article_name)
    if not os.path.isfile(response_filename):
        print(it_is_necessary_to_reload_wikipedia_files(language_code, article_name))
        print(response_filename)
        assert False
    response = get_data_from_cache_files(response_filename, response_code_filename)
    return response

def get_filename_cache_for_url(url):
    #HACK! but simply using get_form_of_link_usable_as_filename is not going to work as filename due to limit of filename length
    return os.path.join(cache_location(), 'cache', 'url', url_to_hash(url) + ".txt")

def get_filename_cache_for_url_response_code(url):
    return os.path.join(cache_location(), 'cache', 'url', url_to_hash(url) + ".code.txt")

def it_is_necessary_to_reload_generic_url(url):
    content_filename = get_filename_cache_for_url(url)
    code_filename = get_filename_cache_for_url_response_code(url)
    return is_it_necessary_to_reload_files(content_filename, code_filename)

def download_data_from_generic_url(url):
    ensure_that_cache_folder_exists('url')
    response_filename = get_filename_cache_for_url(url)
    code_filename = get_filename_cache_for_url_response_code(url)
    result = download(url)
    write_to_file(response_filename, str(result.content.decode()))
    write_to_file(code_filename, str(result.code))

def get_from_generic_url(url, forced_refresh=False):
    if it_is_necessary_to_reload_generic_url(url) or forced_refresh:
        download_data_from_generic_url(url)
    response_filename = get_filename_cache_for_url(url)
    code_filename = get_filename_cache_for_url_response_code(url)
    if not os.path.isfile(response_filename):
        print(it_is_necessary_to_reload_generic_url(url))
        print(response_filename)
        assert False
    response = get_data_from_cache_files(response_filename, code_filename)
    return response
