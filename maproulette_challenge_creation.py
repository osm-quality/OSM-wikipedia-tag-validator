# https://github.com/osmlab/maproulette-python-client
# https://github.com/osmlab/maproulette-python-client/issues/78
import maproulette
import json

api_key = None
user_id = None
with open('secret.json') as f:
    data = json.load(f)
    api_key = data['maproulette_api_key']
    user_id = data['maproulette_user_id']
    # https://github.com/osmlab/maproulette-python-client#getting-started
    # Your API key is listed at the bottom of https://maproulette.org/user/profile page.
    # expected file structure:
    """
{
    "maproulette_api_key": "d88hfhffiigibberishffiojsdjios90su28923h3r2rr"
    "maproulette_user_id": 784242309243
}
"""

def get_matching_maproulette_projects(api, search_term, user_id):
found = api.find_project(search_term)
if(found["status"] != 200):
    raise Exception("Unexpected status")
for project in found["data"]:
    if project["owner"] == user_id:
        yield project

config = maproulette.Configuration(api_key=api_key)
api = maproulette.Project(config)
my_project_name = "404"
for project in get_matching_maproulette_projects(api, my_project_name, user_id):
    print(json.dumps(project, indent=4, sort_keys=True))

# https://github.com/osmlab/maproulette-python-client#getting-started


# 404 links https://maproulette.org/admin/project/50406/challenge/37335/edit

# wikipedia tags linking to nonexisting pages in Germany (this time covers entire Germany)
# wikipedia tags linking to nonexisting pages in USA (note that only part of USA is covered, feel free to request processing of more states)
# reports from https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports/

"""
Try to follow link and fix/repair - if that fails, remove this wikipedia tag

Sometimes there are obvious typos, sometimes tags get mangled when people are editing something else, sometimes Wikipedia editors rename pages and make mistake by not leaving redirects.

Sometimes Wikipedia articles get deleted, sometimes people just add links pointing to nowhere.

And in some cases this report is wrong! For example if someone created a link pointing nowhere, then it was detected by this tool and later article was created then report here will be wrong!
"""

# Fix wikipedia tag pointing nowhere, detected by https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports/ - fixed with #maproulette


# Fix conflicting *wikidata and not:*wikidata tags, detected by https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports/ - fixed with #maproulette


# hmm, mention my site in MR so it is linked from it
# work around https://github.com/maproulette/maproulette3/issues/1563