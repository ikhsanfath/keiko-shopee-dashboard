import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dashboard GMV Shopee", layout="wide")

st.title("📊 Dashboard Performa Produk Shopee")

# Tombol untuk mengunggah file Excel langsung di web Streamlit
uploaded_files = st.file_uploader(
    "Unggah File Excel Laporan Shopee (parentskudetail)",
    type=["xlsx", "xls"],
    accept_multiple_files=True,
)

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        try:
            data = pd.read_excel(file)
            dfs.append(data)
        except Exception as e:
            st.error(f"Gagal membaca file {file.name}: {e}")

    if dfs:
        df = pd.concat(dfs, ignore_index=True)

        gmv_col = "Penjualan (Pesanan Siap Dikirim) (IDR)"
        product_col = "Produk"

        # Cek ketersediaan kolom
        if gmv_col in df.columns and product_col in df.columns:
            # Pembersihan format angka GMV jika bertipe string
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

            # Agregasi GMV per Produk
            gmv_by_product = (
                df.groupby(product_col)[gmv_col]
                .sum()
                .reset_index()
                .sort_values(by=gmv_col, ascending=False)
            )

            # Menyaring produk yang memiliki penjualan > 0
            gmv_by_product = gmv_by_product[gmv_by_product[gmv_col] > 0]
            total_gmv = gmv_by_product[gmv_col].sum()

            # Tampilan Ringkasan
            col1, col2 = st.columns(2)
            col1.metric("Total GMV (Siap Dikirim)", f"Rp {total_gmv:,.0f}".replace(",", "."))
            col2.metric("Jumlah Produk Terjual", len(gmv_by_product))

            st.markdown("---")
            st.subheader("Top Produk Berdasarkan GMV")

            # Format tampilan tabel
            display_df = gmv_by_product.copy()
            display_df["GMV Formatted"] = display_df[gmv_col].apply(
                lambda x: f"Rp {x:,.0f}".replace(",", ".")
            )

            st.dataframe(
                display_df[[product_col, "GMV Formatted"]],
                use_container_width=True,
            )

            # Grafik
            st.subheader("Grafik Top 10 Produk")
            st.bar_chart(gmv_by_product.set_index(product_col)[gmv_col].head(10))

        else:
            st.warning(f"Kolom '{gmv_col}' atau '{product_col}' tidak ditemukan pada file.")
else:
    st.info("Silakan unggah file Excel laporan Shopee kamu melalui tombol di atas.")
