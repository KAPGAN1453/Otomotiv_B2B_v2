import os
import sqlite3
import bcrypt

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Bulut DB adresi varsa PostgreSQL'e, yoksa yerel SQLite veritabanına bağlanır."""
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect("otomotiv_b2b.db", check_same_thread=False)
        return conn

def init_db():
    """Veritabanı tablolarını ilklendirir (PostgreSQL & SQLite Uyumlu)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    id_type = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    # Kullanıcılar Tablosu
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
    
    # Müşteriler Tablosu
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
    
    # Saha Ziyaretleri Tablosu
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
    
    conn.commit()
    conn.close()

# Uyumsuzluk önleme alias'ları
tablolari_olustur = init_db

# --- ŞİFRELEME İŞLEMLERİ ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- KULLANICI İŞLEMLERİ ---
def register_user(full_name, phone, email, address, password):
    conn = get_connection()
    cursor = conn.cursor()
    pw_hash = hash_password(password)
    param = "%s" if DATABASE_URL else "?"
    
    try:
        query = f"INSERT INTO users (full_name, phone, email, address, password_hash) VALUES ({param}, {param}, {param}, {param}, {param})"
        cursor.execute(query, (full_name, phone, email.lower().strip(), address, pw_hash))
        conn.commit()
        return True, "Kayıt başarıyla oluşturuldu! Giriş yapabilirsiniz."
    except Exception as e:
        return False, f"Kayıt hatası: {str(e)}"
    finally:
        conn.close()

def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    query = f"SELECT full_name, phone, email, address, password_hash FROM users WHERE email = {param}"
    
    cursor.execute(query, (email.lower().strip(),))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password(password, user[4]):
        return {
            "full_name": user[0],
            "phone": user[1],
            "email": user[2],
            "address": user[3]
        }
    return None

# --- MÜŞTERİ İŞLEMLERİ ---
def musterileri_getir(user_email=None):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    
    if user_email:
        query = f"SELECT id, company_name, authorized_person, phone, city, address, balance FROM customers WHERE user_email = {param}"
        cursor.execute(query, (user_email,))
    else:
        cursor.execute("SELECT id, company_name, authorized_person, phone, city, address, balance FROM customers")
        
    rows = cursor.fetchall()
    conn.close()
    return rows

def musteri_ekle(user_email, company_name, authorized_person, phone, city, address, balance=0.0):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    
    query = f"""
        INSERT INTO customers (user_email, company_name, authorized_person, phone, city, address, balance)
        VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param})
    """
    cursor.execute(query, (user_email, company_name, authorized_person, phone, city, address, balance))
    conn.commit()
    conn.close()

# --- SAHA ZİYARETLERİ İŞLEMLERİ ---
def ziyaretleri_getir(user_email=None):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    
    if user_email:
        query = f"SELECT id, customer_name, visit_date, notes, status FROM visits WHERE user_email = {param}"
        cursor.execute(query, (user_email,))
    else:
        cursor.execute("SELECT id, customer_name, visit_date, notes, status FROM visits")
        
    rows = cursor.fetchall()
    conn.close()
    return rows

def ziyaret_ekle(user_email, customer_name, visit_date, notes, status):
    conn = get_connection()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"
    
    query = f"""
        INSERT INTO visits (user_email, customer_name, visit_date, notes, status)
        VALUES ({param}, {param}, {param}, {param}, {param})
    """
    cursor.execute(query, (user_email, customer_name, str(visit_date), notes, status))
    conn.commit()
    conn.close()