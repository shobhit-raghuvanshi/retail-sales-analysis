from pathlib import Path
import sqlite3
import chardet
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
csv_file = BASE_DIR/"superstore.csv"
db_file = BASE_DIR/"superstore.db"
schema_file = BASE_DIR/"superstore_schema.sql"

if db_file.exists():
    db_file.unlink()

with open(csv_file,"rb") as f:
    result_csv = chardet.detect(f.read(10000))

df = pd.read_csv(csv_file, encoding=result_csv["encoding"])
df.rename(columns=str.strip, inplace=True)

customers = df[["Customer ID", "Customer Name", "Segment"]].copy().drop_duplicates(subset=["Customer ID"]).reset_index(drop=True)  # type: ignore[call-overload]
locations = df[["Country", "City", "State", "Postal Code", "Region"]].copy()
locations["Postal Code"] = locations["Postal Code"].astype(str).str.split(".").str[0].replace({"nan": None, "None": None, "<NA>": None})  # type: ignore[index]
locations = locations.drop_duplicates().reset_index(drop=True)
locations["location_id"] = range(1, len(locations) + 1)
locations["location_id"] = locations["location_id"].astype(int)
products = df[["Product ID", "Product Name", "Category", "Sub-Category"]].copy().drop_duplicates(subset=["Product ID"]).reset_index(drop=True)  # type: ignore[call-overload]
orders_info = df[["Order ID", "Order Date", "Ship Date", "Ship Mode", "Customer ID", "Country", "City", "State", "Postal Code", "Region"]].copy()
orders_info["Postal Code"] = orders_info["Postal Code"].astype(str).str.split(".").str[0].replace({"nan": None, "None": None, "<NA>": None})  # type: ignore[index]
orders_info = orders_info.drop_duplicates(subset=["Order ID"]).reset_index(drop=True)  # type: ignore[call-overload]
locations_mapping = {(r["Country"], r["City"], r["State"], r["Postal Code"], r["Region"]): int(r["location_id"]) for _, r in locations.iterrows()}  # type: ignore[index]
orders = []
for _, r in orders_info.iterrows():
    key = (r["Country"], r["City"], r["State"], r["Postal Code"], r["Region"])
    orders.append((r["Order ID"], pd.to_datetime(r["Order Date"]).strftime("%Y-%m-%d")  if pd.notna(r["Order Date"]) else None,  # type: ignore[index]
                   pd.to_datetime(r["Ship Date"]).strftime("%Y-%m-%d") if pd.notna(r["Ship Date"]) else None,  # type: ignore[index]
                   r["Ship Mode"], r["Customer ID"], locations_mapping[key]))

conn = sqlite3.connect(db_file)

try:
    conn.execute("pragma foreign_keys = on")
    schema = schema_file.read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.executemany("INSERT INTO customers VALUES (?, ?, ?)", [(r["Customer ID"], r["Customer Name"], r["Segment"]) for _, r in customers.iterrows()])
    conn.executemany("INSERT INTO locations VALUES (?, ?, ?, ?, ?, ?)", [(int(r["location_id"]), r["Country"], r["City"], r["State"], r["Postal Code"], r["Region"]) for _, r in locations.iterrows()])  # type: ignore[index]
    conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", [(r["Product ID"], r["Product Name"], r["Category"], r["Sub-Category"]) for _, r in products.iterrows()])
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", orders)
    conn.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?, ?)", [
        (int(r["Row ID"]), r["Order ID"], r["Product ID"], # type: ignore[index]
         None if pd.isna(r["Sales"]) else float(r["Sales"]), # type: ignore[index]
         None if pd.isna(r["Quantity"]) else int(r["Quantity"]), # type: ignore[index]
         None if pd.isna(r["Discount"]) else float(r["Discount"]), # type: ignore[index]
         None if pd.isna(r["Profit"]) else float(r["Profit"])) # type: ignore[index]
        for _, r in df.iterrows()])
    conn.commit()
    print("Created:", db_file)
    for table in ["customers", "locations", "products", "orders", "order_items"]:
        print(f"{table}: {conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]} rows")
    print("Foreign key errors:", conn.execute("PRAGMA foreign_key_check").fetchall())
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()