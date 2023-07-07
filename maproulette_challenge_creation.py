# https://github.com/osmlab/maproulette-python-client
# https://github.com/osmlab/maproulette-python-client/issues/78
import maproulette
import json
import generate_webpage_with_error_output
import sqlite3
import config
import time
import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer
import random
# https://maproulette.org/admin/project/53065/challenge/40012
# https://maproulette.org/admin/project/53065
# https://maproulette.org/browse/projects/53065
# See https://maproulette.org/browse/projects/53065 for related challenges about fixing `wikipedia` / `wikidata` and related tags.
# https://maproulette.org/browse/projects/53065  set of challenges about fixing `wikipedia` / `wikidata` and related tags
# https://learn.maproulette.org/documentation/rebuilding-challenge-tasks/#content

# https://maproulette.org/challenge/40023/leaderboard - let people know after rescan, thank them

def main():
    api_key = None
    user_id = None
    print("find random edits, get their authors and thank them/verify - see https://www.openstreetmap.org/changeset/138121870")
    print("figure out how to update challenge state (switching featured status, to allow many projects filled with tasks at once")
    print("monitor how many featured challenges are there published (start more if 0, avoid adding tasks if 2 or more are existing)")
    with open('secret.json') as f:
        data = json.load(f)
        api_key = data['maproulette_api_key']
        user_id = data['maproulette_user_id']
        # https://github.com/osmlab/maproulette-python-client#getting-started
        # Your API key is listed at the bottom of https://maproulette.org/user/profile page.
        # expected file structure of secret.json:
        """
        {
            "maproulette_api_key": "d88hfhffiigibberishffiojsdjios90su28923h3r2rr"
            "maproulette_user_id": 784242309243
        }
        """

    maproulette_config = maproulette.Configuration(api_key=api_key)
    project_api = maproulette.Project(maproulette_config)
    task_api = maproulette.Task(maproulette_config)
    challenge_api = maproulette.Challenge(maproulette_config)
    project_id = setup_project(project_api, user_id)
    # docs: https://github.com/osmlab/maproulette-python-client#getting-started


    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()

    greenlit_groups_to_be_featured = [
    ]
    greenlit_groups_not_to_be_featured = [
    ]
    for_later = [
        # will go to featured group
        'should use a secondary wikipedia tag - linking from wikipedia tag to a human',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to an object that exists outside physical reality',

        # upload but not featured group
        'should use a secondary wikipedia tag - linking from wikidata tag to an aspect in a geographic region',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to an aspect in a geographic region',

        # may be full of Wikidata lies and merged entries
        'should use a secondary wikipedia tag - linking from wikipedia tag to a brand',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a brand',
        'should use a secondary wikipedia tag - linking from wikidata tag to a brand',

        'malformed wikipedia tag - for architect prefixed tags', # see 'malformed wikipedia tag - for operator prefixed tags' - very minor example work needed
        'information board with wikipedia tag, not subject:wikipedia', # very minor additional coding needed, see its wikidata variant

        # ideally: supply that known replacement
        'blacklisted connection with known replacement',

        # requires text descriptions
        # no need to feature that
        'malformed secondary wikidata tag',
        'wikipedia wikidata mismatch - for name:etymology prefixed tags',
        'wikipedia wikidata mismatch - for network prefixed tags',
        'wikipedia wikidata mismatch - for operator prefixed tags',
        'wikipedia wikidata mismatch - for brand prefixed tags', # 22k entries [sic!] - requires some special support to limit count of open ones to 1000 or something...
        'no longer existing brand (according to Wikidata)', # >4k entries
        'wikipedia wikidata mismatch',

        # check is special description code working
        'should use a secondary wikipedia tag - linking from wikidata tag to a vehicle model or class',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a vehicle model or class',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a vehicle model or class',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a weapon model or class',
        'should use a secondary wikipedia tag - linking from wikidata tag to a weapon model or class',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a weapon model or class',

        # how to even tag this one?
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a type of structure',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a type of structure',

        # Wikidata misclassifies biblical figures, even ones definitely real so lets wait for refresh here
        'should use a secondary wikipedia tag - linking from wikidata tag to a fictional entity',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a fictional entity',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a fictional entity',

        # may be confusing or raise protests
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a religious denomination',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a religious denomination',
        'should use a secondary wikipedia tag - linking from wikidata tag to a sports competition',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a sports competition',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a sports competition',
        'should use a secondary wikipedia tag - linking from wikidata tag to a religious denomination',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a software', # see https://www.openstreetmap.org/note/3769352
        'should use a secondary wikipedia tag - linking from wikipedia tag to a public transport network',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a public transport network',
        'should use a secondary wikipedia tag - linking from wikidata tag to a public transport network',
        "secondary wikidata tag links to 404", # look at that later - many should be reported as malformed - many should stop being listed here
        "link to an unlinkable article", # disambigs got own category now - many should stop being listed here
        'wikipedia wikidata mismatch - for on_the_list prefixed tags',
        'mismatching teryt:simc codes in wikidata and in osm element',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a film festival',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a festival',
    ]
    already_uploaded_featured_pool = [
        "wikipedia tag links to 404",
        'should use a secondary wikipedia tag - linking from wikipedia tag to a physical process',
        'should use a secondary wikipedia tag - linking from wikidata tag to a human',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a human',
        'should use a secondary wikipedia tag - linking from wikipedia tag to an animal or plant (and not an individual one)',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to an animal or plant (and not an individual one)',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a chain store',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a general industry',
        'information board with wikidata tag, not subject:wikidata',
        "wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not",
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a physical process',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a restaurant chain',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a heraldic animal',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to an explosion',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a protest',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a violation of law',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a transport accident',
        'should use a secondary wikipedia tag - linking from wikipedia tag to an object that exists outside physical reality',
        'should use a secondary wikipedia tag - linking from wikipedia tag to an aspect in a geographic region',
        'should use a secondary wikipedia tag - linking from wikidata tag to a transport accident',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a conflict',
    ] # TODO assign featured status to them as needed, remove featured status from other
    already_uploaded = [
        'should use a secondary wikipedia tag - linking from wikidata tag to an animal or plant (and not an individual one)',
        'should use a secondary wikipedia tag - linking from wikidata tag to a chain store',
        'should use a secondary wikipedia tag - linking from wikidata tag to a social issue',
        'should use a secondary wikipedia tag - linking from wikidata tag to a physical process',
        'should use a secondary wikipedia tag - linking from wikidata tag to a general industry',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a chain store',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a type of world view',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a violation of law',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a transport accident',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a television series',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a historical event',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a social issue',
        'malformed wikipedia tag - for operator prefixed tags',
        "wikipedia/wikidata type tag that is incorrect according to not:* tag",
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for brand prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for subject prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for name:etymology prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for operator prefixed tags',
        
        'wikipedia wikidata mismatch - for species prefixed tags',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to an object that exists outside physical eality',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a conflict',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a social movement',
        "malformed wikipedia tag",
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for taxon prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for species prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for artist prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for architect prefixed tags',
    ]
    show_candidate_reports(cursor, greenlit_groups_to_be_featured + greenlit_groups_not_to_be_featured + for_later, already_uploaded + already_uploaded_featured_pool)
    return

    for error_id in greenlit_groups_to_be_featured:
        update_or_create_challenge_based_on_error_id(challenge_api, task_api, project_id, error_id, featured = True)

    for error_id in greenlit_groups_not_to_be_featured:
        update_or_create_challenge_based_on_error_id(challenge_api, task_api, project_id, error_id, featured = False)

    # this also regenerates descriptions
    set_featured_status_for_challenge_for_given_error_id(challenge_api, project_id, already_uploaded_featured_pool[0], True)
    set_featured_status_for_challenge_for_given_error_id(challenge_api, project_id, already_uploaded_featured_pool[1], True)
    # TODO: skip ones with no tasks remaining for featuration
    for error_id in already_uploaded_featured_pool[2:] + already_uploaded:
        challenge_id = get_challenge_id_based_on_error_id(challenge_api, project_id, error_id)
        if challenge_id != None:
            set_featured_status_for_challenge_for_given_error_id(challenge_api, project_id, error_id, False)

    #random.shuffle(already_uploaded_featured_pool + already_uploaded)
    #for error_id in already_uploaded:
    #    update_or_create_challenge_based_on_error_id(challenge_api, task_api, project_id, error_id, featured = False)

    connection.close()

    #print("trying reports per area")
    #for name in generate_webpage_with_error_output.for_review():
    #    for entry in config.get_entries_to_process():
    #        internal_region_name = entry['internal_region_name']
    #        print("calling get_reports_with_specific_error_id_in_specific_area:", name, len(get_reports_with_specific_error_id_in_specific_area(cursor, name, internal_region_name)), "entries")

    # where it has ended?
    # https://www.maproulette.org/

    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L269

    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L136C9-L136C28
    # get challenge tasks

    exit()
    # TODO hmm, mention my site in MR so it is linked from it

    # https://github.com/osmlab/maproulette-python-client/blob/dev/examples/challenge_examples.py
    # https://github.com/osmlab/maproulette-python-client/blob/38920add1b95b9ec472e1653915faf9eebe2a6b9/maproulette/api/challenge.py#L269 - add_tasks_to_challenge
    # https://github.com/osmlab/maproulette-python-client/blob/0a3e4b68af7892700463c2afc66a1ae4dcbf0825/maproulette/models/challenge.py

