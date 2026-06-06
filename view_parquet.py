import sys
import pandas as pd

path = sys.argv[1] if len(sys.argv) > 1 else "yellow_tripdata_2025-01.parquet"
df = pd.read_parquet(path)

print(f"File: {path}")
print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns\n")
print("Columns and types:")
print(df.dtypes.to_string())
print("\n--- First 10 rows ---")
print(df.head(10).to_string())
print("\n--- Describe (numeric) ---")
print(df.describe().T.to_string())
