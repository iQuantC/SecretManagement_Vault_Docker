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