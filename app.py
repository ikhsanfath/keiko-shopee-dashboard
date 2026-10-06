import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Keiko Automotive - Shopee Dashboard", layout="wide")

st.title("🚗 Keiko Automotive — Dashboard Performa Produk (Juli - Sept 2026)")

# Upload 3 File Excel
uploaded_files = st.sidebar.file_uploader(
    "Upload File Report Shopee (.xlsx)", 
    type=["xlsx"], 
    accept_multiple_files=True
)

def categorize_product(title):
    title_lower = str(title).lower()
    
    if "setir" in title_lower:
        if "deluxe" in title_lower:
            return "Setir Deluxe"
        return "Setir Biasa"
    elif "karpet" in title_lower:
        return "Karpet"
    elif any(k in title_lower for k in ["lap", "kanebo", "microfiber"]):
        return "Lap/Kanebo"
    elif "silver" in title_lower:  # Gabungan Silver & Warna masuk Silver
        return "Silver"
    elif "warna" in title_lower:
        return "Warna"
    elif any(k in title_lower for k in ["ultimate", "armor"]):  # Gabungan Ultimate & Armor masuk Ultimate
        return "Ultimate"
    elif "deluxe" in title_lower:
        return "Deluxe"
    else:
        return "Lainnya"

def assign_funnel(row, gmv_threshold, order_threshold):
    cat = row['Kategori']
    gmv = row['GMV']
    orders = row['Pesanan']
    views = row['Dilihat']
    
    if cat == "Ultimate" or "armor" in str(row['Nama Produk']).lower():
        return "Margin Driven Product"
    elif gmv >= gmv_threshold and orders >= order_threshold:
        return "Hero SKU"
    elif orders >= order_threshold and gmv < gmv_threshold:
        return "Volume Driven Product"
    elif views < 100 or orders == 0:
        return "Flush Product"
    else:
        return "Regular SKU"

if uploaded_files:
    df_list = []
    for file in uploaded_files:
        data = pd.read_excel(file)
        df_list.append(data)
    
    df = pd.concat(df_list, ignore_index=True)
    
    # Standarisasi Nama Kolom Shopee
    col_map = {
        'Nama Produk': 'Nama Produk',
        'Produk Dilihat': 'Dilihat',
        'Halaman Dilihat': 'Dilihat',
        'Klik Produk': 'Klik',
        'Pesanan Dibuat': 'Pesanan',
        'Pesanan Siap Dikirim': 'Pesanan',
        'Total Penjualan (IDR)': 'GMV',
        'Penjualan': 'GMV'
    }
    df = df.rename(columns=col_map)
    
    # Pembersihan Data
    numeric_cols = ['Dilihat', 'Klik', 'Pesanan', 'GMV']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Aggregasi Data per Produk
    df_grouped = df.groupby('Nama Produk').agg({
        'Dilihat': 'sum',
        'Klik': 'sum',
        'Pesanan': 'sum',
        'GMV': 'sum'
    }).reset_index()

    # Kategori & Funnel
    df_grouped['Kategori'] = df_grouped['Nama Produk'].apply(categorize_product)
    
    gmv_q75 = df_grouped['GMV'].quantile(0.75)
    order_q75 = df_grouped['Pesanan'].quantile(0.75)
    df_grouped['Funnel Category'] = df_grouped.apply(lambda r: assign_funnel(r, gmv_q75, order_q75), axis=1)

    # 1. SECTION OVERVIEW
    st.subheader("📌 Overview Performa Toko")
    
    tot_gmv = df_grouped['GMV'].sum()
    tot_views = df_grouped['Dilihat'].sum()
    tot_clicks = df_grouped['Klik'].sum()
    tot_orders = df_grouped['Pesanan'].sum()
    ctr = (tot_clicks / tot_views * 100) if tot_views > 0 else 0
    cvr = (tot_orders / tot_clicks * 100) if tot_clicks > 0 else 0

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total GMV", f"Rp {tot_gmv:,.0f}")
    m2.metric("Total Dilihat", f"{tot_views:,.0f}")
    m3.metric("Total Klik", f"{tot_clicks:,.0f}")
    m4.metric("Pesanan Siap Kirim", f"{tot_orders:,.0f}")
    m5.metric("CTR", f"{ctr:.2f}%")
    m6.metric("CVR", f"{cvr:.2f}%")

    st.markdown("---")

    # 2. SECTION LIST PRODUK PERFORMA TERBAIK
    st.subheader("🏆 List Produk Performa Terbaik")
    selected_cat = st.multiselect(
        "Filter Kategori Produk:",
        options=["Semua"] + list(df_grouped['Kategori'].unique()),
        default=["Semua"]
    )

    if "Semua" in selected_cat or not selected_cat:
        filtered_df = df_grouped
    else:
        filtered_df = df_grouped[df_grouped['Kategori'].isin(selected_cat)]

    st.dataframe(
        filtered_df.sort_values(by='GMV', ascending=False),
        use_container_width=True
    )

    st.markdown("---")

    # 3. SECTION FUNNEL PRODUK
    st.subheader("🎯 Analisis Funnel SKU")
    funnel_filter = st.radio(
        "Pilih Kategori Funnel:",
        options=["Semua", "Hero SKU", "Volume Driven Product", "Margin Driven Product", "Flush Product"],
        horizontal=True
    )

    if funnel_filter != "Semua":
        funnel_df = df_grouped[df_grouped['Funnel Category'] == funnel_filter]
    else:
        funnel_df = df_grouped

    fig = px.pie(df_grouped, names='Funnel Category', title='Distribusi SKU Berdasarkan Funnel')
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        funnel_df[['Nama Produk', 'Kategori', 'Funnel Category', 'Dilihat', 'Klik', 'Pesanan', 'GMV']]
        .sort_values(by='GMV', ascending=False),
        use_container_width=True
    )
