"""
.. topic:: Pessoas (views)

    As Pessoas são os servidores lotados na intituião.


.. topic:: Ações relacionadas às pessoas

    * lista_pessoas: Lista pessoas
    * lista_pessoas_filtro: Lista pessoas de acordo com filtro aplicado
    * lista_gestores_sisgp: pessoas que estão como GestorSistema
    * pessoa_update: Atualiza pessoa
    * cria_pessoa: Acrescenta uma pessoa
    * lista_pessoas_unid: Pessoas de uma unidade

"""

# views.py na pasta pessoas

from flask import render_template,url_for,flash, redirect,request,Blueprint
from flask_login import current_user, login_required

from sqlalchemy import cast, String
from sqlalchemy.sql import label
from sqlalchemy.orm import aliased
from project import db
from project.models import Unidades, Pessoas, Situ_Pessoa, Tipo_Func_Pessoa, Tipo_Vinculo_Pessoa, catdom
from project.pessoas.forms import PessoaForm, PesquisaForm

from project.usuarios.views import registra_log_auto

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
    |Apresenta uma lista das pessoas da instituição.                                        |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    tipo = "inst"

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

    gestorQtd = db.session.query(catdom.descricao)\
                       .filter(catdom.classificacao == 'GestorSistema').count()


    return render_template('lista_pessoas.html', pessoas = pessoas, quantidade=quantidade,
                                                 gestorQtd = gestorQtd, tipo = tipo)


## lista pessoas da instituição conforme filtro aplicado

@pessoas.route('/lista_pessoas_filtro', methods=['GET','POST'])
def lista_pessoas_filtro():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista das pessoas da instituição via filtro                              |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    tipo = "pesq"

    form = PesquisaForm()

    unids = db.session.query(Unidades.unidadeId, Unidades.undSigla).order_by(Unidades.undSigla).all()
    lista_unids = [(u.unidadeId,u.undSigla) for u in unids]
    lista_unids.insert(0,(0,'Todas'))                

    situ = db.session.query(Situ_Pessoa.situacaoPessoaId, Situ_Pessoa.spsDescricao).order_by(Situ_Pessoa.spsDescricao).all()
    lista_situ = [(s.situacaoPessoaId,s.spsDescricao) for s in situ]
    lista_situ.insert(0,(0,'Todas'))

    func = db.session.query(Tipo_Func_Pessoa.tipoFuncaoId, Tipo_Func_Pessoa.tfnDescricao).order_by(Tipo_Func_Pessoa.tfnDescricao).all()
    lista_func = [(f.tipoFuncaoId,f.tfnDescricao) for f in func]
    lista_func.insert(0,(-1,'Sem função'))
    lista_func.insert(0,(0,'Todas'))

    vinc = db.session.query(Tipo_Vinculo_Pessoa.tipoVinculoId, Tipo_Vinculo_Pessoa.tvnDescricao).order_by(Tipo_Vinculo_Pessoa.tvnDescricao).all()
    lista_vinc = [(v.tipoVinculoId,v.tvnDescricao) for v in vinc]
    lista_vinc.insert(0,(0,'Todos'))

    form.func.choices    = lista_func
    form.situ.choices    = lista_situ
    form.vinculo.choices = lista_vinc
    form.unidade.choices = lista_unids

    if form.validate_on_submit():

        if int(form.unidade.data) == 0:
            p_unidade_pattern = '%'
        else:
            p_unidade_pattern = form.unidade.data

        if int(form.vinculo.data) == 0:
            p_vinculo_pattern = '%'
        else:
            p_vinculo_pattern = form.vinculo.data

        # if int(form.func.data) == 0:
        #     p_func_pattern = '%'
        # else:
        #     p_func_pattern = form.func.data

        if int(form.situ.data) == 0:
            p_situ_pattern = '%'
        else:
            p_situ_pattern = form.situ.data   

        # pega valores utilizados como filtro para exibição na tela da lista
        p_vinculo = dict(form.vinculo.choices).get(int(form.vinculo.data))
        p_func    = dict(form.func.choices).get(int(form.func.data))
        p_situ    = dict(form.situ.choices).get(int(form.situ.data))
        p_unid    = dict(form.unidade.choices).get(int(form.unidade.data)) 

        if int(form.func.data) == -1:

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
                                .filter(Pessoas.pesNome.like('%'+form.nome.data+'%'),
                                        Pessoas.unidadeId.like(p_unidade_pattern),
                                        Pessoas.tipoFuncaoId.is_(None),
                                        Pessoas.situacaoPessoaId.like(p_situ_pattern),
                                        Pessoas.tipoVinculoId.like(p_vinculo_pattern))\
                                .order_by(Pessoas.pesNome).all()

            quantidade = len(pessoas)

        elif int(form.func.data) == 0:

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
                                    .filter(Pessoas.pesNome.like('%'+form.nome.data+'%'),
                                            Pessoas.unidadeId.like(p_unidade_pattern),
                                            Pessoas.situacaoPessoaId.like(p_situ_pattern),
                                            Pessoas.tipoVinculoId.like(p_vinculo_pattern))\
                                    .order_by(Pessoas.pesNome).all()

            quantidade = len(pessoas)

        else:

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
                                    .filter(Pessoas.pesNome.like('%'+form.nome.data+'%'),
                                            Pessoas.unidadeId.like(p_unidade_pattern),
                                            Pessoas.tipoFuncaoId == form.func.data,
                                            Pessoas.situacaoPessoaId.like(p_situ_pattern),
                                            Pessoas.tipoVinculoId.like(p_vinculo_pattern))\
                                    .order_by(Pessoas.pesNome).all()

            quantidade = len(pessoas)

        gestorQtd = db.session.query(catdom.descricao)\
                        .filter(catdom.classificacao == 'GestorSistema').count()


        return render_template('lista_pessoas.html', pessoas = pessoas, quantidade=quantidade,
                                                    gestorQtd = gestorQtd, tipo = tipo,
                                                    p_vinculo = p_vinculo, p_func = p_func,
                                                    p_situ = p_situ, p_unid = p_unid, p_nome = form.nome.data)

    return render_template('pesquisa_pessoas.html', form = form)                                                

