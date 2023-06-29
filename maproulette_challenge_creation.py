# https://github.com/osmlab/maproulette-python-client
# https://github.com/osmlab/maproulette-python-client/issues/78
import maproulette
import json
import generate_webpage_with_error_output
import sqlite3
import config

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
    api = maproulette.Project(maproulette_config)
    my_project_name = "404"
    for project in get_matching_maproulette_projects(api, my_project_name, user_id):
        print("my project data found:")
        print(json.dumps(project, indent=4, sort_keys=True))

    my_project_name = "fix broken Wikipedia links"
    projects = get_matching_maproulette_projects(api, my_project_name, user_id)
    if len(projects) == 0:
        """
        my_project = maproulette.ProjectModel(name='fix links: - Germany')
        my_project.description = 'my project description'
        print(json.dumps(api.create_project(my_project), indent=4, sort_keys=True))
        """
        my_project = maproulette.ProjectModel(name=my_project_name)
        # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/models/project.py#L7
        my_project.description = 'my project description'
        my_project.enabled = True
        my_project.featured = True # worth trying, I guess
        my_project.display_name = my_project_name
        print("creating project")
        print(json.dumps(api.create_project(my_project), indent=4, sort_keys=True))
    else:
        print("project exists")
        print(json.dumps(projects, indent=4, sort_keys=True))
    if len(projects) != 1: # handle somehow newly created, handle multiple
        raise

    project_id = projects[0]["id"]

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


    # handle
    # maproulette.api.errors.HttpError: {'status': 500, 'message': 'Challenge with name Test_Challenge_Name already exists in the database'}
    # best check whether challenge was created already
    # how to list challenges?

    # In order to create a new challenge, we can make our lives easier by using the Challenge Model
    challenge_name = "fix Wikipedia links leading to nonexisting pages"
    challenge_data = maproulette.ChallengeModel(name=challenge_name)

    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/models/challenge.py#L7

    # Adding example description
    challenge_data.description = "This is a test challenge"
    challenge_data.instruction = "instruction  instructioninstructioninstructioninstructioninstruction"
    challenge_data.enabled = True
    challenge_data.blurb = "blurbblurbblurbblurbblurbblurbblurbblurbblurbblurbblurbblurbblurb"
    challenge_data.featured = True # worth trying, I guess
    challenge_data.check_in_comment = "changeset comment default"
    challenge_data.check_in_source = "hashtag"
    challenge_data.requires_local = False
    # default_zoom max_zoom min_zoom
    # osm_id_property TODO !!!!!!!!!!!!!!!!!
    # popularity
    # exportable_properties

    # Adding required instruction
    challenge_data.instruction = "Do something"
    challenge_data.parent = project_id # see https://github.com/maproulette/challenge-reports/issues/13

    # Adding example overpass QL input for challenge
    # work around https://github.com/maproulette/maproulette3/issues/1563
    # overpass query cannot be changed
    #challenge_data.overpassQL = open('data/Example_OverpassQL_Query', 'r').read()

    # Create challenge
    challenge_api = maproulette.Challenge(maproulette_config)    

    data = get_challenge_data_from_project(challenge_api, project_id)

    if len(data) == 0:
        print(json.dumps(challenge_api.create_challenge(challenge_data)))
        data = get_challenge_data_from_project(challenge_api, project_id)

    elif len(data) == 1:
        print(data[0])
        if data[0]["name"] != challenge_name:
            raise
    else:
        raise
    challenge_id = data[0]['id']

    # Printing response:
    # https://maproulette.org/admin/projects

    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    print("getting reports from my database")

    geojson_object = {
        "type": "FeatureCollection",
        "features": []
    }

    for name in generate_webpage_with_error_output.for_review():
        if name != "wikipedia tag links to 404":
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
                        "osm": entry['osm_object_url'],
                        "description": entry['error_message'],
                    }
                }
                geojson_object["features"].append(element)

    print("add_tasks_to_challenge")
    print(json.dumps(challenge_api.add_tasks_to_challenge(geojson_object, challenge_id)))

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

    # TODO setup synthethic geojson or load from data

    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L269


    exit()
    # hmm, mention my site in MR so it is linked from it

    # https://github.com/osmlab/maproulette-python-client/blob/dev/examples/project_examples.py

    # https://github.com/osmlab/maproulette-python-client/blob/dev/examples/challenge_examples.py
    # https://github.com/osmlab/maproulette-python-client/blob/0a3e4b68af7892700463c2afc66a1ae4dcbf0825/maproulette/models/challenge.py
    # https://github.com/osmlab/maproulette-python-client/blob/38920add1b95b9ec472e1653915faf9eebe2a6b9/maproulette/api/challenge.py#L269 - add_tasks_to_challenge

def get_challenge_data_from_project(challenge_api, project_id):
    response = challenge_api.get_challenge_listing(project_ids=project_id)
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
