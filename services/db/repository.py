import datetime
import sqlite3
from .connection import get_connection

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # Table for raw listings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            url TEXT PRIMARY KEY,
            source TEXT,
            district TEXT,
            title TEXT,
            price_eur REAL,
            area_m2 REAL,
            eur_m2 REAL,
            search_type TEXT,
            snippet TEXT,
            first_seen DATETIME,
            last_seen DATETIME,
            typology TEXT,
            posted_at DATETIME,
            actualized_at DATETIME,
            is_active INTEGER DEFAULT 1
        )
    """)
    # Table for historical prices (to track updates)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            url TEXT,
            price_eur REAL,
            date DATETIME,
            FOREIGN KEY(url) REFERENCES listings(url)
        )
    """)
    # Table for daily aggregate stats (historical trends)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT,
            district TEXT,
            search_type TEXT,
            typology TEXT,
            avg_eur_m2 REAL,
            avg_price_eur REAL,
            median_eur_m2 REAL,
            count INTEGER,
            PRIMARY KEY (date, district, search_type, typology)
        )
    """)
    
    # Migrations
    try:
        cur.execute("ALTER TABLE listings ADD COLUMN posted_at DATETIME")
    except: pass
    try:
        cur.execute("ALTER TABLE listings ADD COLUMN actualized_at DATETIME")
    except: pass
    try:
        cur.execute("ALTER TABLE listings ADD COLUMN is_active INTEGER DEFAULT 1")
    except: pass
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_listings_search_type ON listings(search_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_listings_district ON listings(district)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_listings_typology ON listings(typology)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_listings_posted_at ON listings(posted_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_price_history_url ON price_history(url)")
    
    conn.commit()
    conn.close()

def save_listings(items, search_type, typology):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.datetime.now().isoformat()
    for item in items:
        url = item.get("url")
        if not url: continue
        
        cur.execute("SELECT price_eur, first_seen, typology, posted_at, actualized_at FROM listings WHERE url = ?", (url,))
        row = cur.fetchone()
        
        item_price = item.get("price_eur")
        item_typology = item.get("typology") or typology
        
        if row:
            old_price, first_seen, old_typology, old_posted_at, old_actualized_at = row
            if (item_typology == "T*" or not item_typology) and old_typology and old_typology != "T*":
                item_typology = old_typology
            
            item_posted_at = item.get('posted_at') or old_posted_at
            item_actualized_at = item.get('actualized_at') or old_actualized_at
            
            cur.execute("""
                UPDATE listings SET
                    source = ?, district = ?, title = ?, price_eur = ?, 
                    area_m2 = ?, eur_m2 = ?, search_type = ?, snippet = ?,
                    last_seen = ?, typology = ?, posted_at = ?, actualized_at = ?, is_active = 1
                WHERE url = ?
            """, (
                item['source'], item['district'], item['title'], item_price,
                item.get('area_m2'), item.get('eur_m2'), search_type, item.get('snippet'),
                now, item_typology, item_posted_at, item_actualized_at, url
            ))
            if item_price != old_price:
                cur.execute("INSERT INTO price_history (url, price_eur, date) VALUES (?, ?, ?)", (url, item_price, now))
        else:
            cur.execute("""
                INSERT INTO listings (
                    url, source, district, title, price_eur, area_m2, eur_m2, 
                    search_type, snippet, first_seen, last_seen, typology, posted_at, actualized_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                url, item['source'], item['district'], item['title'], 
                item_price, item.get('area_m2'), item.get('eur_m2'), 
                search_type, item.get('snippet'), now, now, item_typology, item.get('posted_at'), item.get('actualized_at')
            ))
            cur.execute("INSERT INTO price_history (url, price_eur, date) VALUES (?, ?, ?)", (url, item_price, now))
            
    conn.commit()
    conn.close()

def get_listings_from_db(district, search_type, typology, limit=None, only_active=True):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = "SELECT * FROM listings WHERE district = ? AND search_type = ? AND typology = ?"
    params = [district, search_type, typology]
    
    if only_active:
        query += " AND is_active = 1"
        
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_listing_history(url):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT price_eur, date FROM price_history WHERE url = ? ORDER BY date ASC", (url,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def optimize_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("VACUUM")
    conn.close()
