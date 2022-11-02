OSM-wikipedia-tag-validator
===========================

# Quick summary

* regenerate reports:
* * `python3 script.py`
* launch bot edits:
* * `bash osm_editor_run_bot_in_regions.sh`
* install dependencies:
* * `pip3 install --user -r requirements.txt`
* Run tests:
* * `python3 -m unittest`

# Story behind this tool

I tried to implement tool to recommend interesting places for visit as a tourist.

It turned out quite well, but still not better than existing tools like Trip Advisor. Main plus was that it is not based on content generated specifically for that site.

Though maybe I rate myself too low and I should retry it.

One of main problems with this recommendations is that I based them mostly on `wikipedia` tags. After all, `natural=cave_entrance` with Wikipedia article is far more likely to be interesting than one without it? And tree with Wikipedia article about it is definitely interesting?

But it got derailed by people doing things like tagging `wikipedia=en:Oak` ([example](https://www.openstreetmap.org/node/7430033428/history)). So it was necessary to filter out garbage to display only entries that actually have own pages. Validator was growing due to discovering more and more ways how linking may be broken.

It ended with extracting validator into a separate project and publishing reports, so other mappers may fix detected problems.

So problems were common and relatively easy to fix, so now my [bot account](https://www.openstreetmap.org/user/Mateusz%20Konieczny%20-%20bot%20account) can automatically handle cases of Wikipedia editors deciding to rename articles of all villages in Poland and other similar chores.

But many errors require human to fix them, so I invite you to visit https://matkoniecz.github.io/OSM-wikipedia-tag-validator-reports/ 

Feel free to request report for your area or report incorrect or confusing complaints.

You can open issue on this repository or [send me a message](https://www.openstreetmap.org/message/new/Mateusz%20Konieczny).

# Disclaimers

Python script validating Wikipedia tags in OpenStreetMap database by fetching and analysing linked Wikipedia articles.

Configuration is ridiculous and spread across command line, installed packages, files storing text, files storing json. If someone knows about proper method to handle config - please open an issue and link such documentation or describe it there.


Currently code is poorly documented, partially unpublished and not prepared for reuse. If you want this to change - please open an issue on a bug tracker, it will increase chance that I will work on this.

Architecture is insane. It is using filesystem as a database backend. If you want this to change - please open an issue on a bug tracker, it will increase chance that I will work on this.

Code is GNU GPLv3 licensed.

# Run

`python3 script.py` to run and generate reports in "OSM-wikipedia-tag-validator-reports" folder.

`bash osm_editor_run_bot_in_regions.sh` to run bot edits. Note that this bot edits were approved to be run on specific account, see [OSM rules](https://wiki.openstreetmap.org/wiki/Automated_Edits_code_of_conduct) and [my list of approvals](https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account) for more info.

???? to generate Maproulette tasks.

# Install

`pip3 install --user -r requirements.txt`

## Dependencies
* Python 3.5+
* packages published on pypi, specified in `requirements.txt`
** This includes https://github.com/matkoniecz/wikibrain#installation that sadly has unfortunate not standard way of installing it
# Configuration

## Regions

`regions_processed.yaml`

It requires also osm_handling_config package with global_config.py containing some configuration functions. (TODO: document it, publish an example)

### Generate internal divisions

See `generate_internal_divisions_for_regions_processed.py`

## Passwords

`secret.json` contains account info necessary to run fixing edits.

# Running tests

`python3 -m unittest`

# Alternatives

see https://wiki.openstreetmap.org/wiki/Wikipedia_Link_Improvement_Project for something that my be a better implementation but relies on an external service (external service died)

see also https://wiki.openstreetmap.org/wiki/SPARQL_examples#Quality_Control (relies on dead external service)
