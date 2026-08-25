import streamlit as st
import database as db

# Veritabanını ilklendir
db.init_db()

# Oturum Durumu Kontrolü
if "user" not in st.session_state:
    st.session_state["user"] = None

# --- EĞER KULLANICI GİRİŞ YAPMAMIŞSA ---
if st.session_state["user"] is None:
    st.title("🔒 Kutluk B2B & Saha Yönetim Portalı")
    
    tab_login, tab_register = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol (Yeni İşletme)"])
    
    with tab_login:
        st.subheader("İşletme Girişi")
        login_email = st.text_input("E-Posta Adresi", key="login_email")
        login_password = st.text_input("Şifre", type="password", key="login_pw")
        
        if st.button("Giriş Yap", type="primary"):
            user_info = db.login_user(login_email, login_password)
            if user_info:
                st.session_state["user"] = user_info
                st.success(f"Hoş geldiniz, {user_info['full_name']}!")
                st.rerun()
            else:
                st.error("E-posta adresi veya şifre hatalı!")
                
    with tab_register:
        st.subheader("Yeni Üyelik Oluştur")
        with st.form("register_form"):
            reg_name = st.text_input("Ad Soyad")
            reg_phone = st.text_input("Cep Telefonu")
            reg_email = st.text_input("E-Posta Adresi")
            reg_address = st.text_area("İşyeri Adresi")
            reg_password = st.text_input("Şifre", type="password")
            reg_password_confirm = st.text_input("Şifre (Tekrar)", type="password")
            
            submit_btn = st.form_submit_button("Kayıt Ol")
            
            if submit_btn:
                if not reg_name or not reg_phone or not reg_email or not reg_password:
                    st.warning("Lütfen tüm zorunlu alanları doldurun.")
                elif reg_password != reg_password_confirm:
                    st.error("Şifreler birbiriyle eşleşmiyor!")
                else:
                    success, msg = db.register_user(reg_name, reg_phone, reg_email, reg_address, reg_password)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
    st.stop() # Giriş yapılmadığı sürece panelin kalanını yükleme

# --- KULLANICI GİRİŞ YAPTIYSA UYGULAMA AÇILIR ---
user = st.session_state["user"]

# Sol menüye oturum kapatma ve profil bilgisi
st.sidebar.write(f"👤 **{user['full_name']}**")
st.sidebar.caption(f"🏢 {user['address']}")
if st.sidebar.button("Çıkış Yap"):
    st.session_state["user"] = None
    st.rerun()
    
import streamlit as st
import database as db
import pandas as pd
from datetime import date
import io
import yfinance as yf

# Sayfa Yapılandırması
st.set_page_config(page_title="Otomotiv B2B Saha & Stok Takip", layout="wide")
db.tabloları_olustur()

