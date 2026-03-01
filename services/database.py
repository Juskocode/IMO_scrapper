import sqlite3
import datetime
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
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
            typology TEXT
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
    # Table for "famous indexes" or aggregates
    # We can also compute them on the fly
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_listings_search_type ON listings(search_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_listings_district ON listings(district)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_listings_typology ON listings(typology)")
    
    conn.commit()
    conn.close()

def save_listings(items, search_type, typology):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.datetime.now().isoformat()
    for item in items:
        url = item.get("url")
        if not url: continue
        
        # Check if exists
        cur.execute("SELECT price_eur, first_seen, typology FROM listings WHERE url = ?", (url,))
        row = cur.fetchone()
        
        item_price = item.get("price_eur")
        # Use item's typology if available, else query's typology
        item_typology = item.get("typology") or typology
        
        if row:
            old_price, first_seen, old_typology = row
            # Never overwrite a specific typology (T1, T2, etc.) with a generic one (T*)
            if (item_typology == "T*" or not item_typology) and old_typology and old_typology != "T*":
                item_typology = old_typology
            
            # Update entry
            cur.execute("""
                UPDATE listings SET
                    source = ?, district = ?, title = ?, price_eur = ?, 
                    area_m2 = ?, eur_m2 = ?, search_type = ?, snippet = ?,
                    last_seen = ?, typology = ?
                WHERE url = ?
            """, (
                item['source'], item['district'], item['title'], item_price,
                item.get('area_m2'), item.get('eur_m2'), search_type, item.get('snippet'),
                now, item_typology, url
            ))
            # If price changed, record history
            if item_price != old_price:
                cur.execute("INSERT INTO price_history (url, price_eur, date) VALUES (?, ?, ?)", (url, item_price, now))
        else:
            # New entry
            cur.execute("""
                INSERT INTO listings (
                    url, source, district, title, price_eur, area_m2, eur_m2, 
                    search_type, snippet, first_seen, last_seen, typology
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url, item['source'], item['district'], item['title'], 
                item_price, item.get('area_m2'), item.get('eur_m2'), 
                search_type, item.get('snippet'), now, now, item_typology
            ))
            cur.execute("INSERT INTO price_history (url, price_eur, date) VALUES (?, ?, ?)", (url, item_price, now))
            
    conn.commit()
    conn.close()

def get_stats():
    """Returns some interesting stats for the dynamic graphics."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # 1. Average price per m2 per district for Rent vs Buy
    cur.execute("""
        SELECT district, search_type, AVG(eur_m2) as avg_eur_m2, COUNT(*) as count
        FROM listings
        WHERE eur_m2 IS NOT NULL
        GROUP BY district, search_type
    """)
    rows = cur.fetchall()
    
    district_stats = {}
    for r in rows:
        d = r['district']
        if d not in district_stats: district_stats[d] = {}
        district_stats[d][r['search_type']] = {
            'avg_eur_m2': r['avg_eur_m2'],
            'count': r['count']
        }
    
    # Calculate Buy/Rent ratio (Gross Yield index)
    # Yield = (MonthlyRent * 12) / BuyPrice
    # We can estimate this using avg_eur_m2
    # Yield = (AvgRentEurM2 * 12) / AvgBuyEurM2
    yields = []
    for d, s in district_stats.items():
        if 'rent' in s and 'buy' in s:
            rent_m2 = s['rent']['avg_eur_m2']
            buy_m2 = s['buy']['avg_eur_m2']
            if buy_m2 > 0:
                gross_yield = (rent_m2 * 12) / buy_m2
                yields.append({
                    'district': d,
                    'yield': gross_yield,
                    'rent_m2': rent_m2,
                    'buy_m2': buy_m2
                })
    
    conn.close()
    return {
        'district_stats': district_stats,
        'yields': yields
    }

def update_daily_stats():
    """Recalculates current aggregates and stores them in daily_stats table."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    today = datetime.date.today().isoformat()
    
    # Calculate daily stats per district, search_type, and typology
    cur.execute("""
        SELECT 
            district, search_type, typology, 
            AVG(eur_m2) as avg_eur_m2, 
            AVG(price_eur) as avg_price_eur,
            COUNT(*) as count
        FROM listings
        GROUP BY district, search_type, typology
    """)
    rows = cur.fetchall()
    
    for r in rows:
        # For median, we need a separate query per group (sqlite doesn't have MEDIAN)
        # But for now, we can skip it or use a simpler approach if needed.
        # Let's skip it to keep performance reasonable for now.
        
        cur.execute("""
            INSERT OR REPLACE INTO daily_stats (
                date, district, search_type, typology, 
                avg_eur_m2, avg_price_eur, count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            today, r['district'], r['search_type'], r['typology'],
            r['avg_eur_m2'], r['avg_price_eur'], r['count']
        ))
        
    conn.commit()
    conn.close()

def get_historical_stats(district=None, search_type=None, typology=None):
    """Retrieves historical stats for plotting."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = "SELECT * FROM daily_stats WHERE 1=1"
    params = []
    
    if district:
        query += " AND district = ?"
        params.append(district)
    if search_type:
        query += " AND search_type = ?"
        params.append(search_type)
    if typology:
        query += " AND typology = ?"
        params.append(typology)
        
    query += " ORDER BY date ASC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_listings_from_db(district, search_type, typology, limit=None):
    """Retrieves listings for a specific district, search_type, and typology from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = """
        SELECT * FROM listings 
        WHERE district = ? AND search_type = ? AND typology = ?
    """
    params = [district, search_type, typology]
    
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        
    cur.execute(query, params)
    
    rows = cur.fetchall()
    conn.close()
    
    return [dict(r) for r in rows]

init_db()
