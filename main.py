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

def execute(search_terms, search_period=7, api_key=None):

    config = load_yaml('./config_ext.yaml')

    api_key =  config['api_key']

    if api_key is not None:
        YOUTUBE_API_KEY = api_key
    else:
        YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
        if YOUTUBE_API_KEY is None:
            result = "Missing Credentials"
            raise Exception(result)

    start_date_string = vf.get_start_date_string(search_period)
    try:
        result = vf.search_each_term(search_terms, YOUTUBE_API_KEY, start_date_string)
    except Exception as e:
        logging.error(e)

    return result

def main(request):
    if request.args and 'search_terms' in request.args:
        video_count = 5
        search_terms = request.args.get('search_terms').split('|')

        if 'search_period' in request.args:
            try:
                search_period = int(request.args.get('search_period'))
            except Exception as e:
                logging.warning(f'Unable to cast search_period as int. {e} \ Using default search_period')
        if 'video_count' in request.args:
            try:
                video_count = int(request.args.get('video_count'))
            except Exception as e:
                logging.warning(f'Problem with video_count parameter. Using default')

        search = execute(search_terms, search_period)
        result = search['top_videos'][:video_count].to_html()
    else:
        result = "Missing search_terms parameter"
    return result

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Defining search parameters')
    parser.add_argument('search_terms', type=str, nargs='+',
                        help='The terms to query. Can be multiple.')
    parser.add_argument('--search-period', type=int, default=7,
                        help='The number of days to search for.')
    args = parser.parse_args()

    execute(args.search_terms, args.search_period)
