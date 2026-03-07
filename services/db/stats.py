import datetime
import sqlite3
from .connection import get_connection

def get_stats():
    """Returns some interesting stats for the dynamic graphics."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # 1. Average price per m2 per district for Rent vs Buy
    cur.execute("""
        SELECT district, search_type, AVG(eur_m2) as avg_eur_m2, COUNT(*) as count
        FROM listings
        WHERE eur_m2 IS NOT NULL AND is_active = 1
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
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    today = datetime.date.today().isoformat()
    
    cur.execute("""
        SELECT 
            district, search_type, typology, 
            AVG(eur_m2) as avg_eur_m2, 
            AVG(price_eur) as avg_price_eur,
            COUNT(*) as count
        FROM listings
        WHERE is_active = 1
        GROUP BY district, search_type, typology
    """)
    rows = cur.fetchall()
    
    for r in rows:
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
    conn = get_connection()
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

def get_posted_stats(district=None, search_type=None, typology=None):
    """Retrieves historical stats based on the posted_at date."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    query = """
        SELECT 
            date(posted_at) as date, 
            AVG(eur_m2) as avg_eur_m2, 
            AVG(price_eur) as avg_price_eur, 
            COUNT(*) as count
        FROM listings 
        WHERE posted_at IS NOT NULL AND is_active = 1
    """
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
        
    query += " GROUP BY date ORDER BY date ASC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
