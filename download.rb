require 'rest-client'

def query_text(name, nodes, ways, relations, expand, timeout)
  query = "[timeout:#{timeout}];(\n"
  query += "area[name='" + name + "']->.searchArea;\n"
  query += "node['wikipedia'](area.searchArea);\n" if nodes
  query += "way['wikipedia'](area.searchArea);\n" if ways
  query += "relation['wikipedia'](area.searchArea);\n" if relations

  query += ');
  '
  query += '(._;>;);' if expand
  query += 'out meta;
  <;'
  return query
end

def produced_filename(name, nodes, ways, relations, expand)
  filename = name
  filename += "_nodes" if nodes
  filename += "_ways" if ways
  filename += "_relations" if relations
  filename = "#{name}_all" if nodes && ways && relations
  filename += "_without_geometry" if expand == false
  filename += ".osm"
  return filename
end

def download(name, nodes, ways, relations, expand)
  timeout = 1550
  query = query_text(name, nodes, ways, relations, expand, timeout)
  filename = produced_filename(name, nodes, ways, relations, expand)

  puts query
  puts "downloading: start"
  url = "http://overpass-api.de/api/interpreter?data=#{query.gsub("\n", "")}"
  start = Time.now.to_i
  begin
    text = RestClient.get(URI.escape(url), :user_agent => ARGV[0], :timeout => timeout).to_str
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

#download("Stendal", true, true, true, true)
#download("Bremen", true, true, true, true)
#download("Kraków", true, true, true, true)
download("Berlin", true, false, false, false)
download("Germany", true, false, false, false)
download("Polska", true, false, false, false)
["małopolskie", "podkarpackie", "lubelskie",
  "świętokrzyskie", "mazowieckie", "podlaskie",
  "warmińsko-mazurskie", "pomorskie", "kujawsko-pomorskie",
  "zachodniopomorskie", "lubuskie", "wielkopolskie", "dolnośląskie",
  "opolskie", "śląskie", "łódzkie"].each do |voivodeship|
  while true
    break if download("województwo #{voivodeship}", true, true, true, true)
    sleep 600
  end
  sleep 600
end
#download("Polska", true, false, false, false)
#download("Polska", false, true, false, false)
#download("Polska", false, false, true, false)
