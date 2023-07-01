# https://github.com/osmlab/maproulette-python-client
# https://github.com/osmlab/maproulette-python-client/issues/78
import maproulette
import json
import generate_webpage_with_error_output
import sqlite3
import config
import time

# https://maproulette.org/admin/project/53065/challenge/40012

def main():
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

    maproulette_config = maproulette.Configuration(api_key=api_key)
    project_api = maproulette.Project(maproulette_config)
    project_id = setup_project(project_api, user_id)
    # docs: https://github.com/osmlab/maproulette-python-client#getting-started



    # wikipedia tags linking to nonexisting pages in Germany (this time covers entire Germany)
    # wikipedia tags linking to nonexisting pages in USA (note that only part of USA is covered, feel free to request processing of more states)
    # reports from https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports/
    # Fix conflicting *wikidata and not:*wikidata tags - fixed with #maproulette

    # Create challenge

    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    for name in generate_webpage_with_error_output.for_review():
        reports = get_reports_with_specific_error_id(cursor, name)
        print("calling get_reports_with_specific_error_id:", name, len(reports), "- entries")
    connection.close()

    #error_id = "should use a secondary wikipedia tag - linking from wikipedia to a coat of arms"
    #update_or_create_challenge_based_on_error_id(challenge_api, project_id, error_id)

    #error_id = "should use a secondary wikipedia tag - linking from wikipedia and wikidata to a coat of arms"
    #update_or_create_challenge_based_on_error_id(challenge_api, project_id, error_id)

    #error_id = "should use a secondary wikipedia tag - linking from wikidata to a coat of arms"
    #update_or_create_challenge_based_on_error_id(challenge_api, project_id, error_id)
    exit()

    #error_id = "should use a secondary wikipedia tag - linking from wikipedia to a transport accident"
    #update_or_create_challenge_based_on_error_id(challenge_api, project_id, error_id)
    exit()

    challenge_api = maproulette.Challenge(maproulette_config)    
    error_id = "wikipedia tag links to 404"
    update_or_create_challenge_based_on_error_id(challenge_api, project_id, error_id)

    exit()

    print("trying generate_webpage_with_error_output.list_of_processed_entries_for_each_merged_group")
    merged_outputs =  generate_webpage_with_error_output.list_of_processed_entries_for_each_merged_group()
    for entry in merged_outputs:
        print(entry)

    print("trying reports per area")
    for name in generate_webpage_with_error_output.for_review():
        for entry in config.get_entries_to_process():
            internal_region_name = entry['internal_region_name']
            print("calling get_reports_with_specific_error_id_in_specific_area:", name, len(get_reports_with_specific_error_id_in_specific_area(cursor, name, internal_region_name)), "entries")

    # where it has ended?
    # https://www.maproulette.org/

    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L269

    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L136C9-L136C28
    # get challenge tasks

    exit()
    # hmm, mention my site in MR so it is linked from it

    # https://github.com/osmlab/maproulette-python-client/blob/dev/examples/project_examples.py

    # https://github.com/osmlab/maproulette-python-client/blob/dev/examples/challenge_examples.py
    # https://github.com/osmlab/maproulette-python-client/blob/38920add1b95b9ec472e1653915faf9eebe2a6b9/maproulette/api/challenge.py#L269 - add_tasks_to_challenge
    # https://github.com/osmlab/maproulette-python-client/blob/0a3e4b68af7892700463c2afc66a1ae4dcbf0825/maproulette/models/challenge.py

def update_or_create_challenge_based_on_error_id(challenge_api, project_id, error_id):
    data = get_challenge_data_from_project(challenge_api, project_id)
    challenge_id = None
    for challenge in data:
        if challenge["name"] == challenge_name:
            challenge_id = challenge['id']
    if challenge_id == None:
        create_link_challenge_based_on_error_id(challenge_api, project_id, error_id)

        print(project_id, "is without challenge", challenge_name)
        print(data)
        print(json.dumps(challenge_api.create_challenge(challenge_data)))
        raise "restart script after challenge creation I guess" # TODO do it properly 

    # Printing response:
    # https://maproulette.org/admin/projects

    print("getting reports from my database")

    # work around https://github.com/maproulette/maproulette3/issues/1563
    # overpass query cannot be changed
    # so we need to provide data manually
    geojson_object = get_data_of_a_specific_error_id(error_id)
    print("add_tasks_to_challenge")
    raise("figure way to add only still active ones (avoid readding done in MR), needs to fetch them and check prerequisites - try to reuse code here! Maybe somehow rely on central updater? Or recheck them right now? Number here is not so huge, I guess")
    delete_fresh_challenge_tasks(challenge_api, challenge_id)
    tasks_remaining = get_challenge_tasks(challenge_api, challenge_id)
    for task in tasks_remaining:
        print(task)
    if len(tasks_remaining) == 0:
        print("no tasks to view")
    raise("https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/task.py#L169 - delete tasks one by one? Is delete_fresh_challenge_tasks actually working and deleting only undone?")
    print(json.dumps(challenge_api.add_tasks_to_challenge(geojson_object, challenge_id)))

