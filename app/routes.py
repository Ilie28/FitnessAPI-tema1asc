"""Definirea rutelor API pentru serverul de fitness."""
import json
from flask import request, jsonify
from app import webserver

@webserver.route('/api/post_endpoint', methods=['POST'])
def post_endpoint():
    """Proceseaza o cerere POST si returneaza datele primite ca raspuns JSON"""
    if request.method == 'POST':
        # Assuming the request contains JSON data
        data = request.json
        print(f"got data in post {data}")

        # Process the received data
        # For demonstration purposes, just echoing back the received data
        response = {"message": "Received data successfully", "data": data}

        # Sending back a JSON response
        return jsonify(response)
    # Method Not Allowed
    return jsonify({"error": "Method not allowed"}), 405


@webserver.route('/api/get_results/<job_id>', methods=['GET'])
def get_response(job_id):
    """Returneaza rezultatul unui job pe baza ID-ului"""
    status = webserver.tasks_runner.get_status(job_id)
    if status == "invalid":
        return jsonify({"status": "error", "reason": "Invalid job_id"}), 404
    if status == "running":
        return jsonify({"status": "running"})
    try:
        with open(f"results/{job_id}.json", encoding="utf-8") as f:
            result = json.load(f)
        return jsonify({"status": "done", "data": result["result"]})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"status": "error", "reason": "Result file not found"}), 200


@webserver.route('/api/states_mean', methods=['POST'])
def states_mean_request():
    """Initiaza un job pentru calcularea mediei valorilor pe fiecare stat"""
    if not webserver.accept:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    
    data = request.json
    question = data.get("question")

    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        return webserver.data_ingestor.get_states_mean(question)

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    webserver.logger.info("Received request for states_mean: %s => %s", question, job_id)
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/state_mean', methods=['POST'])
def state_mean_request():
    """Calcularea mediei valorii pentru un stat si o intrebare specificata"""
    if not webserver.accept:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    
    data = request.json
    question = data.get("question")
    state = data.get("state")

    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        mean = webserver.data_ingestor.get_state_mean(question, state)
        return {state: mean}

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    webserver.logger.info("Received request for state_mean: %s + %s => %s", question, state, job_id)
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/best5', methods=['POST'])
def best5_request():
    """Returneaza cele mai bine cotate 5 state pentru o intrebare"""
    if not webserver.accept:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    
    data = request.json
    question = data.get("question")

    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        state_means = webserver.data_ingestor.get_states_mean(question)
        if question in webserver.data_ingestor.questions_best_is_min:
            best = dict(sorted(state_means.items(), key=lambda item: item[1])[:5])
        else:
            best = dict(sorted(state_means.items(), key=lambda item: item[1], reverse=True)[:5])
        return best

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    webserver.logger.info("Received request for best5: %s => %s", question, job_id)
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/worst5', methods=['POST'])
def worst5_request():
    """Returneaza cele mai prost cotate 5 state pentru o intrebare"""
    if not webserver.accept:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    
    data = request.json
    question = data.get("question")

    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        state_means = webserver.data_ingestor.get_states_mean(question)
        if question in webserver.data_ingestor.questions_best_is_min:
            worst = dict(sorted(state_means.items(), key=lambda item: item[1], reverse=True)[:5])
        else:
            worst = dict(sorted(state_means.items(), key=lambda item: item[1])[:5])
        return worst

    res = webserver.tasks_runner.add_task(job_id, job)

    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    webserver.logger.info("Received request for worst5: %s => %s", question, job_id)
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/global_mean', methods=['POST'])
def global_mean_request():
    """Returneaza media globala pentru o intrebare"""
    if not webserver.accept:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    
    data = request.json
    question = data.get("question")

    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        value = webserver.data_ingestor.get_global_mean(question)
        return {"global_mean": value}

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/diff_from_mean', methods=['POST'])
def diff_from_mean_request():
    """Returneaza diferenta dintre media globala si media pe state"""
    if not webserver.accept:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    
    data = request.json
    question = data.get("question")

    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        global_mean = webserver.data_ingestor.get_global_mean(question)
        states_mean = webserver.data_ingestor.get_states_mean(question)

        diff = {}
        for state, state_mean in states_mean.items():
            difference = round(global_mean - state_mean, 3)
            diff[state] = difference

        return diff

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    webserver.logger.info("Received request for diff_from_mean: %s => %s", question, job_id)
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/state_diff_from_mean', methods=['POST'])
def state_diff_from_mean_request():
    """Returneaza diferenta dintre media globala si media unui stat dat"""
    if not webserver.accept:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    
    data = request.json
    question = data.get("question")
    state = data.get("state")

    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        global_mean = webserver.data_ingestor.get_global_mean(question)
        state_mean = webserver.data_ingestor.get_state_mean(question, state)
        diff = round(global_mean - state_mean, 3)
        result = {state: diff}

        return result

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    webserver.logger.info(
        "Received request for state_diff_from_mean: %s + %s => %s",
        question, state, job_id
    )
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/mean_by_category', methods=['POST'])
def mean_by_category_request():
    """Returneaza media valorilor grupate pe categorie pentru o intrebare"""
    if not webserver.accept:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    
    data = request.json
    question = data.get("question")

    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        return webserver.data_ingestor.get_mean_by_category(question)

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    webserver.logger.info("Received request for mean_by_category: %s => %s", question, job_id)
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/state_mean_by_category', methods=['POST'])
def state_mean_by_category_request():
    """Returneaza media valorilor grupate pe categorie pentru un stat si o intrebare"""
    if not webserver.accept:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    
    data = request.json
    question = data.get("question")
    state = data.get("state")

    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        return webserver.data_ingestor.get_mean_by_category(question, state=state)

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    webserver.logger.info(
        "Received request for state_mean_by_category: %s + %s => %s",
        question, state, job_id
    )
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/graceful_shutdown', methods=['GET'])
def graceful_shutdown():
    """Initiaza oprirea controlata a serv dupa finalizarea joburilor in curs"""
    webserver.tasks_runner.graceful_shutdown()
    webserver.accept = False
    if webserver.tasks_runner.pending_jobs() > 0:
        return jsonify({"status": "running"})
    webserver.logger.info("Server is shutting down gracefully.")
    return jsonify({"status": "done"})


