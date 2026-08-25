import sqlite3

def vt_baglan():
    """Veritabanı bağlantısı oluşturur."""
    conn = sqlite3.connect("otomotiv_b2b.db")
    return conn

def tabloları_olustur():
    """Gerekli tüm B2B tablolarını sıfırdan kurar."""
    conn = vt_baglan()
    cursor = conn.cursor()

    # 1. Müşteri Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS musteriler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        firma_adi TEXT NOT NULL,
        yetkili_kisi TEXT,
        telefon TEXT,
        sehir TEXT,
        risk_limiti REAL DEFAULT 0
    )
    """)

    # 2. Stok Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stoklar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stok_kodu TEXT UNIQUE NOT NULL,
        urun_adi TEXT NOT NULL,
        stok_miktari INTEGER DEFAULT 0,
        satis_fiyati REAL DEFAULT 0
    )
    """)

    # 3. Saha Ziyaretleri Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saha_ziyaretleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        musteri_id INTEGER,
        ziyaret_tarihi DATE,
        notlar TEXT,
        FOREIGN KEY (musteri_id) REFERENCES musteriler(id)
    )
    """)

    # 4. Cari İşlemler ve Vade Takibi Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cari_hareketler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        musteri_id INTEGER,
        islem_tipi TEXT,
        tutar REAL,
        vade_tarihi DATE,
        odeme_durumu TEXT DEFAULT 'BEKLIYOR',
        FOREIGN KEY (musteri_id) REFERENCES musteriler(id)
    )
    """)

    conn.commit()
    conn.close()

def musteri_ekle(firma_adi, yetkili_kisi, telefon, sehir, risk_limiti):
    """Yeni müşteri/bayi kaydı ekler."""
    conn = vt_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO musteriler (firma_adi, yetkili_kisi, telefon, sehir, risk_limiti)
        VALUES (?, ?, ?, ?, ?)
    """, (firma_adi, yetkili_kisi, telefon, sehir, risk_limiti))
    conn.commit()
    conn.close()

def urun_ekle(stok_kodu, urun_adi, stok_miktari, satis_fiyati):
    """Yeni stok/ürün kaydı ekler."""
    conn = vt_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO stoklar (stok_kodu, urun_adi, stok_miktari, satis_fiyati)
        VALUES (?, ?, ?, ?)
    """, (stok_kodu, urun_adi, stok_miktari, satis_fiyati))
    conn.commit()
    conn.close()

def musterileri_getir():
    """Tüm kayıtlı müşterileri listeler."""
    conn = vt_baglan()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM musteriler")
    veriler = cursor.fetchall()
    conn.close()
    return veriler

def saha_ziyareti_ekle(musteri_id, ziyaret_tarihi, notlar):
    """Saha ziyaret notu kaydeder."""
    conn = vt_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO saha_ziyaretleri (musteri_id, ziyaret_tarihi, notlar)
        VALUES (?, ?, ?)
    """, (musteri_id, ziyaret_tarihi, notlar))
    conn.commit()
    conn.close()

def cari_hareket_ekle(musteri_id, islem_tipi, tutar, vade_tarihi):
    """Satış veya tahsilat işlemi kaydeder."""
    conn = vt_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cari_hareketler (musteri_id, islem_tipi, tutar, vade_tarihi)
        VALUES (?, ?, ?, ?)
    """, (musteri_id, islem_tipi, tutar, vade_tarihi))
    conn.commit()
    conn.close()

def stoklari_getir():
    """Tüm stok listesini getirir."""
    conn = vt_baglan()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stoklar")
    veriler = cursor.fetchall()
    conn.close()
    return veriler
def saha_ziyaretleri_getir(musteri_id=None):
    """Ziyaret geçmişini müşteri detaylarıyla getirir."""
    conn = vt_baglan()
    cursor = conn.cursor()
    if musteri_id:
        cursor.execute("""
            SELECT z.id, m.firma_adi, z.ziyaret_tarihi, z.notlar 
            FROM saha_ziyaretleri z 
            JOIN musteriler m ON z.musteri_id = m.id 
            WHERE z.musteri_id = ?
            ORDER BY z.ziyaret_tarihi DESC
        """, (musteri_id,))
    else:
        cursor.execute("""
            SELECT z.id, m.firma_adi, z.ziyaret_tarihi, z.notlar 
            FROM saha_ziyaretleri z 
            JOIN musteriler m ON z.musteri_id = m.id 
            ORDER BY z.ziyaret_tarihi DESC
        """)
    veriler = cursor.fetchall()
    conn.close()
    return veriler

def cari_ekstre_getir(musteri_id):
    """Müşterinin satış ve tahsilat geçmişini getirir."""
    conn = vt_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT islem_tipi, tutar, vade_tarihi, odeme_durumu 
        FROM cari_hareketler 
        WHERE musteri_id = ? 
        ORDER BY vade_tarihi DESC
    """, (musteri_id,))
    veriler = cursor.fetchall()
    conn.close()
    return veriler

def musteri_bakiye_hesapla(musteri_id):
    """Müşterinin toplam borç ve tahsilat dengesini hesaplar."""
    conn = vt_baglan()
    cursor = conn.cursor()
    cursor.execute("SELECT islem_tipi, tutar FROM cari_hareketler WHERE musteri_id = ?", (musteri_id,))
    hareketler = cursor.fetchall()
    conn.close()
    
    toplam_satis = sum(h[1] for h in hareketler if h[0] == 'SATIS')
    toplam_tahsilat = sum(h[1] for h in hareketler if h[0] == 'TAHSILAT')
    bakiye = toplam_satis - toplam_tahsilat
    return bakiye
def musteri_sil(musteri_id):
    """Seçilen müşteriyi veritabanından siler."""
    conn = vt_baglan()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM musteriler WHERE id = ?", (musteri_id,))
    conn.commit()
    conn.close()