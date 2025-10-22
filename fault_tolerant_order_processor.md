

# Fault-Tolerant Order Processor

This project is a Django-based REST API designed to handle order creation with fault tolerance and idempotency. It simulates a 10% failure rate, supports asynchronous logging, and ensures duplicate orders are processed efficiently using a unique `hash_key`.

## Project Overview

The application features a single endpoint (`/orders/`) that accepts POST requests with `items` (a list of strings) and `payment_amount` (a positive decimal). Key functionalities include:
- Idempotent order processing with a `200 OK` response for duplicates.
- A 10% random failure simulation returning `503 Service Unavailable` with a 5-second retry header.
- Asynchronous logging of order attempts.
- Validation for non-empty `items` and positive `payment_amount`.

## Configuration Procedures

### Development Environment

1. **Clone the Repository**
   ```bash
   git https://github.com/tbwahacker/order_processor.git
   cd order_processor
   ```

2. **Configure Environment**
   Ensure `.env.docker` is present with the following variables:
   - `DB_NAME=orderprocessordb`
   - `DB_USER=your-user`
   - `DB_PASSWORD=your-password`
   - `DB_HOST=db`
   - `DB_PORT=5432`
   - `DEBUG=True`
   - `SECRET_KEY=your-secret-key-here`
   - `ALLOWED_HOSTS=localhost,127.0.0.1`

3. **Build and Start Containers**
   Use Docker Compose with the `.env.docker` file:
   ```bash
   docker-compose up --build
   ```

4. **Apply Migrations**
   Initialize the database:
   ```bash
   docker-compose exec app python manage.py makemigrations
   docker-compose exec app python manage.py migrate
   ```

5. **Run Tests**
   Execute the test suite:
   ```bash
   docker-compose exec app python manage.py test
   ```

6. **Access the API**
   Test the endpoint at `http://localhost:8000/orders/`:
   ```bash
   curl -X POST http://localhost:8000/orders/ -H "Content-Type: application/json" -d '{"items": ["item1", "item2"], "payment_amount": 100.50}'
   ```

### Production Environment

1. **Configure Environment**
   Update `.env.docker` for production:
   - `DB_NAME=orderprocessordb`
   - `DB_USER=your-user`
   - `DB_PASSWORD=your-password`
   - `DB_HOST=db`
   - `DB_PORT=5432`
   - `DEBUG=False`
   - `SECRET_KEY=your-production-secret-key-here`
   - `ALLOWED_HOSTS=yourdomain.com`

2. **Build Production Containers**
   Build with a production configuration:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
   ```

3. **Apply Migrations**
   Run migrations in production:
   ```bash
   docker-compose -f docker-compose.prod.yml exec app python manage.py migrate
   ```

4. **Set Up Gunicorn**
   Configure Gunicorn as the WSGI server:
   ```bash
   docker-compose -f docker-compose.prod.yml exec app gunicorn --bind 0.0.0.0:8000 order_processor.wsgi:application
   ```

5. **Configure Nginx (Optional)**
   Set up Nginx as a reverse proxy:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

6. **Deploy**
   Deploy using your preferred method (e.g., Docker Swarm or a cloud provider).

## Notes
- The `OrderCreateView` handles idempotency by checking `hash_key` before creation and includes an `IntegrityError` fallback for race conditions.
- Ensure `.env.docker` is properly configured with your database credentials and host settings.
- PostgreSQL is required in production for `IntegrityError` handling to function correctly.

## Assessment Question No. 9 (Why Docker over others?)
- Docker provides a consistent environment across development, testing, and production.
It packages the Django app, PostgreSQL database, and dependencies in reproducible containers, simplifying setup, scaling, and CI/CD deployment.
While Python virtual environments handle dependencies, Docker ensures system-level reproducibility and faster onboarding for any developer or server.

