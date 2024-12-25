import logging
import os
from logging.config import dictConfig

import sentry_sdk
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from segment import analytics

from src.blueprints import example_blueprint
from src.db import db

app = Flask(__name__)

analytics.write_key = os.environ["SEGMENT_WRITE_KEY"]

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                "datefmt": "%B %d, %Y %H:%M:%S %Z",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
            "logtail": {
                "class": "logtail.LogtailHandler",
                "source_token": os.environ["LOGTAIL_SOURCE_TOKEN"],
                "formatter": "default",
            },
        },
        "root": {"level": "DEBUG", "handlers": ["console", "logtail"]},
    },
)

cors = CORS(app, resources={
            r"/api/*": {"origins": [
                "http://localhost:3000",
                "https://*.kreativeusa.com",
            ]}})

if os.environ["FLASK_ENV"] != "development":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        traces_sample_rate=0.7,
        profiles_sample_rate=0.7,
    )

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_size": 10, "pool_recycle": 60, "pool_pre_ping": True}

db.init_app(app)

migrate = Migrate(app, db)

# create tables
with app.app_context():
    db.create_all()

app.register_blueprint(example_blueprint)

@app.route("/")
def hello_world():
    return "hello developer :)"

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)  # noqa: S201
