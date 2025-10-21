from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import random
from django.db import transaction
import threading
import logging

from order_processor.settings import ORDER_LOG_FILE
from .models import Order

logger = logging.getLogger('orders')


class OrderCreateView(APIView):
    def post(self, request):
        items = request.data.get('items', [])
        payment_amount = request.data.get('payment_amount')

        # Validation | I could also uses serializers for separation but lets validate here
        if not items or not isinstance(items, list):
            return Response({"error": "items must not be empty"}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(payment_amount, (int, float)) or payment_amount <= 0:
            return Response({"error": "payment_amount must be a positive number"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Idempotency check
                hash_key = Order.generate_hash(items, payment_amount)
                existing_order = Order.objects.filter(hash_key=hash_key).first()
                if existing_order:
                    self._log_order_async(existing_order.order_id, 'duplicate')
                    return Response({
                        "order_id": existing_order.order_id,
                        "status": "processed"
                    }, status=status.HTTP_200_OK)

                # Simulate failure (~10%)
                if random.random() < 0.1:
                    self._log_order_async(None, 'failure')
                    return Response({
                        "error": "Temporary failure, please retry later"
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE, headers={'Retry-After': '5'})

                # Create order
                order = Order.objects.create(
                    items=items,
                    payment_amount=payment_amount,
                    hash_key=hash_key
                )
                self._log_order_async(order.order_id, 'success')
                return Response({
                    "order_id": str(order.order_id),
                    "status": "processed"
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            self._log_order_async(None, str(e))
            return Response({
                "error": f"Temporary failure: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _log_order_async(self, order_id, result):
        def log_task():
            logger.info(f"Order attempt: ID={order_id}, Result={result}")
            # Ensure the file is flushed by the logging handler
            for handler in logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
        threading.Thread(target=log_task).start()