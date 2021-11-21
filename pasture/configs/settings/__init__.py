import os
from .base import *

env = os.getenv('ENV', 'develop')

if env == 'develop':
    from .develop import *
elif env == 'heroku':
    from .heroku import *
