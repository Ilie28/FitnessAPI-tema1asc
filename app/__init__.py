import os
from flask import Flask
from app.data_ingestor import DataIngestor
from app.task_runner import ThreadPool
from logging.handlers import RotatingFileHandler
import logging
import time

if not os.path.exists('results'):
    os.mkdir('results')

# Configure logging
logger = logging.getLogger("webserver")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("webserver.log", maxBytes=10_000_000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Set UTC logging
logging.Formatter.converter = time.gmtime

# Flask app
webserver = Flask(__name__)
webserver.logger = logger

# FIRST: load CSV
webserver.data_ingestor = DataIngestor("./nutrition_activity_obesity_usa_subset.csv")

# THEN: init thread pool with logger and data_ingestor
webserver.tasks_runner = ThreadPool(webserver.logger, webserver.data_ingestor)

# Job counter
webserver.job_counter = 1

from app import routes