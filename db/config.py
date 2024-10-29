import os
from configparser import ConfigParser

def config(filename='db/database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    db = {}
    if not parser.has_section(section):
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    params = parser.items(section)
    for param in params:
        db[param[0]] = os.getenv(param[1])
    return db