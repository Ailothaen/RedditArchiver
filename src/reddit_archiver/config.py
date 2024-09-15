# 3rd party modules
import yaml

# stdlib
import logging, sys
from logging.handlers import RotatingFileHandler


with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

config['app']['version'] = "1.1.0"
config['app']['project'] = "https://github.com/Ailothaen/RedditArchiver"
config['reddit']['agent'] = f"{config['app']['name']} v{config['app']['version']} (by u/ailothaen)"
config['runtime'] = {}
config['runtime']['average'] = 30

log = logging.getLogger('redditarchiver_main')
log.setLevel(logging.INFO) # Define minimum severity here
handler = RotatingFileHandler('./logs/main.log', maxBytes=1000000, backupCount=10) # Log file of 1 MB, 10 previous files kept
formatter = logging.Formatter('[%(asctime)s][%(module)s][%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S %z') # Custom line format and time format to include the module and delimit all of this well
handler.setFormatter(formatter)
log.addHandler(handler)
log.info("+----------------------------------------+")
log.info("|     ;;;;;                              |")
log.info("|     ;;;;;         R e d d i t          |")
log.info("|     ;;;;;       A r c h i v e r        |")
log.info("|   ..;;;;;..                            |")
log.info("|    ':::::'          v {}            |".format(config['app']['version']))
log.info("|      ':`                               |")
log.info("+----------------------------------------+")
python_version = sys.version.replace("\n", " ")
log.info(f"Python version: {python_version}")
log.debug("Config: {}".format(str(config)))
