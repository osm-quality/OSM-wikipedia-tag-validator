require 'yaml'
require_relative 'download_shared'
require 'fileutils'

def main()
  raise "missing #{download_location} folder" unless Dir.exist?(download_location)
  #download_by_wikidata("Q42424277")
  unprocessed_suffix = "_unprocessed"
  reload_suffix = "_reloaded"
  download_defined_regions(unprocessed_suffix)
  download_defined_regions_from_reload_queries(reload_suffix)
  copy_files_into_positions_expected_by_processing_script(unprocessed_suffix, reload_suffix)
end

def copy_files_into_positions_expected_by_processing_script(unprocessed_suffix, reload_suffix, debug=false)
  region_data.each do |region|
      area_name = region['region_name']
      expand = true
      unprocessed_data = produced_filename_by_name(area_name, expand, unprocessed_suffix)
      reload_data = produced_filename_by_name(area_name, expand, reload_suffix)
      used_data = produced_filename_by_name(area_name, expand, "")
      if File.exists?(reload_data)
        puts "copying reloaded file as source for #{area_name}"
        puts "(<\"#{reload_data}\"> -> <\"#{used_data}\">)" if debug
        FileUtils.cp(reload_data, used_data)
      elsif File.exists?(unprocessed_data)
        puts "copying unprocessed file with all as source for #{area_name}"
        puts "(<\"#{unprocessed_data}\"> -> <\"#{used_data}\">)" if debug
        FileUtils.cp(unprocessed_data, used_data)
      else
        raise "either #{reload_data} or #{unprocessed_data} file must exists!"
      end

      if File.exists?(used_data) == false
        raise "copying failed, #{used_data} was supposed to exist!"
      end
  end
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

def region_data
  return YAML.load_file('regions_processed.yaml')
end

def download_defined_regions_from_reload_queries(suffix)
  region_data.each do |region|
    while true
      area_name = region['region_name']
      downloaded_filename = produced_filename_by_name(area_name, true, suffix)
      query_filepath = get_query_filename_for_reload_of_file(area_name)
      if !File.exists?(query_filepath)
        puts "query file #{query_filepath} is not existing"
        break
      end
      puts
      puts "downloading reload query for #{area_name}"
      if File.exists?(downloaded_filename)
        f = File.new(downloaded_filename)
        download_timestamp = f.mtime.to_i
        f.close
        f = File.new(query_filepath)
        query_timestamp = f.mtime.to_i
        f.close
        break if download_timestamp > query_timestamp
        File.delete(downloaded_filename)
      end
      result = run_query_from_file(query_filepath, downloaded_filename)
      if !result
        puts "failed download with query from #{query_filepath}, after an additional pause download will be retried until it succeeds"
        sleep 500
      end
      sleep 150 # 300 and 200 was working well if it was a sole overpass load
      break if result
    end
  end
end

def download_defined_regions(suffix)
  region_data.each do |region|
    while true
      name = region['region_name']
      break if !is_download_necessary_by_name(name, true, suffix)
      result = download_by_name(name, true, suffix)
      if !result
        puts "failed download, after an additional pause download will be retried until it succeeds"
        sleep 500
      end
      sleep 150 # 300 and 200 was working well if it was a sole overpass load
      break if result
    end
  end
end

def cache_location
  return File.read('cache_location.config')
end

def download_location()
  return cache_location() + "/" + "downloaded_osm_data"
end

def reload_queries_location()
  return cache_location() + "/" + "reload_queries"
end

def get_query_filename_for_reload_of_file(area_name)
  return reload_queries_location() + "/" + area_name + ".query"
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

def what_is_downloaded_to_text(expand)
  returned = ""
  returned += "_without_geometry" if expand == false
  return returned
end

def produced_filename_by_name(name, expand, suffix)
  filename = name
  filename += what_is_downloaded_to_text(expand)
  filename += "#{suffix}.osm"
  return download_location+"/"+filename
end

def is_download_necessary_by_name(name, expand, suffix)
  filename = produced_filename_by_name(name, expand, suffix)
  return !File.exists?(filename)
end

def download_by_name(name, expand, suffix)
  query = query_text_by_name(name, expand)
  filename = produced_filename_by_name(name, expand, suffix)
  return true if !is_download_necessary_by_name(name, expand, suffix)
  return download_and_save(query, filename)
end

main