require 'rest-client'
require 'etc'
require 'yaml'

def user_agent
  "downloader of interesting places, operated by #{Etc.getlogin}, written by Mateusz Konieczny (matkoniecz@gmail.com)"
end

def timeout
  1550
end

def download_location
  return File.read('cache_location.config')
end

QueryBuilder = Struct.new(:timeout, :expand) do
  def query_header()
    return "[timeout:#{timeout}];(\n"
  end
  def query_footer()
    returned = ''
    returned += ');
    '
    returned += '>;' if expand
    returned += "\n"
    returned += 'out meta;'
    return returned
  end
end

def query_text(area_identifier_builder, area_identifier, nodes, ways, relations, expand)
  builder = QueryBuilder.new(timeout, expand)
  query = builder.query_header
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

  query += builder.query_footer()
  return query
end

def teryt_query_text(area_identifier_builder, area_identifier, nodes, ways, relations, expand)
  builder = QueryBuilder.new(timeout, expand)
  query = builder.query_header
  query += area_identifier_builder if area_identifier_builder != nil
  query += "node['teryt:simc'](#{area_identifier});\n" if nodes
  query += "way['teryt:simc'](#{area_identifier});\n" if ways
  query += "relation['teryt:simc'](#{area_identifier});\n" if relations
  query += builder.query_footer()
  return query
end

def missing_namepl_query_text(area_identifier_builder, area_identifier, nodes, ways, relations, expand)
  builder = QueryBuilder.new(timeout, expand)
  query = builder.query_header
  query += area_identifier_builder if area_identifier_builder != nil
  query += "node['name']['name:pl'!~'.*'](#{area_identifier});\n" if nodes
  query += "way['name']['name:pl'!~'.*'](#{area_identifier});\n" if ways
  query += "relation['name']['name:pl'!~'.*'](#{area_identifier});\n" if relations
  query += builder.query_footer()
  return query
end

def area_identifier_builder_by_name(name)
  return "area[name='" + name + "']->.searchArea;\n"
end

def area_identifier_by_name(name)
  return 'area.searchArea'
end

def query_text_by_name(name, nodes, ways, relations, expand)
  area_identifier = area_identifier_by_name(name)
  area_identifier_builder = area_identifier_builder_by_name(name)
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

def main()
  filepath = download_location+"/"+'teryt_simc.osm'
  if !File.exists?(filepath)
    name = "Polska"
    area_identifier = area_identifier_by_name(name)
    area_identifier_builder = area_identifier_builder_by_name(name)
    query = teryt_query_text(area_identifier_builder, area_identifier, true, true, true, false)
    download(query, filepath)
  end

  filepath = download_location+"/"+'namepl_krk.osm'
  if !File.exists?(filepath)
    name = "Kraków"
    area_identifier = area_identifier_by_name(name)
    area_identifier_builder = area_identifier_builder_by_name(name)
    query = missing_namepl_query_text(area_identifier_builder, area_identifier, true, true, true, true)
    download(query, filepath)
  end

  # around Poland - for making map that shows how nicely stuff was fixed in Poland
  for lat in 48..55
    for lon in 14..24
      download_graticule(lat, lon)
    end
  end
  # N 55
  # S 48
  # W 14
  # E 24

  filepath = download_location+"/"+'reloaded_Poland.osm'
  if !File.exists?(filepath)
    query = File.read(download_location+'/reload_querries/reload_Poland.query')
    download(query, filepath)
  end

  region_data = YAML.load_file('processed_regions.yaml')
  region_data.each do |region|
    while true
      name = region['region_name']
      break if !is_download_necessary_by_name(name, true, true, true, true)
      result = download_by_name(name, true, true, true, true)
      if !result
        puts "failed download"
        sleep 300
      end
      sleep 300
      break if result
    end
  end
end

main