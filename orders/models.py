from django.db import models

# Create your models here.
import hashlib
import uuid


class Order(models.Model):
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    items = models.JSONField()
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    hash_key = models.CharField(max_length=64, unique=True, db_index=True)

    @classmethod
    def generate_hash(cls, items, payment_amount):
        data = f"{sorted(items)}{payment_amount}"
        return hashlib.sha256(data.encode()).hexdigest()

    def save(self, *args, **kwargs):
        if not self.hash_key:
            self.hash_key = self.generate_hash(self.items, self.payment_amount)
        super().save(*args, **kwargs)


class OrderItem(models.Model):  # if items will be needed
    name = models.CharField(max_length=255)
    order = models.ForeignKey(Order, related_name='items_list', on_delete=models.CASCADE)
