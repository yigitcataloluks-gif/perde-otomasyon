import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.set_page_config(page_title="Dükkan Satış & Stok", layout="wide", page_icon="🧵")

# --- LİNKLER ---
STOK_CSV_URL = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/gviz/tq?tqx=out:csv&sheet=Form+Yanıtları+1"
SATIŞLAR_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTzXUNpze1FKf3kpYTHGBZ-cqCrR8uOUqrHtbFahqr3D0qZ1_ZT_LXVb4auwSjUO1V2pp-3-ZF_6y47/pub?gid=1188156871&single=true&output=csv"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/formResponse"

# --- FONKSİYONLAR ---
def veri_yukle(url):
    try: return pd.read_csv(StringIO(requests.get(url, timeout=5).text))
    except: return pd.DataFrame()

# --- ARAYÜZ (Giriş & Tabs) ---
if "login" not in st.session_state: st.session_state["login"] = False
if not st.session_state["login"]:
    if st.text_input("Şifre:", type="password") == "perde123":
        st.session_state["login"] = True; st.rerun()
    st.stop()

if "sepet" not in st.session_state: st.session_state["sepet"] = []
stok_df = veri_yukle(STOK_CSV_URL)

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Satış & Fatura", "📦 Stok Ekle", "👥 Cariler", "🔍 Arama"])

with tab1:
    st.header("🛒 Çoklu Satış")
    musteri = st.text_input("👤 Müşteri:")
    
    # SEPET ALANI
    c1, c2 = st.columns(2)
    with c1: urun = st.selectbox("Ürün:", stok_df.iloc[:,1].unique() if not stok_df.empty else [])
    with c2: miktar = st.number_input("Metre:", value=1.0)
    
    if st.button("➕ Sepete Ekle"):
        st.session_state["sepet"].append({"urun": urun, "miktar": miktar})
        st.rerun()
        
    if st.session_state["sepet"]:
        st.write("---")
        toplam = sum(100 for i in st.session_state["sepet"]) # Buraya fiyat çekme mantığını koy
        st.subheader(f"🧾 Toplam Tutar: {toplam} TL")
        
        if st.button("💾 Satışı Tamamla ve Fatura Oluştur"):
            # 1. Kayıt
            payload = {"entry.823126487": musteri, "entry.1481546114": str(st.session_state["sepet"])}
            requests.post(FORM_URL, data=payload)
            # 2. Fatura (WhatsApp linki)
            mesaj = f"Sayın {musteri}, siparişiniz alındı. Toplam: {toplam} TL."
            fatura_link = f"https://wa.me/905000000000?text={mesaj}"
            st.success("✅ Kayıt başarılı!")
            st.link_button("🧾 Müşteriye WhatsApp'tan Fatura Gönder", fatura_link)
            st.session_state["sepet"] = []

with tab2:
    st.header("📦 Stoğa Ürün Ekle")
    st.components.v1.iframe("https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true", height=600)

with tab3:
    st.header("👥 Cariler")
    st.dataframe(veri_yukle(SATIŞLAR_CSV_URL), use_container_width=True)
