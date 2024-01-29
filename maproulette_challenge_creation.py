# https://maproulette.org/admin/project/53065
# 2 sierpnia: Fixed (4479/11597) - 7118 remaining
# 2 sierpnia: Fixed (4480/14141) - 9661 remaining
# 3 sierpnia: Fixed (4518/14141) - 9623 remaining
# 6 sierpnia Fixed (4643/14167) - 9524 remaining
# 9 sierpnia Fixed (4873/14173) - 9300 remaining
# 14 sierpnia Fixed (5103/14173) - 9070 remaining
# 15 sierpnia Fixed (5150/14173) - 9023 remaining
# 16 sierpnia Fixed (5227/14173) - 8946 remaining
# 17 sierpnia Fixed (5231/14180) - 8949 remaining
# 18 sierpnia Fixed (5255/14180) - 8925 remaining
# 19 sierpnia Fixed (5256/14180) - 8924 remaining
# 20 sierpnia Fixed (5265/14199) - 8934 remaining
# 26 sierpnia Fixed (5318/14190) - 8872 remaining
# 30 sierpnia Fixed (5359/14188) - 8829 remaining
# 5 września Fixed (5381/14202) - 8821 remaining
# 30 września Fixed (5430/14461) - 9031 remaining
# 4 listopada Fixed (5507/14461) - 8954 remaining
# 4 listopada Fixed (5519/14814) - 9295 remaining
# 6 listopada Fixed (5547/14833) - 9286 remaining
# 8 listopada Fixed (5565/14979) - 9414 remaining
# 14 listopada Fixed (5583/14673) - 9090 remaining
# 25 listopada Fixed (6143/14827) - 8684 remaining
# 30 listopada Fixed (6483/14566) - 8083 remaining
# 6 grudnia Fixed (6936/14111) - 7175 remaining
# 10 grudnia Fixed (7074/13386) - 6312 remaining
# 11 grudnia Fixed (7177/13373) - 6196 remaining
# 22 grudnia Fixed (7749/13370) - 5621 remaining
# 3 grudnia Fixed (8011/13353) - 5342 remaining


# https://github.com/osmlab/maproulette-python-client
import maproulette
import json
import generate_webpage_with_error_output
import sqlite3
import config
import time
import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer
import random
import requests
import database
import datetime

print("try to list all comments made by users...")
# TODO brand:wikidata / brand:wikipedia without brand tag
# https://maproulette.org/admin/project/53065/challenge/40012
# https://maproulette.org/browse/projects/53065
# See https://maproulette.org/browse/projects/53065 for related challenges about fixing `wikipedia` / `wikidata` and related tags.
# https://maproulette.org/browse/projects/53065  set of challenges about fixing `wikipedia` / `wikidata` and related tags
# https://learn.maproulette.org/documentation/rebuilding-challenge-tasks/#content

# https://maproulette.org/challenge/40023/leaderboard - let people know after rescan, thank them

# https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L198
# 0 = Created, 1 = Fixed, 2 = False Positive, 3 = Skipped, 4 = Deleted, 5 = Already Fixed, 6 = Too Hard
STATUS_CREATED = 0
STATUS_FIXED = 1
STATUS_FALSE_POSITIVE = 2
STATUS_SKIPPED = 3
STATUS_DELETED = 4
STATUS_ALREADY_FIXED = 5
STATUS_TOO_HARD = 6
STATUS_DISABLED = 9 # TODO missing in docs

def greenlit_groups_not_to_be_featured_list():
    return [
        # upload, add to featured
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a ceremony',

        # upload but not featured group
    ]
