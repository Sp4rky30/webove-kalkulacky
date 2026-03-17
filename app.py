import os
import logging

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import BadRequest
from werkzeug.middleware.proxy_fix import ProxyFix

from calculators.catalog import CALCULATORS
from calculators.compound_exports import build_compound_csv_response, build_compound_pdf_response
from calculators.compound_interest import build_compound_context, get_compound_inputs
from calculators.family import (
    build_maternity_context,
    build_parental_context,
    build_sickness_context,
    get_maternity_inputs,
    get_parental_inputs,
    get_sickness_inputs,
)
from calculators.mortgage import build_mortgage_context, get_mortgage_inputs
from calculators.net_salary import build_net_salary_context, get_net_salary_inputs

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_INFO = {
    "title": "Webové kalkulačky pro běžné finance a dávky",
    "intro": "Projekt vzniká jako přehledná sbírka praktických kalkulaček pro osobní finance, bydlení, mzdy a rodinné dávky v Česku.",
    "goals": [
        "Nabídnout rychlé a srozumitelné orientační výpočty bez zbytečné složitosti.",
        "Pokrýt běžné životní situace v oblasti mezd, bydlení, investic a rodinných dávek.",
        "Udržovat jednotné prostředí, kde jsou všechny kalkulačky snadno dostupné na jednom místě.",
    ],
    "disclaimer": "Výsledky slouží jako orientační pomůcka. U dávek, mezd a dalších právně citlivých oblastí vždy záleží na konkrétní životní situaci a aktuálních pravidlech.",
}


@app.context_processor
def inject_global_template_context():
    return {
        "google_analytics_id": os.environ.get("GOOGLE_ANALYTICS_ID", "").strip(),
    }


@app.route("/")
def index():
    logger.info("Render index page")
    return render_template("index.html", calculators=CALCULATORS)


@app.route("/o-projektu")
def about():
    logger.info("Render about page")
    return render_template("about.html", project=PROJECT_INFO, calculators=CALCULATORS)


@app.route("/health")
def health():
    logger.info("Health check")
    return jsonify({"status": "ok"}), 200


@app.route("/kalkulacky/slozene-uroceni", methods=["GET", "POST"])
def compound_interest():
    logger.info("Render compound interest calculator")
    return render_template("compound_interest.html", **build_compound_context(get_compound_inputs(request)))


@app.route("/kalkulacky/cista-mzda", methods=["GET", "POST"])
def net_salary():
    logger.info("Render net salary calculator")
    return render_template("net_salary.html", **build_net_salary_context(get_net_salary_inputs(request)))


@app.route("/kalkulacky/hypoteka", methods=["GET", "POST"])
def mortgage():
    logger.info("Render mortgage calculator")
    return render_template("mortgage.html", **build_mortgage_context(get_mortgage_inputs(request)))


@app.route("/kalkulacky/materska", methods=["GET", "POST"])
def maternity():
    logger.info("Render maternity calculator")
    return render_template("maternity.html", **build_maternity_context(get_maternity_inputs(request)))


@app.route("/kalkulacky/rodicovska", methods=["GET", "POST"])
def parental():
    logger.info("Render parental calculator")
    return render_template("parental.html", **build_parental_context(get_parental_inputs(request)))


@app.route("/kalkulacky/nemocenska", methods=["GET", "POST"])
def sickness():
    logger.info("Render sickness calculator")
    return render_template("sickness.html", **build_sickness_context(get_sickness_inputs(request)))


@app.route("/kalkulacky/slozene-uroceni/export/csv")
def export_csv():
    logger.info("Export compound interest CSV")
    return build_compound_csv_response(get_compound_inputs(request))


@app.route("/kalkulacky/slozene-uroceni/export/pdf")
def export_pdf():
    logger.info("Export compound interest PDF")
    return build_compound_pdf_response(get_compound_inputs(request))


@app.errorhandler(BadRequest)
def handle_bad_request(error):
    logger.warning("Bad request: %s", error.description)
    return (
        render_template(
            "error.html",
            title="Neplatný vstup",
            message=error.description or "Některý ze zadaných údajů není platný.",
            status_code=400,
        ),
        400,
    )


@app.errorhandler(404)
def handle_not_found(error):
    logger.info("Page not found: %s", request.path)
    return (
        render_template(
            "error.html",
            title="Stránka nenalezena",
            message="Požadovaná stránka na tomto webu neexistuje nebo byla přesunuta.",
            status_code=404,
        ),
        404,
    )


@app.errorhandler(500)
def handle_internal_error(error):
    logger.exception("Unhandled server error")
    return (
        render_template(
            "error.html",
            title="Něco se nepovedlo",
            message="Na serveru došlo k chybě. Zkus stránku načíst znovu nebo to prosím zkus o chvíli později.",
            status_code=500,
        ),
        500,
    )


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes", "on"},
    )
