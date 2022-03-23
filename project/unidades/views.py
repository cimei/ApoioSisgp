"""
.. topic:: Unidades (views)

    Os Unidades as caixas na estrutura da instituição.


.. topic:: Ações relacionadas às Unidades

    * Lista unidades: lista_unidades
    * Atualiza unidade: unidade_update
    * Acrescenta unidade: cria_unidade

"""

# views.py na pasta unidades

from flask import render_template,url_for,flash, redirect,request,Blueprint
from flask_login import current_user, login_required

from sqlalchemy import func
from sqlalchemy.sql import label
from sqlalchemy.orm import aliased
from project import db
from project.models import Atividades, Unidades, Pessoas, cat_item_cat, unidade_ativ
from project.unidades.forms import UnidadeForm

from project.usuarios.views import registra_log_auto

unidades = Blueprint('unidades',__name__, template_folder='templates')


## lista unidades da instituição

@unidades.route('/lista_unidades')

def lista_unidades():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista das unidades da instituição.                                       |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
# Lê tabela unidades

    unids_pai = db.session.query(Unidades.unidadeId,Unidades.undSigla).subquery()

    chefes = db.session.query(Pessoas.pessoaId, Pessoas.pesNome)\
                       .filter(Pessoas.tipoFuncaoId != None)\
                       .order_by(Pessoas.pesNome).subquery()

    subs = db.session.query(Pessoas.pessoaId, Pessoas.pesNome)\
                       .filter(Pessoas.tipoFuncaoId != None)\
                       .order_by(Pessoas.pesNome).subquery()    

    lista_tipo_unidade = [(1,'Instituição'),(2,'Diretoria'),(3,'Coordenação-Geral'),(4,'Coordenação'),(5,'Serviço')]

    lista_situ_unidade = [(1,'Ativa'),(2,'Inativa')]

    ativs_lista = db.session.query(Atividades.titulo,
                                   cat_item_cat.catalogoId,
                                   unidade_ativ.unidadeId)\
                            .join(cat_item_cat, cat_item_cat.itemCatalogoId == Atividades.itemCatalogoId)\
                            .join(unidade_ativ, unidade_ativ.catalogoId == cat_item_cat.catalogoId)\
                            .order_by(Atividades.titulo)\
                            .all()    

    ativs = db.session.query(unidade_ativ.unidadeId,
                             label('qtd_ativs',func.count(unidade_ativ.catalogoId)))\
                       .join(cat_item_cat, cat_item_cat.catalogoId == unidade_ativ.catalogoId)\
                       .join(Atividades, Atividades.itemCatalogoId == cat_item_cat.itemCatalogoId)\
                       .group_by(unidade_ativ.unidadeId)\
                       .subquery()

    pessoas_unid = db.session.query(Pessoas.unidadeId,
                                    label('qtd_pes',func.count(Pessoas.unidadeId)))\
                             .group_by(Pessoas.unidadeId)\
                             .subquery()                   

    unids = db.session.query(Unidades.unidadeId,
                             Unidades.undSigla,
                             Unidades.undDescricao,
                             Unidades.unidadeIdPai,
                             unids_pai.c.undSigla.label("Sigla_Pai"),
                             Unidades.tipoUnidadeId,
                             Unidades.situacaoUnidadeId,
                             Unidades.ufId,
                             Unidades.undNivel,
                             Unidades.tipoFuncaoUnidadeId,
                             Unidades.Email,
                             Unidades.undCodigoSIORG,
                             Unidades.pessoaIdChefe,
                             chefes.c.pesNome.label("Chefe"),
                             Unidades.pessoaIdChefeSubstituto,
                             subs.c.pesNome.label("Subs"),
                             ativs.c.qtd_ativs,
                             pessoas_unid.c.qtd_pes)\
                            .outerjoin(unids_pai,unids_pai.c.unidadeId == Unidades.unidadeIdPai)\
                            .outerjoin(chefes,chefes.c.pessoaId == Unidades.pessoaIdChefe)\
                            .outerjoin(subs,subs.c.pessoaId == Unidades.pessoaIdChefeSubstituto)\
                            .outerjoin(ativs,ativs.c.unidadeId == Unidades.unidadeId)\
                            .outerjoin(pessoas_unid, pessoas_unid.c.unidadeId == Unidades.unidadeId)\
                            .order_by(Unidades.undSigla).all()

    quantidade = len(unids)


    return render_template('lista_unidades.html', unids = unids, quantidade = quantidade,
                                                lista_situ_unidade = lista_situ_unidade, 
                                                lista_tipo_unidade = lista_tipo_unidade,
                                                ativs_lista = ativs_lista)

#
### atualiza dados de uma unidade

@unidades.route("/<int:cod_unid>/update", methods=['GET', 'POST'])
@login_required

