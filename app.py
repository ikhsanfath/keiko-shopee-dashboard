import glob
import pandas as pd

# 1. Daftar file Excel yang akan diproses
files = [
    "parentskudetail.20260701_20260731 (2).xlsx",
    "parentskudetail.20260801_20260831 (2).xlsx",
    "parentskudetail.20260901_20260930 (2).xlsx",
]

# Jika ingin otomatis membaca semua file dengan pola nama serupa:
# files = glob.glob("parentskudetail.*.xlsx")

dfs = []
for file in files:
    data = pd.read_excel(file)
    dfs.append(data)

df = pd.concat(dfs, ignore_index=True)

# 2. Pembersihan data pada kolom GMV
gmv_col = "Penjualan (Pesanan Siap Dikirim) (IDR)"
product_col = "Produk"

# Mengonversi format mata uang menjadi numerik jika berupa string
if df[gmv_col].dtype == "object":
    df[gmv_col] = (
        df[gmv_col]
        .astype(str)
        .str.replace("Rp", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

df[gmv_col] = pd.to_numeric(df[gmv_col], errors="coerce").fillna(0)

# 3. Agregasi GMV berdasarkan Produk
gmv_by_product = (
    df.groupby(product_col)[gmv_col]
    .sum()
    .reset_index()
    .sort_values(by=gmv_col, ascending=False)
)

# Format tampilan mata uang
gmv_by_product["GMV Formatted"] = gmv_by_product[gmv_col].apply(
    lambda x: f"Rp {x:,.0f}".replace(",", ".")
)

# 4. Ringkasan Hasil
total_gmv = df[gmv_col].sum()
print(f"Total GMV Keseluruhan: Rp {total_gmv:,.0f}".replace(",", "."))
print("\nTop 10 Produk Berdasarkan GMV:")
print(gmv_by_product[[product_col, "GMV Formatted"]].head(10))

# 5. Simpan ringkasan ke file Excel baru
gmv_by_product.to_excel("Ringkasan_GMV_Produk.xlsx", index=False)
