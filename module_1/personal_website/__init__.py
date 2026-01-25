from flask import Flask
from personal_website import pages

##Creates blueprint that will store the main pages of the website
def create_app():
    app = Flask(__name__)
    app.register_blueprint(pages.bp)
    return app