def regenerate_tasks(challenge_api, task_api, error_ids):
    count = 0
    for error_id in error_ids:
        print(error_id)
        print(error_id)
        challenge_id = get_challenge_id_based_on_error_id(challenge_api, project_id, error_id)
        if challenge_id == None:
            continue
        tasks_in_challenge = get_challenge_tasks(challenge_api, challenge_id)
        for task in tasks_in_challenge:
            status = task['status']
            STATUS_CREATED = 0
            STATUS_DELETED = 4
            if status == STATUS_CREATED:
                link = "https://maproulette.org/task/" + str(task['id'])
                print(link, "deleting item", count)
                count += 1
                task_api.update_task_status(task['id'], STATUS_DELETED, "", "", False)
        set_featured_status_for_challenge_for_given_error_id(challenge_api, project_id, error_id, False)
        update_or_create_challenge_based_on_error_id(challenge_api, task_api, project_id, error_id, featured = False)

def show_candidate_reports(cursor, for_later, already_uploaded):
    no_reports = 0
    few_reports = 0
    already_handled = 0
    for name in generate_webpage_with_error_output.for_review():
        if name in for_later:
            continue
        if name in already_uploaded:
            already_handled += 1
            continue
        reports = get_reports_with_specific_error_id(cursor, name)
        if len(reports) == 0:
            no_reports += 1
        elif len(reports) < 50 and "should use a secondary wikipedia tag" not in name and "wikipedia points to disambiguation page and wikidata does not" not in name:
            few_reports += 1
        else:
            #print("calling get_reports_with_specific_error_id:", name, "-", len(reports), "entries")
            print("        '" + name + "',")
            
    print(no_reports, "categories without reports")
    print(few_reports, "categories with few reports")
    print(already_handled, "already handled")

