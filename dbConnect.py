import psycopg2
import pandas as pd
from urllib.parse import quote_plus

password = quote_plus("Uc~FXtxYWP")

CSV_FILE = "merged_deduplicated.csv"

DB_CONFIG = {
    "dbname": "cosmetics",
    "user": "postgres",
    "password": password,
    "host": "db",
    "port": 5432
}

df = pd.read_csv(CSV_FILE)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

product_cache = {}

for _, row in df.iterrows():
    product_key = (row["brand"], row["name"])

    if product_key not in product_cache:
        cur.execute("""
            INSERT INTO products (canonical_name, brand, description, image_url)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            row["name"],
            row["brand"],
            row.get("description"),
            row.get("image")
        ))

        product_id = cur.fetchone()[0]
        product_cache[product_key] = product_id
    else:
        product_id = product_cache[product_key]

    cur.execute("""
        INSERT INTO offers (
            product_id, website_name, price, url, rating, reviews_count
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        product_id,
        row["source"],
        row["price"],
        row["url"],
        row.get("rating"),
        row.get("reviews_count")
    ))

    if pd.notna(row.get("size")):
        cur.execute("""
            INSERT INTO attributes (product_id, attribute_name, attribute_value)
            VALUES (%s, %s, %s)
        """, (
            product_id,
            "size",
            row["size"]
        ))

    if pd.notna(row.get("sku")):
        cur.execute("""
            INSERT INTO attributes (product_id, attribute_name, attribute_value)
            VALUES (%s, %s, %s)
        """, (
            product_id,
            "sku",
            row["sku"]
        ))

conn.commit()
cur.close()
conn.close()

print("Данные успешно загружены в БД")