from project import app
from flask import render_template
import webbrowser
from threading import Timer
import locale
import os

# filtros cusomizado para o jinja
#
@app.template_filter('verifica_serv_bd')
def verifica_serv_bd(chave):
    return os.getenv(chave)

@app.template_filter('converte_para_real')
def converte_para_real(valor):
    if valor == None or valor == '':
        return 0
    else:
        return locale.currency(valor, symbol=False, grouping = True )

@app.template_filter('decimal_com_virgula')
def decimal_com_virgula(valor):
    if valor == None or valor == '':
        return 0
    else:
        return locale.format_string('%.1f',valor,grouping=True)

@app.template_filter('splitpart')
def splitpart (value, char = '/'):
    return value.split(char)       

# @app.route('/')
# def index():
#     return render_template('home.html')

if __name__ == '__main__':
    app.run(port = 5004)
