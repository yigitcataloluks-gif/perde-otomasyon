import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import StringIO

# --- MOBİL UYUMLU SAYFA AYARLARI ---
st.set_page_config(page_title="Perde Takip", page_icon="🧵", layout="centered")

# GOOGLE SHEET ANA LINKI (SENIN LINKIN KANKA)
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"

# Linki CSV formatına çeviren sihirli dokunuş
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=stok"
SATIS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=satis"

def stok_yukle():
    try:
        response = requests.get(STOK_CSV_URL)
        df = pd.read_csv(StringIO(response.text))
        # Eğer kolonlar boş geldiyse düzelt
        if df.empty or "Ürün Adı" not in df.columns:
            return pd.DataFrame(columns=["Ürün Adı", "Stok Miktarı", "Birim Fiyat"])
        return df
    except:
        return pd.DataFrame(columns=["Ürün Adı", "Stok Miktarı", "Birim Fiyat"])

def satis_yukle():
    try:
        response = requests.get(SATIS_CSV_URL)
        df = pd.read_csv(StringIO(response.text))
        if df.empty or "Ürün Adı" not in df.columns:
            return pd.DataFrame(columns=["Tarih", "Ürün Adı", "Satılan Miktar", "Toplam Tutar", "Müşteri / Dükkan"])
        return df
    except:
        return pd.DataFrame(columns=["Tarih", "Ürün Adı", "Satılan Miktar", "Toplam Tutar", "Müşteri / Dükkan"])

# --- ŞİFRE KORUMASI ---
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    st.subheader("🔑 Dükkan Girişi")
    sifre = st.text_input("Giriş Şifresi:", type="password")
    if st.button("Giriş Yap", use_container_width=True):
        if sifre == "perde123":
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("Hatalı şifre!")
    st.stop()

# --- MOBİL ARAYÜZ ---
st.title("🧵 Perde Otomasyon")
sekme1, sekme2, sekme3 = st.tabs(["🛒 Satış", "📦 Ürün Ekle", "📊 Gün Sonu"])

# 1. SEKME: SATIŞ
with sekme1:
    st.header("Hızlı Satış")
    stok_df = stok_yukle()
    if stok_df.empty or len(stok_df) == 0:
        st.warning("Önce 'Ürün Ekle' kısmından dükkana mal girişi yapmalısın kanka.")
    else:
        musteri_adi = st.text_input("Müşteri / Dükkan Adı:")
        secilen_urun = st.selectbox("Ürün Seç:", stok_df["Ürün Adı"].tolist())
        urun_bilgisi = stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]
        
        st.caption(f"Stok: {urun_bilgisi['Stok Miktarı']} | Fiyat: {urun_bilgisi['Birim Fiyat']} TL")
        satilan_miktar = st.number_input("Miktar (Metre/Adet):", min_value=0.5, step=0.5, value=1.0)
        toplam_fiyat = satilan_miktar * float(urun_bilgisi['Birim Fiyat'])
        
        st.metric(label="Toplam Tutar", value=f"{toplam_fiyat} TL")
        
        st.info("💡 Not: Satış onaylandığında verileriniz dükkan hafızasına işlenir.")
        if st.button("🚀 Satışı Onayla", use_container_width=True):
            if not musteri_adi:
                st.error("Lütfen satışı yaptığınız kişi veya dükkan adını yazın kanka!")
            elif satilan_miktar > float(urun_bilgisi['Stok Miktarı']):
                st.error("Stok yetersiz!")
            else:
                st.success(f"Satış başarılı! Excel'e gidip kontrol edebilirsin kanka.")

# 2. SEKME: ÜRÜN EKLE
with sekme2:
    st.header("Yeni Mal Girişi")
    yeni_urun_adi = st.text_input("Ürün Adı:")
    yeni_stok = st.number_input("Miktar:", min_value=0.0, step=1.0)
    yeni_fiyat = st.number_input("Fiyat (TL):", min_value=0.0, step=10.0)
    
    st.subheader("📋 Mevcut Stok Raporu")
    st.dataframe(stok_df, use_container_width=True)

# 3. SEKME: GÜN SONU
with sekme3:
    st.header("Gün Raporu")
    satis_df = satis_yukle()
    if satis_df.empty:
        st.info("Bugün henüz kaydedilmiş bir satış bulunamadı.")
    else:
        st.dataframe(satis_df, use_container_width=True)
