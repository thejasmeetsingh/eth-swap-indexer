# ETH Swap Indexer
The ETH Swap Indexer is a Python-based Django project designed to store Ethereum swap events in a PostgreSQL database for efficient querying and indexing purposes. It leverages various technologies such as Web3.py, Celery, Redis, Pydantic, and Docker to provide a scalable and reliable solution.

## Key Features
- **Django Admin Panel:** Users can easily add Ethereum contract details, including contract address, ABI JSON, HTTP provider, and starting block number through the Django admin panel.

- **Celery Background Tasks:** Upon adding contract details, a Celery task is triggered in the background. This task fetches swap events related to the specified contract, calculates crucial metrics like execution price, transaction cost, and swapped cost in both ETH and USD along with other transaction and event details, and stores the data in the PostgreSQL database.

- **Concurrency with Celery:** Users can add multiple contract addresses simultaneously. Celery allows for the parallel execution of tasks, ensuring efficient and concurrent processing of swap events for different contracts.

- **Decimal Precision:** All cost and monetary values are stored as Decimal in the database to prevent overflow issues and ensure precise unit values.

- **Coinbase API Integration:** Exchange rates between ETH and USD are obtained from the Coinbase API.

- **Rate Limit:** To handle rate limit errors, a caching layer and a 5-second pause are implemented to mitigate potential rate limit issues from third-party services.

- **Pydantic Schema Validation:** Pydantic schemas are employed to validate swap event data before saving it to the database, ensuring data integrity.

- **Logging:** Inline logging is incorporated to capture errors along with tracebacks and INFO messages, providing a comprehensive logging solution for monitoring and debugging.

- **Asynchronous Server:** The Django server is configured to run on Gunicorn with Uvicorn workers to handle multiple requests asynchronously, ensuring optimal performance.

## Getting Started
To run the ETH Swap Indexer, follow these steps:

1. Clone the repository.
2. Install [docker](https://www.docker.com/products/docker-desktop/).
3. Build and run the docker containers: `docker-compose up -d`.
4. That's it, You can access the django admin panel at http://0.0.0.0:8000/admin.
    * Admin Username: `admin`
    * Admin Password: `1234`

You can view logs of each container using docker desktop app or just by running this command: `docker container logs -f <container_name>`.

## Usage
[](./assets/usage.mov)