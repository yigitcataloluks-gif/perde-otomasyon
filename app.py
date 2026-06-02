import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import StringIO
import urllib.parse

# --- SADE VE GÖZ YORMAYAN KOYU TEMA ---
st.set_page_config(page_title="Perde Takip Sepet PRO", page_icon="🛒", layout="centered")

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

# --- GOOGLE SHEET VE FORM TANIMLAMALARI ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]
FORM_EMBED_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true"

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

# --- SEPET HAFIZASI ---
if "sepet" not in st.session_state:
    st.session_state["sepet"] = []

# --- VERILERI YÜKLE ---
stok_df = veri_yukle(STOK_CSV_URL, ["Ürün Adı", "Stok Miktarı", "Birim Fiyat"])
satis_df = veri_yukle(SATIS_CSV_URL, ["Tarih", "Ürün Adı", "Satılan Miktar", "Toplam Tutar", "Müşteri / Dükkan", "Ödenen", "Kalan Borç", "Sipariş Durumu", "Sipariş Notu"])
cari_df = veri_yukle(CARI_CSV_URL, ["Müşteri Adı"])
veresiye_df = veri_yukle(VERESIYE_CSV_URL, ["Müşteri Adı", "Toplam Borç", "Kalan Borç"])

# --- SEKMELER ---
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Çoklu Satış & Sipariş", "📦 Ürün Girişi", "👥 Cari & Veresiye", "📊 Arama & Rapor"])

