from psycopg2._psycopg import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import random
import threading
import logging
from django.db import transaction
from django.conf import settings
from .models import Order
from .serializers import OrderSerializer

logger = logging.getLogger('orders')

class OrderCreateView(APIView):
    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        items = data['items']
        payment_amount = data['payment_amount']
        hash_key = Order.generate_hash(items, payment_amount)

        #  Idempotency check before any DB write
        existing = Order.objects.filter(hash_key=hash_key).first()
        if existing:
            self._log_order_async(existing.order_id, "duplicate")
            return Response(
                {"order_id": existing.order_id, "status": "processed"},
                status=status.HTTP_200_OK,
            )

        # Random failure simulation
        if random.random() < 0.1:
            self._log_order_async(None, "failure")
            return Response(
                {"error": "Temporary failure, please retry later"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                headers={"Retry-After": "5"},
            )

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    items=items,
                    payment_amount=payment_amount,
                    hash_key=hash_key,
                )
        except IntegrityError:
            # If a race condition caused a duplicate insert, just reuse it
            order = Order.objects.get(hash_key=hash_key)

        self._log_order_async(order.order_id, "success")
        return Response(
            {"order_id": order.order_id, "status": "processed"},
            status=status.HTTP_201_CREATED,
        )

    def _log_order_async(self, order_id, result):
        def log_task():
            logger.info(f"Order attempt: ID={order_id}, Result={result}")
            for handler in logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
        threading.Thread(target=log_task).start()