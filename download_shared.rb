require 'rest-client'
require 'etc'

def run_query_from_file(file_with_query, download_to_filepath)
  if File.exists?(download_to_filepath)
    return
  end
  if !File.exists?(file_with_query)
    puts(file_with_query + " is missing, skipping this download")
    return
  end
  query = File.read(file_with_query)
  download_and_save(query, download_to_filepath)
end

def user_agent
  "wikipedia/wikidata tag validator, operated by #{Etc.getlogin}, written by Mateusz Konieczny (matkoniecz@gmail.com)"
end

def timeout
  2550
end

def download_and_save(query, filepath)
  text = download(query)
  if text == nil
    return false
  end
  if File.exists?(filepath)
    puts "deleting old file: start"
    File.delete(filepath)
    puts "deleting old file: end"
  end
  puts "saving new file: start"
  f = File.new(filepath, "w")
  f.write text
  f.close
  puts "saving new file: end"
  return true
end

def download(query)
  puts query
  puts "downloading: start"
  url = "http://overpass-api.de/api/interpreter"
  start = Time.now.to_i
  begin
     return RestClient::Request.execute(
              :method => :post,
              :url => URI.escape(url),
              :timeout => timeout,
              :payload => {'data': query},
              )
  rescue RestClient::BadRequest => e
    puts url
    puts e
    return nil
  rescue RestClient::Exceptions::ReadTimeout => e
    puts "timeout after #{Time.now.to_i-start}s, requested timeout #{timeout}"
    return nil
  rescue RestClient::TooManyRequests => e
    puts "429 error"
    sleep 600
    return nil
  end
  puts "downloading: end"
end
