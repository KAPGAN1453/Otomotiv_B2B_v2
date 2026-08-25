import os
import sqlite3
import bcrypt

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect("otomotiv_b2b.db", check_same_thread=False)
        return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    id_type = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    # Kullanıcılar
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id {id_type},
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            address TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Müşteriler
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS customers (
            id {id_type},
            user_email TEXT NOT NULL,
            company_name TEXT NOT NULL,
            authorized_person TEXT,
            phone TEXT,
            city TEXT,
            address TEXT,
            balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Ziyaretler
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS visits (
            id {id_type},
            user_email TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            visit_date TEXT NOT NULL,
            notes TEXT,
            status TEXT
        )
    """)
    
    # Stoklar
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS stocks (
            id {id_type},
            user_email TEXT NOT NULL,
            product_code TEXT NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER DEFAULT 0,
            price REAL DEFAULT 0.0
        )
    """)
    
    conn.commit()
    conn.close()

# Aliaslar
tablolari_olustur = init_db

# Şifreleme
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Kullanıcı İşlemleri
def register_user(full_name, phone, email, address, password):
    conn = get_connection()
    cursor = conn.cursor()
    pw_hash = hash_password(password)
    param = "%s" if DATABASE_URL else "?"
    try:
        query = f"INSERT INTO users (full_name, phone, email, address, password_hash) VALUES ({param}, {param}, {param}, {param}, {param})"
        cursor.execute(query, (full_name, phone, email.lower().strip(), address, pw_hash))
        conn.commit()
        return True, "Kayıt başarılı!"
    except Exception as e:
        return False, f"Hata: {str(e)}"
    finally:
        conn.close()

def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT full_name, phone, email, address, password_hash FROM users WHERE email = {param}", (email.lower().strip(),))
    user = cursor.fetchone()
    conn.close()
    if user and check_password(password, user[4]):
        return {"full_name": user[0], "phone": user[1], "email": user[2], "address": user[3]}
    return None

# Müşteri İşlemleri
def musterileri_getir(user_email=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, company_name, authorized_person, phone, city, address, balance FROM customers")
    rows = cursor.fetchall()
    conn.close()
    return rows

def musteri_ekle(firma_adi, yetkili="", telefon="", sehir="", risk_limiti=0.0, user_email="sistem@kutluk.com", address=""):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    query = f"""
        INSERT INTO customers (user_email, company_name, authorized_person, phone, city, address, balance)
        VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param})
    """
    cursor.execute(query, (user_email, firma_adi, yetkili, telefon, sehir, address, float(risk_limiti)))
    conn.commit()
    conn.close()

# Saha Ziyareti İşlemleri
def saha_ziyaretleri_getir(musteri_adi=None):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    if musteri_adi:
        cursor.execute(f"SELECT id, customer_name, visit_date, notes, status FROM visits WHERE customer_name = {param}", (str(musteri_adi),))
    else:
        cursor.execute("SELECT id, customer_name, visit_date, notes, status FROM visits")
    rows = cursor.fetchall()
    conn.close()
    return rows

def saha_ziyareti_ekle(customer_name, visit_date, notes="", status="Tamamlandı", user_email="sistem@kutluk.com"):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    query = f"""
        INSERT INTO visits (user_email, customer_name, visit_date, notes, status)
        VALUES ({param}, {param}, {param}, {param}, {param})
    """
    cursor.execute(query, (str(user_email), str(customer_name), str(visit_date), str(notes), str(status)))
    conn.commit()
    conn.close()

# Stok İşlemleri
def stoklari_getir():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, product_code, product_name, category, quantity, price FROM stocks")
    rows = cursor.fetchall()
    conn.close()
    return rows

def stok_ekle(product_code, product_name, category, quantity, price, user_email="sistem@kutluk.com"):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    query = f"""
        INSERT INTO stocks (user_email, product_code, product_name, category, quantity, price)
        VALUES ({param}, {param}, {param}, {param}, {param}, {param})
    """
    cursor.execute(query, (user_email, product_code, product_name, category, int(quantity), float(price)))
    conn.commit()
    conn.close()

urunleri_getir = stoklari_getir
urun_ekle = stok_ekle