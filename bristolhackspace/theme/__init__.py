from flask import Blueprint

theme_blueprint = Blueprint('theme', __name__, template_folder="templates", static_folder="static", static_url_path="")