@webserver.route('/api/jobs', methods=['GET'])
def all_jobs():
    """Returneaza lista tuturor joburilor si statusul lor"""
    jobs = webserver.tasks_runner.all_jobs()
    result = list(map(lambda item: {"job_id": item[0], "status": item[1]}, jobs.items()))
    webserver.logger.info("Received request for all jobs")
    return jsonify({"status": "done", "data": result})


@webserver.route('/api/num_jobs', methods=['GET'])
def num_jobs():
    """Returneaza numarul de joburi care sunt inca in executie"""
    pending = webserver.tasks_runner.pending_jobs()
    webserver.logger.info("Received request for pending jobs")
    return jsonify({"status": "done", "jobs_left": pending})

@webserver.route('/')
@webserver.route('/index')
def index():
    """Returneaza lista tuturor rutelor disponibile in API"""
    routes = get_defined_routes()
    msg = "Hello, World!\n Interact with the webserver using one of the defined routes:\n"

    paragraphs = ""
    for route in routes:
        paragraphs = ''.join(f"<p>{route}</p>" for route in routes)

    msg += paragraphs
    return msg

def get_defined_routes():
    """Returneaza toate rutele definite in aplicatie impreuna cu metodele lor"""
    routes = []
    for rule in webserver.url_map.iter_rules():
        methods = ', '.join(rule.methods)
        routes.append(f"Endpoint: \"{rule}\" Methods: \"{methods}\"")
    return routes
