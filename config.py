#!/usr/bin/python
import os
from configparser import ConfigParser

def config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = os.getenv(param[1])
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db