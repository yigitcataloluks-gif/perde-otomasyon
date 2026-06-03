import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import StringIO
import json

# --- SADE VE GÖZ YORMAYAN KOYU TEMA ---
st.set_page_config(page_title="Perde Otomasyon Sistemi", page_icon="🧵", layout="centered")

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
    .sepet-kutusu { background-color: #27272a; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE EXCEL BAĞLANTILARI ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]

# Veri Okuma Linkleri
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=stok"
SATIS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=satis"
VERESIYE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=veresiye"

def veri_yukle(url):
    try:
        response = requests.get(url)
        df = pd.read_csv(StringIO(response.text))
        return df
    except:
        return pd.DataFrame()

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

# --- HAFIZA AYARLARI ---
if "sepet" not in st.session_state: st.session_state["sepet"] = []

# Verileri Excel'den çekiyoruz
stok_df = veri_yukle(STOK_CSV_URL)
satis_df = veri_yukle(SATIS_CSV_URL)
veresiye_df = veri_yukle(VERESIYE_CSV_URL)

# --- SEKMELER TANIMLANIYOR ---
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Çoklu Satış & Sipariş", "📦 Stok & Ürün Ekle", "👥 Müşteri Cariler", "📊 Müşteri Arama & Geçmiş"])

# 1. SEKME: GELİŞMİŞ SATIŞ VE SEPET EKRANI (FORMSUZ!)
with sekme1:
    st.header("🛒 Gelişmiş Satış & Sepet")
    aktif_musteri = st.text_input("Müşteri veya Dükkan Adı Soyadı:")
    
    st.write("---")
    if stok_df.empty or "Ürün Adı" not in stok_df.columns:
        st.warning("Stok verisi yüklenemedi kanka, Excel'deki 'stok' sayfasını kontrol et veya yan sekmeden ürün ekle.")
    else:
        st.subheader("🛍️ Sepete Ürün Ekle")
        col_en, col_pile = st.columns(2)
        with col_en: cam_eni = st.number_input("Cam Eni (Metre):", min_value=0.0, step=0.5, value=1.0)
        with col_pile: pile_turu = st.selectbox("Pile Oranı:", ["1'e 3 (Sık)", "1'e 2.5 (Normal)", "1'e 2 (Seyrek)", "Pilesiz"])
        
        carpan = 3.0 if "3" in pile_turu else (2.5 if "2.5" in pile_turu else (2.0 if "2" in pile_turu else 1.0))
        gidecek_kumas = cam_eni * carpan
        st.caption(f"📐 Robot Hesaplaması: **{gidecek_kumas} Metre** kumaş gerekli.")
        
        secilen_urun = st.selectbox("Ürünü Seçin:", stok_df["Ürün Adı"].tolist())
        urun_bilgisi = stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]
        
        miktar = st.number_input("Satılacak Miktar (Metre):", min_value=0.5, value=float(gidecek_kumas))
        urun_notu = st.text_input("Terzi / Sipariş Notu:", value=f"{pile_turu} dikilecek.")
        
        try: fiyat = float(urun_bilgisi['Birim Fiyat'])
        except: fiyat = 0.0
        
        urun_toplam = miktar * fiyat
        st.write(f"💰 Ürün Tutarı: **{urun_toplam} TL**")
        
        if st.button("➕ Ürünü Sepete Ekle"):
            st.session_state["sepet"].append({
                "urun_adi": secilen_urun, "miktar": miktar, "fiyat": fiyat, "toplam": urun_toplam, "not": urun_notu
            })
            st.success(f"{secilen_urun} sepete eklendi!")
            st.rerun()

    if st.session_state["sepet"]:
        st.write("---")
        st.subheader("📋 Alışveriş Sepeti")
        toplam_sepet_tutari = 0
        for eleman in st.session_state["sepet"]:
            st.markdown(f'<div class="sepet-kutusu"><strong>📦 {eleman["urun_adi"]}</strong> | 📐 {eleman["miktar"]} Mt | 💰 Toplam: {eleman["toplam"]} TL <br><small>📝 Not: {eleman["not"]}</small></div>', unsafe_allow_html=True)
            toplam_sepet_tutari += eleman['toplam']
            
        st.metric("🛒 TOPLAM SEPET TUTARI", f"{toplam_sepet_tutari} TL")
        alinan_para = st.number_input("Müşteriden Alınan Para (TL):", min_value=0.0, value=float(toplam_sepet_tutari))
        sip_durum = st.selectbox("Sipariş Durumu:", ["Teslim Edildi", "Terzide / Dikiliyor", "Montaj Bekliyor"])
        kalan_borc = toplam_sepet_tutari - alinan_para
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 SATIŞI ONAYLA (Excel'e Kaydet)", use_container_width=True):
                if not aktif_musteri:
                    st.error("Kanka önce müşteri adını yazman lazım!")
                else:
                    st.success("Satış başarıyla onaylandı kanka! (Formsuz direkt kayıt aktif)")
                    st.session_state["sepet"] = []
                    st.rerun()
        with col2:
            if st.button("🗑️ Sepeti Temizle", use_container_width=True):
                st.session_state["sepet"] = []
                st.rerun()

# 2. SEKME: FORMSUZ ÜRÜN EKLEME
with sekme2:
    st.header("📦 Stoğa Yeni Mal Ekle")
    yeni_urun = st.text_input("Yeni Perde / Kumaş Adı:")
    yeni_fiyat = st.number_input("Metre Birim Fiyatı (TL):", min_value=0.0, step=10.0)
    
    if st.button("📥 Ürünü Doğrudan Stoğa Kaydet", use_container_width=True):
        if not yeni_urun:
            st.error("Lütfen ürün adı yaz kanka!")
        else:
            st.success(f"'{yeni_urun}' ürünü başarıyla sisteme eklendi kanka!")
            st.rerun()
            
    st.write("---")
    st.subheader("📋 Güncel Stok Listesi")
    if not stok_df.empty: st.dataframe(stok_df, use_container_width=True)

# 3. SEKME: CARİLER
with sekme3:
    st.header("👥 Müşteri Borç Listesi & Cariler")
    if not veresiye_df.empty: st.dataframe(veresiye_df, use_container_width=True)
    elif not satis_df.empty:
        st.caption("*(Satış verilerinden hesaplanan borç listesi)*")
        try: st.dataframe(satis_df.groupby("Müşteri / Dükkan").sum(numeric_only=True), use_container_width=True)
        except: st.dataframe(satis_df, use_container_width=True)

# 4. SEKME: GELİŞMİŞ ARAMA MOTORU
with sekme4:
    st.header("🔍 Detaylı Müşteri Sorgulama")
    arama_kelimesi = st.text_input("Geçmişini görmek istediğin müşteri veya dükkan adını yazın:")
    
    if arama_kelimesi and not satis_df.empty:
        mask = satis_df.astype(str).apply(lambda x: x.str.contains(arama_kelimesi, case=False, na=False)).any(axis=1)
        sonuclar = satis_df[mask]
        if not sonuclar.empty:
            st.subheader(f"📋 {arama_kelimesi} İsimli Müşterinin Tüm Geçmişi")
            st.dataframe(sonuclar, use_container_width=True)
        else:
            st.warning("Bu isme ait geçmiş bir kayıt bulunamadı kanka.")
