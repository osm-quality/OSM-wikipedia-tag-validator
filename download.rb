require 'rest-client'
require 'etc'

def user_agent
  "downloader of interesting places, operated by #{Etc.getlogin}, written by Mateusz Konieczny (matkoniecz@gmail.com)"
end

def query_text_by_name(name, nodes, ways, relations, expand, timeout)
  query = "[timeout:#{timeout}];(\n"
  query += "area[name='" + name + "']->.searchArea;\n"
  query += "node['wikipedia'](area.searchArea);\n" if nodes
  query += "way['wikipedia'](area.searchArea);\n" if ways
  query += "relation['wikipedia'](area.searchArea);\n" if relations
  query += "node['wikidata'](area.searchArea);\n" if nodes
  query += "way['wikidata'](area.searchArea);\n" if ways
  query += "relation['wikidata'](area.searchArea);\n" if relations

  query += ');
  '
  query += '(._;>;);' if expand
  query += 'out meta;
  <;'
  return query
end

def produced_filename_by_name(name, nodes, ways, relations, expand)
  filename = name
  filename += "_nodes" if nodes
  filename += "_ways" if ways
  filename += "_relations" if relations
  filename = "#{name}_all" if nodes && ways && relations
  filename += "_without_geometry" if expand == false
  filename += ".osm"
  return filename
end

def is_download_necessary_by_name(name, nodes, ways, relations, expand)
  filename = produced_filename_by_name(name, nodes, ways, relations, expand)
  return !File.exists?(filename)
end

def download(name, nodes, ways, relations, expand)
  timeout = 1550
  query = query_text_by_name(name, nodes, ways, relations, expand, timeout)
  filename = produced_filename_by_name(name, nodes, ways, relations, expand)
  return true if !is_download_necessary_by_name(name, nodes, ways, relations, expand)
  puts query
  puts "downloading: start"
  url = "http://overpass-api.de/api/interpreter?data=#{query.gsub("\n", "")}"
  start = Time.now.to_i
  begin
    text = RestClient::Request.execute(method: :get, url: URI.escape(url), timeout: timeout, user_agent: user_agent).to_str
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

voivoddeships = ["małopolskie", "podkarpackie", "lubelskie",
  "świętokrzyskie", "mazowieckie", "podlaskie",
  "warmińsko-mazurskie", "pomorskie", "kujawsko-pomorskie",
  "zachodniopomorskie", "lubuskie", "wielkopolskie", "dolnośląskie",
  "opolskie", "śląskie", "łódzkie"]
download("Kraków", true, true, true, true)
voivoddeships[0, 1].each do |voivodeship|
  while true
    name = "województwo #{voivodeship}"
    break if !is_download_necessary_by_name(name, true, true, true, true)
    result = download(name, true, true, true, true)
    puts "failed download" if !result
    sleep 600
    break if result
  end
end
#download("Polska", true, false, false, false)
#download("Polska", false, true, false, false)
#download("Polska", false, false, true, false)
download("Deutschland", true, false, false, false)
download("Polska", true, false, false, false)
#download("Stendal", true, true, true, true)
download("Bremen", true, true, true, true)
#download("Berlin", true, false, false, false)
#download("Nigeria", true, true, true, true)
#download("Bolivia", true, true, true, true)
#download("Қазақстан", true, true, true, true)
#download("Magyarország", true, false, false, true)
#download("Magyarország", false, true, false, true)
#download("Magyarország", false, false, true, true)
