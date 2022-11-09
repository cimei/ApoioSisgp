# __init__.py dentro da pasta project

import os
import locale
from flask import Flask,render_template,url_for,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

import pyodbc

from shutil import rmtree

pyodbc.setDecimalSeparator('.')

TOP_LEVEL_DIR = os.path.abspath(os.curdir)

app = Flask (__name__, static_url_path=None, instance_relative_config=True, static_folder='/app/project/static')

app.config.from_pyfile('flask.cfg')

app.static_url_path=app.config.get('STATIC_PATH')

db = SQLAlchemy(app)
Migrate(app,db)

mail = Mail(app)

locale.setlocale( locale.LC_ALL, '' )

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

from project.unidades.views import unidades
from project.pessoas.views import pessoas
from project.padroes.views import padroes
from project.consultas.views import consultas
from project.atividades.views import atividades
from project.envio.views import envio


app.register_blueprint(core)
app.register_blueprint(usuarios)
app.register_blueprint(error_pages)

app.register_blueprint(unidades,url_prefix='/unidades')

app.register_blueprint(pessoas,url_prefix='/pessoas')

app.register_blueprint(padroes,url_prefix='/padroes')

app.register_blueprint(consultas,url_prefix='/consultas')

app.register_blueprint(atividades,url_prefix='/atividades')

app.register_blueprint(envio,url_prefix='/envio')