def get_challenge_id_based_on_error_id(challenge_api, project_id, error_id):
    data = get_challenge_data_from_project(challenge_api, project_id)
    texts = get_challenge_text_based_on_error_id(error_id)
    challenge_name = texts['challenge_name']
    challenge_id = None
    for challenge in data:
        if challenge["name"] == challenge_name:
            challenge_id = challenge['id']
    return challenge_id

def get_osm_link_from_task(task):
    link = "https://maproulette.org/task/" + str(task['id'])
    if len(task['geometries']['features']) != 1:
        print(json.dumps(task, indent=4, sort_keys=True))
        print(len(task['geometries']['features']))
        raise
    if '@id' in task['geometries']['features'][0]['properties']:
        osm_link = "htps://openstreetmap.org" + task['geometries']['features'][0]['properties']['@id']
    elif 'osm_link' in in_mr_already[present_url]['properties']:
        # some old data, should be only for solved/disabled ones
        osm_link = task['geometries']['features'][0]['properties']['osm_link']
    else:
        print(task)
        raise "unexpected"

def update_or_create_challenge_based_on_error_id(challenge_api, task_api, project_id, error_id, featured):
    challenge_id = get_challenge_id_based_on_error_id(challenge_api, project_id, error_id)
    challenge_name = get_challenge_text_based_on_error_id(error_id)['challenge_name']

    collected_data_for_use = get_data_of_a_specific_error_id(error_id)
    if len(collected_data_for_use) == 0 and challenge_id == None:
        print(challenge_name, "no tasks, challenge not created, therefore skipping doing anything")
        return

    if challenge_id == None:
        print(project_id, "is without challenge for")
        print(error_id)
        print("will be named")
        print(challenge_name)
        create_link_challenge_based_on_error_id(challenge_api, project_id, error_id, featured)
        print(project_id, "was without challenge for", error_id)
        time.sleep(5)
        challenge_id = get_challenge_id_based_on_error_id(challenge_api, project_id, error_id)
        #print(data)
        if challenge_id == None:
            raise "restart script after challenge creation I guess" # TODO do it properly 

    tasks_in_challenge = get_challenge_tasks(challenge_api, challenge_id)

    # Printing response:
    # https://maproulette.org/admin/projects

    print("getting reports from my database")

    # work around https://github.com/maproulette/maproulette3/issues/1563
    # overpass query cannot be changed
    # so we need to provide data manually

    # prerequisites checked with live data
    # still, some may be marked on MR as too hard or invalid

    some_require_manual_investigation = False
    in_mr_already = {}
    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L198
    # 0 = Created, 1 = Fixed, 2 = False Positive, 3 = Skipped, 4 = Deleted, 5 = Already Fixed, 6 = Too Hard
    STATUS_CREATED = 0
    STATUS_FIXED = 1
    STATUS_FALSE_POSITIVE = 2
    STATUS_SKIPPED = 3
    STATUS_DELETED = 4
    STATUS_ALREADY_FIXED = 5
    STATUS_TOO_HARD = 6
    for task in tasks_in_challenge:
        #print(json.dumps(task, indent=4, sort_keys=True))
        status = task['status']
        if status == STATUS_DELETED:
            continue
        osm_link = get_osm_link_from_task(task)
        in_mr_already[osm_link] = task
        modified_time = task['modified']
        link = "https://maproulette.org/task/" + str(task['id'])
        if status != STATUS_CREATED and status != STATUS_FIXED and status != STATUS_SKIPPED and status != STATUS_DELETED and status != 5:
            if status == 2:
                print("False positive", link)
                some_require_manual_investigation = True
            elif status == 6:
                print("Too hard", link)
                some_require_manual_investigation = True
            else:
                print("unexpected status", status, "for", link)
                #raise "unexpected"
                some_require_manual_investigation = True

    candidates = []
    for entry in collected_data_for_use:
        candidates.append(entry['osm_object_url'])

    for osm_url in in_mr_already.keys():
        if osm_url not in candidates:
            if in_mr_already[osm_url]['status'] == STATUS_CREATED:
                pass
            elif in_mr_already[osm_url]['status'] == STATUS_FIXED:
                continue
            elif in_mr_already[osm_url]['status'] == STATUS_FALSE_POSITIVE:
                pass
            elif in_mr_already[osm_url]['status'] == STATUS_SKIPPED:
                pass
            elif in_mr_already[osm_url]['status'] == STATUS_DELETED:
                continue
            elif in_mr_already[osm_url]['status'] == STATUS_ALREADY_FIXED:
                continue
            elif in_mr_already[osm_url]['status'] == STATUS_TOO_HARD:
                pass
            else:
                print("unexpected status", in_mr_already[osm_url]['status'])
            link = "https://maproulette.org/task/" + str(in_mr_already[osm_url]['id'])
            print(link, osm_url, "should be marked as deleted as it is present in task and not in reports from database")
            # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/task.py#L169
            print(in_mr_already[osm_url]['id'])
            print(STATUS_DELETED)
            try:
                task_api.update_task_status(in_mr_already[osm_url]['id'], STATUS_DELETED, "", "", False)
            except maproulette.api.errors.HttpError as e:
                print(e)
                print(dir(e))
                print(e.message)
                print(e.status)
                if e.message == "This task is locked by another user, cannot update status at this time.":
                    # happens with entries just being edited
                    pass
                else:
                    raise e
        # on one hand: entries present in MR, missing from my listing (delete them)
            # update status of specific task, including deletion
            # TODO important as the first step to update missing

        # on the other: "Fixed" "False Positive" "Already Fixed" in MR: delete from database, avoid readding them
        # avoid readding any already in MR
        # what about ones in MR already, detected as problem, with newer date? List them I guess

    geojson_object = {
        "type": "FeatureCollection",
        "features": []
    }
    for entry in collected_data_for_use:
        if entry['osm_object_url'] in in_mr_already.keys():
            # link was listed already and is in some state, not need to send it again
            # though what about cases where user falsely claimed that something is fixed? TODO
            # leave it for the future, I guess
            if in_mr_already[present_url]['status'] == STATUS_DELETED:
                raise "was not supposed to happen"
            if "https://www.openstreetmap.org/way/98707279" == entry['osm_object_url']:
                raise "so why it is not shown?"
            pass
        else:
            if entry['geometry'] == 'point':
                element = build_geojson_node_entry(entry['lon'], entry['lat'], entry['osm_object_url'], entry['error_message'], entry['tags'])
                geojson_object["features"].append(element)
            else:
                element = build_geojson_way_entry(entry['way_ids'], entry['osm_object_url'], entry['error_message'], entry['tags'])
                geojson_object["features"].append(element)
            #if (len(in_mr_already.keys()) > 0):
            #    if len(geojson_object["features"]) >= 10:
            #        print(json.dumps(geojson_object, indent=4, sort_keys=True))
            #        break # try to diagnose why only France was listed
    #print(challenge_id)
    try:
        print(json.dumps(challenge_api.add_tasks_to_challenge(geojson_object, challenge_id), indent=4, sort_keys=True))
    except requests.exceptions.ConnectionError as e:
        print(e)
        print("will retry")
        time.sleep(10)
        print(json.dumps(challenge_api.add_tasks_to_challenge(geojson_object, challenge_id), indent=4, sort_keys=True))
    print(challenge_name, "processed")
    if some_require_manual_investigation:
        raise Exception("look at these entries")

