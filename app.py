import streamlit as st
import pandas as pd
import requests
from io import StringIO
import urllib.parse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- TEMA VE AYARLAR ---
st.set_page_config(page_title="Dükkan Satış Otomasyonu", page_icon="🧵", layout="wide")

# --- GOOGLE EXCEL BAĞLANTISI ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form+Yanıtları+1"

def excel_baglan():
    try:
        creds_json = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)
        # Sekme adın "satis" olmalı
        sheet = client.open_by_key(DOC_ID).worksheet("satis")
        return sheet
    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
        return None

def stok_yukle(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200: return pd.read_csv(StringIO(response.text))
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- OTURUM VE GİRİŞ ---
if "login" not in st.session_state: st.session_state["login"] = False
if not st.session_state["login"]:
    st.subheader("🔑 Dükkan Girişi")
    sifre = st.text_input("Şifre:", type="password")
    if st.button("Giriş Yap"):
        if sifre == "perde123":
            st.session_state["login"] = True
            st.rerun()
    st.stop()

if "sepet" not in st.session_state: st.session_state["sepet"] = []

stok_df = stok_yukle(STOK_CSV_URL)
satis_sheet = excel_baglan()

# --- ANA PANEL ---
st.header("🛒 Satış & Cari Paneli")
c1, c2 = st.columns([1, 1])

with c1:
    musteri_adi = st.text_input("Müşteri Adı:")
    urun_listesi = stok_df.iloc[:, 1].dropna().unique().tolist() if not stok_df.empty else []
    secilen_urun = st.selectbox("Ürün:", urun_listesi)
    miktar = st.number_input("Miktar (Metre):", min_value=0.1, value=1.0)
    birim_fiyat = st.number_input("Birim Fiyat:", min_value=0.0, value=100.0)
    notlar = st.text_input("Sipariş Notu:")
    
    if st.button("Sepete Ekle"):
        st.session_state["sepet"].append({"urun": secilen_urun, "miktar": miktar, "fiyat": birim_fiyat, "toplam": miktar*birim_fiyat, "not": notlar})
        st.rerun()

with c2:
    st.subheader("Sepet")
    if st.session_state["sepet"]:
        toplam_tutar = sum(item['toplam'] for item in st.session_state["sepet"])
        st.write(f"Toplam Tutar: {toplam_tutar} TL")
        odenen = st.number_input("Ödenen:", min_value=0.0, value=toplam_tutar)
        
        if st.button("Satışı Kaydet"):
            su_an = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
            for item in st.session_state["sepet"]:
                # SENİN EXCEL SÜTUNLARINA GÖRE GÜNCELLENMİŞ KAYIT SATIRI:
                # [Tarih, Ürün, Miktar, Toplam, Müşteri, Ödenen, Kalan, Durum, Not]
                satis_sheet.append_row([
                    su_an, item['urun'], item['miktar'], item['toplam'], 
                    musteri_adi, odenen, item['toplam']-odenen, "Aktif", item['not']
                ])
            st.session_state["sepet"] = []
            st.success("Satış kaydedildi!")
            st.rerun()

# --- CARİ TABLOSU ---
if satis_sheet:
    data = satis_sheet.get_all_records()
    st.dataframe(pd.DataFrame(data))
