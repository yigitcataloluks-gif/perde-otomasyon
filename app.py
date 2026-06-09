import streamlit as st
import pandas as pd
import requests
from io import StringIO
import urllib.parse

# --- SADE VE GÖZ YORMAYAN KOYU TEMA ---
st.set_page_config(page_title="Dükkan Satış & Stok Otomasyonu", page_icon="🧵", layout="wide")

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
    .sepet-kart {
        background-color: #27272a; padding: 12px; 
        border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #2563eb;
    }
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE EXCEL BAĞLANTILARI (Sadece Stok Okumak İçin) ---
SHEET_LINK = "https://docs.google.com/spreadsheets/d/1ePbMgh3JEflaJ5ZfDp8xQ_rrq0A4U9R-i1RVd3oHN5s/edit"
DOC_ID = SHEET_LINK.split("/d/")[1].split("/")[0]
STOK_CSV_URL = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/gviz/tq?tqx=out:csv&sheet=Form+Yanıtları+1"

def veri_yukle(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text))
        return pd.DataFrame()
    except:
        return pd.DataFrame()

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

# --- KALICI BELLEK ---
if "sepet" not in st.session_state: st.session_state["sepet"] = []
if "fatura_hazir" not in st.session_state: st.session_state["fatura_hazir"] = False
if "son_satis_bilgileri" not in st.session_state: st.session_state["son_satis_bilgileri"] = {}
if "gercek_satis_listesi" not in st.session_state: st.session_state["gercek_satis_listesi"] = []

# --- STOĞU CANLI ÇEK ---
stok_df = veri_yukle(STOK_CSV_URL)
if not stok_df.empty:
    stok_df.columns = [stok_df.columns[0], "Ürün Adı", "Birim Fiyat"] if len(stok_df.columns) >= 3 else ["Zaman", "Ürün Adı", "Birim Fiyat"][:len(stok_df.columns)]

# --- SEKMELER ---
sekme1, sekme2, sekme3, sekme4 = st.tabs(["🛒 Çoklu Satış & Sepet Paneli", "📦 Stoğa Ürün Ekle", "👥 Müşteri Cariler", "📊 Müşteri Arama & Geçmiş"])

