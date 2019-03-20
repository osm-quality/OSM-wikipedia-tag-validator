require 'yaml'

def main()
  #download_by_wikidata("Q42424277")

  filepath = download_location+"/"+'teryt_simc.osm'
  if !File.exists?(filepath)
    name = "Polska"
    area_identifier = area_identifier_by_name(name)
    area_identifier_builder = area_identifier_builder_by_name(name)
    query = filtered_query_text("['teryt:simc']", area_identifier_builder, area_identifier, false)
    download_and_save(query, filepath)
  end

  filepath = download_location+"/"+'namepl_krk.osm'
  if !File.exists?(filepath)
    name = "Kraków"
    area_identifier = area_identifier_by_name(name)
    area_identifier_builder = area_identifier_builder_by_name(name)
    query = filtered_query_text("['name']['name:pl'!~'.*']", area_identifier_builder, area_identifier, false)
    download_and_save(query, filepath)
  end

  target_file = download_location+"/"+'reloaded_Poland.osm'
  file_with_query = download_location+'/reload_querries/reload_Poland.query'
  run_query_from_file(file_with_query, target_file)

  download_defined_regions

  download_graticules

end

def download_by_wikidata(wikidata)
  query = '[timeout:25];
(
  node["wikidata"="' + wikidata + '"];
  way["wikidata"="' + wikidata + '"];
  relation["wikidata"="' + wikidata + '"];
);
out body;
>;
out skel qt;'
  download_and_save(query, download_location+"/"+"test_case.osm")
end

def download_defined_regions
  region_data = YAML.load_file('regions_processed.yaml')
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

def download_graticules
  # around Poland - for making map that shows how nicely stuff was fixed in Poland (TODO - make that map)
  for lat in 48..55
    for lon in 14..24
      download_graticule(lat, lon)
    end
  end
end

def download_location
  return File.read('cache_location.config')
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
  return download_and_save(query, filename)
end

def download_by_name(name, expand)
  query = query_text_by_name(name, expand)
  filename = produced_filename_by_name(name, expand)
  return true if !is_download_necessary_by_name(name, expand)
  return download_and_save(query, filename)
end

main