"""
.. topic:: Pessoas (views)

    As Pessoas são os servidores lotados na intituião.


.. topic:: Ações relacionadas às pessoas

    * Lista pessoas: lista_pessoas
    * Atualiza pessoa: pessoa_update
    * Acrescenta uma pessoa: cria_pessoa

"""

# views.py na pasta pessoas

from flask import render_template,url_for,flash, redirect,request,Blueprint
from sqlalchemy.sql import label
from sqlalchemy.orm import aliased
from project import db
from project.models import Unidades, Pessoas, Situ_Pessoa, Tipo_Func_Pessoa, Tipo_Vinculo_Pessoa
from project.pessoas.forms import PessoaForm

import locale
import datetime
from datetime import date
from calendar import monthrange


pessoas = Blueprint('pessoas',__name__, template_folder='templates')


## lista pessoas da instituição

@pessoas.route('/lista_pessoas')
def lista_pessoas():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista das pessoas da instituição.                                       |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
# Lê tabela pessoas

    pessoas = db.session.query(Pessoas.pessoaId,
                             Pessoas.pesNome,
                             Pessoas.pesCPF,
                             Pessoas.pesDataNascimento,
                             Pessoas.pesMatriculaSiape,
                             Pessoas.pesEmail,
                             Pessoas.unidadeId,
                             Unidades.undSigla,
                             Pessoas.tipoFuncaoId,
                             Tipo_Func_Pessoa.tfnDescricao,
                             Pessoas.cargaHoraria,
                             Pessoas.situacaoPessoaId,
                             Situ_Pessoa.spsDescricao,
                             Pessoas.tipoVinculoId,
                             Tipo_Vinculo_Pessoa.tvnDescricao)\
                            .outerjoin(Unidades,Unidades.unidadeId == Pessoas.unidadeId)\
                            .outerjoin(Situ_Pessoa, Situ_Pessoa.situacaoPessoaId == Pessoas.situacaoPessoaId)\
                            .outerjoin(Tipo_Func_Pessoa,Tipo_Func_Pessoa.tipoFuncaoId == Pessoas.tipoFuncaoId)\
                            .outerjoin(Tipo_Vinculo_Pessoa,Tipo_Vinculo_Pessoa.tipoVinculoId == Pessoas.tipoVinculoId)\
                            .order_by(Pessoas.pesNome).all()

    quantidade = len(pessoas)


    return render_template('lista_pessoas.html', pessoas = pessoas, quantidade=quantidade)

#
### atualiza dados de uma pessoa

@pessoas.route("/<int:cod_pes>/update", methods=['GET', 'POST'])

def pessoa_update(cod_pes):
    """
    +----------------------------------------------------------------------------------------------+
    |Permite atualizar os dados de uma pessoa                                                     |
    |                                                                                              |
    |Recebe o código da pessoa como parâmetro.                                                    |
    +----------------------------------------------------------------------------------------------+
    """

    tp = 'atu'

    pessoa = Pessoas.query.filter(Pessoas.pessoaId==cod_pes).first_or_404()

    unids = db.session.query(Unidades.unidadeId, Unidades.undSigla)\
                      .order_by(Unidades.undSigla).all()
    lista_unids = [(int(u.unidadeId),u.undSigla) for u in unids]
    lista_unids.insert(0,(0,''))                

    situ = db.session.query(Situ_Pessoa.situacaoPessoaId, Situ_Pessoa.spsDescricao)\
                     .order_by(Situ_Pessoa.spsDescricao).all()
    lista_situ = [(int(s.situacaoPessoaId),s.spsDescricao) for s in situ]
    lista_situ.insert(0,(0,''))

    func = db.session.query(Tipo_Func_Pessoa.tipoFuncaoId, Tipo_Func_Pessoa.tfnDescricao)\
                     .order_by(Tipo_Func_Pessoa.tfnDescricao).all()
    lista_func = [(int(f.tipoFuncaoId),f.tfnDescricao) for f in func]
    lista_func.insert(0,(0,'Sem função'))

    vinc = db.session.query(Tipo_Vinculo_Pessoa.tipoVinculoId, Tipo_Vinculo_Pessoa.tvnDescricao)\
                     .order_by(Tipo_Vinculo_Pessoa.tvnDescricao).all()
    lista_vinc = [(int(v.tipoVinculoId),v.tvnDescricao) for v in vinc]
    lista_vinc.insert(0,(0,''))

    form = PessoaForm()

    form.func.choices    = lista_func
    form.situ.choices    = lista_situ
    form.vinculo.choices = lista_vinc
    form.unidade.choices = lista_unids
    
    if form.validate_on_submit():

        if form.func.data == 0:
            funcPes = None
        else:
            funcPes = form.func.data

        if form.situ.data == 0:
            situPes = None
        else:
            situPes = form.situ.data

        if form.vinculo.data == 0:
            vincuPes = None
        else:
            vincuPes = form.vinculo.data

        pessoa.pesNome            = form.nome.data
        pessoa.pesCPF             = form.cpf.data
        pessoa.pesDataNascimento  = form.nasc.data
        pessoa.pesMatriculaSiape  = form.siape.data
        pessoa.pesEmail           = form.email.data
        pessoa.unidadeId          = form.unidade.data
        pessoa.tipoFuncaoId       = funcPes
        pessoa.cargaHoraria       = form.carga.data
        pessoa.situacaoPessoaId   = situPes
        pessoa.tipoVinculoId      = vincuPes

        db.session.commit()

        flash('Dados de '+str(form.nome.data) +' atualizados no DBSISGP!','sucesso')

        return redirect(url_for('pessoas.lista_pessoas'))

    # traz a informação atual do pessoas

    elif request.method == 'GET':

        form.nome.data    = pessoa.pesNome          
        form.cpf.data     = pessoa.pesCPF           
        form.nasc.data    = pessoa.pesDataNascimento 
        form.siape.data   = pessoa.pesMatriculaSiape 
        form.email.data   = pessoa.pesEmail          
        form.unidade.data = pessoa.unidadeId      
        form.func.data    = pessoa.tipoFuncaoId    
        form.carga.data   = pessoa.cargaHoraria  
        form.situ.data    = pessoa.situacaoPessoaId 
        form.vinculo.data = pessoa.tipoVinculoId 

    return render_template('atu_pessoa.html', form=form, tp=tp)

