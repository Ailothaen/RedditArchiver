# 3rd party modules
import yaml

# stdlib
import logging, os, sys
from logging.handlers import RotatingFileHandler


# Loading config
if os.path.isfile("config.yml"):
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)
        config["docker"] = False
elif os.path.isfile("config-docker.yml"):
    with open('config-docker.yml', 'r') as f:
        config = yaml.safe_load(f)
        config["docker"] = True
        config["paths"] = {}
        config["paths"]["output"] = "output"
else:
    print("No configuration file could be found. Check if a file config.yml or config-docker.yml (depending on your case; read the documentation) is present in the same directory as app.py, and if the current working directory is the same directory as app.py.", file=sys.stderr)
    raise SystemExit(1)


config['app']['version'] = "1.2.0"
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