def for_later_list():
    for_later = [
        # wat? why entries are not removed?
        # process tests after Wikidata community fixes what causes noisy reports
        # https://www.wikidata.org/w/index.php?title=User:Mateusz_Konieczny/failing_testcases&action=history
        #
        # after fixing - jest delete it, already listed
        'link to a disambiguation page',

        # requires text descriptions
        'species secondary tag links something that is not species according to wikidata (checking P105)',
        'malformed secondary wikidata tag - for species prefixed tags',
        'malformed secondary wikidata tag - for name:etymology prefixed tags',
        'malformed secondary wikidata tag - for operator prefixed tags',
        'malformed secondary wikidata tag - for parish prefixed tags',
        'malformed secondary wikidata tag - for network prefixed tags',
        'malformed secondary wikipedia tag - for network prefixed tags',
    ]
    """
def model_for_XXXXXX():
    challenge_name = ""
    challenge_description = ""
    challenge_instructions = challenge_description
    changeset_action = "use subject:" + key + ", not " + key + " for linking topic of information board"
    return {"challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}
    """

    for_later += [
        'wikipedia tag links bot wikipedia',
        'genus secondary tag links something that is not genus according to wikidata (checking P105)',
        

        # requires description, may be featurable
        'invalid old-style wikipedia tag',
        'wikipedia tag in outdated form and there is mismatch between links',

        # fix http://overpass-turbo.eu/s/1x68 first
        # bot assisted edit?
        'information board with wikipedia tag, not subject:wikipedia',
        'information board with wikidata tag, not subject:wikidata',

        # may be full of Wikidata lies and merged entries
        'should use a secondary wikipedia tag - linking from wikipedia tag to a brand',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a brand',
        'should use a secondary wikipedia tag - linking from wikidata tag to a brand',

        # ideally: supply that known replacement
        'blacklisted connection with known replacement',

        # how to even tag this one?
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a type of structure',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a type of structure',
        'should use a secondary wikipedia tag - linking from wikidata tag to a type of structure',


        # may be confusing or raise protests
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a religious denomination',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a religious denomination',
        'should use a secondary wikipedia tag - linking from wikidata tag to a sports competition',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a sports competition',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a sports competition',
        'should use a secondary wikipedia tag - linking from wikidata tag to a religious denomination',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a software', # links many software companies, to the point taht arguably Wikidata is simply wrong=
        'should use a secondary wikipedia tag - linking from wikipedia tag to a software',
        'should use a secondary wikipedia tag - linking from wikidata tag to a software',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a public transport network',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a public transport network',
        'should use a secondary wikipedia tag - linking from wikidata tag to a public transport network',
        "secondary wikidata tag links to 404", # look at that later - many should be reported as malformed - many should stop being listed here
        "link to an unlinkable article", # disambigs got own category now - many should stop being listed here
        'wikipedia wikidata mismatch - for on_the_list prefixed tags',
        'mismatching teryt:simc codes in wikidata and in osm element',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a film festival',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a festival',

        'bridge:wikipedia and bridge:wikidata - move to bridge outline',
        'bridge:wikipedia - move to bridge outline',

        # what about say https://www.openstreetmap.org/node/5907460258
        'should use a secondary wikipedia tag - linking from wikipedia tag to a transport accident',
        'should use a secondary wikipedia tag - linking from wikidata tag to a transport accident',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a transport accident',

        'wikipedia wikidata mismatch - for brand prefixed tags', # being removed
    ]
    return for_later

def already_uploaded_featured_pool_list():
    returned = []
    for source in ["wikipedia and wikidata tag", "wikipedia tag", "wikidata tag"]:
        for problem in [
            "a multinational corporation",
            "a migration",
            "a letter",
            "a death",
            "a disaster",
            "a travel",
            "a protest",
            "a conflict",
            "a saying",
            "a coat of arms",
            "a profession",
            "a restaurant chain",
            "a chain store",
            "an object that exists outside physical reality",
            "a type of sport",
            "a legal action",
            "a train category",
            "a cuisine",
            "a robbery",
            "a mental process",
            "a shooting",
            "a sport",
            "a road type",
            "a military operation",
            "a crime",
            "a podcast",
            "a an explosion",
            "a given name",
            "a heraldic animal",
            "a human",
            "a an overview article",
            "a historical event",
        ]:
            returned.append('should use a secondary wikipedia tag - linking from ' + source + ' to ' + problem)
    returned += [
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a history of a geographic region',
        "wikipedia/wikidata type tag that is incorrect according to not:* tag",
        "wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not",

        # exhausted, refilling will happen but lets give it time
        # less likely to be refilled at the bottom
        'link to a disambiguation page',
        "malformed wikipedia tag",

        # only hard-to-fix values in countries outside Europe, also was linked from OSM Weekly so maybe lets not exhaust it
        # was featured for quite long time so lets show something new
        "wikipedia tag links to 404",

        "wikipedia/wikidata type tag that is incorrect according to not:* tag",

        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for subject prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for name:etymology prefixed tags',
        'wikipedia wikidata mismatch - for name:etymology prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for species prefixed tags',
        'wikipedia wikidata mismatch - for species prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for taxon prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for brand prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for operator prefixed tags',
        
        'wikipedia wikidata mismatch - for operator prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for artist prefixed tags',
        'wikipedia wikidata mismatch - wikipedia points to disambiguation page and wikidata does not - for architect prefixed tags',
        'wikipedia wikidata mismatch - for network prefixed tags',
        'wikipedia wikidata mismatch',

        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to an object that exists outside physical eality',
    ]
    return returned

