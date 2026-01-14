import os
from flask import Flask, render_template, request, jsonify
from services.aggregator import get_listings, DISTRICTS

#aggregation

app = Flask(__name__)

@app.get("/")
def index():
    default_district = request.args.get("district", "Leiria")
    return render_template("index.html", districts=DISTRICTS, default_district=default_district)

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

    results, stats = get_listings(
        district=district,
        pages=pages,
        sources=sources,
        filters=filters,
        sort=sort,
        limit=limit,
        typology=typology,
    )
    return jsonify({"results": results, "stats": stats})

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=True)