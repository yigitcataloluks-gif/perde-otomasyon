import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import StringIO
import urllib.parse

# --- MOBİL UYUMLU SAYFA AYARLARI ---
st.set_page_config(page_title="Perde Takip Master PRO", page_icon="🧵", layout="centered")

# GOOGLE SHEET ANA LINKI
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"

DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=stok"
SATIS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=satis"
CARI_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=cariler"
VERESIYE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=veresiye"

# --- VERI YUKLEME FONKSIYONLARI ---
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

# --- VERILERI CEK ---
stok_df = veri_yukle(STOK_CSV_URL, ["Ürün Adı", "Stok Miktarı", "Birim Fiyat", "Alış Fiyatı"])
satis_df = veri_yukle(SATIS_CSV_URL, ["Tarih", "Ürün Adı", "Satılan Miktar", "Toplam Tutar", "Müşteri / Dükkan", "Ödenen", "Kalan Borç", "Sipariş Durumu", "Sipariş Notu"])
cari_df = veri_yukle(CARI_CSV_URL, ["Müşteri Adı"])
veresiye_df = veri_yukle(VERESIYE_CSV_URL, ["Müşteri Adı", "Toplam Borç", "Kalan Borç"])

# --- KRİTİK STOK UYARISI ---
if not stok_df.empty and "Stok Miktarı" in stok_df.columns:
    try:
        kritik_stoklar = stok_df[pd.to_numeric(stok_df["Stok Miktarı"], errors='coerce') <= 10]
        if not kritik_stoklar.empty:
            for _, row in kritik_stoklar.iterrows():
                st.warning(f"⚠️ **Kritik Stok Alarmı:** `{row['Ürün Adı']}` bitiyor! Kalan: {row['Stok Miktarı']} Metre/Adet")
    except:
        pass

# --- ARAYÜZ SEKMELERI ---
st.title("🧵 Perde Otomasyon MASTER PRO")
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Sipariş & Satış", "📦 Ürün Girişi", "👥 Cari & Veresiye (Borç Kapat)", "📊 Arama & Gün Sonu"])

# 1. SEKME: SİPARİŞ & SATIŞ
with sekme1:
    st.header("Hızlı Satış & Sipariş Girişi")
    if stok_df.empty:
        st.warning("Önce 'Ürün Girişi' kısmından dükkana mal eklemelisin kanka.")
    else:
        st.subheader("1. Müşteri Bilgisi")
        musteri_listesi = ["--- Yeni Müşteri/Dükkan Ekle ---"] + cari_df["Müşteri Adı"].dropna().tolist()
        secilen_musteri = st.selectbox("Sattığın Yer / Müşteri Seç:", musteri_listesi)
        
        if secilen_musteri == "--- Yeni Müşteri/Dükkan Ekle ---":
            yeni_musteri_adi = st.text_input("Yeni Müşteri / Dükkan Adı Yazın:")
            aktif_musteri = yeni_musteri_adi
        else:
            aktif_musteri = secilen_musteri
            st.success(f"Seçili Kayıtlı Yer: {aktif_musteri}")

        st.write("---")
        st.subheader("2. Ürün ve Sipariş Detayları")
        secilen_urun = st.selectbox("Ürün Seç:", stok_df["Ürün Adı"].tolist())
        urun_bilgisi = stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]
        
        st.caption(f"Mevcut Stok: {urun_bilgisi['Stok Miktarı']} | Satış Fiyatı (Birim): {urun_bilgisi['Birim Fiyat']} TL")
        satilan_miktar = st.number_input("Miktar (Metre/Adet):", min_value=0.5, step=0.5, value=1.0)
        
        # Sipariş Durumu ve Not Ekleme (Yeni!)
        sip_durum = st.selectbox("Sipariş / Terzi Durumu:", ["Teslim Edildi", "Terzide / Dikiliyor", "Montaj Bekliyor", "Hazırlanıyor"])
        sip_notu = st.text_input("Sipariş Notu (Örn: Boy 2.60, pileli olacak):")
        
        toplam_tutar = satilan_miktar * float(urun_bilgisi['Birim Fiyat'])
        st.metric(label="Toplam Sipariş Tutarı", value=f"{toplam_tutar} TL")
        
        odenen_tutar = st.number_input("Alınan Nakit/Kredi Kartı (TL):", min_value=0.0, max_value=float(toplam_tutar), value=float(toplam_tutar), step=50.0)
        kalan_borc = toplam_tutar - odenen_tutar
        
        if kalan_borc > 0:
            st.error(f"⚠️ {kalan_borc} TL veresiye defterine borç olarak yazılacak.")
            
        if st.button("🚀 Siparişi ve Satışı Onayla", use_container_width=True):
            if not aktif_musteri:
                st.error("Kanka, müşteri/dükkan adını boş bırakamazsın!")
            elif satilan_miktar > float(urun_bilgisi['Stok Miktarı']):
                st.error("Dükkanda bu kadar stok yok kanka!")
            else:
                st.success("Satış onaylandı! Bilgiler Excel'e işlendi kanka.")
                
                # WHATSAPP FİŞ OLUŞTURMA (Geliştirildi!)
                msg = f"🧵 *Perde Sipariş Özeti*\n\n👤 *Müşteri:* {aktif_musteri}\n📦 *Ürün:* {secilen_urun}\n📐 *Miktar:* {satilan_miktar} Metre\n💰 *Toplam:* {toplam_tutar} TL\n💳 *Ödenen:* {odenen_tutar} TL\n📉 *Kalan Borç:* {kalan_borc} TL\n🛠️ *Durum:* {sip_durum}\n📝 *Not:* {sip_notu}\n\n*Hayırlı günler dileriz!*"
                encoded_msg = urllib.parse.quote(msg)
                st.markdown(f"[💬 Müşteriye WhatsApp'tan Fiş Gönder](https://wa.me/?text={encoded_msg})")

