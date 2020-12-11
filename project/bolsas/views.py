"""
.. topic:: Bolsas (views)

    As bolsas são o instrumento básico de fomento dos Acordos, pois o repasse é feito diretamente ao beneficiário,
    sem movimentação financeira entre partícipes.

    No caso do PDCTR, por exemplo, somente uma modalidade de bolsa é utilizada: DCR, cujos níveis e valores ficam
    registrados neste módulo.

    Uma bolsa tem atributos que são registrados no momento de sua criação. Todos são obrigatórios:

    * Modalidade
    * Nível
    * Valor de mensalidade
    * Valor de auxílios

.. topic:: Ações relacionadas às bolsas

    * Listar bolsas cadastradas: lista_bolsas
    * Registrar uma bolsa: cria_bolsa
    * Atualizar dados de uma bolsa: update

"""

# views.py na pasta bolsas

from flask import render_template,url_for,flash, redirect,request,Blueprint
from flask_login import login_required, current_user
from project import db
from project.models import Bolsa
from project.bolsas.forms import BolsaForm
from project.demandas.views import registra_log_auto

import locale

bolsas = Blueprint('bolsas',__name__,
                            template_folder='templates/bolsas')

### ATUALIZAR Bolsa

@bolsas.route("/<int:bolsa_id>/update", methods=['GET', 'POST'])
@login_required
def update(bolsa_id):
    """
    +---------------------------------------------------------------------------------------+
    |Permite atualizar os dados de uma bolsa selecionado na tela de consulta.               |
    |                                                                                       |
    |Recebe o ID da bolsa como parâmetro.                                                   |
    +---------------------------------------------------------------------------------------+
    """

    bolsa = Bolsa.query.get_or_404(bolsa_id)

    form = BolsaForm()

    if form.validate_on_submit():

        bolsa.mod         = form.mod.data
        bolsa.niv         = form.niv.data
        bolsa.mensalidade = float(form.mensalidade.data.replace('.','').replace(',','.'))
        bolsa.auxilio     = float(form.auxilio.data.replace('.','').replace(',','.'))

        db.session.commit()

        registra_log_auto(current_user.id,None,'bol')

        flash('Modalidade atualizada!')
        return redirect(url_for('bolsas.lista_bolsas'))
    # traz a informação atual da bolsa
    elif request.method == 'GET':
        form.mod.data     = bolsa.mod
        form.niv.data     = bolsa.niv
        form.mensalidade.data = locale.currency( bolsa.mensalidade, symbol=False, grouping = True )
        form.auxilio.data     = locale.currency( bolsa.auxilio, symbol=False, grouping = True )

    return render_template('add_bolsa.html', title='Update',
                           form=form)

### CRIAR bolsa

@bolsas.route("/criar", methods=['GET', 'POST'])
@login_required
def cria_bolsa():
    """
    +---------------------------------------------------------------------------------------+
    |Permite registrar, ou alterar, os dados de um bolsa.                                   |
    +---------------------------------------------------------------------------------------+
    """

    form = BolsaForm()

    if form.validate_on_submit():
        bolsa = Bolsa(mod         = form.mod.data,
                      niv         = form.niv.data,
                      mensalidade = float(form.mensalidade.data.replace('.','').replace(',','.')),
                      auxilio     = float(form.auxilio.data.replace('.','').replace(',','.')),
                      )
        db.session.add(bolsa)
        db.session.commit()

        registra_log_auto(current_user.id,None,'bol')

        flash('Bolsa registrada!')
        return redirect(url_for('bolsas.lista_bolsas'))

    return render_template('add_bolsa.html', form=form)


## lista bolsas - todos

@bolsas.route('/bolsas')
def lista_bolsas():
    """
    +---------------------------------------------------------------------------------------+
    |Lista as bolsas cadastradas no sistema.                                                |
    +---------------------------------------------------------------------------------------+
    """


    # traz os dados das bolsas cadastratas

    bolsas = db.session.query(Bolsa.id,Bolsa.mod,Bolsa.niv,Bolsa.mensalidade,Bolsa.auxilio).all()

    quantidade = len(bolsas)

    # reescreve a saida da query 'bolsas' para ajustar formato de dinheiro
    bolsas_s = []
    for bolsa in bolsas:
        bolsa_s = list(bolsa)
        bolsa_s[3] = locale.currency(bolsa_s[3], symbol=False, grouping = True)
        bolsa_s[4] = locale.currency(bolsa_s[4], symbol=False, grouping = True)

        bolsas_s.append(bolsa_s)

    return render_template('list_bolsas.html', quantidade = quantidade,
                            bolsas=bolsas, bolsas_s = bolsas_s)
