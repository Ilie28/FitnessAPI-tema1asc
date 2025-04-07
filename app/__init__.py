"""Initializarea aplicatiei Flask si configurarea componentelor"""
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from threading import Lock
from flask import Flask
from app.data_ingestor import DataIngestor
from app.task_runner import ThreadPool

if not os.path.exists('results'):
    os.mkdir('results')

# Configurare logging
logger = logging.getLogger("webserver")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("webserver.log", maxBytes=10_000_000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# UTC logging
logging.Formatter.converter = time.gmtime

# Flask app
webserver = Flask(__name__)
webserver.logger = logger

# CSV load
webserver.data_ingestor = DataIngestor("./nutrition_activity_obesity_usa_subset.csv")

# Init thread pool with logger and data_ingestor
webserver.tasks_runner = ThreadPool(webserver.logger, webserver.data_ingestor)

# Job counter
webserver.job_counter = 1
webserver.job_lock = Lock()

from app import routes
