import common
import os
from subprocess import call

def merge(source_yaml, target_yaml):
    root = common.get_file_storage_location() + "/"
    system_call('cat "' + root + source_yaml +'" >> "' + root + target_yaml + '"')

def system_call(call):
    print(call)
    os.system(call)

voivoddeships = ["małopolskie", "podkarpackie", "lubelskie",
  "świętokrzyskie", "mazowieckie", "podlaskie",
  "warmińsko-mazurskie", "pomorskie", "kujawsko-pomorskie",
  "zachodniopomorskie", "lubuskie", "wielkopolskie", "dolnośląskie",
  "opolskie", "śląskie", "łódzkie"]
voivoddeships = ["województwo " + name for name in voivoddeships]

yaml_output_files = [
    'Bremen_all.osm.yaml',
    'Berlin_nodes_without_geometry.osm.yaml',
    'Stendal_all.osm.yaml',
    'Kraków_all.osm.yaml',
    'Deutschland.yaml',
    'Polska.yaml',
]

for index, voivoddeship in enumerate(voivoddeships):
    yaml_output_files.append(voivoddeship + "_all.osm.yaml")

root = common.get_file_storage_location() + "/"
for filename in yaml_output_files:
    try:
        os.remove(root + filename)
    except FileNotFoundError:
        pass

call(['python3', 'wikipedia_validator.py', '-expected_language_code', 'de', '-file', 'Bremen_all.osm'])
#call(['python3', 'wikipedia_validator.py', '-expected_language_code', 'de', '-file', 'Berlin_nodes_without_geometry.osm'])
call(['python3', 'wikipedia_validator.py', '-expected_language_code', 'de', '-file', 'Stendal_all.osm'])

merge('Bremen_all.osm.yaml', 'Deutschland.yaml')
#merge('Berlin_nodes_without_geometry.osm.yaml', 'Deutschland.yaml')
merge('Stendal_all.osm.yaml', 'Deutschland.yaml')

system_call('python3 generate_webpage_with_error_output.py -file Deutschland.yaml > Deutschland.html')
system_call('python3 generate_webpage_with_error_output.py -file Bremen_all.osm.yaml > Bremen.html')

# Kraków
system_call('python3 wikipedia_validator.py -expected_language_code pl -file "Kraków_all.osm"')
system_call('python3 generate_webpage_with_error_output.py -file Kraków_all.osm.yaml > Kraków.html')

# Poland
for voivoddeship in voivoddeships:
    filename = voivoddeship + '_all.osm'
    if not os.path.isfile(root + filename):
        print(filename + ' is not present')
        continue
    system_call('python3 wikipedia_validator.py -expected_language_code pl -file "' + filename + '"')
    filename = voivoddeship + '_all.osm.yaml'
    if not os.path.isfile(root + filename):
        print(filename + ' is not present [highly surprising]')
    merge(filename, 'Polska.yaml')
    system_call('python3 generate_webpage_with_error_output.py -file "' + filename + '" > "' + voivoddeship + '.html"')

filename = 'Polska.yaml'
if os.path.isfile(root + filename):
    system_call('python3 generate_webpage_with_error_output.py -file ' + filename  + ' > Polska.html')
else:
    print(filename + ' is not present [highly surprising]')

try:
    os.remove("index.html")
except FileNotFoundError:
    pass

with open('index.html', 'w') as index:
    index.write("<html><body>\n")
    index.write("<a href = Polska.html>Polska</a></br>\n")
    index.write("<a href = Krak&oacute;w.html>Krak&oacute;w</a></br>\n")
    index.write("<a href = Deutschland.html>Deutschland</a></br>\n")
    index.write("<a href = Bremen.html>Bremen</a></br>\n")
    for voivoddeship in voivoddeships:
        name = common.htmlify(voivoddeship)
        filename = name + '.html'
        if os.path.isfile(filename):
            index.write('<a href = "' + filename + '">' + name + "</a></br>\n")
        else:
            print(filename + ' is not present')
    index.write("</html></body>\n")

system_call('mv index.html OSM-wikipedia-tag-validator-reports/ -f')
system_call('mv Polska.html OSM-wikipedia-tag-validator-reports/ -f')
system_call('mv Kraków.html OSM-wikipedia-tag-validator-reports/ -f')
system_call('mv Deutschland.html OSM-wikipedia-tag-validator-reports/ -f')
system_call('mv Bremen.html OSM-wikipedia-tag-validator-reports/ -f')
for voivoddeship in voivoddeships:
    filename = voivoddeship + '.html'
    if os.path.isfile(filename):
        system_call('mv "' + filename + '" OSM-wikipedia-tag-validator-reports/ -f')
    else:
        print(filename + ' is not present')

os.chdir('OSM-wikipedia-tag-validator-reports')
system_call('git add --all')
system_call('git commit -m "automatic update of report files"')
system_call('git diff @~')
