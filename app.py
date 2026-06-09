import streamlit as st
import pandas as pd
import requests
from io import StringIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Perdeci Otomasyon", layout="wide")

# --- GOOGLE BAĞLANTISI ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]

def excel_baglan():
    try:
        # Secrets verisini düz bir sözlüğe çevirerek hatayı kesin çözüyoruz
        secrets_dict = dict(st.secrets["GOOGLE_CREDENTIALS"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(secrets_dict, [
            "https://spreadsheets.google.com/feeds", 
            "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(creds)
        return client.open_by_key(DOC_ID).worksheet("satis")
    except Exception as e:
        st.error(f"Bağlantı Hatası: {e}")
        return None

# --- GİRİŞ KONTROLÜ ---
if "login" not in st.session_state: st.session_state["login"] = False
if not st.session_state["login"]:
    sifre = st.text_input("Giriş Şifresi:", type="password")
    if st.button("Giriş Yap") and sifre == "perde123":
        st.session_state["login"] = True
        st.rerun()
    st.stop()

# --- ARAYÜZ ---
st.header("🧵 Perdeci Satış Paneli")
satis_sheet = excel_baglan()

if "sepet" not in st.session_state: st.session_state["sepet"] = []

col1, col2 = st.columns(2)
with col1:
    musteri = st.text_input("Müşteri/Dükkan Adı")
    urun = st.text_input("Ürün Adı")
    miktar = st.number_input("Miktar (Metre)", min_value=0.1)
    fiyat = st.number_input("Birim Fiyat", min_value=0.0)
    notlar = st.text_input("Sipariş Notu")
    
    if st.button("Sepete Ekle"):
        st.session_state["sepet"].append({"urun": urun, "miktar": miktar, "toplam": miktar*fiyat, "musteri": musteri, "not": notlar})
        st.rerun()

with col2:
    st.subheader("Sepet ve Kayıt")
    toplam = sum(i['toplam'] for i in st.session_state["sepet"])
    st.write(f"Toplam Tutar: {toplam} TL")
    odenen = st.number_input("Ödenen (Kaparo)", min_value=0.0)
    
    if st.button("Satışı Excel'e Kaydet"):
        tarih = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
        for item in st.session_state["sepet"]:
            # Senin istediğin sütun sırası: 
            # [Tarih, Ürün, Miktar, Toplam, Müşteri, Ödenen, Kalan, Durum, Not]
            satis_sheet.append_row([
                tarih, item['urun'], item['miktar'], item['toplam'], 
                item['musteri'], odenen, item['toplam'] - odenen, "Aktif", item['not']
            ])
        st.session_state["sepet"] = []
        st.success("Kaydedildi!")
        st.rerun()

# --- CARİ LİSTE ---
if satis_sheet:
    data = satis_sheet.get_all_records()
    st.dataframe(pd.DataFrame(data))
