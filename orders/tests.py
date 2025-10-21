from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Order
import random
from unittest.mock import patch
import time


class OrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/orders/'
        self.valid_data = {"items": ["item1", "item2"], "payment_amount": 100.50}

    def test_successful_order_creation(self):
        with patch('random.random', return_value=0.15):  # Force success (>0.1, no failure)
            response = self.client.post(self.url, self.valid_data, format='json')
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
            self.assertIn('order_id', response.json())

    def test_duplicate_order_submission(self):
        with patch('random.random', return_value=0.15):  # Force success for both
            # First creation
            self.client.post(self.url, self.valid_data, format='json')
            # Duplicate
            response = self.client.post(self.url, self.valid_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Order.objects.count(), 1)  # No duplicate record

    def test_failed_order_with_retry(self):
        with patch('random.random', return_value=0.05):  # Force failure (<0.1)
            response = self.client.post(self.url, self.valid_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertIn('Retry-After', response.headers)
            self.assertEqual(response.headers['Retry-After'], '5')

    def test_background_logging(self):
        with patch('orders.views.logger.info') as mock_log:
            with patch('random.random', return_value=0.15):  # Force success
                self.client.post(self.url, self.valid_data, format='json')
                time.sleep(0.1)  # Allow async thread to run
            mock_log.assert_called()  # Verifies logging triggered
