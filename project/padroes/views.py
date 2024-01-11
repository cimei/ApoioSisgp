"""
.. topic:: Padrões (views)

    Os padrões são as situações e tipos específicos de uma instituição.


.. topic:: Ações relacionadas às pessoas

    * lista_tipo_funcao: Lista tipos de funções utilizadas na instituição
    * func_pessoas_update: Atualiza dados de um tipo de função para pessoas
    * cria_func_pessoas: Cria função para pessoas
    * lista_vinc_pessoas: Lista tipos de vínculo
    * vinc_pessoas_update: Atualiza tipo de vínculo
    * cria_vinc_pessoas: Cria tipo de vínculo
    * lista_feriados: Lista feriados 
    * feriado_update: Atualizar dados de um feriado
    * cria_feriado: Adiciona feriado no banco
    * padroes_i: Auxiliar no menu em cascata de dados auxiliares

"""

# views.py na pasta padroes

from flask import render_template,url_for,flash, redirect,request,Blueprint
from flask_login import current_user, login_required

from sqlalchemy.sql import label
from sqlalchemy.orm import aliased
from sqlalchemy import insert
from project import db
from project.models import Tipo_Func_Pessoa, Feriados
from project.padroes.forms import Func_PessoasForm, Vinc_PessoasForm, FeriadoForm

from project.usuarios.views import registra_log_auto

import locale
import datetime
from datetime import date

padroes = Blueprint('padroes',__name__, template_folder='templates')


## lista os tipos de função na instituição

@padroes.route('/lista_tipo_funcao')
def lista_tipo_funcao():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos tipos de função comissionada utilizados na instituição.        |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
# Lê tabela Tipo_Func_Pessoa

    func_pessoas = db.session.query(Tipo_Func_Pessoa.tipoFuncaoId,
                                    Tipo_Func_Pessoa.tfnDescricao,
                                    Tipo_Func_Pessoa.tfnCodigoFuncao,
                                    Tipo_Func_Pessoa.tfnIndicadorChefia)\
                             .order_by(Tipo_Func_Pessoa.tipoFuncaoId).all()

    quantidade = len(func_pessoas)


    return render_template('lista_func_pessoas.html', func_pessoas = func_pessoas, quantidade=quantidade)

#
### atualiza dados de um tipo de função

@padroes.route("/<int:cod_func>/atualiza_func", methods=['GET', 'POST'])
@login_required

def func_pessoas_update(cod_func):
    """
    +----------------------------------------------------------------------------------------------+
    |Permite atualizar os dados de uma função                                                      |
    |                                                                                              |
    |Recebe o id da função como parâmetro.                                                         |
    +----------------------------------------------------------------------------------------------+
    """    

    tp = 'atu'

    func_pes = Tipo_Func_Pessoa.query.filter(Tipo_Func_Pessoa.tipoFuncaoId==cod_func).first_or_404()

    form = Func_PessoasForm()
    
    if form.validate_on_submit():

        if current_user.userAtivo:

            func_pes.tfnDescricao       = form.desc.data
            func_pes.tfnCodigoFuncao    = form.cod.data
            func_pes.tfnIndicadorChefia = form.indic.data

            db.session.commit()

            registra_log_auto(current_user.id,'TipoFuncao '+ str(func_pes.tipoFuncaoId) +' '+ func_pes.tfnDescricao +' foi alterada.')

            flash('Dados de Função atualizados!','sucesso')

            return redirect(url_for('padroes.lista_tipo_funcao'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('padroes.lista_tipo_funcao'))

    # traz a dados atuais da função

    elif request.method == 'GET':

        form.id.data   = func_pes.tipoFuncaoId 
        form.desc.data  = func_pes.tfnDescricao
        form.cod.data   = func_pes.tfnCodigoFuncao
        form.indic.data = func_pes.tfnIndicadorChefia


    return render_template('atu_func_pessoas.html', form=form, tp=tp)

### insere nova função de pessoas no banco de dados

@padroes.route("/cria_func_pessoas", methods=['GET', 'POST'])
@login_required

def cria_func_pessoas():
    """
    +----------------------------------------------------------------------------------------------+
    |Inserção de uma nova função para pessoas no sistema                                           |
    |                                                                                              |
    +----------------------------------------------------------------------------------------------+
    """

    tp = 'ins'

    form = Func_PessoasForm()

    if form.validate_on_submit():

        if current_user.userAtivo:

            verifica = db.session.query(Tipo_Func_Pessoa).filter(Tipo_Func_Pessoa.tipoFuncaoId==form.id.data).first()

            if verifica == None:

                func_pes = Tipo_Func_Pessoa(tipoFuncaoId       = form.id.data, 
                                            tfnDescricao       = form.desc.data,
                                            tfnCodigoFuncao    = form.cod.data, 
                                            tfnIndicadorChefia = form.indic.data)

                db.session.add(func_pes)
                db.session.commit()

                registra_log_auto(current_user.id,'TipoFuncao '+ str(func_pes.tipoFuncaoId) +' '+ func_pes.tfnDescricao +' foi inserida no banco.')

                flash('Tipo de função '+str(form.desc.data +' inserido no DBSISGP!'),'sucesso')

                return redirect(url_for('padroes.lista_tipo_funcao'))

            else:

                flash('ID informado já existe no DBSISGP!','erro')

                return render_template('atu_func_pessoas.html', form=form, tp=tp)


        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('padroes.lista_tipo_funcao'))

    return render_template('atu_func_pessoas.html', form=form, tp=tp)




