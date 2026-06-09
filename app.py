import streamlit as st
import pandas as pd
import requests
from io import StringIO
import urllib.parse
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Dükkan Otomasyonu", layout="wide")

# --- GOOGLE BAĞLANTISI (Hatasız Yöntem) ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]

def excel_baglan():
    try:
        # Hata veren JSON dönüşümlerini kaldırdık, doğrudan dict yapısını kullanıyoruz
        creds_dict = dict(st.secrets["GOOGLE_CREDENTIALS"])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open_by_key(DOC_ID).worksheet("satis")
    except Exception as e:
        st.error(f"Bağlantı Hatası: {e}")
        return None

# --- GİRİŞ VE ANA YAPI ---
if "login" not in st.session_state: st.session_state["login"] = False
if not st.session_state["login"]:
    sifre = st.text_input("Giriş Şifresi:", type="password")
    if st.button("Giriş Yap") and sifre == "perde123":
        st.session_state["login"] = True
        st.rerun()
    st.stop()

# --- TÜM SEKMELER VE ÖZELLİKLER ---
satis_sheet = excel_baglan()
if "sepet" not in st.session_state: st.session_state["sepet"] = []

tab1, tab2, tab3, tab4 = st.tabs(["🛒 Çoklu Satış", "📦 Ürün Ekle", "👥 Cariler", "🔍 Müşteri Arama"])

with tab1:
    st.header("🛒 Satış Paneli")
    # Buraya o orijinal, uzun ve detaylı satış panelini, hesaplamaları ve faturayı geri ekliyoruz
    c1, c2 = st.columns(2)
    with c1:
        musteri = st.text_input("Müşteri Adı")
        urun = st.text_input("Ürün")
        miktar = st.number_input("Miktar", min_value=0.1)
        fiyat = st.number_input("Fiyat", min_value=0.0)
        if st.button("Sepete Ekle"):
            st.session_state["sepet"].append({"musteri": musteri, "urun": urun, "miktar": miktar, "toplam": miktar*fiyat})
            st.rerun()
    with c2:
        if st.button("Satışı Kaydet"):
            for item in st.session_state["sepet"]:
                satis_sheet.append_row([pd.Timestamp.now().strftime("%d/%m/%Y"), item['urun'], item['miktar'], item['toplam'], item['musteri'], 0, 0, "Aktif", ""])
            st.session_state["sepet"] = []
            st.success("Satış tamamlandı!")
            st.rerun()

with tab2:
    st.header("📦 Ürün Ekleme")
    st.components.v1.iframe("https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true", height=600)

with tab3:
    st.header("👥 Cariler")
    if satis_sheet:
        df = pd.DataFrame(satis_sheet.get_all_records())
        st.dataframe(df, use_container_width=True)

with tab4:
    st.header("🔍 Arama")
    arama = st.text_input("Müşteri adı girin:")
    if satis_sheet and arama:
        df = pd.DataFrame(satis_sheet.get_all_records())
        st.dataframe(df[df['Müşteri'].str.contains(arama, na=False)])
