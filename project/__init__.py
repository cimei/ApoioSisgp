# __init__.py dentro da pasta project

import sys
import os
import locale
import datetime
from flask import Flask,render_template,url_for,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

from shutil import rmtree
import time
import glob

def deleteOldPyinstallerFolders(time_threshold = 3600): # Por deefault remove depois de 1 hora, time_threshold em segundos
    try:
        base_path = sys._MEIPASS
    except Exception:
        return  # Não está rodando como OneFile Folder -> Return

    temp_path = os.path.abspath(os.path.join(base_path, '..')) # Vai para o parent folder de MEIPASS

    # Deleta os MEIPASS folders antigos...
    mei_folders = glob.glob(os.path.join(temp_path, '_MEI*'))
    for item in mei_folders:
        if (time.time()-os.path.getctime(item)) > time_threshold:
            rmtree(item)

TOP_LEVEL_DIR = os.path.abspath(os.curdir)
frozen = ' não '

if getattr(sys, 'frozen', False):
    frozen = ' sim '
    deleteOldPyinstallerFolders()

app = Flask (__name__, static_url_path=None, instance_relative_config=True)

app.config.from_pyfile('flask.cfg')

app.static_url_path=app.config.get('STATIC_PATH')

print( 'rodando no modo frozen:',frozen)

#########################################
## banco de dados - preparação
###############################################

#app.config['SECRET_KEY'] = 'pdctrkey'

#TOP_LEVEL_DIR = os.path.abspath(os.curdir)

#app.config['SECRET_KEY'] = '\x8b\xe5\xdb\x17\xe8\x93h\\\xae\xe8\x13e.\xb0\xabU\xdc\xf8q\xf4\xef>~\xce'
#
#app.config['MAIL_SERVER'] = 'smtp.gmail.com'
#app.config['MAIL_PORT'] = 587
#app.config['MAIL_USE_TLS'] = True
#app.config['MAIL_USE_SSL'] = False
#app.config['MAIL_USERNAME'] = 'projeto.copes@gmail.com'
#app.config['MAIL_PASSWORD'] = 'copes#123'
#app.config['MAIL_DEFAULT_SENDER'] = 'projeto.copes@gmail.com'

#basedir = os.path.abspath(os.path.dirname(__file__))
#dir = "//srv2/servicos/base/acn/_COPES/8-MATERIAL_APOIO/APLICATIVOS/"
#basedir = os.path.abspath(os.path.dirname(dir))
#
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir,'acordos.sqlite')
#app.config['SQLALCHEMY_BINDS'] = {'demandas_banco':'sqlite:///'+os.path.join(basedir,'demandas.db')}
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
from project.users.views import users
from project.demandas.views import demandas
from project.error_pages.handlers import error_pages

from project.bolsas.views import bolsas
from project.acordos.views import acordos

from project.convenios.views import convenios

app.register_blueprint(core)
app.register_blueprint(users)
app.register_blueprint(demandas,url_prefix='/demandas')
app.register_blueprint(error_pages)

app.register_blueprint(bolsas,url_prefix='/bolsas')
app.register_blueprint(acordos,url_prefix='/acordos')

app.register_blueprint(convenios,url_prefix='/convenios')
