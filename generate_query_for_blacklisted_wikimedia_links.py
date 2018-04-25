import wikimedia_connection.wikimedia_connection as wikimedia_connection
import wikimedia_link_issue_reporter
import wikipedia_knowledge
import osm_handling_config.global_config as osm_handling_config


def print_all_types(filter):
    print('node' + filter + ';')
    print('way' + filter + ';')
    print('relation' + filter + ';')


wikimedia_connection.set_cache_location(osm_handling_config.get_wikimedia_connection_cache_location())

blacklist = wikimedia_link_issue_reporter.WikimediaLinkIssueDetector().wikidata_connection_blacklist()
wikipedia_language_list = wikipedia_knowledge.WikipediaKnowledge.all_wikipedia_language_codes_order_by_importance()


print('[out:xml][timeout:3600];')
print('(')
for wikidata_id, data in blacklist.items():
    print_all_types('[wikidata=' + wikidata_id + ']')
    for potential_language_code in wikipedia_language_list:
        potential_article_name = wikimedia_connection.get_interwiki_article_name_by_id(wikidata_id, potential_language_code)
        if potential_article_name != None:
            print_all_types("[wikipedia='" + potential_language_code + ':' + potential_article_name + "']")

print(');')
print('out meta qt;')