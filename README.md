OSM-wikipedia-tag-validator
===========================

Python script validating Wikipedia tags in OpenStreetMap database by fetching and analysing linked Wikipedia articles.

Dependencies: python 3.5+ and unpublished osm_iterator, wikimedia_connection package (TODO: publish osm iterator, wikimedia_connection).

To install: `pip3 install -r requirements.txt`

see https://wiki.openstreetmap.org/wiki/Wikipedia_Link_Improvement_Project for something that my be a better implementation but relies on an external service

see also https://wiki.openstreetmap.org/wiki/SPARQL_examples#Quality_Control

to run tests:

```nosetests3``` or ```python3 -m unittest```