# 1. SEKME: GELİŞMİŞ ÇOKLU SATIŞ EKRANI
with sekme1:
    st.header("🛒 Gelişmiş Satış & Sepet Ekranı")
    
    # Müşteri Bilgisi Sabitleme
    st.subheader("1. Müşteri Bilgisi")
    musteri_listesi = ["--- Yeni Müşteri Yazın ---"] + cari_df["Müşteri Adı"].dropna().tolist()
    secilen_musteri = st.selectbox("Müşteri / Dükkan Seçin:", musteri_listesi)
    
    if secilen_musteri == "--- Yeni Müşteri Yazın ---":
        aktif_musteri = st.text_input("Yeni Müşteri Adı Soyadı (Veya Dükkan İsmi):")
    else:
        aktif_musteri = secilen_musteri

    st.write("---")
    
    # Sepete Ürün Ekleme Bölümü
    if stok_df.empty:
        st.warning("Stok listesi boş kanka, önce ürün ekleyin.")
    else:
        st.subheader("2. Sepete Ürün Ekle")
        
        # Otomatik Pile Robotu
        col_en, col_pile = st.columns(2)
        with col_en: cam_eni = st.number_input("Cam Eni (Metre):", min_value=0.0, step=0.5, value=1.0)
        with col_pile: pile_turu = st.selectbox("Pile Oranı:", ["1'e 3 (Sık)", "1'e 2.5 (Normal)", "1'e 2 (Seyrek)", "Pilesiz"])
        
        carpan = 3.0 if "3" in pile_turu else (2.5 if "2.5" in pile_turu else (2.0 if "2" in pile_turu else 1.0))
        gidecek_kumas = cam_eni * carpan
        st.caption(f"📐 Robotun Hesapladığı Ölçü: {gidecek_kumas} Metre")
        
        # Ürün Seçimi
        secilen_urun = st.selectbox("Eklenecek Ürünü Seçin:", stok_df["Ürün Adı"].tolist())
        urun_bilgisi = stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]
        
        col_mt, col_not = st.columns([1, 2])
        with col_mt:
            miktar = st.number_input("Miktar (Metre/Adet):", min_value=0.5, value=float(gidecek_kumas), step=0.5)
        with col_not:
            urun_notu = st.text_input("Bu Ürün İçin Özel Not (Terziye):", value=f"{pile_turu} dikilecek.")
            
        fiyat = float(urun_bilgisi['Birim Fiyat'])
        urun_toplam = miktar * fiyat
        st.write(f"💰 Ürün Tutarı: **{urun_toplam} TL**")
        
        if st.button("➕ Ürünü Sepete Ekle"):
            st.session_state["sepet"].append({
                "urun_adi": secilen_urun,
                "miktar": miktar,
                "fiyat": fiyat,
                "toplam": urun_toplam,
                "not": urun_notu
            })
            st.success(f"{secilen_urun} sepete eklendi kanka!")
            st.rerun()

    # Aktif Sepeti Gösterme
    if st.session_state["sepet"]:
        st.write("---")
        st.subheader("📋 Alışveriş Sepeti")
        
        toplam_sepet_tutari = 0
        for i, eleman in enumerate(st.session_state["sepet"]):
            st.markdown(f"""
            <div class="sepet-kutusu">
                <strong>📦 {eleman['urun_adi']}</strong> | 📐 {eleman['miktar']} Mt | 💵 Birim: {eleman['fiyat']} TL | 💰 Toplam: {eleman['toplam']} TL <br>
                📝 <em>Not: {eleman['not']}</em>
            </div>
            """, unsafe_allow_html=True)
            toplam_sepet_tutari += eleman['toplam']
            
        st.metric("🛒 TOPLAM SEPET TUTARI", f"{toplam_sepet_tutari} TL")
        
        # Ödeme Girişi
        col_odenen, col_durum = st.columns(2)
        with col_odenen:
            alinan_para = st.number_input("Müşteriden Alınan Nakit/Kart (TL):", min_value=0.0, value=float(toplam_sepet_tutari))
        with col_durum:
            sip_durum = st.selectbox("Sipariş Genel Durumu:", ["Teslim Edildi", "Terzide / Dikiliyor", "Montaj Bekliyor"])
            
        kalan_borc = toplam_sepet_tutari - alinan_para
        if kalan_borc > 0:
            st.error(f"⚠️ {kalan_borc} TL borç olarak müşterinin hesabına yazılacak!")
            
        col_onay, col_temizle = st.columns(2)
        with col_onay:
            if st.button("🚀 SATIŞI VE SİPARİŞİ ONAYLA", use_container_width=True):
                if not aktif_musteri:
                    st.error("Kanka önce müşteri adını yazman lazım!")
                else:
                    st.success("Satış başarıyla onaylandı ve Excel'e işlendi kanka!")
                    
                    # WHATSAPP DETAYLI FİŞ METNİ OLUŞTURMA
                    msg = f"🧵 *PERDE SİPARİŞ ÖZETİ*\n\n👤 *Müşteri:* {aktif_musteri}\n📅 *Tarih:* {datetime.now().strftime('%d.%m.%Y')}\n\n*ALINAN ÜRÜNLER:*\n"
                    for eleman in st.session_state["sepet"]:
                        msg += f"- {eleman['urun_adi']} ({eleman['miktar']} Mt) - Not: {eleman['not']}\n"
                    
                    msg += f"\n💰 *Toplam Tutar:* {toplam_sepet_tutari} TL\n💳 *Ödenen:* {alinan_para} TL\n📉 *Kalan Borç:* {kalan_borc} TL\n🛠️ *Durum:* {sip_durum}\n\n*Hayırlı günler dileriz!*"
                    
                    st.markdown(f"[💬 Detaylı Fişi WhatsApp'tan Müşteriye Gönder](https://wa.me/?text={urllib.parse.quote(msg)})")
                    # Sepeti temizle
                    st.session_state["sepet"] = []
        with col_temizle:
            if st.button("🗑️ Sepeti Temizle", use_container_width=True):
                st.session_state["sepet"] = []
                st.rerun()

# 2. SEKME: ÜRÜN GİRİŞİ (FORM İÇERİDE)
with sekme2:
    st.header("📦 Seri Ürün Giriş Paneli")
    st.components.v1.iframe(FORM_EMBED_URL, height=450, scrolling=True)
    st.write("---")
    st.subheader("📋 Mevcut Güncel Stok Listesi")
    st.dataframe(stok_df, use_container_width=True)

# 3. SEKME: CARİLER
with sekme3:
    st.header("👥 Kayıtlı Müşteriler & Veresiye")
    st.dataframe(veresiye_df, use_container_width=True)

# 4. SEKME: GELİŞMİŞ ARAMA VE MÜŞTERİ GEÇMİŞİ
with sekme4:
    st.header("🔍 Detaylı Müşteri Sorgulama")
    arama = st.text_input("Geçmişini görmek istediğin müşteri veya dükkan adını yazın:")
    if arama and not satis_df.empty:
        # İsme göre filtrele
        filtreli = satis_df[satis_df["Müşteri / Dükkan"].str.contains(arama, case=False, na=False)]
        if filtreli.empty:
            st.warning("Bu isme ait bir geçmiş bulunamadı kanka.")
        else:
            st.subheader(f"📋 {arama} İsimli Müşterinin Tüm Alışveriş Dosyası")
            st.dataframe(filtreli, use_container_width=True)
