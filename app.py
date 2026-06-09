import streamlit as st
import pandas as pd
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
        # Secrets'ı JSON formatında okuyup sisteme güvenli şekilde veriyoruz
        creds_dict = json.loads(json.dumps(st.secrets["GOOGLE_CREDENTIALS"]))
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # Sadece "satis" sekmesine odaklanıyoruz
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

if satis_sheet:
    # Veri girişi
    col1, col2 = st.columns(2)
    with col1:
        musteri = st.text_input("Müşteri/Dükkan Adı")
        urun = st.text_input("Ürün Adı")
        miktar = st.number_input("Miktar (Metre)", min_value=0.1)
        fiyat = st.number_input("Birim Fiyat", min_value=0.0)
        notlar = st.text_input("Sipariş Notu")
        
        if st.button("Satışı Excel'e Kaydet"):
            tarih = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
            # [Tarih, Ürün, Miktar, Toplam, Müşteri, Ödenen, Kalan, Durum, Not]
            satis_sheet.append_row([
                tarih, urun, miktar, miktar*fiyat, 
                musteri, fiyat, 0, "Aktif", notlar # Örnek hesaplama
            ])
            st.success("Kaydedildi!")
            st.rerun()

    # Cari Liste (Tüm veriyi gösterir)
    st.subheader("Cari Kayıtlar")
    data = satis_sheet.get_all_records()
    st.dataframe(pd.DataFrame(data))
else:
    st.warning("Excel dosyasına bağlantı sağlanamadı. Lütfen interneti ve Google Cloud izinlerini kontrol et.")
