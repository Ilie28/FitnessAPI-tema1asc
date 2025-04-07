from app import webserver
from flask import request, jsonify

import os
import json

def make_job(func):
    return lambda: {"result": func()}


# Example endpoint definition
@webserver.route('/api/post_endpoint', methods=['POST'])
def post_endpoint():
    if request.method == 'POST':
        # Assuming the request contains JSON data
        data = request.json
        print(f"got data in post {data}")

        # Process the received data
        # For demonstration purposes, just echoing back the received data
        response = {"message": "Received data successfully", "data": data}

        # Sending back a JSON response
        return jsonify(response)
    else:
        # Method Not Allowed
        return jsonify({"error": "Method not allowed"}), 405

@webserver.route('/api/get_results/<job_id>', methods=['GET'])
def get_response(job_id):
    status = webserver.tasks_runner.get_status(job_id)
    if status == "invalid":
        return jsonify({"status": "error", "reason": "Invalid job_id"}), 404
    elif status == "running":
        return jsonify({"status": "running"})
    else:
        try:
            with open(f"results/{job_id}.json") as f:
                result = json.load(f)
            # Se returnează direct rezultatul job‑ului
            return jsonify({"status": "done", "data": result["result"]})
        except:
            return jsonify({"status": "error", "reason": "Result file not found"}), 200


@webserver.route('/api/states_mean', methods=['POST'])
def states_mean_request():
    data = request.json
    question = data.get("question")
    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        # Returnăm direct dicţionarul de medii pe state
        return webserver.data_ingestor.get_states_mean(question)

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    webserver.logger.info(f"Received request for states_mean: {question} => {job_id}")
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/state_mean', methods=['POST'])
def state_mean_request():
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
    webserver.logger.info(f"Received request for state_mean: {question} + {state} => {job_id}")
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/best5', methods=['POST'])
def best5_request():
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
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/worst5', methods=['POST'])
def worst5_request():
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
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/global_mean', methods=['POST'])
def global_mean_request():
    data = request.json
    question = data.get("question")
    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        value = webserver.data_ingestor.get_global_mean(question)
        return {"status": "done", "data": value}

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/diff_from_mean', methods=['POST'])
def diff_from_mean_request():
    data = request.json
    question = data.get("question")
    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        global_mean = webserver.data_ingestor.get_global_mean(question)
        states_mean = webserver.data_ingestor.get_states_mean(question)
        diff = {state: round(global_mean - mean, 3) for state, mean in states_mean.items()}
        return diff

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/state_diff_from_mean', methods=['POST'])
def state_diff_from_mean_request():
    data = request.json
    question = data.get("question")
    state = data.get("state")
    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        global_mean = webserver.data_ingestor.get_global_mean(question)
        state_mean = webserver.data_ingestor.get_state_mean(question, state)
        diff = round(global_mean - state_mean, 3)
        return {state: diff}

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/mean_by_category', methods=['POST'])
def mean_by_category_request():
    data = request.json
    question = data.get("question")
    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        result = webserver.data_ingestor.get_mean_by_category(question)
        return {"status": "done", "data": result}

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/state_mean_by_category', methods=['POST'])
def state_mean_by_category_request():
    data = request.json
    question = data.get("question")
    state = data.get("state")
    job_id = f"job_id_{webserver.job_counter}"
    webserver.job_counter += 1

    def job():
        result = webserver.data_ingestor.get_mean_by_category(question, state=state)
        return {"status": "done", "data": result}

    res = webserver.tasks_runner.add_task(job_id, job)
    if res == -1:
        return jsonify({"status": "error", "reason": "shutting down"}), 405
    return jsonify({"status": "running", "job_id": job_id})


@webserver.route('/api/graceful_shutdown', methods=['GET'])
def graceful_shutdown():
    webserver.tasks_runner.graceful_shutdown()
    if webserver.tasks_runner.pending_jobs() > 0:
        return jsonify({"status": "running"})
    else:
        return jsonify({"status": "done"})


@webserver.route('/api/jobs', methods=['GET'])
def all_jobs():
    status_dict = webserver.tasks_runner.all_jobs()
    result = [{"job_id": job_id, "status": status} for job_id, status in status_dict.items()]
    return jsonify({"status": "done", "data": result})


@webserver.route('/api/num_jobs', methods=['GET'])
def num_jobs():
    pending = webserver.tasks_runner.pending_jobs()
    return jsonify({"status": "done", "jobs_left": pending})


# You can check localhost in your browser to see what this displays
@webserver.route('/')
@webserver.route('/index')
def index():
    routes = get_defined_routes()
    msg = f"Hello, World!\n Interact with the webserver using one of the defined routes:\n"

    # Display each route as a separate HTML <p> tag
    paragraphs = ""
    for route in routes:
        paragraphs += f"<p>{route}</p>"

    msg += paragraphs
    return msg

def get_defined_routes():
    routes = []
    for rule in webserver.url_map.iter_rules():
        methods = ', '.join(rule.methods)
        routes.append(f"Endpoint: \"{rule}\" Methods: \"{methods}\"")
    return routes