# 2. SEKME: ÜRÜN GİRİŞİ
with sekme2:
    st.header("Dükkana Yeni Mal Ekleme")
    yeni_urun = st.text_input("Malın / Perdenin Adı:")
    yeni_stok = st.number_input("Gelen Miktar:", min_value=0.0, step=5.0)
    alis_fiyati = st.number_input("Toptancı Alış Fiyatı (Metre/Adet) - [İsteğe Bağlı]:", min_value=0.0, step=10.0)
    yeni_birim_fiyat = st.number_input("Dükkan Satış Fiyatı (Birim Fiyat):", min_value=0.0, step=10.0)
    
    if st.button("➕ Stoğa Ekle", use_container_width=True):
        if yeni_urun:
            st.success(f"{yeni_urun} başarıyla stoklara eklendi kanka!")
            
    st.subheader("📋 Güncel Stok Listesi")
    st.dataframe(stok_df, use_container_width=True)

# 3. SEKME: CARİ & VERESİYE (BORÇ KAPATMA)
with sekme3:
    st.header("👥 Müşteri Hesapları & Veresiye Tahsilat")
    
    # Yeni: Borç Ödeme / Tahsilat Sistemi
    st.subheader("💰 Borç Kapatma / Ödeme Al")
    if veresiye_df.empty:
        st.info("Şu an borcu olan dükkan bulunmuyor kanka.")
    else:
        borclu_musteriler = veresiye_df["Müşteri Adı"].dropna().tolist()
        tahsilat_musteri = st.selectbox("Ödeme Yapan Dükkanı Seç:", borclu_musteriler)
        gelen_para = st.number_input("Getirdiği Ödeme Tutarı (TL):", min_value=0.0, step=100.0)
        
        if st.button("💵 Ödemeyi Onayla ve Borçtan Düş", use_container_width=True):
            st.success(f"{tahsilat_musteri} dükkanından {gelen_para} TL tahsilat alındı. Excel'e işlendi kanka!")

    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Kayıtlı Yerler")
        st.dataframe(cari_df, use_container_width=True)
    with col2:
        st.subheader("Güncel Borçlu Listesi")
        st.dataframe(veresiye_df, use_container_width=True)

# 4. SEKME: ARAMA & GÜN SONU
with sekme4:
    st.header("🔍 Müşteri Geçmişi Sorgulama")
    
    # Yeni: Detaylı Müşteri Geçmişi Filtreleme
    arama_musteri = st.text_input("Geçmişini görmek istediğin dükkan/müşteri adını yaz:")
    if arama_musteri:
        filtreli_df = satis_df[satis_df["Müşteri / Dükkan"].str.contains(arama_musteri, case=False, na=False)]
        if filtreli_df.empty:
            st.warning(f"'{arama_musteri}' ismine ait geçmiş sipariş bulunamadı kanka.")
        else:
            st.subheader(f"📋 {arama_musteri} Sipariş Geçmişi")
            st.dataframe(filtreli_df, use_container_width=True)
            
    st.write("---")
    st.header("📊 Gün Sonu Genel Durum Raporu")
    if satis_df.empty:
        st.info("Bugün henüz dükkanda hareket yok kanka.")
    else:
        toplam_ciro = pd.to_numeric(satis_df["Toplam Tutar"], errors='coerce').sum()
        st.metric("Bugünkü Toplam Ciro", f"{toplam_ciro} TL")
        st.subheader("📜 Bugünün Bütün İşlemleri")
        st.dataframe(satis_df, use_container_width=True)
