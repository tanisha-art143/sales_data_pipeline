
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

np.random.seed(42)


products = pd.DataFrame({
    "product_id":   [f"P{str(i).zfill(3)}" for i in range(1, 11)],
    "product_name": [
        "Samsung 55\" LED TV", "iPhone 15 Pro", "Basmati Rice 5kg",
        "Nike Running Shoes", "Prestige Pressure Cooker", "Levi's Jeans",
        "Amul Butter 500g", "Sony Headphones WH1000", "Colgate Toothpaste",
        "Woodland Boots"
    ],
    "category": [
        "Electronics", "Electronics", "Grocery",
        "Footwear", "Kitchen", "Clothing",
        "Grocery", "Electronics", "Personal Care",
        "Footwear"
    ],
    "price": [45999, 134900, 389, 4599, 2299, 3499, 245, 29990, 89, 5999]
})
products.to_csv(DATA_DIR / "products.csv", index=False)
print("products.csv created")


stores = pd.DataFrame({
    "store_id":   [f"S{str(i).zfill(2)}" for i in range(1, 9)],
    "store_name": [
        "RetailMart Andheri", "RetailMart Connaught Place",
        "RetailMart Koramangala", "RetailMart T Nagar",
        "RetailMart Hitech City", "RetailMart Salt Lake",
        "RetailMart Aundh", "RetailMart Vastrapur"
    ],
    "city":   ["Mumbai", "Delhi", "Bengaluru", "Chennai",
               "Hyderabad", "Kolkata", "Pune", "Ahmedabad"],
    "region": ["West", "North", "South", "South",
               "South", "East", "West", "West"]
})
stores.to_csv(DATA_DIR / "stores.csv", index=False)
print("stores.csv created")


store_ids   = stores["store_id"].tolist()
product_ids = products["product_id"].tolist()
dates       = pd.date_range("2026-01-01", "2026-01-07", freq="D")

rows = []
sale_id = 1001
for _ in range(40):
    rows.append({
        "sale_id":    f"TXN{sale_id}",
        "store_id":   np.random.choice(store_ids),
        "product_id": np.random.choice(product_ids),
        "quantity":   np.random.randint(1, 15),
        "sale_date":  str(np.random.choice(dates))[:10],
        "amount":     round(np.random.uniform(200, 150000), 2)
    })
    sale_id += 1


for i in [3, 8, 14, 22, 35]:
    rows[i]["quantity"] = None


for i in [5, 17, 29]:
    rows[i]["amount"] = None


rows.append(rows[0].copy())
rows.append(rows[7].copy())
rows.append(rows[15].copy())


rows[10]["quantity"] = -2

rows[20]["amount"] = 750000.00

df_sales = pd.DataFrame(rows)
df_sales = df_sales.sample(frac=1, random_state=42).reset_index(drop=True)
df_sales.to_csv(DATA_DIR / "sales_data.csv", index=False)
print(f"sales_data.csv created — {len(df_sales)} rows (includes intentional duplicates + nulls)")
