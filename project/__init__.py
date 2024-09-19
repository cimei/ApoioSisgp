# __init__.py dentro da pasta project

import os
import locale
from flask import Flask,render_template,url_for,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
# from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

import pyodbc

from shutil import rmtree

pyodbc.setDecimalSeparator('.')

TOP_LEVEL_DIR = os.path.abspath(os.curdir)

app = Flask (__name__, static_url_path=None, instance_relative_config=True, static_folder='/app/project/static')

app.config.from_pyfile('flask.cfg')

app.static_url_path=app.config.get('STATIC_PATH')

db = SQLAlchemy(app)

mail = Mail(app)

locale.setlocale( locale.LC_ALL, '' )

# sched = APScheduler()
# sched = BackgroundScheduler(jobstores={'default': SQLAlchemyJobStore(url=os.environ.get('DB_URL'))})
sched = BackgroundScheduler()


#################################
## log in - cofigurações

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'users.login'


############################################
## blueprints - registros

from project.core.views import core
from project.error_pages.handlers import error_pages
from project.usuarios.views import usuarios

from project.envio.views import envio


app.register_blueprint(core)
app.register_blueprint(usuarios)
app.register_blueprint(error_pages)


app.register_blueprint(envio,url_prefix='/envio')

