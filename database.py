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
    
    # DB Türüne göre ID veri tipini belirle
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

# --- ŞİFRELEME İŞLEMLERİ ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- KULLANICI İŞLEMLERİ ---
def register_user(full_name, phone, email, address, password):
    """Yeni üye/işletme kaydeder."""
    conn = get_connection()
    cursor = conn.cursor()
    pw_hash = hash_password(password)
    
    # SQL parametre işareti: PostgreSQL için %s, SQLite için ?
    param = "%s" if DATABASE_URL else "?"
    
    try:
        query = f"INSERT INTO users (full_name, phone, email, address, password_hash) VALUES ({param}, {param}, {param}, {param}, {param})"
        cursor.execute(query, (full_name, phone, email.lower().strip(), address, pw_hash))
        conn.commit()
        return True, "Kayıt başarıyla oluşturuldu! Giriş yapabilirsiniz."
    except Exception as e:
        return False, f"Kayıt hatası (Bu e-posta adresi zaten kayıtlı olabilir): {str(e)}"
    finally:
        conn.close()

def login_user(email, password):
    """Kullanıcı girişini doğrular."""
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