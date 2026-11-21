import os
import sqlite3
import hashlib
import secrets
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'v_variedades.db')

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return hashed, salt

def verify_password(password: str, hashed: str, salt: str) -> bool:
    expected_hash = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return secrets.compare_digest(expected_hash, hashed)

def is_postgres():
    return bool(DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://")))

def get_db():
    if is_postgres():
        import psycopg2
        import psycopg2.extras
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url)
        return conn
    else:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    if is_postgres():
        import psycopg2.extras
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            store TEXT NOT NULL,
            original_price NUMERIC,
            current_price NUMERIC,
            discount_percent INTEGER,
            image_url TEXT NOT NULL,
            affiliate_url TEXT NOT NULL,
            is_featured INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            click_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            admin_id INTEGER NOT NULL REFERENCES admins(id),
            expires_at TIMESTAMP NOT NULL
        );
        ''')

        conn.commit()

        # Admin padrão
        cursor.execute('SELECT id FROM admins WHERE username = %s', ('admin',))
        if not cursor.fetchone():
            hashed, salt = hash_password('admin123')
            cursor.execute(
                'INSERT INTO admins (username, password_hash, password_salt) VALUES (%s, %s, %s)',
                ('admin', hashed, salt)
            )

        # Configurações padrão
        default_settings = {
            'brand_name': 'V Variedades',
            'slogan': 'Achadinhos, ofertas e variedades em um só lugar!',
            'header_subtitle': 'Os melhores achadinhos e ofertas selecionados para você.',
            'instagram_url': 'https://instagram.com/',
            'tiktok_url': 'https://tiktok.com/',
            'facebook_url': 'https://facebook.com/',
            'whatsapp_url': 'https://wa.me/5511999999999',
            'disclaimer': 'Alguns links desta página podem ser links de afiliados. Podemos receber uma comissão pelas compras realizadas através deles, sem custo adicional para você.'
        }

        for key, val in default_settings.items():
            cursor.execute('''
                INSERT INTO settings (key, value) VALUES (%s, %s)
                ON CONFLICT (key) DO NOTHING
            ''', (key, val))

        # Produtos de exemplo
        cursor.execute('SELECT COUNT(*) as count FROM products')
        row = cursor.fetchone()
        if row and row['count'] == 0:
            sample_products = [
                (
                    'Mini Processador e Triturador de Alimentos USB Elétrico',
                    'Casa', 'Shopee', 69.90, 32.90, 53,
                    'https://images.unsplash.com/photo-1588854337221-4cf9fa96059c?w=600&auto=format&fit=crop&q=80',
                    'https://shopee.com.br/', 1, 1
                ),
                (
                    'Fone de Ouvido Bluetooth Sem Fio TWS com Cancelamento de Ruído',
                    'Tecnologia', 'Amazon', 199.00, 89.90, 55,
                    'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&auto=format&fit=crop&q=80',
                    'https://amazon.com.br/', 1, 1
                ),
                (
                    'Kit 6 Organizadores de Malas Viagem Impermeável',
                    'Achadinhos', 'Mercado Livre', 85.00, 49.90, 41,
                    'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80',
                    'https://mercadolivre.com.br/', 1, 1
                ),
                (
                    'Luminária Projetor Galáxia Astronauta LED 360 Graus',
                    'Casa', 'AliExpress', 149.90, 64.50, 57,
                    'https://images.unsplash.com/photo-1507499739999-097706ad8914?w=600&auto=format&fit=crop&q=80',
                    'https://aliexpress.com/', 1, 1
                ),
                (
                    'Smartwatch Monitor Cardíaco Esportivo Resistente à Água',
                    'Tecnologia', 'Shopee', 159.00, 78.00, 51,
                    'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80',
                    'https://shopee.com.br/', 0, 1
                ),
                (
                    'Escova Secadora e Alisadora de Cabelos Multifuncional Íons',
                    'Beleza', 'Amazon', 189.90, 109.90, 42,
                    'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=600&auto=format&fit=crop&q=80',
                    'https://amazon.com.br/', 0, 1
                ),
                (
                    'Fonte Bebedouro para Gatos e Cães com Filtro de Carvão',
                    'Pets', 'Mercado Livre', 99.00, 59.90, 39,
                    'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=600&auto=format&fit=crop&q=80',
                    'https://mercadolivre.com.br/', 0, 1
                ),
                (
                    'Mochila Antifurto Impermeável com Entrada USB para Notebook',
                    'Moda', 'Temu', 140.00, 69.90, 50,
                    'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80',
                    'https://temu.com/', 0, 1
                )
            ]

            for p in sample_products:
                cursor.execute('''
                    INSERT INTO products (
                        title, category, store, original_price, current_price, discount_percent,
                        image_url, affiliate_url, is_featured, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', p)

        conn.commit()
        conn.close()

    else:
        # SQLite local padrão
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            store TEXT NOT NULL,
            original_price REAL,
            current_price REAL,
            discount_percent INTEGER,
            image_url TEXT NOT NULL,
            affiliate_url TEXT NOT NULL,
            is_featured INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            click_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            admin_id INTEGER NOT NULL,
            expires_at DATETIME NOT NULL,
            FOREIGN KEY(admin_id) REFERENCES admins(id)
        )
        ''')

        conn.commit()

        cursor.execute('SELECT id FROM admins WHERE username = ?', ('admin',))
        if not cursor.fetchone():
            hashed, salt = hash_password('admin123')
            cursor.execute(
                'INSERT INTO admins (username, password_hash, password_salt) VALUES (?, ?, ?)',
                ('admin', hashed, salt)
            )

        default_settings = {
            'brand_name': 'V Variedades',
            'slogan': 'Achadinhos, ofertas e variedades em um só lugar!',
            'header_subtitle': 'Os melhores achadinhos e ofertas selecionados para você.',
            'instagram_url': 'https://instagram.com/',
            'tiktok_url': 'https://tiktok.com/',
            'facebook_url': 'https://facebook.com/',
            'whatsapp_url': 'https://wa.me/5511999999999',
            'disclaimer': 'Alguns links desta página podem ser links de afiliados. Podemos receber uma comissão pelas compras realizadas através deles, sem custo adicional para você.'
        }

        for key, val in default_settings.items():
            cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, val))

        cursor.execute('SELECT COUNT(*) as count FROM products')
        row = cursor.fetchone()
        if row and row['count'] == 0:
            sample_products = [
                (
                    'Mini Processador e Triturador de Alimentos USB Elétrico',
                    'Casa', 'Shopee', 69.90, 32.90, 53,
                    'https://images.unsplash.com/photo-1588854337221-4cf9fa96059c?w=600&auto=format&fit=crop&q=80',
                    'https://shopee.com.br/', 1, 1
                ),
                (
                    'Fone de Ouvido Bluetooth Sem Fio TWS com Cancelamento de Ruído',
                    'Tecnologia', 'Amazon', 199.00, 89.90, 55,
                    'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&auto=format&fit=crop&q=80',
                    'https://amazon.com.br/', 1, 1
                ),
                (
                    'Kit 6 Organizadores de Malas Viagem Impermeável',
                    'Achadinhos', 'Mercado Livre', 85.00, 49.90, 41,
                    'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80',
                    'https://mercadolivre.com.br/', 1, 1
                ),
                (
                    'Luminária Projetor Galáxia Astronauta LED 360 Graus',
                    'Casa', 'AliExpress', 149.90, 64.50, 57,
                    'https://images.unsplash.com/photo-1507499739999-097706ad8914?w=600&auto=format&fit=crop&q=80',
                    'https://aliexpress.com/', 1, 1
                ),
                (
                    'Smartwatch Monitor Cardíaco Esportivo Resistente à Água',
                    'Tecnologia', 'Shopee', 159.00, 78.00, 51,
                    'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80',
                    'https://shopee.com.br/', 0, 1
                ),
                (
                    'Escova Secadora e Alisadora de Cabelos Multifuncional Íons',
                    'Beleza', 'Amazon', 189.90, 109.90, 42,
                    'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=600&auto=format&fit=crop&q=80',
                    'https://amazon.com.br/', 0, 1
                ),
                (
                    'Fonte Bebedouro para Gatos e Cães com Filtro de Carvão',
                    'Pets', 'Mercado Livre', 99.00, 59.90, 39,
                    'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=600&auto=format&fit=crop&q=80',
                    'https://mercadolivre.com.br/', 0, 1
                ),
                (
                    'Mochila Antifurto Impermeável com Entrada USB para Notebook',
                    'Moda', 'Temu', 140.00, 69.90, 50,
                    'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80',
                    'https://temu.com/', 0, 1
                )
            ]

            for p in sample_products:
                cursor.execute('''
                    INSERT INTO products (
                        title, category, store, original_price, current_price, discount_percent,
                        image_url, affiliate_url, is_featured, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', p)

        conn.commit()
        conn.close()

if __name__ == '__main__':
    init_db()
    print("Database init ok.")