def already_uploaded_not_to_be_featured_list():
    return [
        # check description, should be featureable
        'should use a secondary wikipedia tag - linking from wikipedia tag to an animal or plant (and not an individual one)',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to an animal or plant (and not an individual one)',
        'should use a secondary wikipedia tag - linking from wikidata tag to an animal or plant (and not an individual one)',

        # with better description move to featured list
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a food',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a food',
        'should use a secondary wikipedia tag - linking from wikidata tag to a food',

        'should use a secondary wikipedia tag - linking from wikidata tag to a postal service',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to an electric vehicle charging network',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a postal service',
        'should use a secondary wikipedia tag - linking from wikipedia tag to an electric utility',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a website',
        'should use a secondary wikipedia tag - linking from wikidata tag to a website',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a website',
        'should use a secondary wikipedia tag - linking from wikidata tag to a bicycle sharing system',
        'should use a secondary wikipedia tag - linking from wikidata tag to a vehicle model or class',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a vehicle model or class',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a vehicle model or class',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a weapon model or class',
        'should use a secondary wikipedia tag - linking from wikidata tag to a weapon model or class',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a weapon model or class',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a type of world view',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a conflict',
        'should use a secondary wikipedia tag - linking from wikipedia tag to an aspect in a geographic region',
        'should use a secondary wikipedia tag - linking from wikidata tag to an aspect in a geographic region',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to an aspect in a geographic region',
        'malformed secondary wikipedia tag - for architect prefixed tags',
        'malformed secondary wikipedia tag - for operator prefixed tags',
        'malformed secondary wikipedia tag - for brand prefixed tags',
        'should use a secondary wikipedia tag - linking from wikidata tag to a conflict',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a bicycle sharing system',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a bicycle sharing system',
        'should use a secondary wikipedia tag - linking from wikidata tag to an electric utility',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to an electric utility',

        # TODO, see https://www.openstreetmap.org/way/613183124 - https://www.openstreetmap.org/note/3972766
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a meeting',

        # quite fragile with repeated reveals of bad Wikidata ontology - lets not feature it
        'should use a secondary wikipedia tag - linking from wikidata tag to a fictional entity',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a fictional entity',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a fictional entity',

        # also multiple reveal of bogus Wikidata ontology
        'should use a secondary wikipedia tag - linking from wikidata tag to a social issue',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a social issue',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a social issue',


        # some argue that linking from offices/factories is fine
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a multinational corporation',

        # some filming locations are bordeline
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a film',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a film',
        'should use a secondary wikipedia tag - linking from wikidata tag to a film',    
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a television series',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a television series',
        'should use a secondary wikipedia tag - linking from wikidata tag to a television series',

        #tricky
        'should use a secondary wikipedia tag - linking from wikidata tag to a violation of law',
        'should use a secondary wikipedia tag - linking from wikipedia tag to a violation of law',
        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a violation of law',

        'should use a secondary wikipedia tag - linking from wikipedia and wikidata tag to a recurring sports event',
    ]

def get_login_data():
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
        return api_key, user_id


def show_state_on_maproulette(challenge_api, task_api, project_id):
    if datetime.datetime.now().hour < 19:
        print("before 19:00, wikidata.org should not be accessible for now")
        return
    total_error_count = 0
    total_fixed_count = 0
    for error_id in already_uploaded_not_to_be_featured_list() + already_uploaded_featured_pool_list():
        challenge_id = get_challenge_id_based_on_error_id(challenge_api, project_id, error_id)
        if challenge_id != None:
            dict_of_tasks, _, fixed_count, live_count = get_dict_of_tasks_in_challenge_and_info_is_any_in_weird_state_and_show_these(error_id, task_api, challenge_api, challenge_id, None, debug = False)
            total_error_count += live_count
            total_fixed_count += fixed_count
    print()
    print()
    print()
    print("Fixed (" + str(total_fixed_count) + "/" + str(total_error_count) + ") - " + str(total_error_count - total_fixed_count) + " remaining")
    print()
    print()
    print()

def show_new_not_yet_supported_error_classes(cursor):
    categories = {}
    greenlit_groups_not_to_be_featured = greenlit_groups_not_to_be_featured_list()
    for_later = for_later_list()
    already_uploaded_featured_pool = already_uploaded_featured_pool_list()

    show_candidate_reports(cursor, greenlit_groups_not_to_be_featured + for_later, already_uploaded_not_to_be_featured_list() + already_uploaded_featured_pool_list())

def main():
    api_key, user_id = get_login_data()
    print("find random edits, get their authors and thank them/verify - see https://www.openstreetmap.org/changeset/138121870")

    maproulette_config = maproulette.Configuration(api_key=api_key)
    project_api = maproulette.Project(maproulette_config)
    task_api = maproulette.Task(maproulette_config)
    challenge_api = maproulette.Challenge(maproulette_config)
    project_id = setup_project(project_api, user_id)
    # docs: https://github.com/osmlab/maproulette-python-client#getting-started

    # manually trigger an update
    #update_or_create_challenge_based_on_error_id(challenge_api, task_api, project_id, 'wikipedia wikidata mismatch - for operator prefixed tags', featured = False)

    show_state_on_maproulette(challenge_api, task_api, project_id)

    connection = sqlite3.connect(config.database_filepath())
    cursor = connection.cursor()

    show_new_not_yet_supported_error_classes(cursor)


    print("ensure_correct_number_of_featured_groups")
    ensure_correct_number_of_featured_groups(challenge_api, project_id)
    return

    for error_id in greenlit_groups_not_to_be_featured_list():
        update_or_create_challenge_based_on_error_id(challenge_api, task_api, project_id, error_id, featured = False)

    pool = already_uploaded_featured_pool_list() + already_uploaded_not_to_be_featured_list()
    random.shuffle(pool)
    for error_id in pool:
        update_or_create_challenge_based_on_error_id(challenge_api, task_api, project_id, error_id, featured = False)

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

    # TODO hmm, mention my site in MR so it is linked from it

    # https://github.com/osmlab/maproulette-python-client/blob/dev/examples/challenge_examples.py
    # https://github.com/osmlab/maproulette-python-client/blob/38920add1b95b9ec472e1653915faf9eebe2a6b9/maproulette/api/challenge.py#L269 - add_tasks_to_challenge
    # https://github.com/osmlab/maproulette-python-client/blob/0a3e4b68af7892700463c2afc66a1ae4dcbf0825/maproulette/models/challenge.py

