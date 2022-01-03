import logging
import logging.config

import yaml


def get_logger(name):
    with open('logging_config.yaml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    return logging.getLogger(name)
