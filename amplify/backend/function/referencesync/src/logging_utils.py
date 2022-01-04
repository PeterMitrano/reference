import logging
import logging.config
import os

import yaml


def get_logger(name):
    if os.path.exists('logging_config.yaml'):
        with open('logging_config.yaml', 'r') as f:
            config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)
    return logging.getLogger(name)
