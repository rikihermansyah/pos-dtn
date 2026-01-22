import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIG ---
NAMA_TOKO = "Dapur Teh Nunung (DTN)"
SLOGAN = "Makan Enak,,,Enak Makan,,,"
# Masukkan URL Google Sheets Anda di sini
URL_SHEET = "https://docs.google.com/spreadsheets/d/1gRsF4YZtDLAhIRquST9I0UqxfnYqUVvPL9nq0IOFuTE/edit?usp=sharing"

st.set_page_config(page_title=NAMA_TOKO, layout="centered")

# Koneksi Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNGSI LOAD DATA ---
def load_data():
    try:
        # Mengambil data dari tab pertama (Penjualan) dan tab kedua (Menu)
        df_penjualan = conn.read(spreadsheet=URL_SHEET, worksheet="Sheet1")
        # Pastikan Anda membuat tab bernama "Menu" di Google Sheets yang sama
        df_menu = conn.read(spreadsheet=URL_SHEET, worksheet="Menu")
        return df_penjualan, df_menu
    except:
        # Jika tab Menu belum ada, gunakan data darurat
        df_menu = pd.DataFrame({'kategori': ['Makanan'], 'nama': ['Contoh Menu'], 'harga': [10000]})
        return pd.DataFrame(), df_menu

# --- INISIALISASI ---
if 'orders' not in st.session_state: st.session_state.orders = []
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

df_penjualan, df_menu = load_data()

# --- SIDEBAR: TAMBAH MENU ---
with st.sidebar:
    st.header("⚙️ Admin DTN")
    with st.expander("➕ Tambah Menu Baru"):
        kat = st.selectbox("Kategori", ["Makanan", "Minuman", "Snack"])
        nama = st.text_input("Nama Menu")
        hrg = st.number_input("Harga", min_value=0, step=500)
        
        if st.button("Simpan ke Daftar Menu", width='stretch'):
            new_item = pd.DataFrame([{"kategori": kat, "nama": nama, "harga": hrg}])
            updated_menu = pd.concat([df_menu, new_item], ignore_index=True)
            # Simpan ke tab "Menu" di Google Sheets
            conn.update(spreadsheet=URL_SHEET, worksheet="Menu", data=updated_menu)
            st.success(f"Menu {nama} berhasil ditambah!")
            st.rerun()

# --- HALAMAN UTAMA ---
st.title(f"🍴 {NAMA_TOKO}")
st.write(f"*{SLOGAN}*")

no_meja = st.text_input("📍 Meja", "01")

# Tabs Menu berdasarkan Kategori
categories = df_menu['kategori'].unique()
tabs = st.tabs(list(categories))

for i, cat in enumerate(categories):
    with tabs[i]:
        items = df_menu[df_menu['kategori'] == cat].reset_index()
        cols = st.columns(2)
        for idx, row in items.iterrows():
            if cols[idx % 2].button(f"{row['nama']}\nRp{row['harga']:,}", key=f"m_{idx}_{i}", width='stretch'):
                st.session_state.orders.append({"Item": row['nama'], "Harga": row['harga']})

st.divider()

# --- KERANJANG ---
if st.session_state.orders:
    st.subheader(f"🛒 Keranjang Meja {no_meja}")
    st.table(pd.DataFrame(st.session_state.orders))
    total = sum(i['Harga'] for i in st.session_state.orders)
    st.write(f"### Total: Rp{total:,}")
    
    if st.button("✅ BAYAR & SIMPAN CLOUD", type="primary", width='stretch'):
        waktu = datetime.now().strftime("%d/%m/%Y %H:%M")
        detail = ", ".join([i['Item'] for i in st.session_state.orders])
        
        new_row = pd.DataFrame([{"Waktu": waktu, "Meja": no_meja, "Total": total, "Detail": detail}])
        updated_sales = pd.concat([df_penjualan, new_row], ignore_index=True)
        # Simpan ke tab pertama (Sheet1)
        conn.update(spreadsheet=URL_SHEET, worksheet="Sheet1", data=updated_sales)
        
        st.session_state.last_receipt = {"waktu": waktu, "meja": no_meja, "items": st.session_state.orders, "total": total}
        st.session_state.orders = []
        st.rerun()

# --- STRUK ---
if st.session_state.last_receipt:
    r = st.session_state.last_receipt
    st.balloons()
    with st.container(border=True):
        st.markdown(f"<h3 style='text-align:center'>{NAMA_TOKO}</h3>", unsafe_allow_html=True)
        st.write(f"**Meja:** {r['meja']} | {r['waktu']}")
        st.write("---")
        for item in r['items']:
            st.text(f"{item['Item']:<18} Rp{item['Harga']:>8,}")
        st.write("---")
        st.markdown(f"### TOTAL: Rp{r['total']:,}")
    if st.button("PESANAN BARU", width='stretch'):
        st.session_state.last_receipt = None
        st.rerun()
