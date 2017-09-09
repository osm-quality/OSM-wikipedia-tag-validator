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
[ -e "1.yaml" ] && rm "1.yaml"
[ -e "2.yaml" ] && rm "2.yaml"
[ -e "3.yaml" ] && rm "3.yaml"
[ -e "4.yaml" ] && rm "4.yaml"
[ -e "5.yaml" ] && rm "5.yaml"
[ -e "6.yaml" ] && rm "6.yaml"
[ -e "7.yaml" ] && rm "7.yaml"
[ -e "8.yaml" ] && rm "8.yaml"
[ -e "9.yaml" ] && rm "9.yaml"
[ -e "10.yaml" ] && rm "10.yaml"
[ -e "11.yaml" ] && rm "11.yaml"
[ -e "12.yaml" ] && rm "12.yaml"
[ -e "13.yaml" ] && rm "13.yaml"

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

cat "województwo małopolskie_all.osm.yaml" >> 1.yaml
cat "województwo podkarpackie_all.osm.yaml" >> 2.yaml
cat "województwo lubelskie_all.osm.yaml" >> 3.yaml
cat "województwo świętokrzyskie_all.osm.yaml" >> 4.yaml
cat "województwo mazowieckie_all.osm.yaml" >> 5.yaml
cat "województwo podlaskie_all.osm.yaml" >> 6.yaml

cd "/home/mateusz/Desktop/kolejka/Na_później/Na_później/OSM-wikipedia-tag-validator"
python3 generate_webpage_with_error_output.py -file Polska.yaml > Polska.html
python3 generate_webpage_with_error_output.py -file "1.yaml" > 1.html
python3 generate_webpage_with_error_output.py -file "2.yaml" > 2.html
python3 generate_webpage_with_error_output.py -file "3.yaml" > 3.html
python3 generate_webpage_with_error_output.py -file "4.yaml" > 4.html
python3 generate_webpage_with_error_output.py -file "5.yaml" > 5.html
python3 generate_webpage_with_error_output.py -file "6.yaml" > 6.html

[ -e index.html ] && rm index.html
echo "<html><body>" >> index.html
echo "<a href = Polska.html>Polska</a>" >> index.html
echo "<a href = Krak&oacute;w.html>Krak&oacute;w</a>" >> index.html
echo "<a href = Deutschland.html>Deutschland</a>" >> index.html
echo "<a href = Bremen.html>Bremen</a>" >> index.html
echo "<a href = 1.html>1</a>" >> index.html
echo "<a href = 2.html>2</a>" >> index.html
echo "<a href = 3.html>3</a>" >> index.html
echo "<a href = 4.html>4</a>" >> index.html
echo "<a href = 5.html>5</a>" >> index.html
echo "<a href = 6.html>6</a>" >> index.html
echo "</html></body>" >> index.html

mv index.html OSM-wikipedia-tag-validator-reports/ -f
mv Polska.html OSM-wikipedia-tag-validator-reports/ -f
mv Kraków.html OSM-wikipedia-tag-validator-reports/ -f
mv Deutschland.html OSM-wikipedia-tag-validator-reports/ -f
mv Bremen.html OSM-wikipedia-tag-validator-reports/ -f
mv 1.html OSM-wikipedia-tag-validator-reports/ -f
mv 2.html OSM-wikipedia-tag-validator-reports/ -f
mv 3.html OSM-wikipedia-tag-validator-reports/ -f
mv 4.html OSM-wikipedia-tag-validator-reports/ -f
mv 5.html OSM-wikipedia-tag-validator-reports/ -f
mv 6.html OSM-wikipedia-tag-validator-reports/ -f
cd OSM-wikipedia-tag-validator-reports
git add --all
git commit "+"
git diff @~