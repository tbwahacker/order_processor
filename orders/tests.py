from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Order
from unittest.mock import patch
import time
import os

class OrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/orders/'
        self.valid_data = {
            "items": ["item1", "item2"],
            "payment_amount": 100.50
        }

    def test_successful_order_creation(self):
        with patch('orders.views.random.random', return_value=0.15):  # Success (>0.1)
            response = self.client.post(self.url, self.valid_data, format='json')
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
            self.assertIn('order_id', response.json())
            self.assertEqual(Order.objects.count(), 1)

    def test_duplicate_order_submission(self):
        with patch('orders.views.random.random', return_value=0.15):  # Success for both
            first_response = self.client.post(self.url, self.valid_data, format='json')
            self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
            response = self.client.post(self.url, self.valid_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Order.objects.count(), 1)

    def test_failed_order_with_retry(self):
        with patch('orders.views.random.random', return_value=0.05):  # Failure (<0.1)
            response = self.client.post(self.url, self.valid_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertIn('Retry-After', response.headers)
            self.assertEqual(response.headers['Retry-After'], '5')
            self.assertEqual(Order.objects.count(), 0)

    def test_background_logging(self):
        with patch('orders.views.random.random', return_value=0.15):  # Success
            with patch('orders.views.logger.info') as mock_log:
                self.client.post(self.url, self.valid_data, format='json')
                time.sleep(0.5)  # Wait for async thread
            mock_log.assert_called()

    def test_validation_errors(self):
        invalid_data = {"items": [], "payment_amount": 100.50}  # Empty items
        response = self.client.post(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_data = {"items": ["item1"], "payment_amount": -1}  # Negative amount
        response = self.client.post(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)