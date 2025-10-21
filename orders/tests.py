from django.test import TestCase, Client
from rest_framework import status
from .models import Order
import random
from unittest.mock import patch

class OrderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/orders/'
        self.valid_data = {"items": ["item1", "item2"], "payment_amount": 100.50}

    def test_successful_order_creation(self):
        with patch('random.random', return_value=0.05):  # Force success (<0.1)
            response = self.client.post(self.url, self.valid_data, content_type='application/json')
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
            self.assertIn('order_id', response.json())

    def test_duplicate_order_submission(self):
        # Create first
        self.client.post(self.url, self.valid_data, content_type='application/json')
        # Duplicate
        response = self.client.post(self.url, self.valid_data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Order.objects.count(), 1)  # No duplicate

    def test_failed_order_with_retry(self):
        with patch('random.random', return_value=0.15):  # Force failure (>0.1? Wait, <0.1 is failure? No: in code <0.1 fails.
           # Adjust: random.random() < 0.1 -> fail
           print('0.15 random test')

        with patch('random.random', return_value=0.05):  # Fail
            response = self.client.post(self.url, self.valid_data, content_type='application/json')
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertIn('Retry-After', response.headers)
            self.assertEqual(response.headers['Retry-After'], '5')

    def test_background_logging(self):
        # Logging is async, so we can't assert file content easily in unit test.
        # Mock logger to verify call
        with patch('orders.views.logger.info') as mock_log:
            self.client.post(self.url, self.valid_data, content_type='application/json')
            mock_log.assert_called()  # Verifies logging was triggered