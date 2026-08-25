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
    
    # Saha Ziyaretleri
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
    
    # Stok / Ürünler Tablosu
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

tablolari_olustur = init_db

# --- ŞİFRELEME ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- KULLANICI ---
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

# --- MÜŞTERİ ---
def musterileri_getir(user_email=None):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    if user_email:
        cursor.execute(f"SELECT id, company_name, authorized_person, phone, city, address, balance FROM customers WHERE user_email = {param}", (user_email,))
    else:
        cursor.execute("SELECT id, company_name, authorized_person, phone, city, address, balance FROM customers")
    rows = cursor.fetchall()
    conn.close()
    return rows

def musteri_ekle(user_email, company_name, authorized_person, phone, city, address, balance=0.0):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    cursor.execute(f"INSERT INTO customers (user_email, company_name, authorized_person, phone, city, address, balance) VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param})",
                   (user_email, company_name, authorized_person, phone, city, address, balance))
    conn.commit()
    conn.close()

# --- ZİYARET ---
def ziyaretleri_getir(user_email=None):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    if user_email:
        cursor.execute(f"SELECT id, customer_name, visit_date, notes, status FROM visits WHERE user_email = {param}", (user_email,))
    else:
        cursor.execute("SELECT id, customer_name, visit_date, notes, status FROM visits")
    rows = cursor.fetchall()
    conn.close()
    return rows

def ziyaret_ekle(user_email, customer_name, visit_date, notes, status):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    cursor.execute(f"INSERT INTO visits (user_email, customer_name, visit_date, notes, status) VALUES ({param}, {param}, {param}, {param}, {param})",
                   (user_email, customer_name, str(visit_date), notes, status))
    conn.commit()
    conn.close()

saha_ziyaretleri_getir = ziyaretleri_getir
saha_ziyareti_ekle = ziyaret_ekle

# --- STOK / ÜRÜN ---
def stoklari_getir(user_email=None):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    if user_email:
        cursor.execute(f"SELECT id, product_code, product_name, category, quantity, price FROM stocks WHERE user_email = {param}", (user_email,))
    else:
        cursor.execute("SELECT id, product_code, product_name, category, quantity, price FROM stocks")
    rows = cursor.fetchall()
    conn.close()
    return rows

def stok_ekle(user_email, product_code, product_name, category, quantity, price):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    cursor.execute(f"INSERT INTO stocks (user_email, product_code, product_name, category, quantity, price) VALUES ({param}, {param}, {param}, {param}, {param}, {param})",
                   (user_email, product_code, product_name, category, quantity, price))
    conn.commit()
    conn.close()

urunleri_getir = stoklari_getir
urun_ekle = stok_ekle