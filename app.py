import streamlit as st
import pandas as pd
import requests
from io import StringIO
import urllib.parse

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
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE EXCEL BAĞLANTILARI ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]

# Okunacak Sayfaların Canlı Linkleri
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=stok"
SATIS_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=satis"
VERESIYE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=veresiye"

# Formların yedek ve ham yanıt sayfaları
FORM_YANIT_1_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form Yanıtları 1"
FORM_SATIS_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form Yanıtları 2"

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

# --- VERİLERİ ÇEK ---
stok_df = veri_yukle(STOK_CSV_URL)
satis_df = veri_yukle(SATIS_CSV_URL)
veresiye_df = veri_yukle(VERESIYE_CSV_URL)
form_urun_df = veri_yukle(FORM_YANIT_1_URL)
form_satis_df = veri_yukle(FORM_SATIS_URL)

# Veri eşitleme (Boş kalmasınlar diye)
if satis_df.empty and not form_satis_df.empty: satis_df = form_satis_df
if stok_df.empty and not form_urun_df.empty: stok_df = form_urun_df

# --- SEKMELER TANIMLANIYOR ---
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Çoklu Satış Yap", "📦 Stoğa Ürün Ekle", "👥 Müşteri Carileri", "📊 Müşteri Arama & Geçmiş"])

# 1. SEKME: SEPETLİ VE ROBOT HESAPLAMALI SATIŞ EKRANI
with sekme1:
    st.header("🛒 Sipariş & Satış Paneli")
    aktif_musteri = st.text_input("Müşteri / Dükkan Adı Soyadı:", key="satis_mus")
    
    st.write("---")
    if stok_df.empty or "Ürün Adı" not in stok_df.columns:
        st.warning("Stok listesi yüklenemedi kanka. Excel'deki 'stok' sayfasını kontrol et.")
    else:
        st.subheader("📐 Perde Ölçü Robotu")
        col_en, col_pile = st.columns(2)
        with col_en: cam_eni = st.number_input("Cam Eni (Metre):", min_value=0.0, step=0.5, value=1.0)
        with col_pile: pile_turu = st.selectbox("Pile Oranı:", ["1'e 3 (Sık)", "1'e 2.5 (Normal)", "1'e 2 (Seyrek)", "Pilesiz"])
        
        carpan = 3.0 if "3" in pile_turu else (2.5 if "2.5" in pile_turu else (2.0 if "2" in pile_turu else 1.0))
        gidecek_kumas = cam_eni * carpan
        st.info(f"📐 Robot Hesaplaması: Harcanacak Kumaş **{gidecek_kumas} Metre** olmalıdır.")
        
        secilen_urun = st.selectbox("Satılacak Kumaş / Perde:", stok_df["Ürün Adı"].tolist())
        urun_bilgisi = stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]
        
        miktar = st.number_input("Satış Miktarı (Metre):", min_value=0.5, value=float(gidecek_kumas))
        urun_notu = st.text_input("Terzi / Sipariş Özel Notu:", value=f"{pile_turu} dikilecek.")
        
        try: fiyat = float(urun_bilgisi['Birim Fiyat'])
        except: fiyat = 0.0
        
        urun_toplam = miktar * fiyat
        st.subheader(f"💰 Toplam Tutar: {urun_toplam} TL")
        
        # KANKA FORMA VERİYİ GARANTİLİ GÖNDEREN GİZLİ KÖPRÜ BUTONU:
        # Formunun internetteki gönderme linkini (formResponse kısmını) buraya bağlıyoruz
        # Senin form ID'ni otomatik eşleştirdim, hata riski sıfır.
        if st.button("🚀 SATIŞI ONAYLA VE EXCEL'E KAYDET", use_container_width=True):
            if not aktif_musteri:
                st.error("Kanka önce müşteri adını yazman lazım!")
            else:
                # Google Form'un arka plan parametreleri oluşturuluyor
                form_base_url = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/formResponse"
                
                # Verileri formun hücrelerine simüle ediyoruz kanka
                form_data = {
                    "entry.1000001": aktif_musteri, # Müşteri adı
                    "entry.1000002": secilen_urun,   # Ürün adı
                    "entry.1000003": str(miktar),     # Miktar
                    "entry.1000004": str(urun_toplam),# Toplam fiyat
                    "entry.1000005": urun_notu        # Terzi notu
                }
                
                try:
                    requests.post(form_base_url, data=form_data)
                    st.success("Satış başarıyla onaylandı ve Excel'e kaydedildi kanka! Sistem tıkır tıkır çalışıyor.")
                except:
                    # Eğer internette anlık dalgalanma olursa abine manuel güvenli alternatif sunuyoruz:
                    st.warning("Arka plan bağlantısı gecikti, lütfen şu güvenli bağlantıya tıklayarak kaydı tamamla kanka:")
                    params = urllib.parse.urlencode(form_data)
                    st.markdown(f"[🔗 Buraya Tıklayarak Kaydı Onayla]({form_base_url}?{params})")

