import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIG ---
NAMA_TOKO = "Dapur Teh Nunung (DTN)"
SLOGAN = "Makan Enak,,,Enak Makan,,,"
MENU_FILE = "menu.csv"
LOG_FILE = "laporan_penjualan.csv"

def load_menu():
    if os.path.exists(MENU_FILE):
        return pd.read_csv(MENU_FILE)
    return pd.DataFrame({'kategori': ['Makanan', 'Minuman'], 'nama': ['Nasi Timbel', 'Teh Manis'], 'harga': [25000, 5000]})

def simpan_menu_callback():
    if st.session_state.input_nama:
        df = load_menu()
        new_row = pd.DataFrame({'kategori': [st.session_state.input_kategori], 'nama': [st.session_state.input_nama], 'harga': [st.session_state.input_harga]})
        pd.concat([df, new_row], ignore_index=True).to_csv(MENU_FILE, index=False)
        st.session_state.input_nama = ""
        st.session_state.input_harga = 0
        st.toast("✅ Menu Tersimpan!")

st.set_page_config(page_title=NAMA_TOKO, layout="centered")

if 'orders' not in st.session_state: st.session_state.orders = []
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

# --- UI ---
st.title(f"🍴 {NAMA_TOKO}")
with st.sidebar:
    st.header("⚙️ Admin")
    with st.expander("Tambah Menu"):
        st.selectbox("Kategori", ["Makanan", "Minuman", "Snack"], key="input_kategori")
        st.text_input("Nama", key="input_nama")
        st.number_input("Harga", min_value=0, step=1000, key="input_harga")
        st.button("Simpan", width='stretch', on_click=simpan_menu_callback)

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
    st.dataframe(pd.DataFrame(st.session_state.orders), width='stretch', hide_index=True)
    total = sum(i['Harga'] for i in st.session_state.orders)
    st.write(f"### Total: Rp{total:,}")
    if st.button("✅ PROSES BAYAR", type="primary", width='stretch'):
        waktu = datetime.now().strftime("%d/%m/%Y %H:%M")
        pd.DataFrame([{"Waktu": waktu, "Meja": no_meja, "Total": total}]).to_csv(LOG_FILE, mode='a', header=not os.path.exists(LOG_FILE), index=False)
        st.session_state.last_receipt = {"waktu": waktu, "meja": no_meja, "items": st.session_state.orders, "total": total}
        st.session_state.orders = []
        st.rerun()

if st.session_state.last_receipt:
    r = st.session_state.last_receipt
    st.balloons()
    with st.container(border=True):
        st.markdown(f"<h3 style='text-align:center'>{NAMA_TOKO}</h3><p style='text-align:center'>{SLOGAN}</p>", unsafe_allow_html=True)
        st.write(f"**Meja:** {r['meja']} | {r['waktu']}")
        for item in r['items']: st.text(f"{item['Item']:<18} Rp{item['Harga']:>8,}")
        st.markdown(f"--- \n ### TOTAL: Rp{r['total']:,}")
    if st.button("PESANAN BARU", width='stretch'):
        st.session_state.last_receipt = None
        st.rerun()