def create_link_challenge_based_on_error_id(challenge_api, project_id, error_id):
    for from_tags in [
        "wikipedia and wikidata",
        "wikipedia",
        "wikidata",
    ]
        if "should use a secondary wikipedia tag - linking from " + from_tags + " tag to " in error_id:
            new_tag_form = None
            if from_tags == "wikipedia and wikidata":
                new_tag_form = "subject:wikipedia and subject:wikidata"
            what = error_id.replace("should use a secondary wikipedia tag - linking from " + from_tags + " tag to ", "")
            challenge_name = from_tags + " tag linking to " + what + " - should use secondary wikipedia/wikidata tag"
            challenge_description = """Wikipedia article or wikidata entry linked from OSM object using wikipedia tag is not about something expected to be directly linkable
        
as thing such as """ + what + """is not being mapped in Wikipedia it is extremely unlikely that this """ + from_tags + """ tag is valid

it likely should be changed into """ + new_tag_form + """

for example historic=memorial commemorating """ + what + """ should link article about it using subject:wikipedia / subject:wikidata - as article is about subject of memorial, not about memorial itself]

(if article would be about memorial then linking it in main wikipedia/wikidata tag is fine)

in some cases wikipedia/wikidata tags should be simply removed if they are simply wrong or about entire class of object

in case that linked wikipedia/wikidata entry is not about """ + what + """ please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny so I can handle this false positive

REMEMBER: This is on Maproluette rather than being done by bot because some of this reports are wrong. Please review each entry rather than blindly retagging! If you start blindly editing, take a break."""
            # TODO synchronize with my own website, I guess
            challenge_instructions = """ """
    linked wikidata entry (Q204476) is about a human, so it is very unlikely to be correct
    subject:wikipedia=* or name:wikipedia tag would be probably better (see https://wiki.openstreetmap.org/wiki/Key:wikipedia#Secondary_Wikipedia_links for full list of what else may be applicable)
            changeset_action = "fixing primary link leading to " + what + " entry"
            create_challenge(challenge_api, project_id, challenge_name, challenge_description, challenge_instructions, changeset_action)

    if error_id == "wikipedia tag links to 404":
        challenge_name = "404 - fix Wikipedia links leading to an article which does not exist"
        challenge_description = "Wikipedia article linked from OSM object using wikipedia tag is missing and should be fixed"
        # TODO synchronize with my own website, I guess
        challenge_instructions = """Wikipedia article linked from OSM object using wikipedia tag is missing.

Try to follow link and fix/repair - if that fails, remove this wikipedia tag.

This problem can happen for multiple reasons and fix depends on what went wrong


- article was moved without leaving redirect and wikipedia tag should be edited to point to the new one (wikidata tag if present may help to find correct tag)
- someone made typo, for example failed to copy final letter of article title (fix link in such case)
- link is somehow malformed but fixable
- sometimes link was accidentally deleted by people editing something else - look at object history in such cases
- article may be deleted or never existed. In such cases wikipedia tag should be deleted.
- sometimes link was simply invalid anyway and should be deleted
- something else happened

And in some cases this report is wrong! For example if someone created a link pointing nowhere, then it was detected by this tool and later article was created then report here will be wrong!

It is useful to look at Wikipedia logs of not existing item - sadly, articles are often moved without leaving redirect (which is a major annoyance)

Please fix other problems if you spot them! Often they will be far more valuable than fixing wikipedia linking.

REMEMBER: This is on Maproluette rather than being done by bot because some of this reports are wrong, some are fixable but not in obvious ways. Please review each entry rather than blindly deleting! If you start blindly deleting, take a break.
"""
        changeset_action = "fixing links to nonexisting wikipedia articles"
        create_challenge(challenge_api, project_id, challenge_name, challenge_description, challenge_instructions, changeset_action)
    else:
        raise Unsupported # TODO find proper exception

def create_challenge(challenge_api, project_id, challenge_name, challenge_description, challenge_instructions, changeset_action):
    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/models/challenge.py#L7
    challenge_data = maproulette.ChallengeModel(name=challenge_name)
    challenge_data.description = challenge_description
    challenge_data.instruction = challenge_instructions
    challenge_data.enabled = True
    #challenge_data.blurb = "blurb blurb blurbblurb" # appears to be unused
    challenge_data.featured = True
    challenge_data.check_in_comment = changeset_action + ", detected by https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports/"
    challenge_data.check_in_source = None
    challenge_data.requires_local = False
    challenge_data.osm_id_property = "osm_link"
    # default_zoom max_zoom min_zoom
    # popularity
    # exportable_properties

    # Adding required instruction
    challenge_data.parent = project_id

def setup_project(project_api, user_id):
    my_project_name = "404"
    for project in get_matching_maproulette_projects(project_api, my_project_name, user_id):
        print("my project data found:")
        print(json.dumps(project, indent=4, sort_keys=True))

    my_project_name = "fix broken Wikipedia tags"
    projects = get_matching_maproulette_projects(project_api, my_project_name, user_id)
    if len(projects) == 0:
        my_project = maproulette.ProjectModel(name=my_project_name)
        # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/models/project.py#L7
        my_project.description = 'MapRoulette export/mirror of https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports/ reports'
        my_project.enabled = True
        my_project.featured = True # it actually works!
        my_project.display_name = my_project_name
        print("creating project")
        print(json.dumps(project_api.create_project(my_project), indent=4, sort_keys=True))
        projects = get_matching_maproulette_projects(project_api, my_project_name, user_id)
    else:
        print("project exists")
        print(json.dumps(projects, indent=4, sort_keys=True))
    if projects[0]["deleted"]:
        raise "project is deleted!"

    project_id = projects[0]["id"]
    return project_id

def get_data_of_a_specific_error_id(report_id):
    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    geojson_object = {
        "type": "FeatureCollection",
        "features": []
    }
    for name in generate_webpage_with_error_output.for_review():
        if name != report_id:
            print("skipping", name, "for now")
            continue
        reports = get_reports_with_specific_error_id(cursor, name)
        print("calling get_reports_with_specific_error_id:", name, len(reports), "entries")
        for entry in reports:
            print(json.dumps(entry, indent=4, sort_keys=True))
            print(entry['osm_object_url'])
            print(entry['error_id'])
            print(entry['error_message'])
            print(entry['location'])
            if "node" in entry['osm_object_url']:
                lon = entry['location']['lon']
                lat = entry['location']['lat']
                element = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat], # [longitude, latitude] 
                    },
                    "properties": {
                        "osm_link": entry['osm_object_url'],
                    }
                }
                if entry['error_message'] != "":
                    element['properties']['error_message'] = entry['error_message']
                for tag_key in entry['tags'].keys():
                    element['properties'][tag_key] = entry['tags'][tag_key]
                geojson_object["features"].append(element)
    connection.close()
    return geojson_object

