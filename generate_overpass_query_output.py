import argparse
import common

def parsed_args():
    parser = argparse.ArgumentParser(description='Production of webpage about validation of wikipedia tag in osm data.')
    parser.add_argument('-file', '-f', dest='file', type=str, help='name of yaml file produced by validator')
    args = parser.parse_args()
    if not (args.file):
        parser.error('Provide .osm file')
    return args

def main():
    args = parsed_args()
    print(common.get_query(filename = args.file, printed_error_ids = ['wikipedia tag links to 404'], format = "maproulette"))

if __name__ == '__main__':
    main()