#
### insere nova pessoa no banco de dados

@pessoas.route("/cria_pessoa", methods=['GET', 'POST'])

def cria_pessoa():
    """
    +----------------------------------------------------------------------------------------------+
    |Inserção de uma nova pessoa no sistema                                                       |
    |                                                                                              |
    +----------------------------------------------------------------------------------------------+
    """

    tp = 'ins'

    unids = db.session.query(Unidades.unidadeId, Unidades.undSigla)\
                      .order_by(Unidades.undSigla).all()
    lista_unids = [(int(u.unidadeId),u.undSigla) for u in unids]
    lista_unids.insert(0,(0,''))

    situ = db.session.query(Situ_Pessoa.situacaoPessoaId, Situ_Pessoa.spsDescricao)\
                     .order_by(Situ_Pessoa.spsDescricao).all()
    lista_situ = [(int(s.situacaoPessoaId),s.spsDescricao) for s in situ]
    lista_situ.insert(0,(0,''))

    func = db.session.query(Tipo_Func_Pessoa.tipoFuncaoId, Tipo_Func_Pessoa.tfnDescricao)\
                     .order_by(Tipo_Func_Pessoa.tfnDescricao).all()
    lista_func = [(int(f.tipoFuncaoId),f.tfnDescricao) for f in func]
    lista_func.insert(0,(0,'Sem função'))

    vinc = db.session.query(Tipo_Vinculo_Pessoa.tipoVinculoId, Tipo_Vinculo_Pessoa.tvnDescricao)\
                     .order_by(Tipo_Vinculo_Pessoa.tvnDescricao).all()
    lista_vinc = [(int(v.tipoVinculoId),v.tvnDescricao) for v in vinc]
    lista_vinc.insert(0,(0,''))

    form = PessoaForm()

    form.func.choices    = lista_func
    form.situ.choices    = lista_situ
    form.vinculo.choices = lista_vinc
    form.unidade.choices = lista_unids


    if form.validate_on_submit():

        if form.func.data == 0:
            funcPes = None
        else:
            funcPes = form.func.data

        if form.situ.data == 0:
            situPes = None
        else:
            situPes = form.situ.data

        if form.vinculo.data == 0:
            vincuPes = None
        else:
            vincuPes = form.vinculo.data     

        pessoa = Pessoas(pesNome           = form.nome.data,
                         pesCPF            = form.cpf.data,
                         pesDataNascimento = form.nasc.data,
                         pesMatriculaSiape = form.siape.data,
                         pesEmail          = form.email.data,
                         unidadeId         = form.unidade.data,
                         tipoFuncaoId      = funcPes,
                         cargaHoraria      = form.carga.data,
                         situacaoPessoaId  = situPes,
                         tipoVinculoId     = vincuPes)

        db.session.add(pessoa)
        db.session.commit()

        flash(str(form.nome.data +' inserido(a) no DBSISGP!'),'sucesso')

        return redirect(url_for('pessoas.lista_pessoas'))

    return render_template('atu_pessoa.html', form=form, tp=tp)