# 1. SEKME: ÇOKLU SATIŞ PANELİ
with sekme1:
    st.header("🛒 Gelişmiş Sipariş & Çoklu Satış")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        musteri_adi = st.text_input("👤 Müşteri / Dükkan Adı Soyadı:")
    with col_m2:
        musteri_telefon = st.text_input("📱 Müşteri Telefon Numarası (İsteğe Bağlı):")

    st.write("---")

    if stok_df.empty or "Ürün Adı" not in stok_df.columns:
        st.warning("⚠️ Stokta hiç ürün yok kanka. Lütfen önce 'Stoğa Ürün Ekle' sekmesinden ürün ekleyin.")
    else:
        col_sol, col_sag = st.columns([1.2, 1])
        
        with col_sol:
            st.subheader("🛍️ Sepete Ürün Ekle")
            
            c1, c2 = st.columns(2)
            with c1: cam_eni = st.number_input("📐 Cam Eni (Metre):", min_value=0.0, step=0.5, value=1.0)
            with c2: pile_turu = st.selectbox("🧵 Pile Oranı:", ["1'e 3 (Sık)", "1'e 2.5 (Normal)", "1'e 2 (Seyrek)", "Pilesiz"])
            
            carpan = 3.0 if "3" in pile_turu else (2.5 if "2.5" in pile_turu else (2.0 if "2" in pile_turu else 1.0))
            gidecek_kumas = cam_eni * carpan
            st.caption(f"🤖 Robot Hesaplaması: Gerekli Kumaş Kumaş Miktarı **{gidecek_kumas} Metre**")

            urun_listesi = stok_df["Ürün Adı"].dropna().unique().tolist()
            secilen_urun = st.selectbox("📦 Satılacak Kumaşı Seçin:", urun_listesi)
            
            urun_row = stok_df[stok_df["Ürün Adı"] == secilen_urun].iloc[0]
            try: birim_fiyat = float(urun_row['Birim Fiyat'])
            except: birim_fiyat = 0.0
            
            st.info(f"💰 Seçilen Ürünün Metre Fiyatı: {birim_fiyat} TL")
            
            miktar = st.number_input("📏 Satış Miktarı (Metre):", min_value=0.1, value=float(gidecek_kumas) if gidecek_kumas > 0 else 1.0)
            urun_notu = st.text_input("📝 Terzi / Dikim Notu:", value=f"{pile_turu} dikilecek.")
            
            toplam_urun_fiyati = miktar * birim_fiyat
            
            if st.button("➕ Ürünü Sepete Ekle", use_container_width=True):
                st.session_state["sepet"].append({
                    "urun": secilen_urun,
                    "miktar": miktar,
                    "fiyat": birim_fiyat,
                    "toplam": toplam_urun_fiyati,
                    "not": urun_notu
                })
                st.success(f"'{secilen_urun}' sepete eklendi!")
                st.rerun()

        with col_sag:
            st.subheader("📋 Güncel Sepetiniz")
            if not st.session_state["sepet"]:
                st.info("Sepetiniz şu an boş kanka. Soldan ürün ekleyin.")
            else:
                toplam_sepet_tutari = 0.0
                sepet_ozeti_yazi = ""
                for idx, eleman in enumerate(st.session_state["sepet"]):
                    st.markdown(f"""
                    <div class="sepet-kart">
                        <strong>{eleman['urun']}</strong><br>
                        📐 Miktar: {eleman['miktar']} Mt | Tutar: {eleman['toplam']} TL<br>
                        <small>📝 Not: {eleman['not']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    toplam_sepet_tutari += eleman['toplam']
                    sepet_ozeti_yazi += f"{eleman['urun']} ({eleman['miktar']}Mt), "
                
                st.markdown(f"### 🧾 Toplam Tutar: {toplam_sepet_tutari} TL")
                
                alinan_para = st.number_input("💵 Alınan Kaparo / Ödeme (TL):", min_value=0.0, value=toplam_sepet_tutari)
                kalan_borc = toplam_sepet_tutari - alinan_para
                st.write(f"🔴 Kalan Borç (Veresiye): **{kalan_borc} TL**")
                
                c_b1, c_b2 = st.columns(2)
                with c_b1:
                    if st.button("💾 Satışı Tamamla & Kaydet", use_container_width=True):
                        if not musteri_adi:
                            st.error("Kanka kaydetmek için önce Müşteri Adı yazmalısın!")
                        else:
                            su_an = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                            
                            st.session_state["son_satis_bilgileri"] = {
                                "musteri": musteri_adi,
                                "sepet": st.session_state["sepet"].copy(),
                                "toplam": toplam_sepet_tutari,
                                "alinan": alinan_para,
                                "kalan": kalan_borc,
                                "tarih": su_an
                            }
                            
                            # KANKA HESAPLAMA KOLAYLIĞI: Tabloda matematik yapabilmek için sayıları saf haliyle (float) listeye atıyoruz.
                            yeni_cari_kayit = {
                                "Tarih / Zaman": su_an,
                                "Müşteri / Dükkan": musteri_adi,
                                "Satılan Ürün Detayı": sepet_ozeti_yazi.strip(", "),
                                "Toplam Tutar (TL)": float(toplam_sepet_tutari),
                                "Alınan Kaparo (TL)": float(alinan_para),
                                "Kalan Net Borç (TL)": float(kalan_borc)
                            }
                            st.session_state["gercek_satis_listesi"].append(yeni_cari_kayit)
                            
                            st.session_state["fatura_hazir"] = True
                            st.session_state["sepet"] = []
                            st.toast("Satış başarıyla carilere kaydedildi! 👥", icon="💾")
                            st.rerun()
                with c_b2:
                    if st.button("🗑️ Sepeti Boşalt", use_container_width=True):
                        st.session_state["sepet"] = []
                        st.session_state["fatura_hazir"] = False
                        st.rerun()

    # --- FATURA GÖSTERİMİ VE REHBER SEÇMELİ WHATSAPP ---
    if st.session_state["fatura_hazir"]:
        st.write("---")
        st.subheader("🧾 Müşteri Satış Faturası")
        info = st.session_state["son_satis_bilgileri"]
        
        fatura_metni = f"========================================\n"
        fatura_metni += f"             SATIŞ FİŞİ / ÖZET          \n"
        fatura_metni += f" Tarih: {info['tarih']}\n"
        fatura_metni += f" Müşteri: {info['musteri']}\n"
        fatura_metni += f"----------------------------------------\n"
        
        whatsapp_urunler = ""
        for s in info['sepet']:
            fatura_metni += f" * {s['urun']}\n"
            fatura_metni += f"   {s['miktar']} Mt x {s['fiyat']} TL = {s['toplam']} TL\n"
            fatura_metni += f"   Not: {s['not']}\n"
            whatsapp_urunler += f"- {s['urun']} ({s['miktar']} Mt): {s['toplam']} TL\n"
            
        fatura_metni += f"----------------------------------------\n"
        fatura_metni += f" TOPLAM TUTAR : {info['toplam']} TL\n"
        fatura_metni += f" ALINAN NAKİT : {info['alinan']} TL\n"
        fatura_metni += f" KALAN BORÇ   : {info['kalan']} TL\n"
        fatura_metni += f"========================================"
        
        st.code(fatura_metni)
        
        wp_mesaj = f"*Hayırlı İşler, Sipariş Özetiniz:*\n\n"
        wp_mesaj += f"👤 *Müşteri:* {info['musteri']}\n"
        wp_mesaj += f"📅 *Tarih:* {info['tarih']}\n\n"
        wp_mesaj += f"📦 *Alınan Ürünler:*\n{whatsapp_urunler}\n"
        wp_mesaj += f"💰 *Toplam Tutar:* {info['toplam']} TL\n"
        wp_mesaj += f"💵 *Ödenen Kaparo:* {info['alinan']} TL\n"
        wp_mesaj += f"📉 *Kalan Borç:* {info['kalan']} TL\n\n"
        wp_mesaj += f"Bizi tercih ettiğiniz için teşekkür ederiz!"
        
        encoded_wp = urllib.parse.quote(wp_mesaj)
        wp_link = f"https://web.whatsapp.com/send?text={encoded_wp}"
        
        st.markdown(f'<a href="{wp_link}" target="_blank"><button style="background-color: #25d366; color: white; border: none; padding: 12px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%;">💬 Faturayı Gönder (Açılan Ekrandan Kişiyi Seçin)</button></a>', unsafe_allow_html=True)

# 2. SEKME: ÜRÜN EKLEME FORMU
with sekme2:
    st.header("📦 Stoğa Yeni Mal Ekleme")
    st.components.v1.iframe("https://docs.google.com/forms/d/e/1FAIpQLSd_culVxwiQH_wUY9TnPn53fnvuuZDqx9b64cLJU7A3mBYWVw/viewform?embedded=true", height=600, scrolling=True)

# 3. SEKME: MÜŞTERİ CARİLERİ (KANKA BURAYA GENEL TOPLAMLAR EKLENDİ!)
with sekme3:
    st.header("👥 Kayıtlı Müşteriler & Borç Durumları")
    if st.session_state["gercek_satis_listesi"]:
        df_cariler = pd.DataFrame(st.session_state["gercek_satis_listesi"])
        st.dataframe(df_cariler, use_container_width=True)
        
        st.write("---")
        # KANKA EKLEME: Tablodaki değerleri toplayıp dev esnaf panosu yapıyoruz
        toplam_ciro = df_cariler["Toplam Tutar (TL)"].sum()
        toplam_alinan = df_cariler["Alınan Kaparo (TL)"].sum()
        toplam_kalan_borc = df_cariler["Kalan Net Borç (TL)"].sum()
        
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            st.metric(label="📊 Toplam Yapılan Satış (Ciro)", value=f"{toplam_ciro:,.2f} TL")
        with col_t2:
            st.metric(label="💰 Kasaya Giren Toplam Nakit", value=f"{toplam_alinan:,.2f} TL")
        with col_t3:
            # Dışarıdaki toplam alacak, kırmızımsı uyarıyla çok net duracak
            st.metric(label="🔴 Dışarıdaki Toplam Alacak (Veresiye)", value=f"{toplam_kalan_borc:,.2f} TL")
    else:
        st.info("Uygulamada henüz yapılmış bir satış kaydı bulunmuyor kanka.")

# 4. SEKME: DETAYLI MÜŞTERİ GEÇMİŞİ ARAMA
with sekme4:
    st.header("🔍 Detaylı Müşteri Sorgulama")
    arama_kelimesi = st.text_input("Müşteri adı veya dükkan adı yazın kanka:")
    
    if arama_kelimesi:
        if st.session_state["gercek_satis_listesi"]:
            df_cariler = pd.DataFrame(st.session_state["gercek_satis_listesi"])
            mask = df_cariler.astype(str).apply(lambda x: x.str.contains(arama_kelimesi, case=False, na=False)).any(axis=1)
            sonuclar = df_cariler[mask]
            if not sonuclar.empty:
                st.dataframe(sonuclar, use_container_width=True)
            else:
                st.warning("Bu isme ait geçmiş bir kayıt bulunamadı kanka.")
        else:
            st.info("Sistemde arama yapacak kayıtlı satış bulunmuyor.")
