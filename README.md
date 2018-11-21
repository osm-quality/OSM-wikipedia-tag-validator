OSM-wikipedia-tag-validator
===========================

Python script validating Wikipedia tags in OpenStreetMap database by fetching and analysing linked Wikipedia articles.

Currently code is poorly documented, partially unpublished and not prepared for reuse. If you want it to change - please open an issue on a bug tracker, it will increase chance that I will work on this.

Dependencies: python 3.5+, unpublished wikimedia_connection package (TODO: publish this package) and some packages published on pypi

It requires also osm_handling_config package with global_config.py containing some configuration functions. (TODO: document it, publish an example)

To install: `pip3 install -r requirements.txt`

see https://wiki.openstreetmap.org/wiki/Wikipedia_Link_Improvement_Project for something that my be a better implementation but relies on an external service

see also https://wiki.openstreetmap.org/wiki/SPARQL_examples#Quality_Control

# Running tests

```nosetests3``` or ```python3 -m unittest```
