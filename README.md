# Fault-Tolerant Order Processor

## Setup
- Clone repo.
- Create `.env` with DB vars.
- `docker-compose up --build`
- Migrate: `docker-compose exec app python manage.py migrate`
- Test: `docker-compose exec app python manage.py test`

## Run
- API at http://localhost:8000/orders/
- Logs at ./logs/orders.log

## Docs
See docs/OrderProcessor.postman_collection.json