## lista gestores do SISGP

@pessoas.route('/lista_gestores_sisgp')

def lista_gestores_sisgp():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista das pessoas que foram cadastratas como gestores do sisgp.          |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    tipo = "gest"

# Lê tabela pessoas

    gestores = db.session.query(Pessoas.pessoaId,
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
                            .outerjoin(catdom, catdom.descricao == cast(Pessoas.pessoaId,String))\
                            .filter(catdom.classificacao == 'GestorSistema')\
                            .order_by(Pessoas.pesNome).all()

    quantidade = len(gestores)


    return render_template('lista_pessoas.html', pessoas = gestores, quantidade=quantidade,
                                                 gestorQtd = quantidade, tipo = tipo)

#
### atualiza dados de uma pessoa

@pessoas.route("/<int:cod_pes>/update", methods=['GET', 'POST'])
@login_required

def pessoa_update(cod_pes):
    """
    +----------------------------------------------------------------------------------------------+
    |Permite atualizar os dados de uma pessoa                                                      |
    |                                                                                              |
    |Recebe o código da pessoa como parâmetro.                                                     |
    +----------------------------------------------------------------------------------------------+
    """

    tp = 'atu'

    pessoa = Pessoas.query.filter(Pessoas.pessoaId==cod_pes).first_or_404()

    gestor = db.session.query(catdom).filter(catdom.descricao == str(cod_pes), catdom.classificacao == 'GestorSistema')

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

        if current_user.userAtivo:

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

            if gestor.first() == None and form.gestor.data == True:

                last_cat_dom = db.session.query(catdom).order_by(catdom.catalogoDominioId.desc()).first()

                novo_gestor = catdom(catalogoDominioId = last_cat_dom.catalogoDominioId + 1,
                                     classificacao='GestorSistema',
                                     descricao = pessoa.pessoaId,
                                     ativo = True)
                db.session.add(novo_gestor)
                db.session.commit()
                registra_log_auto(current_user.id, pessoa.pesNome + 'colocada como gestora do SISGP.')
            
            if gestor != None and form.gestor.data == False:
                gestor.delete()
                db.session.commit()

            registra_log_auto(current_user.id,'Pessoa '+ str(pessoa.pessoaId) +' '+ pessoa.pesNome +' teve dados alterados.')

            flash('Dados de '+str(form.nome.data) +' atualizados no DBSISGP!','sucesso')

            return redirect(url_for('pessoas.lista_pessoas'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

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

        if gestor.first() != None:
            form.gestor.data = True
        else:
            form.gestor.data = False 

    return render_template('atu_pessoa.html', form=form, tp=tp)

#
### insere nova pessoa no banco de dados

@pessoas.route("/cria_pessoa", methods=['GET', 'POST'])
@login_required

def cria_pessoa():
    """
    +----------------------------------------------------------------------------------------------+
    |Inserção de uma nova pessoa no sistema                                                        |
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

        if current_user.userAtivo:

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

            registra_log_auto(current_user.id,'Pessoa '+ str(pessoa.pessoaId) +' '+ pessoa.pesNome +' inserida no banco de dados.')

            flash(str(form.nome.data +' inserido(a) no DBSISGP!'),'sucesso')

            return redirect(url_for('pessoas.lista_pessoas'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('pessoas.lista_pessoas'))


    return render_template('atu_pessoa.html', form=form, tp=tp)

## lista pessoas de uma unidade

@pessoas.route('/<unid>/lista_pessoas_unid')
def lista_pessoas_unid(unid):
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista das pessoas de uma unidade.                                        |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
# Lê tabela pessoas

    tipo = "unid"

    r_unid = unid.replace('[','').replace(']','').replace(' ','').replace("'","")

    l_unid = r_unid.split(',')

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
                            .filter(Unidades.undSigla.in_(l_unid))\
                            .order_by(Pessoas.unidadeId,Pessoas.pesNome).all()

    quantidade = len(pessoas)

    return render_template('lista_pessoas.html', pessoas = pessoas, quantidade=quantidade,
                                                 gestorNome = None, tipo = tipo, unid=unid)

#