## lista os feriados cadastrados

@padroes.route('/lista_feriados')
def lista_feriados():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos feriados cadastrados.                                          |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
# Lê tabela Feriados

    feriados = db.session.query(Feriados.feriadoId,
                                Feriados.ferData,
                                Feriados.ferFixo,
                                Feriados.ferDescricao,
                                Feriados.ufId)\
                          .order_by(Feriados.ferData).all()

    quantidade = len(feriados)


    return render_template('lista_feriados.html', feriados = feriados, quantidade=quantidade)

#
### atualiza dados de um feriado

@padroes.route("/<int:cod_fer>/atualiza_fer", methods=['GET', 'POST'])
@login_required

def feriado_update(cod_fer):
    """
    +----------------------------------------------------------------------------------------------+
    |Permite atualizar os dados de um feriado.                                                     |
    |                                                                                              |
    |Recebe o id do feriado como parâmetro.                                                        |
    +----------------------------------------------------------------------------------------------+
    """    

    tp = 'atu'

    feriado = Feriados.query.filter(Feriados.feriadoId==cod_fer).first_or_404()

    form = FeriadoForm()
    
    if form.validate_on_submit():

        if current_user.userAtivo:

            if form.ufId.data == '':
                uf = None
            else:
                uf = form.ufId.data

            feriado.ferData      = form.ferData.data
            feriado.ferFixo      = form.ferFixo.data
            feriado.ferDescricao = form.ferDescricao.data
            feriado.ufId         = uf

            db.session.commit()

            registra_log_auto(current_user.id,'Feriado '+ str(feriado.ferData.strftime('%d/%m/%Y'))  +' foi alterado.')

            flash('Dados de Feriado atualizados!','sucesso')

            return redirect(url_for('padroes.lista_feriados'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('padroes.lista_feriados'))



    # traz dados atuais do feriado

    elif request.method == 'GET':

        form.ferData.data      = feriado.ferData 
        form.ferDescricao.data = feriado.ferDescricao
        form.ferFixo.data      = feriado.ferFixo
        form.ufId.data         = feriado.ufId


    return render_template('atu_feriados.html', form=form, tp=tp)

### insere novo feriado no banco de dados

@padroes.route("/cria_feriado", methods=['GET', 'POST'])
@login_required

def cria_feriado():
    """
    +----------------------------------------------------------------------------------------------+
    |Inserção de novo feriado.                                                                     |
    |                                                                                              |
    +----------------------------------------------------------------------------------------------+
    """

    tp = 'ins'

    last = db.session.query(Feriados).order_by(Feriados.feriadoId.desc()).first()

    form = FeriadoForm()

    if form.validate_on_submit():

        if current_user.userAtivo:

            if form.ufId.data == '':
                uf = None
            else:
                uf = form.ufId.data

            feriado = Feriados(ferData      = form.ferData.data, 
                            ferFixo      = form.ferFixo.data,
                            ferDescricao = form.ferDescricao.data, 
                            ufId         = uf)

            db.session.add(feriado)
            db.session.commit()

            registra_log_auto(current_user.id,'Feriado '+ str(feriado.ferData.strftime('%d/%m/%Y'))  +' foi incluido no banco de dados.')

            flash('Feriado '+str(form.ferDescricao.data +' inserido no DBSISGP!'),'sucesso')

            return redirect(url_for('padroes.lista_feriados'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('padroes.lista_feriados'))

    #form.feriadoId.data = last.feriadoId + 1

    return render_template('atu_feriados.html', form=form, tp=tp)

## renderiza tela inicial do padrões

@padroes.route('/padroes_i')
@login_required

def padroes_i():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta tela inicial ddos padrões.                                                   |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    
    return render_template('padroes.html') 