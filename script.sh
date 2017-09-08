set -x
cd /media/mateusz/5bfa9dfc-ed86-4d19-ac36-78df1060707c

[ -e Bremen_all.osm.yaml ] && rm Bremen_all.osm.yaml
[ -e Berlin_nodes_without_geometry.osm.yaml ] && rm Berlin_nodes_without_geometry.osm.yaml
[ -e Stendal_all.osm.yaml ] && rm Stendal_all.osm.yaml
[ -e Kraków_all.osm.yaml ] && rm Kraków_all.osm.yaml
[ -e "województwo małopolskie_all.osm.yaml" ] && rm "województwo małopolskie_all.osm.yaml"
[ -e "województwo podkarpackie_all.osm.yaml" ] && rm "województwo podkarpackie_all.osm.yaml"
[ -e "województwo lubelskie_all.osm.yaml" ] && rm "województwo lubelskie_all.osm.yaml"
[ -e "województwo świętokrzyskie_all.osm.yaml" ] && rm "województwo świętokrzyskie_all.osm.yaml"
[ -e "województwo mazowieckie_all.osm.yaml" ] && rm "województwo mazowieckie_all.osm.yaml"
[ -e "województwo podlaskie_all.osm.yaml" ] && rm "województwo podlaskie_all.osm.yaml"
[ -e "województwo województwo warmińsko-mazurskie_all.osm.yaml" ] && rm "województwo warmińsko-mazurskie_all.osm.yaml"
[ -e "województwo pomorskie_all.osm.yaml" ] && rm "województwo pomorskie_all.osm.yaml"
[ -e "województwo kujawsko-pomorskie_all.osm.yaml" ] && rm "województwo kujawsko-pomorskie_all.osm.yaml"
[ -e "województwo zachodniopomorskie_all.osm.yaml" ] && rm "województwo zachodniopomorskie_all.osm.yaml"
[ -e "województwo lubuskie_all.osm.yaml" ] && rm "województwo lubuskie_all.osm.yaml"
[ -e "województwo wielkopolskie_all.osm.yaml" ] && rm "województwo wielkopolskie_all.osm.yaml"
[ -e "województwo dolnośląskie_all.osm.yaml" ] && rm "województwo dolnośląskie_all.osm.yaml"
[ -e "województwo opolskie_all.osm.yaml" ] && rm "województwo opolskie_all.osm.yaml"
[ -e "województwo śląskie_all.osm.yaml" ] && rm "województwo śląskie_all.osm.yaml"
[ -e "województwo łódzkie_all.osm.yaml" ] && rm "województwo łódzkie_all.osm.yaml"

cd "/home/mateusz/Desktop/kolejka/Na_później/Na_później/OSM-wikipedia-tag-validator"

# Germany

python3 wikipedia_validator.py -expected_language_code de -file "Bremen_all.osm"
#python3 wikipedia_validator.py -expected_language_code de -file "Berlin_nodes_without_geometry.osm"
python3 wikipedia_validator.py -expected_language_code de -file "Stendal_all.osm"

cd /media/mateusz/5bfa9dfc-ed86-4d19-ac36-78df1060707c

rm Deutschland.yaml
cat Bremen_all.osm.yaml >> Deutschland.yaml
#cat Berlin_nodes_without_geometry.osm.yaml >> Deutschland.yaml
cat Stendal_all.osm.yaml >> Deutschland.yaml

cd "/home/mateusz/Desktop/kolejka/Na_później/Na_później/OSM-wikipedia-tag-validator"

python3 generate_webpage_with_error_output.py -file Deutschland.yaml > Deutschland.html
python3 generate_webpage_with_error_output.py -file Bremen_all.osm.yaml > Bremen.html


# Kraków
python3 wikipedia_validator.py -expected_language_code pl -file "Kraków_all.osm"
python3 generate_webpage_with_error_output.py -file Kraków_all.osm.yaml > Kraków.html

