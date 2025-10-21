# Fault-Tolerant Order Processor

## Requirements
- Docker & Docker Compose
- Python 3.11 , Django==5.2.7 and PostgreSQL 16 for local run ( Was the tested during implementation)

## Setup
- Clone repo from https://github.com/tbwahacker/order_processor.git or for ssh git@github.com:tbwahacker/order_processor.git
- Create `.env` with DB vars. (or rename the file .env.rename_this_file to .env and keep your DB setups)
  example:
  DB_NAME=orderprocessordb
  DB_USER=postgres
  DB_PASSWORD=your_postgres_passowrd_here
  DB_HOST=localhost
  DB_PORT=5432

- `docker-compose up --build`
- Migrate: `docker-compose exec app python manage.py migrate`
- Test: `docker-compose exec app python manage.py test`

## Run
- API at http://localhost:8000/orders/
- Logs at ./logs/orders.log

## Docs
- - (Depends on how frontend developer will need me to deliver api docs, I provided both swagger UI and postman collection json file)
See docs/OrderProcessor.postman_collection.json
See Swagger UI via /swagger end point (eg. http://127.0.0.1:8000/swagger/) and
get API specification at http://127.0.0.1:8000/redoc/
---

## Important implementation explainations & rationale (addresses evaluation)

**Reliability / Idempotency**
- Idempotency key is deterministic: same set of items and payment amount produce the same key.
- We check the DB for existing order — if it exists, return same `order_id` and do not create a duplicate.

**Failure Simulation**
- Random failure happens *before* writing to DB, so unsuccessful requests do not create partial records. also this is defended by transaction.atomic() as added advantage
- On DB errors (lookup/create exception), we also return 503 + `Retry-After` header.

**Background Logging**
- `_log_order_async` function in views.py writes log entries asynchronously using `threading.Thread(target=log_task).start()` in background.
- The log file is placed in `/app/logs/orders.log` and `./logs/orders.log` is mounted to host by docker-compose.

**Testing**
- Tests use Django `TestCase`.
- Simulated failure test uses `unittest.mock.patch` to force `random.random()` to produce failure and retries.
- Successful tests must pass the mock patch for function `test_successful_order_creation`

- Note:
  - Idempotency: computed as SHA-256 of sorted items + payment_amount string.
  - Simulated transient failures: ~10% probability. Returns 503 with header Retry-After: 5.
  - Logging: written asynchronously to logs/orders.log so requests do not block.

**Dockerization**
- `docker-compose.yml` defines `db` (postgres:18) and `app` (Django app).
- Volume `db_data` persists DB.
- `./logs/orders.log` is host-mounted so `/app/logs/orders.log` is accessible outside container.

**Documentation**
- Swagger UI via `drf_yasg` at `/swagger/`.
- Postman test script (to check either success or retry):
  - ` pm.test("Has valid response", function () {
      var json = pm.response.json();
      pm.expect(pm.response.code === 201 || pm.response.code === 200 || pm.response.code === 503).to.be.true;
      if (pm.response.code === 503) {
        pm.expect(pm.response.headers.has('Retry-After')).to.be.true;
      } else {
        pm.expect(json).to.have.property("order_id");
      }
     });
   `
- Postman collection tests results included at `docs/OrderProcessor.postman_collection.json`.

---