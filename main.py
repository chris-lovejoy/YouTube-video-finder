"""
This module imports and calls the function to execute the API call
and print results to the console.
"""

import yaml
import video_finder as vf
import argparse


def load_yaml(filepath):
    """Import YAML config file."""
    with open(filepath, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

def main(search_terms, search_period, api_key):

    start_date_string = vf.get_start_date_string(search_period)
    vf.search_each_term(search_terms, api_key, start_date_string)

    return

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Defining search parameters')
    parser.add_argument('search_terms', type=str, nargs='+',
                        help='The terms to query. Can be multiple.')
    parser.add_argument('--search-period', type=int, default=7,
                        help='The number of days to search for.')
    args = parser.parse_args()

    config = load_yaml('./config_ext.yaml')

    main(args.search_terms, args.search_period, config['api_key'])
