import os
import json
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from services.aggregator import get_listings, DISTRICTS

#aggregation

app = Flask(__name__)

# --- Favorites/Discard persistence (JSON file) ---
MARKS_LOCK = threading.Lock()
PROJECT_ROOT = Path(__file__).resolve().parent
MARKS_FILE = Path(os.environ.get("MARKS_FILE", PROJECT_ROOT / "marks.json"))

def _load_marks():
    try:
        if MARKS_FILE.exists():
            with MARKS_LOCK:
                with open(MARKS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
    except Exception:
        pass
    return {}

def _save_marks(data: dict):
    try:
        MARKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = str(MARKS_FILE) + ".tmp"
        with MARKS_LOCK:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, MARKS_FILE)
    except Exception:
        pass

@app.get("/")
def index():
    default_district = request.args.get("district", "Leiria")
    return render_template("dashboard.html", districts=DISTRICTS, default_district=default_district)

@app.get("/api/listings")
def api_listings():
    district = request.args.get("district", "Leiria")
    pages = int(request.args.get("pages", "2"))
    pages = max(1, min(pages, 10))

    # tipologia (T*, T0, T1, T2, T3, T1+1, ...)
    typology = request.args.get("typology", "T2")

    # fontes selecionadas (se vazio => todas)
    sources = request.args.getlist("sources")
    if not sources:
        sources = ["idealista", "imovirtual", "supercasa", "casasapo", "remax", "olx"]

    # filtros numéricos (opcionais)
    def fnum(name):
        v = request.args.get(name, "").strip()
        return None if not v else float(v)

    filters = {
        "min_price": fnum("min_price"),
        "max_price": fnum("max_price"),
        "min_area": fnum("min_area"),
        "max_area": fnum("max_area"),
        "only_with_eurm2": request.args.get("only_with_eurm2", "0") == "1",
        "exclude_temporary": request.args.get("exclude_temporary", "1") == "1",
    }

    sort = request.args.get("sort", "eur_m2_asc")
    limit = int(request.args.get("limit", "200"))
    limit = max(10, min(limit, 1000))

    search_type = request.args.get("search_type", "rent")

    results, stats = get_listings(
        district=district,
        pages=pages,
        sources=sources,
        filters=filters,
        sort=sort,
        limit=limit,
        typology=typology,
        search_type=search_type,
    )
    return jsonify({"results": results, "stats": stats})

@app.get("/api/marks")
def api_get_marks():
    return jsonify(_load_marks())

@app.post("/api/marks")
def api_post_mark():
    try:
        data = request.get_json(force=True) or {}
        url = (data.get("url") or "").strip()
        state = (data.get("state") or "").strip() or None
        if not url:
            return jsonify({"error": "missing url"}), 400
        marks = _load_marks()
        if state in ("loved", "discarded"):
            marks[url] = state
        else:
            # clear mark when state invalid/empty
            if url in marks:
                del marks[url]
        _save_marks(marks)
        return jsonify({"ok": True, "state": marks.get(url)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=True)