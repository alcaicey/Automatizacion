from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__, template_folder="../templates")

NAV_PAGES = [
    {"rule": "/",           "template": "index.html",      "key": "home",       "label": "Inicio"},
    {"rule": "/historico",  "template": "historico.html",  "key": "historico",  "label": "Histórico"},
    {"rule": "/analisis",   "template": "analisis.html",   "key": "analisis",   "label": "Análisis"},
    {"rule": "/base-datos", "template": "base_datos.html", "key": "base_datos", "label": "Base de Datos"},
    {"rule": "/logs",       "template": "logs.html",       "key": "logs",       "label": "Logs"},
]

for page in NAV_PAGES:
    pages_bp.add_url_rule(
        page["rule"],
        endpoint=page["key"],
        view_func=lambda t=page["template"], k=page["key"]: render_template(t, active=k),
    )

@pages_bp.route("/index")
def index_alias():
    return render_template("index.html", active="home")

@pages_bp.app_context_processor
def inject_nav_pages():
    return {"NAV_PAGES": NAV_PAGES}
