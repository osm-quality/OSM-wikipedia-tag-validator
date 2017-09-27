require 'rest-client'
require 'etc'

def user_agent
  "downloader of interesting places, operated by #{Etc.getlogin}, written by Mateusz Konieczny (matkoniecz@gmail.com)"
end

def timeout
  1550
end

def download_location
  return File.read('cache_location.config')
end

def query_text(area_identifier_builder, area_identifier, nodes, ways, relations, expand)
  query = "[timeout:#{timeout}];(\n"
  query += area_identifier_builder if area_identifier_builder != nil
  query += "node['wikipedia'](#{area_identifier});\n" if nodes
  query += "way['wikipedia'](#{area_identifier});\n" if ways
  query += "relation['wikipedia'](#{area_identifier});\n" if relations
  query += "node['wikidata'](#{area_identifier});\n" if nodes
  query += "way['wikidata'](#{area_identifier});\n" if ways
  query += "relation['wikidata'](#{area_identifier});\n" if relations

  query += "node[~'wikipedia:.*'~'.*'](#{area_identifier});\n" if nodes
  query += "way[~'wikipedia:.*'~'.*'](#{area_identifier});\n" if ways
  query += "relation[~'wikipedia:.*'~'.*'](#{area_identifier});\n" if relations

  query += ');
  '
  query += '(._;>;);' if expand
  query += 'out meta;
  <;'
  return query
end

def query_text_by_name(name, nodes, ways, relations, expand)
  area_identifier = 'area.searchArea'
  area_identifier_builder = "area[name='" + name + "']->.searchArea;\n"
  query_text(area_identifier_builder, area_identifier, nodes, ways, relations, expand)
end

def query_text_by_graticule(lower_lat, left_lon, nodes, ways, relations, expand)
  area_identifier_builder = nil
  area_identifier = "#{lower_lat},#{left_lon},#{lower_lat+1},#{left_lon+1}"
  query_text(area_identifier_builder, area_identifier, nodes, ways, relations, expand)
end

def what_is_downloaded_to_text(nodes, ways, relations, expand)
  returned = ""
  returned += "_nodes" if nodes
  returned += "_ways" if ways
  returned += "_relations" if relations
  returned = "_all" if nodes && ways && relations
  returned += "_without_geometry" if expand == false
  return returned
end

def produced_filename_by_name(name, nodes, ways, relations, expand)
  filename = name
  filename += what_is_downloaded_to_text(nodes, ways, relations, expand)
  filename += ".osm"
  return download_location+"/"+filename
end

def produced_filename_by_graticule(lower_lat, left_lon, nodes, ways, relations, expand)
  filename = "#{lower_lat}, #{left_lon}"
  filename += what_is_downloaded_to_text(nodes, ways, relations, expand)
  filename += ".osm"
  return download_location+"/"+filename
end

def is_download_necessary_by_name(name, nodes, ways, relations, expand)
  filename = produced_filename_by_name(name, nodes, ways, relations, expand)
  return !File.exists?(filename)
end

def is_download_necessary_by_graticule(lower_lat, left_lon, nodes, ways, relations, expand)
  filename = produced_filename_by_graticule(lower_lat, left_lon, nodes, ways, relations, expand)
  return !File.exists?(filename)
end

def download_graticule(lower_lat, left_lon)
  nodes, ways, relations, expand = true, true, true, true
  query = query_text_by_graticule(lower_lat, left_lon, nodes, ways, relations, expand) 
  filename = produced_filename_by_graticule(lower_lat, left_lon, nodes, ways, relations, expand)
  return true if !is_download_necessary_by_graticule(lower_lat, left_lon, nodes, ways, relations, expand)
  return download(query, filename)
end

def download(query, filename)
  puts query
  puts "downloading: start"
  url = "http://overpass-api.de/api/interpreter"
  start = Time.now.to_i
  begin
     text = RestClient::Request.execute(
              :method => :post,
              :url => URI.escape(url),
              :timeout => timeout,
              :payload => {'data': query},
              )
  rescue RestClient::BadRequest => e
    puts url
    puts e
    return false
  rescue RestClient::Exceptions::ReadTimeout => e
    puts "timeout after #{Time.now.to_i-start}s, requested timeout #{timeout}"
    return false
  rescue RestClient::TooManyRequests => e
    puts "429 error"
    sleep 600
    return false
  end
  puts "downloading: end"

  if File.exists?(filename)
    puts "deleting old file: start"
    File.delete(filename)
    puts "deleting old file: end"
  end
  puts "saving new file: start"
  f = File.new(filename, "w")
  f.write text
  f.close
  puts "saving new file: end"
  return true
end

def download_by_name(name, nodes, ways, relations, expand)
  query = query_text_by_name(name, nodes, ways, relations, expand)
  filename = produced_filename_by_name(name, nodes, ways, relations, expand)
  return true if !is_download_necessary_by_name(name, nodes, ways, relations, expand)
  return download(query, filename)
end

voivoddeships = ["małopolskie", "podkarpackie", "lubelskie",
  "świętokrzyskie", "mazowieckie", "podlaskie",
  "warmińsko-mazurskie", "pomorskie", "kujawsko-pomorskie",
  "zachodniopomorskie", "lubuskie", "wielkopolskie", "dolnośląskie",
  "opolskie", "śląskie", "łódzkie"]
download_by_name("Kraków", true, true, true, true)
voivoddeships.each do |voivodeship|
  while true
    name = "województwo #{voivodeship}"
    break if !is_download_necessary_by_name(name, true, true, true, true)
    result = download_by_name(name, true, true, true, true)
    puts "failed download" if !result
    sleep 600
    break if result
  end
end
#download_by_name("Polska", true, false, false, false)
#download_by_name("Polska", false, true, false, false)
#download_by_name("Polska", false, false, true, false)
download_by_name("Stendal", true, true, true, true)
download_by_name("Bremen", true, true, true, true)
#download_by_name("Berlin", true, false, false, false)
download_by_name("Nigeria", true, true, true, true)
#download_by_name("Bolivia", true, true, true, true)
#download_by_name("Қазақстан", true, true, true, true)
#download_by_name("Magyarország", true, false, false, true)
#download_by_name("Magyarország", false, true, false, true)
#download_by_name("Magyarország", false, false, true, true)
#TODO blocked by URL length https://josm.openstreetmap.de/ticket/15141
#http://overpass-api.de/command_line.html
#https://github.com/BrunoSalerno/overpass-api-ruby/issues/6
#query = File.read('reload_Poland.query')
#download(query, 'reloaded_Poland.osm')