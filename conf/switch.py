import os

env = os.getenv('ENV', 'local')

if env == 'prod':
    from conf.prod import *
else:
    from conf.local import *