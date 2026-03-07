from .connection import DB_PATH
from .repository import init_db, save_listings, get_listings_from_db, get_listing_history, optimize_db
from .stats import get_stats, get_historical_stats, update_daily_stats, get_posted_stats

def cleanup_old_listings(days=7):
    # Data deletion disabled
    return 0

init_db()