def delete_fresh_challenge_tasks(challenge_api, challenge_id):
    # docs: https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L136C9-L136C28
    tasks = get_challenge_tasks(challenge_api, challenge_id)
    if len(tasks) == 0:
        print("no tasks here")
        return

    while True:
        try:
            challenge_api.delete_challenge_tasks(challenge_id, status_filters="0,4") # Delete created and deleted
            return
        except maproulette.api.errors.HttpError as e:
            print("delete_fresh_challenge_tasks", e)
            time.sleep(10)

def get_challenge_tasks(challenge_api, challenge_id):
    returned = []
    while True:
        try:
            for entry in challenge_api.get_challenge_tasks(challenge_id, limit=10000, page=0):
                returned.append(entry)
            return returned
        except maproulette.api.errors.HttpError as e:
            print("get_challenge_tasks", e)
            time.sleep(10)

def get_challenge_data_from_project(challenge_api, project_id):

    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L95
    response = challenge_api.get_challenge_listing(project_ids=project_id) # yes, stringified boolean
    if response["status"] != 200:
        raise
    data = response["data"]
    return data

def get_matching_maproulette_projects(api, search_term, user_id):
    returned = []
    found = api.find_project(search_term)
    if(found["status"] != 200):
        raise Exception("Unexpected status")
    for project in found["data"]:
        if project["owner"] == user_id:
            returned.append(project)
    return returned

def get_reports_with_specific_error_id(cursor, error_id):
    cursor.execute('SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id FROM osm_data WHERE error_id = :error_id', {"error_id": error_id})
    returned = []
    for entry in cursor.fetchall():
        rowid, object_type, id, lat, lon, tags, area_identifier, updated, validator_complaint, error_id = entry
        tags = json.loads(tags)
        validator_complaint = json.loads(validator_complaint)
        validator_complaint['location'] = {'lat': lat, 'lon': lon}
        returned.append(validator_complaint)
    return returned

def get_reports_with_specific_error_id_in_specific_area(cursor, error_id, internal_region_name):
    cursor.execute('SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id FROM osm_data WHERE error_id = :error_id AND area_identifier = :area_identifier', {"error_id": error_id, 'area_identifier': internal_region_name})
    returned = []
    for entry in cursor.fetchall():
        rowid, object_type, id, lat, lon, tags, area_identifier, updated, validator_complaint, error_id = entry
        tags = json.loads(tags)
        validator_complaint = json.loads(validator_complaint)
        returned.append(validator_complaint)
    return returned


main()
