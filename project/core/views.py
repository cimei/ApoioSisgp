"""
.. topic:: Core (views)

    Este é o módulo inicial do sistema.

    Apresenta as telas de início, informação.

.. topic:: Ações relacionadas aos bolsistas

    * Tela inicial: index
    * Tela de informações: info
    * Carregar dados SICONV: carregaSICONV
    * Inserir dados de chamadas homologadas: cria_chamada

"""

# core/views.py

from flask import render_template,url_for,flash, redirect,request,Blueprint

import os
import re
import datetime
from datetime import datetime as dt
import shutil
import urllib.request
import locale
import tempfile


core = Blueprint("core",__name__)

@core.route('/')
def index():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta a tela inicial do aplicativo.                                                |
    +---------------------------------------------------------------------------------------+
    """

    return render_template ('index.html',sistema='Apoio SISGP')

@core.route('/info')
def info():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta a tela de informações do aplicativo.                                         |
    +---------------------------------------------------------------------------------------+
    """

    return render_template('info.html')






