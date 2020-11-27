"""
This module imports and calls the function to execute the API call
and print results to the console.
"""

import os
import yaml
import video_finder as vf
import argparse
import logging

def load_yaml(filepath):
    """Import YAML config file."""
    with open(filepath, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logging.error(exc)

def main(search_terms, search_period, api_key=None):

    config = load_yaml('./config_ext.yaml')

    api_key =  config['api_key']

    if api_key is not None:
        YOUTUBE_API_KEY = api_key
    else:
        YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
        if YOUTUBE_API_KEY is None:
            raise Exception("Missing Credentials")

    start_date_string = vf.get_start_date_string(search_period)
    try:
        vf.search_each_term(search_terms, YOUTUBE_API_KEY, start_date_string)
    except Exception as e:
        logging.error(e)

    return

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Defining search parameters')
    parser.add_argument('search_terms', type=str, nargs='+',
                        help='The terms to query. Can be multiple.')
    parser.add_argument('--search-period', type=int, default=7,
                        help='The number of days to search for.')
    args = parser.parse_args()

    main(args.search_terms, args.search_period)
