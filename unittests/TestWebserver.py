import unittest
import time
from app import webserver
from app.data_ingestor import DataIngestor

class TestWebserver(unittest.TestCase):

    def setUp(self):
        self.client = webserver.test_client()
        self.ingestor = DataIngestor("nutrition_activity_obesity_usa_subset.csv")

    def get_result_data(self, job_id, timeout=5):
        """Verifica rezultatul periodic pana cand jobul este terminat"""
        for _ in range(int(timeout * 10)):  # verifica timp de max 5 secunde
            response = self.client.get(f"/api/get_results/{job_id}")
            result_data = response.get_json()
            if result_data["status"] == "done":
                return result_data["data"]
            time.sleep(0.1)  # asteapta 100ms
        self.fail("Job did not finish in expected time.")
    
    def test_get_results_endpoint(self):
        """Testare pentru endpointul /api/get_results/<job_id>"""
        # 1. Test job_id invalid
        response = self.client.get("/api/get_results/job_id_inexistent")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["status"], "error")

        # 2. Test job_id existent dar jobul e inca in executie
        response = self.client.post("/api/global_mean", json={"question": "Percent of adults aged 18 years and older who have obesity"})
        job_id = response.get_json()["job_id"]

        check_response = self.client.get(f"/api/get_results/{job_id}")
        self.assertEqual(check_response.status_code, 200)
        self.assertIn(check_response.get_json()["status"], ["running", "done"])

    def test_post_endpoint(self):
        """Testare POST endpoint"""
        data = {"test_key": "test_value"}
        response = self.client.post('/api/post_endpoint', json=data)
        self.assertEqual(response.status_code, 200)
        resp_data = response.get_json()
        self.assertIn("data", resp_data)
        self.assertEqual(resp_data["data"], data)

    def test_states_mean(self):
        """Testare media pe state pentru o intrebare anume"""
        payload = {
            "question": "Percent of adults aged 18 years and older who have obesity"
        }
        expected = self.ingestor.get_states_mean(payload["question"])

        response = self.client.post("/api/states_mean", json=payload)
        job_id = response.get_json()["job_id"]
        result = self.get_result_data(job_id)
        self.assertEqual(result, expected)

    def test_state_mean(self):
        """Testare media pentru o intrebare anume si un stat specific"""
        payload = {
            "question": "Percent of adults aged 18 years and older who have obesity",
            "state": "Ohio"
        }
        expected = {payload["state"]: self.ingestor.get_state_mean(**payload)}

        response = self.client.post("/api/state_mean", json=payload)
        job_id = response.get_json()["job_id"]
        result = self.get_result_data(job_id)
        self.assertEqual(result, expected)

    def test_global_mean(self):
        """Testare media globala pentru o intrebare anume"""
        payload = {
            "question": "Percent of adults aged 18 years and older who have obesity"
        }
        expected = {"global_mean": self.ingestor.get_global_mean(payload["question"])}

        response = self.client.post("/api/global_mean", json=payload)
        job_id = response.get_json()["job_id"]
        result = self.get_result_data(job_id)
        self.assertEqual(result, expected)

    def test_diff_from_mean(self):
        """Testare diferenta fata de media globala pentru o intrebare anume"""
        question = "Percent of adults aged 18 years and older who have obesity"
        global_mean = self.ingestor.get_global_mean(question)
        states_mean = self.ingestor.get_states_mean(question)
        expected = {
            state: round(global_mean - val, 3)
            for state, val in states_mean.items()
        }

        response = self.client.post("/api/diff_from_mean", json={"question": question})
        job_id = response.get_json()["job_id"]
        result = self.get_result_data(job_id)
        self.assertEqual(result, expected)

    def test_state_diff_from_mean(self):
        """Testare diferenta fata de media globala pentru o intrebare anume si un stat specific"""
        payload = {
            "question": "Percent of adults aged 18 years and older who have obesity",
            "state": "Ohio"
        }
        global_mean = self.ingestor.get_global_mean(payload["question"])
        state_mean = self.ingestor.get_state_mean(**payload)
        expected = {payload["state"]: round(global_mean - state_mean, 3)}

        response = self.client.post("/api/state_diff_from_mean", json=payload)
        job_id = response.get_json()["job_id"]
        result = self.get_result_data(job_id)
        self.assertEqual(result, expected)

    def test_best5(self):
        """Testare cele mai bune 5 state pentru o intrebare anume"""
        question = "Percent of adults aged 18 years and older who have obesity"
        states_mean = self.ingestor.get_states_mean(question)
        expected = dict(sorted(states_mean.items(), key=lambda x: x[1])[:5])

        response = self.client.post("/api/best5", json={"question": question})
        job_id = response.get_json()["job_id"]
        result = self.get_result_data(job_id)
        self.assertEqual(result, expected)

    def test_worst5(self):
        """Testare cele mai proaste 5 state pentru o intrebare anume"""
        question = "Percent of adults aged 18 years and older who have obesity"
        states_mean = self.ingestor.get_states_mean(question)
        expected = dict(sorted(states_mean.items(), key=lambda x: x[1], reverse=True)[:5])

        response = self.client.post("/api/worst5", json={"question": question})
        job_id = response.get_json()["job_id"]
        result = self.get_result_data(job_id)
        self.assertEqual(result, expected)

    def test_mean_by_category(self):
        question = "Percent of adults aged 18 years and older who have obesity"
        expected = self.ingestor.get_mean_by_category(question)

        response = self.client.post("/api/mean_by_category", json={"question": question})
        job_id = response.get_json()["job_id"]
        result = self.get_result_data(job_id)
        self.assertEqual(result, expected)

    def test_state_mean_by_category(self):
        """Testare media pe categorii de stratificare pentru o intrebare anume si un stat specific"""
        payload = {
            "question": "Percent of adults aged 18 years and older who have obesity",
            "state": "Ohio"
        }
        expected = self.ingestor.get_mean_by_category(**payload)

        response = self.client.post("/api/state_mean_by_category", json=payload)
        job_id = response.get_json()["job_id"]
        result = self.get_result_data(job_id)
        self.assertEqual(result, expected)

    def test_all_jobs(self):
        """Testare GET pentru lista tuturor joburilor"""
        response = self.client.get("/api/jobs")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn("data", json_data)
        self.assertIsInstance(json_data["data"], list)

    def test_num_jobs(self):
        """Testare GET pentru numarul de joburi in asteptare"""
        response = self.client.get("/api/num_jobs")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn("jobs_left", json_data)
        self.assertIsInstance(json_data["jobs_left"], int)

    def test_index(self):
        """Testare pagina de start"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Interact with the webserver", response.get_data(as_text=True))

    def test_z_graceful_shutdown(self):
        """Testare inchidere controlata a serverului"""
        response = self.client.get("/api/graceful_shutdown")
        data = response.get_json()
        self.assertIn("status", data)
        self.assertIn(data["status"], ["done", "running"])

if __name__ == "__main__":
    unittest.main()