def ensure_correct_number_of_featured_groups(challenge_api, project_id):
    already_uploaded_featured_pool = already_uploaded_featured_pool_list()
    featured_count_request = 2
    looked_at_potentially_featured_tasks = 0
    marked_featured = 0
    total_featured_tasks = 0

    for error_id in already_uploaded_featured_pool_list() + already_uploaded_not_to_be_featured_list():
        challenge_id = get_challenge_id_based_on_error_id(challenge_api, project_id, error_id)
        if challenge_id != None:
            set_featured_status_for_challenge_for_given_error_id(challenge_api, project_id, error_id, False)

    while marked_featured < featured_count_request:
        error_id = already_uploaded_featured_pool[looked_at_potentially_featured_tasks]
        looked_at_potentially_featured_tasks += 1
        challenge_id = get_challenge_id_based_on_error_id(challenge_api, project_id, error_id)
        if challenge_id == None:
            print("no challenge for", error_id)
            print()
        else:
            tasks = get_challenge_tasks(challenge_api, challenge_id)
            active_tasks = 0
            for task in tasks:
                if is_active_task_status(task['status']):
                    active_tasks += 1
            print(active_tasks, "active tasks in", '"' + error_id + '"')
            print()
            if total_featured_tasks + active_tasks < 50 and marked_featured + 1 == featured_count_request:
                print("trying to get entry with more active tasks, at least for last one")
                continue
            if active_tasks > 0:
                set_featured_status_for_challenge_for_given_error_id(challenge_api, project_id, error_id, True)
                marked_featured += 1
                total_featured_tasks += active_tasks
            else:
                set_featured_status_for_challenge_for_given_error_id(challenge_api, project_id, error_id, False)
        if len(already_uploaded_featured_pool) == looked_at_potentially_featured_tasks:
            raise Exception("run out of task to feature")
            break
    
    if marked_featured < featured_count_request:
        raise Exception("run out of task to feature")
    
    print("featured", marked_featured, "with", total_featured_tasks, "available tasks")

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
            #STATUS_CREATED = 0
            #STATUS_DELETED = 4
            if is_active_task_status(status):
                link = "https://maproulette.org/task/" + str(task['id'])
                print(link, "deleting item", count)
                count += 1
                task_api.update_task_status(task['id'], STATUS_DELETED, "", "", False)
        set_featured_status_for_challenge_for_given_error_id(challenge_api, project_id, error_id, False)
        update_or_create_challenge_based_on_error_id(challenge_api, task_api, project_id, error_id, featured = False)

def is_active_task_status(status):
    if status == STATUS_SKIPPED:
        return True
    if status == STATUS_CREATED:
        return True
    return False

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
    if challenge_id == None:
        #print("no match found for", error_id, "with expected name", challenge_name, "in project", project_id)
        if 'old_challenge_name' in texts:
            challenge_name = texts['old_challenge_name']
            challenge_id = None
            for challenge in data:
                if challenge["name"] == challenge_name:
                    challenge_id = challenge['id']
            if challenge_id != None:
                return challenge_id
            #else:
            #    print("no match found for", error_id, "also with an old name", challenge_name, "in project", project_id)
    return challenge_id

def get_osm_link_from_task(task):
    link = "https://maproulette.org/task/" + str(task['id'])
    if len(task['geometries']['features']) != 1:
        print(json.dumps(task, indent=4, sort_keys=True))
        print(len(task['geometries']['features']))
        raise
    if '@id' in task['geometries']['features'][0]['properties']:
        return "https://openstreetmap.org/" + task['geometries']['features'][0]['properties']['@id']
    elif 'osm_link' in task['geometries']['features'][0]['properties']:
        # some old data, should be only for solved/disabled ones
        return task['geometries']['features'][0]['properties']['osm_link']
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

    # Printing response:
    # https://maproulette.org/admin/projects

    print("getting reports from my database")

    # work around https://github.com/maproulette/maproulette3/issues/1563
    # overpass query cannot be changed
    # so we need to provide data manually

    # prerequisites checked with live data
    # still, some may be marked on MR as too hard or invalid

    candidates = []
    for entry in collected_data_for_use:
        candidates.append(entry['osm_object_url'])

    some_require_manual_investigation = False
    in_mr_already, some_require_manual_investigation, _fixed_count, _live_count = get_dict_of_tasks_in_challenge_and_info_is_any_in_weird_state_and_show_these(error_id, task_api, challenge_api, challenge_id, candidates, debug=False)

    array_of_urls_in_mr_already = in_mr_already.keys()
    geojson_object = build_geojson_of_tasks_to_add_challenge(collected_data_for_use, array_of_urls_in_mr_already)
    try:
        print(json.dumps(challenge_api.add_tasks_to_challenge(geojson_object, challenge_id), indent=4, sort_keys=True))
    except requests.exceptions.ConnectionError as e:
        print(e)
        print("will retry")
        time.sleep(10)
        print(json.dumps(challenge_api.add_tasks_to_challenge(geojson_object, challenge_id), indent=4, sort_keys=True))
    print(challenge_name, "processed", len(geojson_object["features"]), "features added")
    if some_require_manual_investigation:
        print("https://maproulette.org/admin/project/53065/challenge/" + str(challenge_id) + "?filters.metaReviewStatus=0%2C1%2C2%2C3%2C5%2C6%2C7%2C-2&filters.priorities=0%2C1%2C2&filters.reviewStatus=0%2C1%2C2%2C3%2C4%2C5%2C6%2C7%2C-1&filters.status=2%2C5%2C6&includeTags=false&page=0&pageSize=40&sortCriteria.direction=DESC&sortCriteria.sortBy=name")
        raise Exception("look at these entries")

