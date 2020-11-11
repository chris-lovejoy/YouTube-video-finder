"""This module imports and calls the main function."""

import yaml
import video_finder as vf

def load_yaml(filepath):
    """Import YAML config file."""
    with open(filepath, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
config = load_yaml('./config.yaml')

if __name__ == "__main__":
    start_date_string = vf.get_start_date_string(config['search_period_days'])
    vf.search_each_term(config['search_terms'], config['api_key'],\
                            start_date_string)
