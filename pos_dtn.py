import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIG ---
NAMA_TOKO = "Dapur Teh Nunung (DTN)"
SLOGAN = "Makan Enak,,,Enak Makan,,,"
# Ganti URL di bawah ini dengan URL Google Sheets Anda
URL_SHEET = "https://docs.google.com/spreadsheets/d/1gRsF4YZtDLAhIRquST9I0UqxfnYqUVvPL9nq0IOFuTE/edit?usp=sharing"

st.set_page_config(page_title=NAMA_TOKO, layout="centered")

# Inisialisasi Koneksi ke Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi Memuat Menu (Tetap menggunakan CSV lokal untuk menu agar cepat)
def load_menu():
    if os.path.exists("menu.csv"):
        return pd.read_csv("menu.csv")
    return pd.DataFrame({'kategori': ['Makanan', 'Minuman'], 'nama': ['Nasi Timbel', 'Teh Manis'], 'harga': [25000, 5000]})

# --- UI & LOGIC ---
if 'orders' not in st.session_state: st.session_state.orders = []
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

st.title(f"🍴 {NAMA_TOKO}")
no_meja = st.text_input("📍 Meja", "01")

df_menu = load_menu()
tabs = st.tabs(list(df_menu['kategori'].unique()))

for i, cat in enumerate(df_menu['kategori'].unique()):
    with tabs[i]:
        items = df_menu[df_menu['kategori'] == cat].reset_index()
        cols = st.columns(2)
        for idx, row in items.iterrows():
            if cols[idx % 2].button(f"{row['nama']}\nRp{row['harga']:,}", key=f"m_{idx}_{i}", width='stretch'):
                st.session_state.orders.append({"Item": row['nama'], "Harga": row['harga']})

if st.session_state.orders:
    st.divider()
    st.subheader(f"🛒 Keranjang Meja {no_meja}")
    total = sum(i['Harga'] for i in st.session_state.orders)
    st.write(f"### Total: Rp{total:,}")
    
    if st.button("✅ PROSES BAYAR & SIMPAN KE CLOUD", type="primary", width='stretch'):
        waktu = datetime.now().strftime("%d/%m/%Y %H:%M")
        detail = ", ".join([i['Item'] for i in st.session_state.orders])
        
        # Simpan ke Google Sheets
        new_data = pd.DataFrame([{"Waktu": waktu, "Meja": no_meja, "Total": total, "Detail": detail}])
        existing_data = conn.read(spreadsheet=URL_SHEET)
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        conn.update(spreadsheet=URL_SHEET, data=updated_df)
        
        st.session_state.last_receipt = {"waktu": waktu, "meja": no_meja, "items": st.session_state.orders, "total": total}
        st.session_state.orders = []
        st.rerun()

# --- STRUK DIGITAL ---
if st.session_state.last_receipt:
    r = st.session_state.last_receipt
    st.balloons()
    with st.container(border=True):
        st.markdown(f"<h3 style='text-align:center'>{NAMA_TOKO}</h3>", unsafe_allow_html=True)
        for item in r['items']: st.text(f"{item['Item']:<18} Rp{item['Harga']:>8,}")
        st.markdown(f"--- \n ### TOTAL: Rp{r['total']:,}")
    if st.button("PESANAN BARU", width='stretch'):
        st.session_state.last_receipt = None
        st.rerun()

