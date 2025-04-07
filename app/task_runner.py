"""Modul pentru gestionarea executiei in paralel a task-urilor folosind un thread pool"""
import os
import json
from threading import Thread, Event
from queue import Queue, Empty
import multiprocessing

class ThreadPool:
    """Gestioneaza un grup de thread-uri care executa in paralel taskurile"""
    def __init__(self, logger, data_ingestor):
        """Initializeaza thread pool-ul si porneste thread-urile de lucru"""
        self.logger = logger
        self.data_ingestor = data_ingestor
        self.tasks = Queue()
        self.shutdown_event = Event()
        self.job_status = {}
        self.num_threads = int(os.environ.get("TP_NUM_OF_THREADS", multiprocessing.cpu_count()))
        self.workers = []

        for _ in range(self.num_threads):
            worker = TaskRunner(
                self.tasks,
                self.job_status,
                self.shutdown_event,
                logger,
                data_ingestor
            )
            self.workers.append(worker)
            worker.start()
        self.logger.info(f"Thread pool initialized with {self.num_threads} threads.")

    def add_task(self, job_id, func):
        """Adauga un task nou in coada daca serverul nu este in shutdown."""
        if self.shutdown_event.is_set():
            return -1
        self.job_status[job_id] = "running"
        self.tasks.put((job_id, func))
        return job_id

    def graceful_shutdown(self):
        """Porneste inchiderea controlata a thread pool-ului"""
        self.shutdown_event.set()

    def get_status(self, job_id):
        """Returneaza statusul unui job dupa ID"""
        return self.job_status.get(job_id, "invalid")

    def all_jobs(self):
        """Returneaza toate job-urile"""
        return self.job_status

    def pending_jobs(self):
        """Returneaza numarul de job-uri care sunt inca in executie"""
        return sum(1 for status in self.job_status.values() if status == "running")

class TaskRunner(Thread):
    """Thread care preia task-uri din coada si le executa"""
    def __init__(self, tasks, job_status, shutdown_event, logger, data_ingestor):
        """Initializeaza un thread cu resursele necesare pentru a rula task-uri"""
        super().__init__(daemon=True)
        self.tasks = tasks
        self.job_status = job_status
        self.shutdown_event = shutdown_event
        self.logger = logger
        self.data_ingestor = data_ingestor

    def run(self):
        """Executa task-urile din coada pana cand este initiat shutdown-ul"""
        while not self.shutdown_event.is_set() or not self.tasks.empty():
            job_id = None
            try:
                job_id, func = self.tasks.get(timeout=1)
                result = func()
                os.makedirs("results", exist_ok=True)
                with open(f"results/{job_id}.json", "w", encoding="utf-8") as f:
                    json.dump({"result": result}, f)
                self.job_status[job_id] = "done"
                self.logger.info(f"{job_id} finished and saved to disk.")
            except Empty:
                continue
            except (ValueError, IOError) as e:
                if job_id:
                    self.job_status[job_id] = "error"
                    self.logger.error(f"Error in job {job_id}: {e}")
                else:
                    self.logger.error(f"Thread error before getting job_id: {e}")
