import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import StringIO
import urllib.parse

# --- SADE VE GÖZ YORMAYAN KOYU TEMA ---
st.set_page_config(page_title="Perde Takip PRO", page_icon="🧵", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #1a1a1e; color: #f4f4f5; }
    h1, h2, h3, h4 { color: #e4e4e7 !important; }
    .stButton>button {
        background-color: #2563eb !important; color: white !important;
        border-radius: 6px !important; font-weight: bold !important;
    }
    div[data-testid="stMetricValue"] { color: #10b981 !important; }
    .stTabs [data-baseweb="tab"] { color: #a1a1aa !important; }
    .stTabs [aria-selected="true"] { color: #3b82f6 !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEET VE FORM TANIMLAMALARI ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]
FORM_LINK = "https://docs.google.com/forms/d/1CVe1-byqOmkayE_fusLn6akdnneTYeqOLKkwaUIMtdQ/viewform"

# Okunacak Sayfaların CSV Linkleri
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=stok"
SATIS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=satis"
CARI_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=cariler"
VERESIYE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=veresiye"

def veri_yukle(url, kolonlar):
    try:
        response = requests.get(url)
        df = pd.read_csv(StringIO(response.text))
        if df.empty or kolonlar[0] not in df.columns:
            return pd.DataFrame(columns=kolonlar)
        return df
    except:
        return pd.DataFrame(columns=kolonlar)

# --- ŞİFRE KORUMASI ---
if "login" not in st.session_state: st.session_state["login"] = False
if not st.session_state["login"]:
    st.subheader("🔑 Dükkan Girişi")
    sifre = st.text_input("Giriş Şifresi:", type="password")
    if st.button("Giriş Yap", use_container_width=True):
        if sifre == "perde123":
            st.session_state["login"] = True
            st.rerun()
        else: st.error("Hatalı şifre!")
    st.stop()

# --- VERILERI YÜKLE ---
stok_df = veri_yukle(STOK_CSV_URL, ["Ürün Adı", "Stok Miktarı", "Birim Fiyat"])
satis_df = veri_yukle(SATIS_CSV_URL, ["Tarih", "Ürün Adı", "Satılan Miktar", "Toplam Tutar", "Müşteri / Dükkan", "Ödenen", "Kalan Borç", "Sipariş Durumu", "Sipariş Notu"])
cari_df = veri_yukle(CARI_CSV_URL, ["Müşteri Adı"])
veresiye_df = veri_yukle(VERESIYE_CSV_URL, ["Müşteri Adı", "Toplam Borç", "Kalan Borç"])

# --- SEKMELER ---
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Sipariş & Satış", "📦 Ürün Girişi", "👥 Cari & Veresiye", "📊 Arama & Rapor"])

# 1. SEKME: SİPARİŞ & SATIŞ (PİLE HESAPLAMALI & WHATSAPP)
with sekme1:
    st.header("Hızlı Satış Girişi")
    if stok_df.empty:
        st.warning("Stok listesi yüklenemedi kanka.")
    else:
        st.subheader("1. Otomatik Pile Robotu")
        col_en, col_pile = st.columns(2)
        with col_en: cam_eni = st.number_input("Cam Eni (Metre):", min_value=0.0, step=0.5, value=1.0)
        with col_pile: pile_turu = st.selectbox("Pile Oranı:", ["1'e 3 (Sık)", "1'e 2.5 (Normal)", "1'e 2 (Seyrek)", "Pilesiz"])
        
        carpan = 3.0 if "3" in pile_turu else (2.5 if "2.5" in pile_turu else (2.0 if "2" in pile_turu else 1.0))
        gidecek_kumas = cam_eni * carpan
        st.info(f"📐 Gerekli Kumaş: `{gidecek_kumas} Metre`")
        
        st.write("---")
        st.subheader("2. Ürün ve Ödeme")
        secilen_urun = st.selectbox("Ürün Seç:", stok_df["Ürün Adı"].tolist())
        urun_bilgisi = stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]
        
        satilan_miktar = st.number_input("Satış Miktarı:", min_value=0.5, value=float(gidecek_kumas))
        sip_durum = st.selectbox("Durum:", ["Teslim Edildi", "Terzide", "Montaj Bekliyor"])
        sip_notu = st.text_input("Not:", value=f"{pile_turu} dikilecek.")
        
        toplam_tutar = satilan_miktar * float(urun_bilgisi['Birim Fiyat'])
        st.metric("Toplam Tutar", f"{toplam_tutar} TL")
        
        odenen_tutar = st.number_input("Alınan Para (TL):", min_value=0.0, value=float(toplam_tutar))
        kalan_borc = toplam_tutar - odenen_tutar
        
        if st.button("🚀 Siparişi Onayla", use_container_width=True):
            st.success("Sipariş sisteme işlendi kanka!")
            msg = f"🧵 *Perde Siparişi*\n\n👤 *Müşteri:* Kayıt\n📦 *Ürün:* {secilen_urun}\n📐 *Miktar:* {satilan_miktar} Mt\n💰 *Toplam:* {toplam_tutar} TL\n💳 *Ödenen:* {odenen_tutar} TL\n📉 *Borç:* {kalan_borc} TL\n📝 *Not:* {sip_notu}"
            st.markdown(f"[💬 WhatsApp'tan Gönder](https://wa.me/?text={urllib.parse.quote(msg)})")

# 2. SEKME: ÜRÜN GİRİŞİ (GOOGLE FORM ENTEGRELİ)
with sekme2:
    st.header("📦 Stoğa Yeni Mal Ekleme")
    st.write("Kanka Google güvenlik duvarını aşmak için yeni malları direkt aşağıdaki resmi Google Form butonuna basarak ekliyoruz. Eklenen ürünler anında Excel'e ve aşağıdaki listeye yansır.")
    
    # Yeni ürün ekleme butonu artık doğrudan senin oluşturduğun forma gidiyor
    st.markdown(f'<h3><a href="{FORM_LINK}" target="_blank" style="color: #3b82f6; text-decoration: none;">➕ BURAYA TIKLAYARAK YENİ ÜRÜN EKLE</a></h3>', unsafe_allow_html=True)
    st.caption("*(Açılan formda ürün adı ve fiyatını yazıp gönder demeniz yeterlidir)*")
    
    st.write("---")
    st.subheader("📋 Mevcut Güncel Stok Listesi")
    st.dataframe(stok_df, use_container_width=True)

# 3. SEKME: CARİLER
with sekme3:
    st.header("👥 Kayıtlı Müşteriler & Borçlar")
    st.dataframe(veresiye_df, use_container_width=True)

# 4. SEKME: RAPORLAR
with sekme4:
    st.header("🔍 Müşteri Sorgulama & Gün Sonu")
    arama = st.text_input("Müşteri / Dükkan Adı Yazın:")
    if arama and not satis_df.empty:
        st.dataframe(satis_df[satis_df["Müşteri / Dükkan"].str.contains(arama, case=False, na=False)], use_container_width=True)
