# coding=utf-8

import os.path
import re

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


def get_filename_with_article(language_code, article_link):
    return os.path.join('cache', language_code, get_form_of_link_usable_as_filename(article_link) + ".txt")


def get_filename_with_code(language_code, article_link):
    return os.path.join('cache', language_code, get_form_of_link_usable_as_filename(article_link) + ".code.txt")

class UrlResponse:
    def __init__(self, content, code):
        self.content = content
        self.code = code


def fetch(url):
    while True:
        try:
            f = urllib2.urlopen(url)
            return UrlResponse(f.read(), f.getcode())
        except urllib2.HTTPError as e:
            return UrlResponse("", e.getcode())
        except urllib2.URLError as e:
            print "no response from server for url " + url
            print e
            continue

def write_to_file(filename, content):
    specified_file = open(filename, 'w')
    specified_file.write(content)
    specified_file.close()

def fetch_data_from_wikipedia(language_code, article_link):
    path = os.path.join('cache', language_code)
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
    print "fetching from " + language_code + "wiki: " + article_link
    article_filename = get_filename_with_article(language_code, article_link)
    code_filename = get_filename_with_code(language_code, article_link)
    url = "https://" + language_code + ".wikipedia.org/wiki/" + urllib2.quote(article_link)
    result = fetch(url)
    write_to_file(article_filename, str(result.content))
    write_to_file(code_filename, str(result.code))


def it_is_necessary_to_reload_files(language_code, article_link):
    article_filename = get_filename_with_article(language_code, article_link)
    code_filename = get_filename_with_code(language_code, article_link)

    if not os.path.isfile(article_filename) or not os.path.isfile(code_filename):
        files_need_reloading = True
    else:
        code_file = open(code_filename, 'r')
        if code_file.read() == "":
            files_need_reloading = True
        code_file.close()
    return False

def get_wikipedia_page(language_code, article_name, forced_refresh):
    if it_is_necessary_to_reload_files(language_code, article_name) or forced_refresh:
        fetch_data_from_wikipedia(language_code, article_name)
    article_file = open(get_filename_with_article(language_code, article_name), 'r')
    page = article_file.read()
    article_file.close()
    code_file = open(get_filename_with_code(language_code, article_name), 'r')
    code = int(code_file.read())
    code_file.close()
    if code != 200:
        return None
    return page
