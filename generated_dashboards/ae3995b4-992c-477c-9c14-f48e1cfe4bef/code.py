import pandas as pd
import numpy as np

np.random.seed(42)

n_rows = 100
users = [f"U{1000+i}" for i in range(n_rows)]

age_groups = ["18-25", "26-35", "36-45", "46-60"]
spending_categories = ["Food", "Travel", "Shopping", "Healthcare", "Education", "Entertainment"]
payment_modes = ["UPI", "Credit Card", "Debit Card", "Wallet", "NetBanking", "Crypto"]
geo_regions = ["North", "South", "East", "West", "Central"]

data = {
    "User_ID": users,
    "Age_Group": np.random.choice(age_groups, n_rows, p=[0.25,0.35,0.25,0.15]),
    "Monthly_Income_USD": np.random.randint(500, 15000, n_rows),
    "Spending_Category": np.random.choice(spending_categories, n_rows),
    "Transaction_Amount": np.round(np.random.exponential(scale=700, size=n_rows).clip(5, 30000), 2),
    "Payment_Mode": np.random.choice(payment_modes, n_rows),
    "Transaction_Hour": np.random.randint(0, 24, n_rows),
    "Geo_Region": np.random.choice(geo_regions, n_rows),
    "Loyalty_Points": np.random.randint(0, 5001, n_rows)
}

df = pd.DataFrame(data)
df.to_csv("fintech_ultimate.csv", index=False)

print("✅ fintech_ultimate.csv generated with shape:", df.shape)
print(df.head())