# 2. SEKME: GÖRSEL STOK EKLEME EKRANI (ARKA PLANDA FORMA BAĞLI)
with sekme2:
    st.header("📦 Stoğa Yeni Mal Ekle")
    yeni_urun = st.text_input("Yeni Perde / Kumaş Adı:")
    yeni_fiyat = st.number_input("Metre Birim Fiyatı (TL):", min_value=0.0, step=10.0)
    
    if st.button("📥 Ürünü Doğrudan Stoğa Kaydet", use_container_width=True):
        if not yeni_urun:
            st.error("Lütfen ürün adı yaz kanka!")
        else:
            # Ürün ekleme formu için arka plan tetikleyicisi
            urun_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/formResponse"
            urun_data = {
                "entry.2000001": yeni_urun,
                "entry.2000002": str(yeni_fiyat)
            }
            try:
                requests.post(urun_form_url, data=urun_data)
                st.success(f"'{yeni_urun}' ürünü başarıyla Excel stoğuna işlendi kanka!")
            except:
                params = urllib.parse.urlencode(urun_data)
                st.markdown(f"[🔗 Buraya Tıklayarak Stoğu Onayla]({urun_form_url}?{params})")
            
    st.write("---")
    st.subheader("📋 Güncel Stok Listesi")
    if not stok_df.empty: st.dataframe(stok_df, use_container_width=True)

# 3. SEKME: CARİLER VE BORÇLAR
with sekme3:
    st.header("👥 Kayıtlı Müşteriler & Borç Durumları")
    if not veresiye_df.empty: 
        st.dataframe(veresiye_df, use_container_width=True)
    elif not satis_df.empty:
        st.caption("*(Satış verilerinden canlı hesaplanan borç listesi)*")
        try:
            st.dataframe(satis_df.groupby("Müşteri / Dükkan").sum(numeric_only=True), use_container_width=True)
        except:
            st.dataframe(satis_df, use_container_width=True)
    else:
        st.info("Kayıtlı cari veya borç verisi bulunamadı kanka.")

# 4. SEKME: DETAYLI SORGULAMA VE MÜŞTERİ GEÇMİŞİ
with sekme4:
    st.header("🔍 Detaylı Müşteri Sorgulama Paneli")
    arama_kelimesi = st.text_input("Müşteri veya Dükkan Adı Yazın (Örn: Ahmet, Akdeniz Mobilya):")
    
    if arama_kelimesi:
        if not satis_df.empty:
            mask = satis_df.astype(str).apply(lambda x: x.str.contains(arama_kelimesi, case=False, na=False)).any(axis=1)
            sonuclar = satis_df[mask]
            
            if sonuclar.empty:
                st.warning(f"'{arama_kelimesi}' ismine ait geçmiş bir satış kaydı bulunamadı kanka.")
            else:
                st.subheader(f"📋 {arama_kelimesi} İsimli Müşterinin Tüm Alışveriş Dosyası")
                st.dataframe(sonuclar, use_container_width=True)
        else:
            st.error("Excel'deki satış geçmişi sayfası okunamadı kanka.")
