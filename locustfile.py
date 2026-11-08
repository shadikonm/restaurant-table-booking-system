"""Read-only load test. Run ONLY against your own local server.
locust -f locustfile.py --host http://127.0.0.1:5000
"""
from locust import HttpUser, between, task
from datetime import datetime, timedelta

class RestaurantVisitor(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def home(self):
        self.client.get('/', name='GET /')

    @task(3)
    def menu(self):
        self.client.get('/api/menu', name='GET /api/menu')

    @task(3)
    def availability(self):
        date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        self.client.get('/api/availability', params={'date':date,'time':'19:00','guests':2}, name='GET /api/availability')

    @task(2)
    def health(self):
        self.client.get('/health', name='GET /health')
