# Secret Management System with Zero Trust using HashiCorp Vault, and Docker
In this project, we will build a secure system that uses HashiCorp Vault to dynamically generate secrets (e.g., database credentials), runs services in Docker and applies Zero Trust principles. We demonstrate with secrets for PostgreSQL and a Python microservice. 


## Prerequisites
1. Docker & Docker Compose
2. HashiCorp Vault
3. PostgreSQL (Docker Container)
4. Python App for DB Access


## Part 1: Local Docker-Based Setup with Vault & PostgreSQL

### Install Required Tools
```sh
sudo apt update
sudo apt install -y docker.io docker-compose unzip curl jq
```
```sh
docker -v
docker-compose -v
```

### Create Docker Compose File

Create docker-compose.yml with the content below for the services: 
1. Vault
2. PostgreSQL


```sh
# docker-compose.yml

services:
  vault:
    image: hashicorp/vault:latest
    container_name: vault
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: root
      VAULT_DEV_LISTEN_ADDRESS: "0.0.0.0:8200"
    cap_add:
      - IPC_LOCK
    command: vault server -dev -dev-root-token-id=root -dev-listen-address=0.0.0.0:8200

  postgres:
    image: postgres:15
    container_name: postgres
    environment:
      POSTGRES_USER: root
      POSTGRES_PASSWORD: rootpw
      POSTGRES_DB: mydb
    ports:
      - "6432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  pg_data:
```


### Run the PostgreSQL & Vault Containers 
```sh
docker compose up -d
```

```sh
docker ps
```


### Check the logs of Vault
```sh
docker logs vault
```


## Part 2: Install Vault CLI (Using snap utility for Ubuntu)

```sh
sudo snap install vault
```

```sh
vault status
```

### Initialize Vault by Setting Environment Variables
```sh
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=root
```

### Enable Database Secrets Engine
```sh
vault secrets enable database
```

### Configure Vault to Connect to PostgreSQL DB
Since both services are in the same Docker Compose network, use the postgres service name (postgres) as the hostname:

```sh
vault write database/config/my-postgres-database \
    plugin_name=postgresql-database-plugin \
    allowed_roles="my-role" \
    connection_url="postgresql://{{username}}:{{password}}@postgres:5432/mydb?sslmode=disable" \
    username="root" \
    password="rootpw"
```

### Create a Vault Role for Dynamic Credentials
```sh
vault write database/roles/my-role \
    db_name=my-postgres-database \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"
```

### Test Dynamic Credential Generation
```sh
vault read database/creds/my-role
```

## Part 3: Python App Fetching Secrets
Create a simple Python App with psycopg2 (a PostgreSQL database adapter for Python programming language) to get dynamic credentials.

```sh
# app.py

import os
import requests
import psycopg2

VAULT_TOKEN = os.environ['VAULT_TOKEN']
VAULT_ADDR = os.environ['VAULT_ADDR']

# Step 1: Fetch dynamic credentials from Vault
res = requests.get(f"{VAULT_ADDR}/v1/database/creds/my-role", headers={"X-Vault-Token": VAULT_TOKEN})

res.raise_for_status()
creds = res.json()["data"]
username = creds["username"]
password = creds["password"]

print(f"[Vault] issued dynamic username: {username}")
print(f"[Vault] issued dynamic password: {password}")


# Step 2: Connect to PostgreSQL DB using Dynamic Credentials
print("Connecting to PostgreSQL with dynamic credentials ...")

conn = psycopg2.connect(
    dbname="mydb",
    user=username,
    password=password,
    host="postgres",  # The Docker Compose service name for Postgres Container
    port=5432
)

cur = conn.cursor()
cur.execute("SELECT NOW();")
db_time = cur.fetchone()
print("PostgreSQL connection successful")
print("[PostgreSQL] Current DB time:", db_time)

cur.close()
conn.close()
```

### Write a Dockerfile to Package the Python App
Add the following content to your Dockerfile:

```sh
# Dockerfile

FROM python:3.10-slim
WORKDIR /app
COPY app.py .
RUN pip install --no-cache-dir psycopg2-binary requests
CMD ["python", "app.py"]
```


### Build & Run the Python App that Fetches Secrets from Vault
```sh
docker build -t vault-python-app .
```

Make sure to run the App in the same network as the running Vault container in order to have access to postgreSQL
```sh
docker run --rm \
  --network container:vault \
  -e VAULT_ADDR=http://127.0.0.1:8200 \
  -e VAULT_TOKEN=root \
  vault-python-app
```

#### Expected Output
```sh
[Vault] Received dynamic credentials: v-token-hJ5d12AbCqEa9MzhYdTf-1699577927
[PostgreSQL] Current DB time: (datetime.datetime(2025, 7, 8, 17, 34, 12, 123456),)
```

## Clean UP
```sh
docker compose down -v
```