# Poland
python3 wikipedia_validator.py -expected_language_code pl -file "województwo małopolskie_all.osm"
python3 wikipedia_validator.py -expected_language_code pl -file "województwo podkarpackie_all.osm"
python3 wikipedia_validator.py -expected_language_code pl -file "województwo lubelskie_all.osm"
python3 wikipedia_validator.py -expected_language_code pl -file "województwo świętokrzyskie_all.osm"
python3 wikipedia_validator.py -expected_language_code pl -file "województwo mazowieckie_all.osm"
python3 wikipedia_validator.py -expected_language_code pl -file "województwo podlaskie_all.osm"
#python3 wikipedia_validator.py -expected_language_code pl -file "województwo warmińsko-mazurskie_all.osm"
#python3 wikipedia_validator.py -expected_language_code pl -file "województwo pomorskie_all.osm"
#python3 wikipedia_validator.py -expected_language_code pl -file "województwo kujawsko-pomorskie_all.osm"
#python3 wikipedia_validator.py -expected_language_code pl -file "województwo zachodniopomorskie_all.osm"
#python3 wikipedia_validator.py -expected_language_code pl -file "województwo lubuskie_all.osm"
#python3 wikipedia_validator.py -expected_language_code pl -file "województwo wielkopolskie_all.osm"
#python3 wikipedia_validator.py -expected_language_code pl -file "województwo dolnośląskie_all.osm"
#python3 wikipedia_validator.py -expected_language_code pl -file "województwo opolskie_all.osm"
#python3 wikipedia_validator.py -expected_language_code pl -file "województwo śląskie_all.osm"
#python3 wikipedia_validator.py -expected_language_code pl -file "województwo łódzkie_all.osm"

cd /media/mateusz/5bfa9dfc-ed86-4d19-ac36-78df1060707c
rm Polska.yaml
cat "województwo małopolskie_all.osm.yaml" >> Polska.yaml
cat "województwo podkarpackie_all.osm.yaml" >> Polska.yaml
cat "województwo lubelskie_all.osm.yaml" >> Polska.yaml
cat "województwo świętokrzyskie_all.osm.yaml" >> Polska.yaml
cat "województwo mazowieckie_all.osm.yaml" >> Polska.yaml
cat "województwo podlaskie_all.osm.yaml" >> Polska.yaml

cat "województwo małopolskie_all.osm.yaml" >> B.yaml
cat "województwo podkarpackie_all.osm.yaml" >> B.yaml
cat "województwo lubelskie_all.osm.yaml" >> B.yaml

cat "województwo podlaskie_all.osm.yaml" >> A.yaml #TMP

cd "/home/mateusz/Desktop/kolejka/Na_później/Na_później/OSM-wikipedia-tag-validator"
python3 generate_webpage_with_error_output.py -file Polska.yaml > Polska.html
python3 generate_webpage_with_error_output.py -file "A.yaml" > A.html
python3 generate_webpage_with_error_output.py -file "B.yaml" > B.html

[ -e index.html ] && rm index.html
echo "<html><body>" >> index.html
echo "<a href = Polska.html>Polska</a>" >> index.html
echo "<a href = Krak&oacute;w.html>Krak&oacute;w</a>" >> index.html
echo "<a href = Deutschland.html>Deutschland</a>" >> index.html
echo "<a href = Bremen.html>Bremen</a>" >> index.html
echo "<a href = A.html>A</a>" >> index.html
echo "<a href = B.html>B</a>" >> index.html
echo "</html></body>" >> index.html

mv index.html OSM-wikipedia-tag-validator-reports/ -f
mv Polska.html OSM-wikipedia-tag-validator-reports/ -f
mv Kraków.html OSM-wikipedia-tag-validator-reports/ -f
mv Deutschland.html OSM-wikipedia-tag-validator-reports/ -f
mv Bremen.html OSM-wikipedia-tag-validator-reports/ -f
mv A.html OSM-wikipedia-tag-validator-reports/ -f
mv B.html OSM-wikipedia-tag-validator-reports/ -f
