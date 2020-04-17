import logging

global LOGGER

if 'LOGGER' not in globals():
    LOGGER = logging.getLogger()
    LOGGER.addHandler(logging.StreamHandler())
    LOGGER.setLevel(logging.INFO)