def unidade_update(cod_unid):
    """
    +----------------------------------------------------------------------------------------------+
    |Permite atualizar os dados de uma Unidade                                                     |
    |                                                                                              |
    |Recebe o código da unidade como parâmetro.                                                    |
    +----------------------------------------------------------------------------------------------+
    """

    pais = db.session.query(Unidades.unidadeId, Unidades.undSigla)\
                         .filter(Unidades.tipoUnidadeId < 5)\
                         .order_by(Unidades.undSigla).all()
    lista_pais = [(int(p.unidadeId),p.undSigla) for p in pais]
    lista_pais.insert(0,(0,''))

    chefes = db.session.query(Pessoas.pessoaId, Pessoas.pesNome)\
                         .filter(Pessoas.tipoFuncaoId != None)\
                         .order_by(Pessoas.pesNome).all()
    lista_chefes = [(int(c.pessoaId),c.pesNome) for c in chefes]
    lista_chefes.insert(0,(0,''))

    lista_tipo_unidade = [(1,'Instituição'),(2,'Diretoria'),(3,'Coordenação-Geral'),(4,'Coordenação'),(5,'Serviço')]

    lista_situ_unidade = [(1,'Ativa'),(2,'Inativa')]

    unidade = Unidades.query.filter(Unidades.unidadeId==cod_unid).first_or_404()

    form = UnidadeForm()

    form.pai.choices = lista_pais
    form.chefe.choices = lista_chefes
    form.subs.choices = lista_chefes
    form.tipo.choices = lista_tipo_unidade
    form.situ.choices = lista_situ_unidade


    if form.validate_on_submit():

        if current_user.userAtivo:

            unidade.undSigla                 = form.sigla.data
            unidade.undDescricao             = form.desc.data
            unidade.unidadeIdPai             = form.pai.data
            unidade.tipoUnidadeId            = form.tipo.data
            unidade.situacaoUnidadeId        = form.situ.data
            unidade.ufId                     = form.uf.data
            unidade.undNivel                 = form.nivel.data
            unidade.tipoFuncaoUnidadeId      = form.tipoFun.data
            unidade.Email                    = form.email.data
            unidade.undCodigoSIORG           = form.siorg.data
            unidade.pessoaIdChefe            = form.chefe.data
            unidade.pessoaIdChefeSubstituto  = form.subs.data

            db.session.commit()

            registra_log_auto(current_user.id,'Unidade '+ str(unidade.unidadeId) +' '+ unidade.undSigla +' teve dados alterados.')

            flash('Unidade atualizada!','sucesso')

            return redirect(url_for('unidades.lista_unidades'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('unidades.lista_unidades'))


    # traz a informação atual do Unidades

    elif request.method == 'GET':

        form.sigla.data   = unidade.undSigla
        form.desc.data    = unidade.undDescricao
        form.pai.data     = unidade.unidadeIdPai
        form.tipo.data    = unidade.tipoUnidadeId
        form.situ.data    = unidade.situacaoUnidadeId
        form.uf.data      = unidade.ufId
        form.nivel.data   = unidade.undNivel
        form.tipoFun.data = unidade.tipoFuncaoUnidadeId
        form.email.data   = unidade.Email
        form.siorg.data   = unidade.undCodigoSIORG
        form.chefe.data   = unidade.pessoaIdChefe
        form.subs.data    = unidade.pessoaIdChefeSubstituto

    return render_template('atu_unidade.html', form=form)

#
### insere nova unidade no banco de dados

@unidades.route("/cria_unidade", methods=['GET', 'POST'])
@login_required

def cria_unidade():
    """
    +----------------------------------------------------------------------------------------------+
    |Inserção de uma nova unidade no sistema                                                       |
    |                                                                                              |
    +----------------------------------------------------------------------------------------------+
    """

    pais = db.session.query(Unidades.unidadeId, Unidades.undSigla)\
                         .filter(Unidades.tipoUnidadeId < 5)\
                         .order_by(Unidades.undSigla).all()
    lista_pais = [(int(p.unidadeId),p.undSigla) for p in pais]
    lista_pais.insert(0,(0,''))

    chefes = db.session.query(Pessoas.pessoaId, Pessoas.pesNome)\
                         .filter(Pessoas.tipoFuncaoId != None)\
                         .order_by(Pessoas.pesNome).all()
    lista_chefes = [(int(c.pessoaId),c.pesNome) for c in chefes]
    lista_chefes.insert(0,(0,''))

    lista_tipo_unidade = [(1,'Instituição'),(2,'Diretoria'),(3,'Coordenação-Geral'),(4,'Coordenação'),(5,'Serviço')]

    lista_situ_unidade = [(1,'Ativa'),(2,'Inativa')]

    form = UnidadeForm()

    form.pai.choices = lista_pais
    form.chefe.choices = lista_chefes
    form.subs.choices = lista_chefes
    form.tipo.choices = lista_tipo_unidade
    form.situ.choices = lista_situ_unidade


    if form.validate_on_submit():

        if current_user.userAtivo:

            if form.pai.data == 0:
                pai = None
            else:
                pai = form.pai.data

            if form.chefe.data == 0:
                chefe = None
            else:
                chefe = form.chefe.data

            if form.subs.data == 0:
                subs = None
            else:
                subs = form.chefe.data     

            unidade = Unidades(undSigla                = form.sigla.data,
                               undDescricao            = form.desc.data,
                               unidadeIdPai            = pai,
                               tipoUnidadeId           = form.tipo.data,
                               situacaoUnidadeId       = form.situ.data,
                               ufId                    = form.uf.data,
                               undNivel                = form.nivel.data,
                               tipoFuncaoUnidadeId     = form.tipoFun.data,
                               Email                   = form.email.data,
                               undCodigoSIORG          = form.siorg.data,
                               pessoaIdChefe           = chefe,
                               pessoaIdChefeSubstituto = subs)

            db.session.add(unidade)
            db.session.commit()

            registra_log_auto(current_user.id,'Unidade '+ str(unidade.unidadeId) +' '+ unidade.undSigla +' inserida no banco de dados.')

            flash(str('Unidade ' + form.sigla.data +' inserida no banco!'),'sucesso')

            return redirect(url_for('unidades.lista_unidades'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('unidades.lista_unidades'))


    return render_template('atu_unidade.html', form=form)
