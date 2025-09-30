# Simple Bank Django Project

## Prerequisites

- Docker
- Docker Compose

## Setup Instructions

1. Clone the repository:

   ```bash
   git clone https://github.com/magicjohnson/simple_bank.git
   cd simple_bank
   ```

2. Ensure directory is shared from the host and is known to Docker.

3. Build and run the application:

   ```bash
   docker-compose up --build
   ```

4. Access the Django app at `http://localhost:8000`.

## API Endpoints

- **Register**: `POST /api/register/`
  - Payload: `{ "email": "user@example.com", "password": "yourpassword" }`
  - Response: `201 CREATED`
  - Creates a user and a bank account with a unique 10-digit account number and €10,000 welcome bonus.
- **Login**: `POST /api/login/`
  - Payload: `{ "email": "user@example.com", "password": "yourpassword" }`
  - Response: `{ "token": "<auth_token>" }`
- **Get Balance**: `GET /api/balance/`
  - Headers: `Authorization: Token <auth_token>`
  - Response: `{ "balance": 10000.00 }`
- **List Transactions**: `GET /api/transactions/`
  - Headers: `Authorization: Token <auth_token>`
  - Optional Query Params: `date_from=YYYY-MM-DDTHH:MM:SSZ`, `date_to=YYYY-MM-DDTHH:MM:SSZ`
  - Response: `{ "transactions": [{ "amount": 10000.00, "type": "credit", "timestamp": "2025-09-30T12:08:00Z" }, ...] }`
- **Transfer Money**: `POST /api/transfer/`
  - Headers: `Authorization: Token <auth_token>`
  - Payload: `{ "receiver_account_number": "1234567890", "amount": "100.00" }`
  - Response: `{ "message": "Transfer successful" }`
  - Transfers the specified amount to the receiver's account, applying a 2.5% fee (minimum €5). Records debit (sender) and credit (receiver) transactions.

## Testing

- Build the test environment:

  ```bash
  docker-compose build
  ```
- Run tests with verbose output and coverage report:

  ```bash
  docker-compose up -d db
  docker-compose run --rm test
  ```

  This applies migrations, runs tests with verbose output, and generates a coverage report.
