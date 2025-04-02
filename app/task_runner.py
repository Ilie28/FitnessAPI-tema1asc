import os
import json
import logging
from queue import Queue, Empty
from threading import Thread, Event
from app.data_ingestor import DataIngestor

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
logger.addHandler(ch)

class ThreadPool:
    def __init__(self):
        # You must implement a ThreadPool of TaskRunners
        # Your ThreadPool should check if an environment variable TP_NUM_OF_THREADS is defined
        # If the env var is defined, that is the number of threads to be used by the thread pool
        # Otherwise, you are to use what the hardware concurrency allows
        # You are free to write your implementation as you see fit, but
        # You must NOT:
        #   * create more threads than the hardware concurrency allows
        #   * recreate threads for each task
        # Note: the TP_NUM_OF_THREADS env var will be defined by the checker

        self.tasks = Queue()
        self.workers = []
        self.job_status = {}
        self.graceful_shutdown = Event()

        num_threads = int(os.getenv("TP_NUM_OF_THREADS", multiprocessing.cpu_count()))
        self.num_threads = max(1, min(num_threads, multiprocessing.cpu_count()))

        self.data_ingestor = DataIngestor("./nutrition_activity_obesity_usa_subset.csv")
        self.logger = logger if logger else logging.getLogger(__name__)

        self.logger.info(f"ThreadPool has been initialised with: {self.num_threads} threads")

        for i in range(self.num_threads):
            worker = TaskRunner(self)
            worker.start()
            self.workers.append(worker)
            self.logger.info(f"Thread {i} has been started")
        
    def shutdown(self):
        if not self.graceful_shutdown.is_set():
            self.graceful_shutdown.set()
            self.logger.info("ThreadPool is shutting down")
            for _ in self.workers:
                self.tasks.put((None, None))

            # Așteptăm să se termine toate joburile
            for w in self.workers:
                w.join()

            self.logger.info("Thread pool has been shut down.")
        else:
            self.logger.warning("ThreadPool is already shutting down.")
    
    def add_task(self, job_id, closure):
        self.job_status[job_id] = "running"
        self.tasks.put((job_id, closure))
        self.logger.info(f"Task {job_id} has been added to the queue")

    def get_status(self, job_id):
        return self.job_status.get(job_id, "invalid")
    
    def get_all_jobs(self):
        return self.job_status


class TaskRunner(Thread):
    def __init__(self, pool):
        super().__init__()
        self.pool = pool

    def run(self):
        """
        Intrăm într-un loop atâta timp cât ThreadPool-ul nu e închis (sau mai există joburi).
        """
        while True:
            # Dacă s-a dat shutdown și coada e goală, worker-ul poate ieși
            if self.pool.graceful_shutdown.is_set() and self.pool.tasks.empty():
                break

            try:
                job_id, closure = self.pool.tasks.get(timeout=0.5)
            except Empty:
                # Nu am job în coadă, mai verificăm dacă e cazul să ieșim
                continue

            if job_id is None and closure is None:
                # „Sentinelă” explicită de terminare.
                break

            # Executăm efectiv job-ul
            try:
                result = closure()
                # Salvăm rezultatul în results/<job_id>.json
                with open(f"results/{job_id}.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                self.pool.job_status[job_id] = "done"
            except Exception as e:
                logger.exception(f"Exception in job {job_id}: {e}")
                self.pool.job_status[job_id] = "error"
            finally:
                self.pool.tasks.task_done()