# --- ÖZEL CSS (Göz Yormayan Tipografi ve Kayar Yazı CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Kayar Yazı Bandı Stili */
    .ticker-wrap {
        width: 100%;
        background-color: #1E293B;
        color: #94A3B8;
        padding: 10px 0;
        overflow: hidden;
        border-top: 1px solid #334155;
        border-bottom: 1px solid #334155;
        margin-top: 20px;
        white-space: nowrap;
    }
    
    .ticker-move {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%;
        animation: ticker 35s linear infinite;
    }
    
    .ticker-item {
        display: inline-block;
        padding: 0 30px;
        font-size: 14px;
        color: #E2E8F0;
    }
    
    @keyframes ticker {
        0% { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚗 Otomotiv B2B Yönetim Paneli")

# Sol Menü
menu = st.sidebar.radio("Modül Seçin", [
    "Ana Sayfa & Raporlar", 
    "Müşteri Yönetimi", 
    "Stok Yönetimi", 
    "Saha Ziyaretleri", 
    "Cari & Tahsilat Takibi"
])

musteri_listesi = db.musterileri_getir()
musteri_dict = {f"{m[1]} ({m[4]})": m[0] for m in musteri_listesi} if musteri_listesi else {}

# --- 1. ANA SAYFA & RAPORLAR ---
if menu == "Ana Sayfa & Raporlar":
    st.subheader("📊 Genel Durum & Raporlama")
    col1, col2 = st.columns(2)
    col1.metric("Toplam Müşteri Sayısı", len(musteri_listesi))
    col2.metric("Sistem Durumu", "Aktif", delta="Veritabanı Hazır")
    
    st.divider()
    
    tab1, tab2 = st.tabs(["Müşteri Listesi", "Tüm Saha Ziyaretleri"])
    
    with tab1:
        if musteri_listesi:
            df_m = pd.DataFrame(musteri_listesi, columns=["ID", "Firma Adı", "Yetkili", "Telefon", "Şehir", "Risk Limiti (₺)"])
            st.dataframe(df_m, use_container_width=True)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_m.to_excel(writer, index=False, sheet_name='Musteriler')
            
            st.download_button(
                label="📊 Müşteri Listesini Excel (.xlsx) Olarak İndir",
                data=buffer.getvalue(),
                file_name="Musteri_Listesi.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Kayıtlı müşteri yok.")
            
    with tab2:
        ziyaretler = db.saha_ziyaretleri_getir()
        if ziyaretler:
            df_z = pd.DataFrame(ziyaretler, columns=["Ziyaret ID", "Firma Adı", "Tarih", "Görüşme Notu"])
            st.dataframe(df_z, use_container_width=True)
        else:
            st.info("Henüz kaydedilmiş saha ziyareti bulunmuyor.")

# --- 2. MÜŞTERİ YÖNETİMİ ---
elif menu == "Müşteri Yönetimi":
    tab_ekle, tab_sil = st.tabs(["➕ Yeni Müşteri Ekle", "🗑️ Müşteri Sil"])
    
    with tab_ekle:
        st.subheader("Yeni Müşteri / Bayi Ekle")
        with st.form("musteri_formu"):
            col1, col2 = st.columns(2)
            with col1:
                firma_adi = st.text_input("Firma Adı")
                yetkili = st.text_input("Yetkili Kişi")
                telefon = st.text_input("Telefon")
            with col2:
                sehir = st.text_input("Şehir")
                risk_limiti = st.number_input("Risk Limiti (₺)", min_value=0.0, step=1000.0)
            
            if st.form_submit_button("Müşteriyi Kaydet"):
                if firma_adi:
                    db.musteri_ekle(firma_adi, yetkili, telefon, sehir, risk_limiti)
                    st.success(f"{firma_adi} kaydedildi!")
                    st.rerun()

    with tab_sil:
        st.subheader("Müşteri Kaydı Sil")
        if musteri_dict:
            silinecek_m = st.selectbox("Silinecek Müşteriyi Seçin", list(musteri_dict.keys()), key="sil_m")
            m_id_sil = musteri_dict[silinecek_m]
            
            st.warning(f"⚠️ **{silinecek_m}** firmasını kalıcı olarak silmek üzeresiniz!")
            if st.button("Müşteriyi Sistemden Sil", type="primary"):
                db.musteri_sil(m_id_sil)
                st.success("Müşteri kaydı silindi.")
                st.rerun()
        else:
            st.info("Silinecek kayıtlı müşteri bulunmuyor.")

# --- 3. STOK YÖNETİMİ ---
elif menu == "Stok Yönetimi":
    st.subheader("📦 Stok Listesi ve Yeni Ürün Ekle")
    stoklar = db.stoklari_getir()
    if stoklar:
        df_s = pd.DataFrame(stoklar, columns=["ID", "Stok Kodu", "Ürün Adı", "Stok Adedi", "Fiyat (₺)"])
        st.dataframe(df_s, use_container_width=True)
    
    with st.expander("➕ Yeni Ürün Ekle Formu"):
        with st.form("stok_formu"):
            stok_kodu = st.text_input("Stok Kodu (Örn: AKU-12V-70AH)")
            urun_adi = st.text_input("Ürün Adı")
            stok_miktari = st.number_input("Stok Adedi", min_value=0, step=1)
            satis_fiyati = st.number_input("Satış Fiyatı (₺)", min_value=0.0, step=50.0)
            
            if st.form_submit_button("Ürünü Kaydet"):
                if stok_kodu and urun_adi:
                    db.urun_ekle(stok_kodu, urun_adi, stok_miktari, satis_fiyati)
                    st.success(f"{urun_adi} eklendi!")
                    st.rerun()

# --- 4. SAHA ZİYARETLERİ ---
elif menu == "Saha Ziyaretleri":
    st.subheader("📍 Saha Ziyaret Kaydı")
    if musteri_dict:
        selected_m = st.selectbox("Müşteri Seçin", list(musteri_dict.keys()))
        z_tarih = st.date_input("Ziyaret Tarihi", date.today())
        notlar = st.text_area("Ziyaret Notları / Görüşme Detayı")
        
        if st.button("Ziyareti Kaydet"):
            db.saha_ziyareti_ekle(musteri_dict[selected_m], z_tarih, notlar)
            st.success("Saha ziyaret notu başarıyla eklendi!")
            st.rerun()
            
        st.divider()
        st.write("### Seçili Müşterinin Geçmiş Ziyaretleri")
        m_ziyaretler = db.saha_ziyaretleri_getir(musteri_dict[selected_m])
        if m_ziyaretler:
            st.dataframe(pd.DataFrame(m_ziyaretler, columns=["ID", "Firma", "Tarih", "Not"]), use_container_width=True)
    else:
        st.info("Henüz kayıtlı müşteri yok.")

# --- 5. CARİ & TAHSİLAT TAKİBİ ---
elif menu == "Cari & Tahsilat Takibi":
    st.subheader("💳 Cari İşlem & Bakiye Takibi")
    if musteri_dict:
        selected_m = st.selectbox("Müşteri Seçin", list(musteri_dict.keys()), key="cari_m")
        m_id = musteri_dict[selected_m]
        
        bakiye = db.musteri_bakiye_hesapla(m_id)
        st.metric("Güncel Açık Bakiye / Borç", f"{bakiye:,.2f} ₺", delta_color="inverse")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            islem_tipi = st.selectbox("İşlem Tipi", ["SATIS", "TAHSILAT"])
            tutar = st.number_input("Tutar (₺)", min_value=0.0, step=100.0)
            vade = st.date_input("Vade / Ödeme Tarihi", date.today())
            
            if st.button("İşlemi Kaydet"):
                db.cari_hareket_ekle(m_id, islem_tipi, tutar, vade)
                st.success("Cari hareket kaydedildi!")
                st.rerun()
                
        with col_c2:
            st.write("### Ekstre Geçmişi")
            ekstre = db.cari_ekstre_getir(m_id)
            if ekstre:
                st.dataframe(pd.DataFrame(ekstre, columns=["İşlem", "Tutar (₺)", "Vade", "Durum"]), use_container_width=True)
    else:
        st.info("Henüz kayıtlı müşteri yok.")

# --- CANLI DÖVİZ KURLARI BÖLÜMÜ ---
st.markdown("---")
st.subheader("💱 Canlı Piyasalar")

@st.cache_data(ttl=300)
def doviz_getir():
    try:
        usd = yf.Ticker("TRY=X").history(period="1d")['Close'].iloc[-1]
        eur = yf.Ticker("EURTRY=X").history(period="1d")['Close'].iloc[-1]
        gbp = yf.Ticker("GBPTRY=X").history(period="1d")['Close'].iloc[-1]
        return round(usd, 2), round(eur, 2), round(gbp, 2)
    except:
        return 36.50, 39.20, 46.80

usd_kuru, eur_kuru, gbp_kuru = doviz_getir()

d_col1, d_col2, d_col3, d_col4 = st.columns(4)
d_col1.metric("USD / TRY", f"{usd_kuru} ₺")
d_col2.metric("EUR / TRY", f"{eur_kuru} ₺")
d_col3.metric("GBP / TRY", f"{gbp_kuru} ₺")
d_col4.metric("Piyasa Durumu", "AÇIK", delta="Canlı Veri")

import feedparser

# --- CANLI OTOMOTİV HABERLERİ (RSS) ---
@st.cache_data(ttl=3600)  # Haberleri 1 saatte bir günceller
def canlı_otomotiv_haberleri_getir():
    try:
        # Google News Otomotiv RSS Akışı (Türkçe)
        rss_url = "https://news.google.com/rss/search?q=otomotiv+ak%C3%BC+ara%C3%A7&hl=tr&gl=TR&ceid=TR:tr"
        feed = feedparser.parse(rss_url)
        
        haber_listesi = []
        for entry in feed.entries[:6]:  # En son 6 otomotiv haberini al
            # Haber başlığı ve kaynak adını temiz biçimde biçimlendir
            baslik = entry.title.split(" - ")[0]
            kaynak = entry.title.split(" - ")[-1] if " - " in entry.title else "Gündem"
            haber_listesi.append(f"🔴 <b>{kaynak}:</b> {baslik}")
            
        return haber_listesi if haber_listesi else ["📌 Otomotiv piyasası canlı haber akışı aktif."]
    except:
        return ["📌 Otomotiv ve akü sektöründeki son gelişmeler canlı olarak güncellenmektedir."]

haberler = canlı_otomotiv_haberleri_getir()

# Kayar haber HTML içeriğini dinamik olarak oluştur
haber_html_items = "".join([f'<div class="ticker-item">{h}</div>' for h in haberler])

haber_html = f"""
<div class="ticker-wrap">
    <div class="ticker-move">
        {haber_html_items}
    </div>
</div>
"""
st.markdown(haber_html, unsafe_allow_html=True)

# --- SAYFA ALTI (FOOTER) ---
st.markdown(
    """
    <div style='text-align: center; color: #64748B; padding: 15px 0; font-size: 13px;'>
        Designed & Developed by <b>Ümit Tahir KUTLUK</b>
    </div>
    """,
    unsafe_allow_html=True
)