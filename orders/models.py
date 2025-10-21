from django.db import models

# Create your models here.
import hashlib
import uuid

class Order(models.Model):
    order_id = models.CharField(max_length=36, unique=True, default=uuid.uuid4)
    items = models.JSONField()  # Store as list
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    hash_key = models.CharField(max_length=64, unique=True)  # Ensure idempotency by checking if an identical order exists

    @classmethod
    def generate_hash(cls, items, payment_amount):
        sorted_items = sorted(items)
        data = f"{sorted_items}{payment_amount}" # after Sort items for consistency, then hash items + amount
        return hashlib.sha256(data.encode()).hexdigest()