def get_challenge_text_based_on_error_id(error_id):
    for from_tags in [
        "wikipedia and wikidata",
        "wikipedia",
        "wikidata",
    ]:
        if "should use a secondary wikipedia tag - linking from " + from_tags + " tag to " in error_id:
            what = error_id.replace("should use a secondary wikipedia tag - linking from " + from_tags + " tag to ", "")
            challenge_name = from_tags + " tag linking to " + what + " - should use secondary " + from_tags + " tag"
            challenge_description = """Things like """ + what + """ are never directly linkable from `wikidata`/`wikipedia` tags - they can be linked in some cases from properly prefixed secondary tags - and in some should be removed.
            
For example `subject:wikipedia` to link subject of a sculpture - `wikipedia` tag is for linking article about sculpture itself, not about what it is depicting).
And `name:etymology:wikidata` links Wikidata entry that describes source of name of a given object.
            
See https://wiki.openstreetmap.org/wiki/Key:wikipedia#Secondary_Wikipedia_links and https://wiki.openstreetmap.org/wiki/Key:wikidata#Secondary_Wikidata_links

In some cases these links are utterly invalid/mismatching/hopelessly generic and should be rather removed.

please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"""
            # TODO synchronize with my own website, I guess
            challenge_instructions = instructions_for_mislinked_object_type(what, from_tags)
            changeset_action = "fixing primary link leading to " + what + " entry"
            return {"challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}

    if error_id == "wikipedia/wikidata type tag that is incorrect according to not:* tag":
        return model_for_violated_not_prefix_restrictions()
    if error_id == 'malformed wikipedia tag - for operator prefixed tags':
        return model_for_malformed_wikipedia_tags("operator:wikipedia", "en:Kraków", "en", "London")
    if error_id == "malformed wikipedia tag":
        return model_for_malformed_wikipedia_tags("wikipedia", "en:Kraków", "en", "London")
    if error_id == 'information board with wikipedia tag, not subject:wikipedia':
        raise ""
    if error_id == "information board with wikidata tag, not subject:wikidata":
        key = "wikidata"
        alt_key = "wikipedia"
        challenge_name = "Information board with " + key + " tag rather subject:" + key
        challenge_description = "for linking subject of information board please use `subject:" + key + "` not `" + key + """` (and `subject:""" + alt_key + "`, not `" + alt_key + """`)

`""" + key + "` / `" + alt_key + """` would be valid if entry would be specifically about information board (please check is it happening and write to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if any such case exists!)
        
please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"""
        # TODO synchronize with my own website, I guess
        challenge_instructions = challenge_description
        changeset_action = "use subject:" + key + ", not " + key + " for linking topic of information board"
        return {"challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}
    if error_id == "wikipedia tag links to 404":
        challenge_name = "404 - fix Wikipedia links leading to an article which does not exist"
        challenge_description = """Wikipedia article linked from OSM object using wikipedia tag is missing and should be fixed
        
please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"""
        # TODO synchronize with my own website, I guess
        challenge_instructions = instructions_for_404_wikipedia_challenge()
        changeset_action = "fixing links to nonexisting wikipedia articles"
        return {"challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}
   
    prefix = "wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for "
    suffix = " prefixed tags"
    if error_id.startswith(prefix):
        if error_id.endswith(suffix):
            what = error_id.replace(prefix, "")
            what = what.replace(suffix, "")
            what += ":"
            return model_for_wikipedia_wikidata_mismatch_with_link_to_disambig_page(what)
    if error_id == "wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not":
        return model_for_wikipedia_wikidata_mismatch_with_link_to_disambig_page("")
    prefix = "wikipedia wikidata mismatch - for "
    suffix = " prefixed tags"
    if error_id.startswith(prefix):
        if error_id.endswith(suffix):
            what = error_id.replace(prefix, "")
            what = what.replace(suffix, "")
            what += ":"
            return model_for_wikipedia_wikidata_mismatch(what)
    if error_id == "wikipedia wikidata mismatch":
        return model_for_wikipedia_wikidata_mismatch("")
    else:
        print(error_id)
        raise Unsupported # TODO find proper exception

def model_for_wikipedia_wikidata_mismatch(prefix_if_any):
    challenge_name = "mismatch between " + prefix_if_any + "wikipedia and " + prefix_if_any + "wikidata"
    intro = "`" + prefix_if_any + "wikipedia` and `" + prefix_if_any + "wikidata` should link to matching entries. Here it is not happening and should be fixed."
    challenge_description = intro + """

please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"""
    # TODO synchronize with my own website, I guess
    challenge_instructions = intro + """

review whether links actually mismatch and which one, if any is correct - then amend/remove the second one.


please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"""
    changeset_action = "fixing wikipedia-wikidata mismatch"
    return {"challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}

def model_for_wikipedia_wikidata_mismatch_with_link_to_disambig_page(prefix_if_any):
    challenge_name = "mismatch: " + prefix_if_any + "wikipedia links disambiguation page, " + prefix_if_any + "wikidata does not"
    tag_examples = """`wikipedia` or `""" + prefix_if_any + """wikipedia`"""
    if prefix_if_any == "":
        tag_examples = """`wikipedia`"""
    intro = tag_examples + " and so on should never link disambiguation pages (not an actual article but a list of articles sharing name). Here such link happens, with `" + prefix_if_any + "wikidata` not linking disambiguation page and being more likely to be valid"
    challenge_description = intro + """

please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"""
    # TODO synchronize with my own website, I guess
    challenge_instructions = intro + """

review whether links actually mismatch and is `""" + prefix_if_any + """wikidata` correct one

in vast majority cases `""" + prefix_if_any + """wikipedia` should be updated to match `""" + prefix_if_any + """wikidata` - though `""" + prefix_if_any + """wikidata` may be also invalid

(some people prefer to use only `""" + prefix_if_any + """wikidata`)

please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"""
    changeset_action = "fixing links to disambiguation page"
    return {"challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}

def model_for_violated_not_prefix_restrictions():
    challenge_name = "Fix conflict involving not: prefixed tags"
    challenge_description = """objects listed here have both not: prefixed tag describing that some other wikipedia-related tag is not applying and exactly this tag - this is self-contradictory and invalid"""
    # TODO synchronize with my own website, I guess
    challenge_instructions = """this object has both not: prefixed tag describing that some other wikipedia-related tag is not applying and exactly this tag

one of them is invalid

for example `species:wikipedia=en:Oak` and `not:species:wikipedia=en:Oak` should never be on the same object as they contradict each other

in this cases it is necessary to investigate which tag is wrong - and remove one of them (or do more edits if necessary)

REMEMBER: This is on Maproluette rather than being done by bot because some of this reports are wrong. Please review each entry rather than blindly retagging! If you start blindly editing, take a break.

please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if something reported here is well formed link"""
    changeset_action = "fix conflict involving not: prefixed tags"
    return {"challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}

def model_for_malformed_wikipedia_tags(key, example_link, another_example_language, another_example_article):
    challenge_name = "Fix malformed " + key + " tags"
    challenge_description = key + """ tag is invalid and in form not matching expected one - should be rescued and fixed or deleted
    
please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"""
    # TODO synchronize with my own website, I guess
    challenge_instructions = """expected format of `""" + key + """` tag is `""" + key + "=" + example_link + """`

Value must always contain:

- language code
- : separating it from
- article title

Sometimes it is malformed in various ways, for example:

`""" + key + "=" + another_example_article + """`
should be
`""" + key + "=" + another_example_language + ":" + another_example_article + """`

Very often it is fixable, though sometimes needs to be simply removed as invalid or not recoverable

REMEMBER: This is on Maproluette rather than being done by bot because some of this reports are wrong. Please review each entry rather than blindly retagging! If you start blindly editing, take a break.

please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if something reported here is well formed link"""
    changeset_action = "fixing malformed links to wikipedia articles"
    return {"challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}

def instructions_for_mislinked_object_type(what, from_tags):
    markdowned_new_subject_tag_form = None
    markdowned_new_brand_tag_form = None
    markdowned_new_etymology_tag_form = None
    markdowned_from_tags = None
    primary_special_mardowned_tag_form_if_any = ""
    what_is_linked = None
    if from_tags == "wikipedia and wikidata":
        markdowned_new_subject_tag_form = "`subject:wikipedia` and `subject:wikidata`"
        markdowned_new_brand_tag_form = "`brand:wikipedia` and `brand:wikidata`"
        markdowned_new_etymology_tag_form = "`name:etymology:wikipedia` and `name:etymology:brand:wikidata`"
        markdowned_from_tags = "`wikipedia` and `wikidata` tags"
    else:
        markdowned_new_subject_tag_form = "`subject:" + from_tags + "`"
        markdowned_new_brand_tag_form = "`brand:" + from_tags + "`"
        markdowned_new_etymology_tag_form = "`name:etymology:" + from_tags + "`"
        markdowned_from_tags = "`" + from_tags + "` tag"
    if what in ["a vehicle model or class", "a weapon model or class"]:
        if from_tags == "wikipedia and wikidata":
            primary_special_mardowned_tag_form_if_any = "`model:wikipedia` and `model:wikidata` or "
        else:
            primary_special_mardowned_tag_form_if_any = "`model:" + from_tags + "` or "
    if what == "an animal or plant (and not an individual one)":
        if from_tags == "wikipedia and wikidata":
            primary_special_mardowned_tag_form_if_any = "`taxon:wikipedia` and `taxon:wikidata` or `species:wikipedia` and `species:wikidata` or `genus:wikipedia` and `genus:wikidata` or "
        else:
            primary_special_mardowned_tag_form_if_any = "`taxon:" + from_tags + "` or `species:" + from_tags + "` or `genus:" + from_tags + "` or "
    if from_tags == "wikidata":
        what_is_linked = "Wikidata entry"
    else:
        what_is_linked = "Wikipedia article"
    return what_is_linked + """ linked from OSM object using """ + markdowned_from_tags + """ is not about something expected to be directly linkable
        
as thing such as """ + what + """ is not being mapped in Wikipedia it is extremely unlikely that this """ + markdowned_from_tags + """ is valid

it likely should be changed into """ + primary_special_mardowned_tag_form_if_any + markdowned_new_subject_tag_form + " or " + markdowned_new_etymology_tag_form + """ or other secondary tag form or removed

for example `historic=memorial` commemorating """ + what + """ should link article about it using `subject:wikipedia` / `subject:wikidata` - as article is about subject of memorial, not about memorial itself

(if article would be about memorial then linking it in main wikipedia/wikidata tag is fine)

for example `shop=supermarket` should no link company article with """ + markdowned_from_tags + """ but rather with """ + markdowned_new_brand_tag_form + """.

And road named after something should not link """ + what + """ from """ + markdowned_from_tags + " but using " + markdowned_new_etymology_tag_form + """

See https://wiki.openstreetmap.org/wiki/Key:wikipedia#Secondary_Wikipedia_links and https://wiki.openstreetmap.org/wiki/Key:wikidata#Secondary_Wikidata_links for overview of possibilities - there are ones for linking taxons, species, operators... 

in some cases """ + markdowned_from_tags + """ should be simply removed if they are simply wrong or not specifically about linked object

in case that linked wikipedia/wikidata entry is not about """ + what + """ please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny so I can handle this false positive

REMEMBER: This is on Maproluette rather than being done by bot because some of this reports are wrong. Please review each entry rather than blindly retagging! If you start blindly editing, take a break."""

def instructions_for_404_wikipedia_challenge():
    return """Wikipedia article linked from OSM object using wikipedia tag is missing.

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

def create_link_challenge_based_on_error_id(challenge_api, project_id, error_id, featured):
    texts = get_challenge_text_based_on_error_id(error_id)
    create_challenge(challenge_api, project_id, texts['challenge_name'], texts['challenge_description'], texts['challenge_instructions'], texts['changeset_action'], featured)


def create_challenge_model(challenge_api, project_id, challenge_name, challenge_description, challenge_instructions, changeset_action, featured):
    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/models/challenge.py#L7
    challenge_data = maproulette.ChallengeModel(name=challenge_name)
    challenge_data.description = challenge_description
    challenge_data.instruction = challenge_instructions
    challenge_data.enabled = True
    challenge_data.blurb = "blurb (appears to be unused) let me know if it appears anywhere" 
    challenge_data.featured = featured
    challenge_data.check_in_comment = changeset_action + ", detected by https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports/"
    challenge_data.check_in_source = None
    challenge_data.requires_local = False
    challenge_data.osm_id_property = "@id"
    # default_zoom max_zoom min_zoom
    # popularity
    # exportable_properties

    # Adding required instruction
    challenge_data.parent = project_id
    return challenge_data

def create_challenge(challenge_api, project_id, challenge_name, challenge_description, challenge_instructions, changeset_action, featured):
    challenge_data = create_challenge_model(challenge_api, project_id, challenge_name, challenge_description, challenge_instructions, changeset_action, featured)
    print("challenge creation response", json.dumps(challenge_api.create_challenge(challenge_data), indent=4, sort_keys=True))

def update_challenge(challenge_api, project_id, challenge_id, challenge_name, challenge_description, challenge_instructions, changeset_action, featured):
    challenge_data = create_challenge_model(challenge_api, project_id, challenge_name, challenge_description, challenge_instructions, changeset_action, featured)
    print("challenge update response", json.dumps(update_challenge.update_challenge(challenge_id, challenge_data), indent=4, sort_keys=True))

def set_featured_status_for_challenge_for_given_error_id(challenge_api, project_id, error_id, featured_status):
    # seems to be not working at all anyway...
    challenge_id = get_challenge_id_based_on_error_id(challenge_api, project_id, error_id)
    if challenge_id == None:
        raise Exception("no such challenge: " + str(error_id))

    texts = get_challenge_text_based_on_error_id(error_id)

    challenge_data = create_challenge_model(challenge_api, project_id, texts['challenge_name'], texts['challenge_description'], texts['challenge_instructions'], texts['changeset_action'], featured_status)
    print("requested features status for", error_id, "is", challenge_data.featured)
    try:
        # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L340C9-L340C51
        print(json.dumps(challenge_api.update_challenge(challenge_id, challenge_data), indent=4, sort_keys=True))
    except maproulette.api.errors.InvalidJsonError as e:
        print("challenge_id", challenge_id)
        print(challenge_data)
        print(json.dumps(maproulette.ChallengeModel.to_dict(challenge_data), indent=4, sort_keys=True))
        print(e)
        raise e
    return

def setup_project(project_api, user_id):
    my_project_name = "fix broken Wikipedia tags"
    projects = get_matching_maproulette_projects(project_api, my_project_name, user_id)
    if len(projects) == 0:
        my_project = maproulette.ProjectModel(name=my_project_name)
        # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/models/project.py#L7
        my_project.description = 'Lists various problems with `wikipedia`, `wikidata` and related tags such as `subject:wikidata` or `taxon:wikipedia` or  `name:etymology:wikidata` and other secondary wikipedia/wikidata links. \n\nMapRoulette export/mirror of https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports/ reports'
        my_project.enabled = True
        my_project.featured = True # it actually works!
        my_project.display_name = my_project_name
        print("creating project")
        print(json.dumps(project_api.create_project(my_project), indent=4, sort_keys=True))
        projects = get_matching_maproulette_projects(project_api, my_project_name, user_id)
    else:
        pass
        #print("project exists")
    if projects[0]["deleted"]:
        raise "project is deleted!" # TODO what about archived

    project_id = projects[0]["id"]
    return project_id

def get_data_of_a_specific_error_id(report_id):
    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()
    collected_data_for_use = []
    for name in generate_webpage_with_error_output.for_review():
        if name != report_id:
            continue
        reports = get_reports_with_specific_error_id(cursor, name)
        print("calling get_reports_with_specific_error_id:", name, len(reports), "entries")
        for entry in reports:
            if "relation" in entry['osm_object_url']:
                print("skipping relation")
                continue

            #print(json.dumps(entry, indent=4, sort_keys=True))
            #print(entry['osm_object_url'])
            #print(entry['error_id'])
            #print(entry['error_message'])
            #print(entry['location'])
            #print(entry['prerequisite'])
            live_osm_data = osm_bot_abstraction_layer.get_data_based_on_object_link(entry['osm_object_url'])
            if live_osm_data == None: # deleted
                rowid_in_osm_data = entry['rowid'] # modified, usually not present there
                # also update data table if we checked correctness...
                cursor.execute("DELETE FROM osm_data WHERE rowid = :rowid", {"rowid": rowid_in_osm_data})
                print(entry['osm_object_url'], "is deleted, marking error as gone")
                # TODO - delete row?
                continue
            #print(live_osm_data)
            #print(json.dumps(live_osm_data, indent=4, sort_keys=True))
            if osm_bot_abstraction_layer.prerequisite_failure_reason(entry['osm_object_url'], entry['prerequisite'], live_osm_data, prerequisite_failure_callback=None) != None:
                rowid_in_osm_data = entry['rowid'] # modified, usually not present there
                # also update data table if we checked correctness...
                cursor.execute("""
                UPDATE osm_data
                SET validator_complaint = :validator_complaint, error_id = :error_id
                WHERE rowid = :rowid""",
                {"validator_complaint": None, "error_id": None, "rowid": rowid_in_osm_data}
                )
                print(entry['osm_object_url'], "is no longer applicable, marking error as gone")
                continue
            # update timestamp so time will not be wasted elsewhere
            rowid_in_osm_data = entry['rowid'] # modified, usually not present there
            cursor.execute("""
            UPDATE osm_data
            SET download_timestamp = :timestamp
            WHERE rowid = :rowid""",
            {"timestamp": int(time.time()), "rowid": rowid_in_osm_data}
            )
            error_message = entry['error_message']
            if error_message == "":
                error_message = None
            if "node" in entry['osm_object_url']:
                lon = entry['location']['lon']
                lat = entry['location']['lat']
                collected_data_for_use.append({"lon": lon, "lat": lat, "geometry": "point", "osm_object_url": entry['osm_object_url'], 'error_message': error_message, 'tags': entry['tags']})
            elif "way" in entry['osm_object_url']:
                # currently skipped early, see above
                # way vs area... TODO
                collected_data_for_use.append({"way_ids": live_osm_data['nd'], "geometry": "way", "osm_object_url": entry['osm_object_url'], 'error_message': error_message, 'tags': entry['tags']})
            else:
                print("skipping", entry['osm_object_url'])
    connection.commit()
    connection.close()
    return collected_data_for_use

def build_geojson_entry(geometry, osm_object_url, error_message, tag_dictionary):
    element = {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            # https://learn.maproulette.org/documentation/rebuilding-challenge-tasks/#content
            "@id": osm_object_url.replace("https://openstreetmap.org/", ""),
        }
    }
    if error_message != None:
        element['properties']['error_message'] = error_message
    for tag_key in tag_dictionary.keys():
        element['properties'][tag_key] = tag_dictionary[tag_key]
    return element

def build_geojson_node_entry(lon, lat, osm_object_url, error_message, tag_dictionary):
    geometry = build_geojson_node_geometry(lon, lat)
    return build_geojson_entry(geometry, osm_object_url, error_message, tag_dictionary)

def build_geojson_way_entry(way_ids, osm_object_url, error_message, tag_dictionary):
    way_coords = []
    for node_id in way_ids:
        live_node_osm_data = osm_bot_abstraction_layer.get_data_based_on_object_link("https://openstreetmap.org/node/" + str(node_id))
        print(live_node_osm_data['lat'], live_node_osm_data['lon'])
        way_coords.append({'lat': live_node_osm_data['lat'], 'lon': live_node_osm_data['lon']})
    geometry = build_geojson_way_geometry(way_coords)
    return build_geojson_entry(geometry, osm_object_url, error_message, tag_dictionary)

def build_geojson_node_geometry(lon, lat):
    return {
            "type": "Point",
            "coordinates": [lon, lat], # [longitude, latitude] 
        }

def build_geojson_way_geometry(way_coords):
    returned = {
            "type": "LineString",
            "coordinates": [],
        }
    for entry in way_coords:
        returned['coordinates'].append([entry['lon'], entry['lat']])
    return returned

def get_challenge_tasks(challenge_api, challenge_id):
    returned = []
    while True:
        try:
            page = 0
            limit = 500
            while True:
                response = challenge_api.get_challenge_tasks(challenge_id, limit=limit, page=page)
                page += 1
                if response["status"] != 200:
                    raise
                data = response["data"]
                for entry in data:
                    returned.append(entry)
                print("fetching challenge tasks, processing page with", len(data), "entries")
                if len(data) < limit:
                    return returned
        except maproulette.api.errors.HttpError as e:
            print("https://maproulette.org/browse/challenges/" + str(challenge_id), "get_challenge_tasks", e)
            time.sleep(10)

def get_challenge_data_from_project(challenge_api, project_id):

    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L95
    limit_send = 1000
    response = challenge_api.get_challenge_listing(project_ids=project_id, only_enabled='false', limit=limit_send) # yes, stringified boolean
    if response["status"] != 200:
        raise
    data = response["data"]
    if len(data) == limit_send:
        raise "paginate"
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
        validator_complaint['rowid'] = rowid
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
