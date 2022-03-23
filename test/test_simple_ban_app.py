from unittest import TestCase
from app import create_app, db
from config import TestConfig
from json import loads
from datetime import datetime

class MockedSMTPClient:
    def sendmail(self, sender, recipient, message):
        if sender != "simple_ban_app@python":
            raise ValueError("The sender is incorrect")
        
        if recipient != "test@domain.com":
            raise ValueError("The recipient is incorrect")
    
    def close(self):
        pass


class SimpleBanAppTestCase(TestCase):

    def setUp(self):
        app = create_app(TestConfig)
        app.config["SMTP_CLIENT"] = MockedSMTPClient()
        app.app_context().push()
        db.create_all()
        self.test_client = app.test_client()
    
    def test_get_num_square_success(self):
        response = self.test_client.get("/", query_string={"n": 5})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)["result"], 25)
    
    def test_get_num_square_failure_incorrect_argument(self):
        response = self.test_client.get("/", query_string={"x": 5})
        self.assertEqual(response.status_code, 400)
    
    def test_get_num_square_failure_more_than_one_argument(self):
        response = self.test_client.get("/", query_string={"x": 5, "n": 6})
        self.assertEqual(response.status_code, 400)
    
    def test_get_num_square_failure_no_arguments(self):
        response = self.test_client.get("/")
        self.assertEqual(response.status_code, 400)
    
    def test_get_num_square_failure_the_ip_is_banned(self):
        # Adding a new record to the blocklist table
        from app.models import BlockList
        record = BlockList(path="/", ip="127.0.0.1", timestamp=datetime.now())
        db.session.add(record)
        db.session.commit()
        # Making a request to the correct endpoint with banned IP to make sure that the access is forbidden
        response = self.test_client.get("/", query_string={"n": 5})
        self.assertEqual(response.status_code, 403)

    def test_ban_visitor_of_the_page_successfully_banned(self):
        response = self.test_client.get("/blacklisted")
        self.assertEqual(response.status_code, 444)
        # Making a request once again to make sure that the record with correct IP was created in the DB
        response = self.test_client.get("/blacklisted")
        self.assertEqual(response.status_code, 403)
    
    def test_healtcheck_available(self):
        response = self.test_client.get("/healthcheck")
        self.assertEqual(response.status_code, 200)
    
    def test_healtcheck_unavailable_from_banned_ip(self):
        # First of all, banning or current IP
        response = self.test_client.get("/blacklisted")
        self.assertEqual(response.status_code, 444)
        # Checking that access to /healthcheck is forbidden
        response = self.test_client.get("/healthcheck")
        self.assertEqual(response.status_code, 403)
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()