def get_dict_of_tasks_in_challenge_and_info_is_any_in_weird_state_and_show_these(error_id, task_api, challenge_api, challenge_id, candidates, debug):
    in_mr_already = {}
    tasks_in_challenge = get_challenge_tasks(challenge_api, challenge_id, debug)
    fixed_count = 0
    visible_tasks = 0
    some_require_manual_investigation = False
    for task in tasks_in_challenge:
        #print(json.dumps(task, indent=4, sort_keys=True))
        status = task['status']
        if status == STATUS_DELETED:
            continue
        link = "https://maproulette.org/task/" + str(task['id'])
        osm_link = get_osm_link_from_task(task)
        if osm_link == None:
            print(link)
            raise "wat"
        if candidates != None and osm_link not in candidates: # TODO fix this double use horribleness, two functions are better
            if is_live_task_shown_to_people(status):
                delete_task_if_not_locked(task_api, task['id'], osm_link)
        else:
            in_mr_already[osm_link] = task
            modified_time = task['modified']
            if status == STATUS_FIXED:
                fixed_count += 1
                visible_tasks += 1
            elif status == STATUS_DISABLED:
                pass
            elif status == STATUS_CREATED or status == STATUS_SKIPPED or status == STATUS_ALREADY_FIXED:
                visible_tasks += 1
            elif status == STATUS_FALSE_POSITIVE:
                visible_tasks += 1
                print("False positive", link, osm_link, error_id)
                some_require_manual_investigation = True
            elif status == STATUS_TOO_HARD:
                visible_tasks += 1
                print("Too hard", link, osm_link, error_id)
                some_require_manual_investigation = True
            else:
                print("unexpected status", status, "for", link, osm_link, error_id)
                raise "unexpected"
                some_require_manual_investigation = True
    return in_mr_already, some_require_manual_investigation, fixed_count, visible_tasks


def build_geojson_of_tasks_to_add_challenge(collected_data_for_use, array_of_urls_in_mr_already):
    geojson_object = {
        "type": "FeatureCollection",
        "features": []
    }
    for entry in collected_data_for_use:
        if entry['osm_object_url'] in array_of_urls_in_mr_already:
            # link was listed already and is in some state, not need to send it again
            # though what about cases where user falsely claimed that something is fixed? TODO
            # leave it for the future, I guess
            pass
        else:
            if entry['geometry'] == 'point':
                element = build_geojson_node_entry(entry['lon'], entry['lat'], entry['osm_object_url'], entry['error_message'], entry['tags'])
                geojson_object["features"].append(element)
            elif entry['geometry'] == 'way':
                element = build_geojson_way_entry(entry['nodes_ids_from_way'], entry['osm_object_url'], entry['error_message'], entry['tags'])
                geojson_object["features"].append(element)
            else:
                raise
    return geojson_object

def is_live_task_shown_to_people(status):
    if status == STATUS_CREATED:
        return True
    elif status == STATUS_FIXED:
        return False
    elif status == STATUS_FALSE_POSITIVE:
        return True
    elif status == STATUS_SKIPPED:
        return True
    elif status == STATUS_DELETED:
        return False
    elif status == STATUS_DISABLED:
        return False
    elif status == STATUS_ALREADY_FIXED:
        return False
    elif status == STATUS_TOO_HARD:
        return True
    print("unexpected status", status)

def get_challenge_text_based_on_error_id(error_id):
    for from_tags in [
        "wikipedia and wikidata",
        "wikipedia",
        "wikidata",
    ]:
        if "should use a secondary wikipedia tag - linking from " + from_tags + " tag to " in error_id:
            what = error_id.replace("should use a secondary wikipedia tag - linking from " + from_tags + " tag to ", "")
            return switch_to_secondary_tag_model(from_tags, what)

    if error_id == 'link to a disambiguation page':
        return model_for_linking_disambiguation_page()
    if error_id == "wikipedia/wikidata type tag that is incorrect according to not:* tag":
        return model_for_violated_not_prefix_restrictions()
    if error_id == 'malformed secondary wikipedia tag - for brand prefixed tags':
        return model_for_malformed_wikipedia_tags("brand:wikipedia", "en:House (brand)", "en", "House (brand)")
    if error_id == 'malformed secondary wikipedia tag - for operator prefixed tags':
        return model_for_malformed_wikipedia_tags("operator:wikipedia", "en:Kraków", "en", "London")
    if error_id == 'malformed secondary wikipedia tag - for architect prefixed tags':
        return model_for_malformed_wikipedia_tags("architect:wikipedia", "en:Jan Sas Zubrzycki", "en", "Filippo Brunelleschi")
    if error_id == "malformed wikipedia tag":
        return model_for_malformed_wikipedia_tags("wikipedia", "en:Kraków", "en", "London")
    if "malformed secondary wikipedia tag - for" in error_id:
        raise Exception("note that some custom data is expected for malformed secondary tags, see model_for_malformed_wikipedia_tags")
    if error_id == 'information board with wikipedia tag, not subject:wikipedia':
        key = "wikipedia"
        alt_key = "wikidata"
        return model_for_information_board_with_primary_tag(key, alt_key)
    if error_id == "information board with wikidata tag, not subject:wikidata":
        key = "wikidata"
        alt_key = "wikipedia"
        return model_for_information_board_with_primary_tag(key, alt_key)
    if error_id == "wikipedia tag links to 404":
        return model_for_dead_wikipedia_links()
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
    if error_id == "wikipedia wikidata mismatch - for brand prefixed tags":
        return model_for_wikipedia_wikidata_mismatch("brand:")
    if error_id == "wikipedia wikidata mismatch - for operator prefixed tags":
        return model_for_wikipedia_wikidata_mismatch("operator:")
    if error_id == "wikipedia wikidata mismatch - for name:etymology prefixed tags":
        return model_for_wikipedia_wikidata_mismatch("name:etymology:")
    if error_id == "wikipedia wikidata mismatch - for network prefixed tags":
        return model_for_wikipedia_wikidata_mismatch("network:")
    else:
        print(error_id)
        raise Exception(error_id + " is not supported, no matching text model") # TODO find proper exception

