import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# --- MOBİL UYUMLU SAYFA AYARLARI ---
st.set_page_config(page_title="Perde Takip", page_icon="🧵", layout="centered")

# GOOGLE SHEET BAĞLANTISI
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit?gid=2100858186#gid=2100858186"

try:
    gc = gspread.public_link(SHEET_LINK)
    stok_sheet = gc.worksheet("stok")
    satis_sheet = gc.worksheet("satis")
except Exception as e:
    st.error("Google Sheet bağlantısı kurulamadı. Linki kontrol et kanka.")

def stok_yukle():
    data = stok_sheet.get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["Ürün Adı", "Stok Miktarı", "Birim Fiyat"])

def satis_yukle():
    data = satis_sheet.get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["Tarih", "Ürün Adı", "Satılan Miktar", "Toplam Tutar"])

# --- ŞİFRE KORUMASI ---
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    st.subheader("🔑 Dükkan Girişi")
    sifre = st.text_input("Giriş Şifresi:", type="password")
    if st.button("Giriş Yap", use_container_width=True):
        if sifre == "perde123": # Abinin şifresi bu, istersen değiştirebilirsin
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
    if stok_df.empty:
        st.warning("Önce 'Ürün Ekle' kısmından dükkana mal girişi yapmalısın.")
    else:
        secilen_urun = st.selectbox("Ürün Seç:", stok_df["Ürün Adı"].tolist())
        urun_bilgisi = stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]
        
        st.caption(f"Stok: {urun_bilgisi['Stok Miktarı']} | Fiyat: {urun_bilgisi['Birim Fiyat']} TL")
        satilan_miktar = st.number_input("Miktar (Metre/Adet):", min_value=0.5, step=0.5, value=1.0)
        toplam_fiyat = satilan_miktar * float(urun_bilgisi['Birim Fiyat'])
        
        st.metric(label="Toplam Tutar", value=f"{toplam_fiyat} TL")
        
        if st.button("🚀 Satışı Onayla", use_container_width=True):
            if satilan_miktar > float(urun_bilgisi['Stok Miktarı']):
                st.error("Stok yetersiz!")
            else:
                # Stoğu güncelle (Google Sheet üzerinde)
                cell = stok_sheet.find(secilen_urun)
                yeni_stok = float(urun_bilgisi['Stok Miktarı']) - satilan_miktar
                stok_sheet.update_cell(cell.row, 2, yeni_stok)
                
                # Satışı kaydet
                tarih_str = datetime.now().strftime("%d-%m-%Y %H:%M")
                satis_sheet.append_row([tarih_str, secilen_urun, satilan_miktar, toplam_fiyat])
                
                st.success("Satış kaydedildi!")
                st.rerun()

# 2. SEKME: ÜRÜN EKLE
with sekme2:
    st.header("Yeni Mal Girişi")
    yeni_urun_adi = st.text_input("Ürün Adı:")
    yeni_stok = st.number_input("Miktar:", min_value=0.0, step=1.0)
    yeni_fiyat = st.number_input("Fiyat (TL):", min_value=0.0, step=10.0)
    
    if st.button("➕ Dükkana Ekle", use_container_width=True):
        if yeni_urun_adi:
            stok_df = stok_yukle()
            if yeni_urun_adi in stok_df["Ürün Adı"].values:
                cell = stok_sheet.find(yeni_urun_adi)
                eski_stok = float(stok_df[stok_df["Ürün Adı"] == yeni_urun_adi].iloc[0]['Stok Miktarı'])
                stok_sheet.update_cell(cell.row, 2, eski_stok + yeni_stok)
                stok_sheet.update_cell(cell.row, 3, yeni_fiyat)
            else:
                stok_sheet.append_row([yeni_urun_adi, yeni_stok, yeni_fiyat])
            st.success("Ürün başarıyla eklendi/güncellendi!")
            st.rerun()
            
    st.subheader("📋 Mevcut Stok")
    st.dataframe(stok_yukle(), use_container_width=True)

# 3. SEKME: GÜN SONU
with sekme3:
    st.header("Gün Raporu")
    satis_df = satis_yukle()
    if satis_df.empty:
        st.info("Bugün henüz satış yapılmadı.")
    else:
        toplam_ciro = pd.to_numeric(satis_df["Toplam Tutar"]).sum()
        st.metric("Bugünkü Toplam Ciro", f"{toplam_ciro} TL")
        st.dataframe(satis_df, use_container_width=True)
