require 'rest-client'
require 'etc'
require 'yaml'

def main()
  filepath = download_location+"/"+'teryt_simc.osm'
  if !File.exists?(filepath)
    name = "Polska"
    area_identifier = area_identifier_by_name(name)
    area_identifier_builder = area_identifier_builder_by_name(name)
    query = filtered_query_text("['teryt:simc']", area_identifier_builder, area_identifier, false)
    download(query, filepath)
  end

  filepath = download_location+"/"+'namepl_krk.osm'
  if !File.exists?(filepath)
    name = "Kraków"
    area_identifier = area_identifier_by_name(name)
    area_identifier_builder = area_identifier_builder_by_name(name)
    query = filtered_query_text("['name']['name:pl'!~'.*']", area_identifier_builder, area_identifier, false)
    download(query, filepath)
  end

  # around Poland - for making map that shows how nicely stuff was fixed in Poland
  for lat in 48..55
    for lon in 14..24
      download_graticule(lat, lon)
    end
  end

  filepath = download_location+"/"+'reloaded_Poland.osm'
  if !File.exists?(filepath)
    query = File.read(download_location+'/reload_querries/reload_Poland.query')
    download(query, filepath)
  end

  region_data = YAML.load_file('processed_regions.yaml')
  region_data.each do |region|
    while true
      name = region['region_name']
      break if !is_download_necessary_by_name(name, true)
      result = download_by_name(name, true)
      if !result
        puts "failed download"
        sleep 300
      end
      sleep 300
      break if result
    end
  end
end

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
    returned += 'out body;'
    returned += '>;' if expand
    returned += "\n"
    returned += 'out skel qt;'
    return returned
  end
end

def query_text(area_identifier_builder, area_identifier, expand)
  builder = QueryBuilder.new(timeout, expand)
  query = builder.query_header
  query += area_identifier_builder if area_identifier_builder != nil
  query += "node['wikipedia'](#{area_identifier});\n"
  query += "way['wikipedia'](#{area_identifier});\n"
  query += "relation['wikipedia'](#{area_identifier});\n"
  query += "node['wikidata'](#{area_identifier});\n"
  query += "way['wikidata'](#{area_identifier});\n"
  query += "relation['wikidata'](#{area_identifier});\n"

  query += "node[~'wikipedia:.*'~'.*'](#{area_identifier});\n"
  query += "way[~'wikipedia:.*'~'.*'](#{area_identifier});\n"
  query += "relation[~'wikipedia:.*'~'.*'](#{area_identifier});\n"

  query += builder.query_footer()
  return query
end

def filtered_query_text(filter, area_identifier_builder, area_identifier, expand)
  builder = QueryBuilder.new(timeout, expand)
  query = builder.query_header
  query += area_identifier_builder if area_identifier_builder != nil
  query += "node" + filter + "(#{area_identifier});\n"
  query += "way" + filter + "(#{area_identifier});\n"
  query += "relation" + filter + "(#{area_identifier});\n"
  query += builder.query_footer()
  return query
end

def area_identifier_builder_by_name(name)
  return "area[name='" + name + "']->.searchArea;\n"
end

def area_identifier_by_name(name)
  return 'area.searchArea'
end

def query_text_by_name(name, expand)
  area_identifier = area_identifier_by_name(name)
  area_identifier_builder = area_identifier_builder_by_name(name)
  query_text(area_identifier_builder, area_identifier, expand)
end

def graticule_bbox(lower_lat, left_lon)
  return "#{lower_lat},#{left_lon},#{lower_lat+1},#{left_lon+1}"
end

def query_text_by_graticule(lower_lat, left_lon, expand)
  area_identifier_builder = nil
  area_identifier = graticule_bbox(lower_lat, left_lon)
  query_text(area_identifier_builder, area_identifier, expand)
end

def what_is_downloaded_to_text(expand)
  returned = ""
  returned += "_without_geometry" if expand == false
  return returned
end

def produced_filename_by_name(name, expand)
  filename = name
  filename += what_is_downloaded_to_text(expand)
  filename += ".osm"
  return download_location+"/"+filename
end

def produced_filename_by_graticule(lower_lat, left_lon, expand)
  filename = "#{lower_lat}, #{left_lon}"
  filename += what_is_downloaded_to_text(expand)
  filename += ".osm"
  return download_location+"/"+filename
end

def is_download_necessary_by_name(name, expand)
  filename = produced_filename_by_name(name, expand)
  return !File.exists?(filename)
end

def is_download_necessary_by_graticule(lower_lat, left_lon, expand)
  filename = produced_filename_by_graticule(lower_lat, left_lon, expand)
  return !File.exists?(filename)
end

def download_graticule(lower_lat, left_lon)
  expand = true
  query = query_text_by_graticule(lower_lat, left_lon, expand) 
  filename = produced_filename_by_graticule(lower_lat, left_lon, expand)
  return true if !is_download_necessary_by_graticule(lower_lat, left_lon, expand)
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

def download_by_name(name, expand)
  query = query_text_by_name(name, expand)
  filename = produced_filename_by_name(name, expand)
  return true if !is_download_necessary_by_name(name, expand)
  return download(query, filename)
end

main