def model_for_linking_disambiguation_page():
    challenge_name = "Linking disambiguation page"
    challenge_description = "Disambiguation pages are not an actual articles but a list of articles sharing name. These should never be linked in `wikipedia`/`wikidata` or secondary tag variants. Here main link goes to such disambiguation page and should be fixed.\n\nplease send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"
    challenge_instructions = challenge_description
    changeset_action = "fixing link to a disambiguation page"
    return {"challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}

def switch_to_secondary_tag_model(from_tags, what):
    challenge_name = from_tags + " tag linking to " + what + " - should use secondary " + from_tags + " tag - or be removed"
    old_challenge_name = from_tags + " tag linking to " + what + " - should use secondary " + from_tags + " tag"
    challenge_description = """Things like """ + what + """ are never directly linkable from `wikidata`/`wikipedia` tags - they can be linked in some cases from properly prefixed secondary tags - and in some should be removed.
    
For example `subject:wikipedia` to link subject of a sculpture - `wikipedia` tag is for linking article about sculpture itself, not about what it is depicting).
And `name:etymology:wikidata` links Wikidata entry that describes source of name of a given object.
    
See https://wiki.openstreetmap.org/wiki/Key:wikipedia#Secondary_Wikipedia_links and https://wiki.openstreetmap.org/wiki/Key:wikidata#Secondary_Wikidata_links

In some cases these links are utterly invalid/mismatching/hopelessly generic and should be rather removed.

please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"""
    # TODO synchronize with my own website, I guess
    challenge_instructions = instructions_for_mislinked_object_type(what, from_tags)
    changeset_action = "fixing primary link leading to " + what + " entry"
    return {"old_challenge_name": old_challenge_name, "challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}

def model_for_information_board_with_primary_tag(key, alt_key):
    challenge_name = "Information board with " + key + " tag rather subject:" + key
    challenge_description = "for linking subject of information board please use `subject:" + key + "` not `" + key + """` (and `subject:""" + alt_key + "`, not `" + alt_key + """`)

`""" + key + "` / `" + alt_key + """` would be valid if entry would be specifically about information board (please check is it happening and write to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if any such case exists!)
    
please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"""
    # TODO synchronize with my own website, I guess
    challenge_instructions = challenge_description
    changeset_action = "use subject:" + key + ", not " + key + " for linking topic of information board"
    return {"challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}

def model_for_wikipedia_wikidata_mismatch(prefix_if_any):
    challenge_name = "mismatch between " + prefix_if_any + "wikipedia and " + prefix_if_any + "wikidata"
    intro = "`" + prefix_if_any + "wikipedia` and `" + prefix_if_any + "wikidata` are mismatching and linking different entries."
    challenge_description = intro + """

please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits"""
    # TODO synchronize with my own website, I guess
    challenge_instructions = """review whether links actually mismatch and which one, if any is correct - then amend/remove the wrong one.

note that in some cases entire element may need to be deleted or both links should be replaced/removed

in some rare cases they may be actually OK - in such case send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny or comment in MapRoulette with an explanation why it is valid
""" + intro
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

in vast majority cases `""" + prefix_if_any + """wikipedia` should be updated to match `""" + prefix_if_any + """wikidata` - though `""" + prefix_if_any + """wikidata` may be also invalid, maybe `wikipedia` tag is now correct and automatic detection was confused, maybe both are wrong... As usual: this is on Maproulette as it required human review.

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
    if what in ["a restaurant chain"]:
        if from_tags == "wikipedia and wikidata":
            primary_special_mardowned_tag_form_if_any = "`brand:wikipedia` and `brand:wikidata` or "
        else:
            primary_special_mardowned_tag_form_if_any = "`brand:" + from_tags + "` or "
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

It likely should be changed into """ + primary_special_mardowned_tag_form_if_any + markdowned_new_subject_tag_form + " or " + markdowned_new_etymology_tag_form + """ or other secondary tag form or removed. In some cases entire objects should be deleted, for example in cases of duplicates, mapping events such as crimes that left no traces whatsoever at a given place and mapping no longer existing objects that were destroyed without trace.

for example `historic=memorial` commemorating """ + what + """ should link article about it using `subject:wikipedia` / `subject:wikidata` - as article is about subject of memorial, not about memorial itself

(if article would be about memorial then linking it in main wikipedia/wikidata tag is fine)

for example `shop=supermarket` should no link company article with """ + markdowned_from_tags + """ but rather with """ + markdowned_new_brand_tag_form + """.

And road named after something should not link """ + what + """ from """ + markdowned_from_tags + " but using " + markdowned_new_etymology_tag_form + """

See https://wiki.openstreetmap.org/wiki/Key:wikipedia#Secondary_Wikipedia_links and https://wiki.openstreetmap.org/wiki/Key:wikidata#Secondary_Wikidata_links for overview of possibilities - there are ones for linking taxons, species, operators... 

in some cases """ + markdowned_from_tags + """ should be simply removed if they are simply wrong or not specifically about linked object

in case that linked wikipedia/wikidata entry is not about """ + what + """ please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny so I can handle this false positive

REMEMBER: This is on Maproluette rather than being done by bot because some of this reports are wrong. Please review each entry rather than blindly retagging! If you start blindly editing, take a break."""

def model_for_dead_wikipedia_links():
    challenge_name = "404 - fix Wikipedia links leading to an article which does not exist"
    challenge_description = """Wikipedia article linked from OSM object using wikipedia tag is missing and should be fixed
    
please send a message to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny if anything is wrong with this listing or it causes people to make bad edits

see also https://maproulette.org/browse/projects/53065 for other challenges"""
    # TODO synchronize with my own website, I guess
    challenge_instructions = instructions_for_404_wikipedia_challenge()
    changeset_action = "fixing links to nonexisting wikipedia articles"
    return {"challenge_name": challenge_name, "challenge_description": challenge_description, "challenge_instructions": challenge_instructions, "changeset_action": changeset_action}

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

def setup_project(project_api, user_id):
    my_project_name = "fix broken Wikipedia tags"
    projects = get_matching_maproulette_projects(project_api, my_project_name, user_id)
    if len(projects) == 0:
        my_project = maproulette.ProjectModel(name=my_project_name)
        # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/models/project.py#L7
        my_project.description = 'Lists various problems with `wikipedia`, `wikidata` and related tags such as `subject:wikidata` or `taxon:wikipedia` or  `name:etymology:wikidata` and other secondary wikipedia/wikidata links. \n\nMapRoulette export/mirror of https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports/ reports\n\nWrite to https://www.openstreetmap.org/message/new/Mateusz%20Konieczny to request enabling reports for additional areas (currently only small part of world is covered) or to request update if it is not happening for some time.'
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
    reports = get_reports_with_specific_error_id(cursor, report_id)
    print("calling get_reports_with_specific_error_id:", report_id, len(reports), "entries")
    for entry in reports:

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
        if "relation" in entry['osm_object_url']:
            if len(live_osm_data['member']) > 100:
                print("skipping relation with many elements:", len(live_osm_data['member']))
        if osm_bot_abstraction_layer.prerequisite_failure_reason(entry['osm_object_url'], entry['prerequisite'], live_osm_data, prerequisite_failure_callback=None) != None:
            rowid_in_osm_data = entry['rowid'] # modified, usually not present there
            # also update data table if we checked correctness...
            database.clear_error_and_request_update(cursor, rowid_in_osm_data)
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
            print(live_osm_data)
            #print(json.dumps(live_osm_data, indent=4, sort_keys=True)) # TypeError: Object of type datetime is not JSON serializable
        if "node" in entry['osm_object_url']:
            lon = entry['location']['lon']
            lat = entry['location']['lat']
            collected_data_for_use.append({"lon": lon, "lat": lat, "geometry": "point", "osm_object_url": entry['osm_object_url'], 'error_message': error_message, 'tags': entry['tags']})
        elif "way" in entry['osm_object_url']:
            # currently skipped early, see above
            # way vs area... TODO
            collected_data_for_use.append({"nodes_ids_from_way": live_osm_data['nd'], "geometry": "way", "osm_object_url": entry['osm_object_url'], 'error_message': error_message, 'tags': entry['tags']})
        elif "relation" in entry['osm_object_url']:
            ways = []
            nodes = []
            for entry in live_osm_data['member']:
                print(json.dumps(entry, indent=4, sort_keys=True))
                ref = entry["ref"]
                object_type = entry["type"]
                if object_type == "relation":
                    print("relation in relation, will ignore this part and hope that it also has ways/nodes")
            if len(ways) == 1 and len(nodes) == 0:
                print("relation with just a single way, vould be reduced to a way")
            print("skipping relation, see ")
            continue
            collected_data_for_use.append({"way_ids_from_relation": ways, "node_ids_from_relation": nodes, "geometry": "relation", "osm_object_url": entry['osm_object_url'], 'error_message': error_message, 'tags': entry['tags']})
            """
            {
            "type": "GeometryCollection",
            "geometries": [
                {
                    "type": "Point",
                    "coordinates": [40.0, 10.0]
                },
                {
                    "type": "LineString",
                    "coordinates": [
                        [10.0, 10.0],
                        [20.0, 20.0],
                        [10.0, 40.0]
                    ]
                },
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [40.0, 40.0],
                            [20.0, 45.0],
                            [45.0, 30.0],
                            [40.0, 40.0]
                        ]
                    ]
                }
            ]
            }"""
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

def build_geojson_way_entry(nodes_ids_from_way, osm_object_url, error_message, tag_dictionary):
    way_coords = []
    for node_id in nodes_ids_from_way:
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

def create_link_challenge_based_on_error_id(challenge_api, project_id, error_id, featured):
    texts = get_challenge_text_based_on_error_id(error_id)
    try:
        create_challenge(challenge_api, project_id, texts['challenge_name'], texts['challenge_description'], texts['challenge_instructions'], texts['changeset_action'], featured)
    except requests.exceptions.ConnectionError as e:
        print(e)
        print("will retry")
        print(challenge_api, project_id, error_id, featured)
        print(texts)
        time.sleep(10)
        return create_link_challenge_based_on_error_id(challenge_api, project_id, error_id, featured)

def delete_task_if_not_locked(task_api, task_id, osm_link):
    link = "https://maproulette.org/task/" + str(task_id)
    print(link, osm_link, "should be marked as deleted as it is present in task and not in reports from database")
    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/task.py#L169
    #print(STATUS_DELETED)
    try:
        task_api.update_task_status(task_id, STATUS_DELETED, "", "", False)
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
    except requests.exceptions.ConnectionError as e:
        print(e)
        print("will retry")
        time.sleep(10)
        return delete_task_if_not_locked(task_api, task_id, osm_link)

def set_featured_status_for_challenge_for_given_error_id(challenge_api, project_id, error_id, featured_status):
    # seems to be not working at all anyway...
    challenge_id = get_challenge_id_based_on_error_id(challenge_api, project_id, error_id)
    if challenge_id == None:
        raise Exception("no such challenge: " + str(error_id))

    texts = get_challenge_text_based_on_error_id(error_id)

    challenge_data = create_challenge_model(challenge_api, project_id, texts['challenge_name'], texts['challenge_description'], texts['challenge_instructions'], texts['changeset_action'], featured_status)
    #print("requested features status for", error_id, "is", challenge_data.featured)
    try:
        # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L340C9-L340C51
        response = challenge_api.update_challenge(challenge_id, challenge_data)
        if response["status"] != 200:
            print(json.dumps(response, indent=4, sort_keys=True))
    except maproulette.api.errors.InvalidJsonError as e:
        print("challenge_id", challenge_id)
        print(challenge_data)
        print(json.dumps(maproulette.ChallengeModel.to_dict(challenge_data), indent=4, sort_keys=True))
        print(e)
        raise e
    except requests.exceptions.ConnectionError as e:
        print(e)
        print("will retry from start")
        time.sleep(10)
        return set_featured_status_for_challenge_for_given_error_id(challenge_api, project_id, error_id, featured_status)
    return

def get_challenge_tasks(challenge_api, challenge_id, debug=True):
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
                if debug:
                    print("fetching challenge tasks for", challenge_id, "processing page with", len(data), "entries")
                if len(data) < limit:
                    return returned
        except maproulette.api.errors.HttpError as e:
            print("https://maproulette.org/browse/challenges/" + str(challenge_id), "get_challenge_tasks", e)
            print("will retry from start")
            time.sleep(10)
        except requests.exceptions.ConnectionError as e:
            print("https://maproulette.org/browse/challenges/" + str(challenge_id), "get_challenge_tasks", e)
            print("will retry from start")
            time.sleep(10)

def get_challenge_data_from_project(challenge_api, project_id):

    # https://github.com/osmlab/maproulette-python-client/blob/1740b54a112021889e42f727de8f43fbc7860fd9/maproulette/api/challenge.py#L95
    limit_send = 1000
    response = None
    while True:
        try:
            response = challenge_api.get_challenge_listing(project_ids=project_id, only_enabled='false', limit=limit_send) # yes, stringified boolean
            break
        except maproulette.api.errors.HttpError as e:
            print(e)
            print("get_challenge_data_from_project for project_id", project_id)
            print("will retry after sleeping a bit")
            time.sleep(10)
        except requests.exceptions.ConnectionError as e:
            print(e)
            print("get_challenge_data_from_project for project_id", project_id)
            print("will retry after sleeping a bit")
            time.sleep(10)
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
    cursor.execute('SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id FROM osm_data WHERE error_id = :error_id ORDER BY type, id LIMIT 1000', {"error_id": error_id})
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
    cursor.execute('SELECT rowid, type, id, lat, lon, tags, area_identifier, download_timestamp, validator_complaint, error_id FROM osm_data WHERE error_id = :error_id AND area_identifier = :area_identifier ORDER BY id', {"error_id": error_id, 'area_identifier': internal_region_name})
    returned = []
    for entry in cursor.fetchall():
        rowid, object_type, id, lat, lon, tags, area_identifier, updated, validator_complaint, error_id = entry
        tags = json.loads(tags)
        validator_complaint = json.loads(validator_complaint)
        returned.append(validator_complaint)
    return returned

if __name__ == '__main__':
    main()
