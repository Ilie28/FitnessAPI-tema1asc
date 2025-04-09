"""Initializarea aplicatiei Flask si configurarea componentelor"""
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from app.data_ingestor import DataIngestor
from app.task_runner import ThreadPool

if not os.path.exists('results'):
    os.mkdir('results')

# Configurarea logging ului
logger = logging.getLogger("webserver")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("webserver.log", maxBytes=10_000_000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# timestamp in format utc/gmt
logging.Formatter.converter = time.gmtime

# Aplicatia Flask
webserver = Flask(__name__)
webserver.logger = logger
webserver.accept = True

# Fisierul CSV cu datele
webserver.data_ingestor = DataIngestor("./nutrition_activity_obesity_usa_subset.csv")

# Am initializat un pool de thread-uri pentru a rula task-urile in paralel
webserver.tasks_runner = ThreadPool(webserver.logger, webserver.data_ingestor)

# Retinem id ul job-ului curent
webserver.job_counter = 1

from app import routes
