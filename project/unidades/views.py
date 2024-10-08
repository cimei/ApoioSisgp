"""
.. topic:: Unidades (views)

    As Unidades na estrutura da instituição.
    Este sistema restringe os tipos aos valores (1,'Instituição'),(2,'Diretoria'),(3,'Coordenação-Geral'),(4,'Coordenação'),(5,'Serviço'),(6,'Outro').
    Para situação, ou é (1,'Ativa'), ou (2,'Inativa').


.. topic:: Ações relacionadas às Unidades

    * lista_unidades: Lista unidades
    * lista_unidades_filtro: Lista unidades conforme filtro aplicado
    * unidade_update: Atualiza unidade
    * cria_unidade: Acrescenta unidade
    * lista_atividades_unidade: Atividades associadas a uma unidade
    * desassocia_ativ: Desassocia atividade de uma unidade

"""

# views.py na pasta unidades

from flask import render_template,url_for,flash, redirect,request,Blueprint
from flask_login import current_user, login_required

from sqlalchemy import func
from sqlalchemy.sql import label
from sqlalchemy.orm import aliased
from project import db
from project.models import Atividades, Unidades, Pessoas, cat_item_cat, unidade_ativ, VW_Unidades
from project.unidades.forms import UnidadeForm, PesquisaUnidForm
from project.pessoas.views import instituicao_user

from project.usuarios.views import registra_log_auto

unidades = Blueprint('unidades',__name__, template_folder='templates')


## lista unidades da instituição

@unidades.route('<lista>/lista_unidades')

def lista_unidades(lista):
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista das unidades da instituição.                                       |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """ 
    
    # Preparação para leitura de unidades

    page = request.args.get('page', 1, type=int)

    unids_pai = db.session.query(Unidades.unidadeId,Unidades.undSigla).subquery()

    dic_tipo_unidade = {1:'Instituição',2:'Diretoria',3:'Coordenação-Geral',4:'Coordenação',5:'Serviço',6:'Outro'}

    dic_situ_unidade = {1:'Ativa',2:'Inativa'}

    chefes = db.session.query(Pessoas.pessoaId,Pessoas.pesNome).filter(Pessoas.tipoFuncaoId != None, Pessoas.tipoFuncaoId != '').subquery()
    substitutos = aliased(chefes)

    # Verifica se há unidade relacionada como próprio pai
    unids_erro_pai = db.session.query(Unidades.unidadeId,
                                      Unidades.unidadeIdPai)\
                               .filter(Unidades.unidadeId == Unidades.unidadeIdPai)\
                               .all()
    
    # sobre paginação    
    pag = 500

    if lista == 'ativas':
        unids = db.session.query(VW_Unidades.unidadeId,
                                 VW_Unidades.undSigla,
                                 VW_Unidades.undDescricao,
                                 VW_Unidades.unidadeIdPai,
                                 unids_pai.c.undSigla.label("Sigla_Pai"),
                                 VW_Unidades.tipoUnidadeId,
                                 VW_Unidades.situacaoUnidadeId,
                                 VW_Unidades.ufId,
                                 VW_Unidades.undNivel,
                                 VW_Unidades.tipoFuncaoUnidadeId,
                                 VW_Unidades.Email,
                                 VW_Unidades.undCodigoSIORG,
                                 label('titular',chefes.c.pesNome),
                                 label('substituto',substitutos.c.pesNome))\
                          .join(Unidades, Unidades.unidadeId == VW_Unidades.unidadeId)\
                          .outerjoin(chefes, chefes.c.pessoaId == Unidades.pessoaIdChefe)\
                          .outerjoin(substitutos, substitutos.c.pessoaId == Unidades.pessoaIdChefeSubstituto)\
                          .outerjoin(unids_pai,unids_pai.c.unidadeId == VW_Unidades.unidadeIdPai)\
                          .filter(VW_Unidades.situacaoUnidadeId == 1,
                                  VW_Unidades.undSiglaCompleta.like(instituicao_user()))\
                          .order_by(VW_Unidades.undSigla)\
                          .paginate(page=page,per_page=pag)
        
    elif lista == 'inativas':
        unids = db.session.query(VW_Unidades.unidadeId,
                                 VW_Unidades.undSigla,
                                 VW_Unidades.undDescricao,
                                 VW_Unidades.unidadeIdPai,
                                 unids_pai.c.undSigla.label("Sigla_Pai"),
                                 VW_Unidades.tipoUnidadeId,
                                 VW_Unidades.situacaoUnidadeId,
                                 VW_Unidades.ufId,
                                 VW_Unidades.undNivel,
                                 VW_Unidades.tipoFuncaoUnidadeId,
                                 VW_Unidades.Email,
                                 VW_Unidades.undCodigoSIORG,
                                 label('titular',chefes.c.pesNome),
                                 label('substituto',substitutos.c.pesNome))\
                          .join(Unidades, Unidades.unidadeId == VW_Unidades.unidadeId)\
                          .outerjoin(chefes, chefes.c.pessoaId == Unidades.pessoaIdChefe)\
                          .outerjoin(substitutos, substitutos.c.pessoaId == Unidades.pessoaIdChefeSubstituto)\
                          .outerjoin(unids_pai,unids_pai.c.unidadeId == VW_Unidades.unidadeIdPai)\
                          .filter(VW_Unidades.situacaoUnidadeId != 1)\
                          .order_by(VW_Unidades.undSigla)\
                          .paginate(page=page,per_page=pag)

    quantidade = unids.total

    # Avisa se houver unidade pai de si mesma
    if len(unids_erro_pai) > 0:
        flash('Atenção! Exite(m) unidade(s) que está(ão) referenciada(s) como pai de si mesma(s). Isto provocará erro de acesso no SISGP!','erro')
        print('** Unidades pai de si mesmas: ', unids_erro_pai)

    # Avisa se houver referência circular em unidades e seus pais
    # unidades = db.session.query(Unidades.undSigla, Unidades.unidadeIdPai).all()

    # for item in unidades:

    #     sigla = item.undSigla
    #     pai   = item.unidadeIdPai
    #     erro_circular = 0

    #     hier = []
    #     hier.append(sigla)
    #     while pai != None:
    #         sup = Unidades.query.filter(Unidades.unidadeId==pai).first()
    #         if sup.undSigla in hier:
    #             erro_circular += 1
    #         hier.append(sup.undSigla)
    #         pai = sup.unidadeIdPai

    # if erro_circular > 0:
    #     flash('Atenção! Exite(m) '+ str(erro_circular) +' referência(s) circulares entre unidades e seus pais!','erro')        
 

    return render_template('lista_unidades.html', unids = unids, quantidade = quantidade,
                                                  instituicao_sigla = instituicao_user().split('%')[1],
                                                  dic_situ_unidade = dic_situ_unidade, 
                                                  dic_tipo_unidade = dic_tipo_unidade,
                                                  lista = lista,
                                                  unids_erro_pai = unids_erro_pai)


## lista unidades da instituição

@unidades.route('<lista>/lista_unidades_filtro', methods=['GET','POST'])

def lista_unidades_filtro(lista):
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista das unidades da instituição de acordo com filtro aplicado.         |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """ 

    page = request.args.get('page', 1, type=int)

    form = PesquisaUnidForm()
    
    unids = db.session.query(VW_Unidades.undSiglaCompleta, VW_Unidades.undSigla)\
                      .filter(VW_Unidades.situacaoUnidadeId==1,
                              VW_Unidades.undSiglaCompleta.like(instituicao_user()))\
                      .order_by(VW_Unidades.undSigla).all()
    lista_unids = [(u.undSiglaCompleta,u.undSigla) for u in unids]
    lista_unids.insert(0,('','Todas'))            

    dic_tipo_unidade = {1:'Instituição',2:'Diretoria',3:'Coordenação-Geral',4:'Coordenação',5:'Serviço',6:'Outro'}
    lista_tipo = [(t,dic_tipo_unidade[t]) for t in dic_tipo_unidade]
    lista_tipo.insert(0,(0,'Todos'))
    
    dic_situ_unidade = {1:'Ativa',2:'Inativa'}
    lista_situ = [(s,dic_situ_unidade[s]) for s in dic_situ_unidade]
    lista_situ.insert(0,(0,'Todas'))

    form.sigla.choices = lista_unids
    form.tipo.choices  = lista_tipo

    if form.validate_on_submit():

        if form.sigla.data == '':
            p_sigla_pattern = instituicao_user()
        else:
            p_sigla_pattern = '%'+form.sigla.data+'%'

        if int(form.tipo.data) == 0:
            p_tipo_pattern = '%'
        else:
            p_tipo_pattern = form.tipo.data    

        # pega valores utilizados como filtro para exibição na tela da lista
        p_sigla = dict(form.sigla.choices).get(form.sigla.data)
        p_tipo  = dict(form.tipo.choices).get(int(form.tipo.data))
    
        # Lê tabela unidades

        unids_pai = db.session.query(Unidades.unidadeId,Unidades.undSigla).subquery()

        chefes = db.session.query(Pessoas.pessoaId,Pessoas.pesNome).filter(Pessoas.tipoFuncaoId != None, Pessoas.tipoFuncaoId != '').subquery()
        substitutos = aliased(chefes)

        unids = db.session.query(VW_Unidades.unidadeId,
                                 VW_Unidades.undSigla,
                                 VW_Unidades.undDescricao,
                                 VW_Unidades.unidadeIdPai,
                                 unids_pai.c.undSigla.label("Sigla_Pai"),
                                 VW_Unidades.tipoUnidadeId,
                                 VW_Unidades.situacaoUnidadeId,
                                 VW_Unidades.ufId,
                                 VW_Unidades.undNivel,
                                 VW_Unidades.tipoFuncaoUnidadeId,
                                 VW_Unidades.Email,
                                 VW_Unidades.undCodigoSIORG,
                                label('titular',chefes.c.pesNome),
                                label('substituto',substitutos.c.pesNome))\
                            .join(Unidades, Unidades.unidadeId == VW_Unidades.unidadeId)\
                            .outerjoin(chefes, chefes.c.pessoaId == Unidades.pessoaIdChefe)\
                            .outerjoin(substitutos, substitutos.c.pessoaId == Unidades.pessoaIdChefeSubstituto)\
                            .outerjoin(unids_pai,unids_pai.c.unidadeId == VW_Unidades.unidadeIdPai)\
                            .filter(VW_Unidades.undSiglaCompleta.like(p_sigla_pattern),
                                    VW_Unidades.undDescricao.like('%'+form.desc.data+'%'),
                                    VW_Unidades.tipoUnidadeId.like(p_tipo_pattern),
                                    VW_Unidades.ufId.like('%'+form.uf.data+'%'))\
                            .order_by(VW_Unidades.undSigla)\
                            .paginate(page=page,per_page=500)

        quantidade = unids.total

        return render_template('lista_unidades.html', unids = unids, quantidade = quantidade,
                                                    dic_situ_unidade = dic_situ_unidade, 
                                                    dic_tipo_unidade = dic_tipo_unidade,
                                                    lista = lista,
                                                    p_sigla = p_sigla,
                                                    p_tipo = p_tipo,
                                                    p_nome = form.desc.data,
                                                    p_uf = form.uf.data)

    return render_template('pesquisa_unidades.html', form = form)

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
                     .filter(Unidades.situacaoUnidadeId == 1,
                             Unidades.unidadeId != int(cod_unid))\
                     .order_by(Unidades.undSigla).all()
    lista_pais = [(int(p.unidadeId),p.undSigla) for p in pais]
    lista_pais.insert(0,(0,''))

    chefes = db.session.query(Pessoas.pessoaId, Pessoas.pesNome)\
                       .filter(Pessoas.tipoFuncaoId != None)\
                       .order_by(Pessoas.pesNome).all()
    lista_chefes = [(int(c.pessoaId),c.pesNome) for c in chefes]
    lista_chefes.insert(0,(0,''))

    lista_tipo_unidade = [(1,'Instituição'),(2,'Diretoria'),(3,'Coordenação-Geral'),(4,'Coordenação'),(5,'Serviço'),(6,'Outro')]

    lista_situ_unidade = [(1,'Ativa'),(2,'Inativa')]

    unidade = Unidades.query.filter(Unidades.unidadeId==cod_unid).first_or_404()
    
    unidade_view = db.session.query(VW_Unidades.undSiglaCompleta).filter(VW_Unidades.unidadeId==unidade.unidadeId).first()
    if unidade_view == None:
        sigla_completa = 'Não encontrada'
    else:
        sigla_completa = unidade_view.undSiglaCompleta

    form = UnidadeForm()

    form.pai.choices = lista_pais
    form.chefe.choices = lista_chefes
    form.subs.choices = lista_chefes
    form.tipo.choices = lista_tipo_unidade
    form.situ.choices = lista_situ_unidade


    if form.validate_on_submit():

        if current_user.userAtivo:

            # conferir se unidade está sendo colocada como pai dela mesma
            if form.pai.data == unidade.unidadeId:
                flash('Unidade não pode ser pai de si mesma, alteração não realizada!','erro')
                return redirect(url_for('unidades.lista_unidades',lista='ativas'))

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

            return redirect(url_for('unidades.lista_unidades',lista='ativas'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('unidades.lista_unidades',lista='ativas'))


    # traz a informação atual da Unidade

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

        # quantidade de atividade da unidade
        ativs = db.session.query(unidade_ativ.unidadeId,
                                 label('qtd_ativs',func.count(unidade_ativ.catalogoId)))\
                          .join(cat_item_cat, cat_item_cat.catalogoId == unidade_ativ.catalogoId)\
                          .join(Atividades, Atividades.itemCatalogoId == cat_item_cat.itemCatalogoId)\
                          .group_by(unidade_ativ.unidadeId)\
                          .filter(unidade_ativ.unidadeId == cod_unid)\
                          .first()

        if ativs:
            qtd_ativs = ativs.qtd_ativs
        else:
            qtd_ativs = 0                  
        
        # quantide de pessoas na unidade
        qtd_pes = db.session.query(Pessoas)\
                                 .filter(Pessoas.unidadeId == cod_unid)\
                                 .count()
                                 
        # quantidade de pessoas sob as unidades da unidade e sob ela mesma
        qtd_geral = {}
        tree = {}
        total_pessoas = 0
        pai = [unidade.unidadeId]
        und_sigla = unidade.undSigla.replace('/','$')
        tree[unidade.undSigla] = [und_sigla]

        while pai != []:

            prox_pai = []

            for p in pai:

                filhos = Unidades.query.filter(Unidades.unidadeIdPai==p, Unidades.situacaoUnidadeId == 1).all()

                for unid in filhos:

                    if unid.unidadeId == p:
                        prox_pai = []
                    else:
                        prox_pai.append(unid.unidadeId)

                        pessoas = db.session.query(Pessoas.unidadeId,
                                                    label('qtd_pes',func.count(Pessoas.unidadeId)))\
                                        .group_by(Pessoas.unidadeId)\
                                        .filter(Pessoas.unidadeId == unid.unidadeId)\
                                        .first()

                        if pessoas is not None:
                            total_pessoas += pessoas.qtd_pes

                        tree[unidade.undSigla].append(unid.undSigla.replace('/','$'))    

            pai =  prox_pai

        qtd_geral[unidade.undSigla] = total_pessoas + qtd_pes
                             
        return render_template('atu_unidade.html', form = form,
                                                   id = cod_unid,
                                                   qtd_ativs = qtd_ativs,
                                                   qtd_pes = qtd_pes,
                                                   sigla = unidade.undSigla,
                                                   sigla_completa = sigla_completa,
                                                   qtd_geral = qtd_geral,
                                                   tree = tree)

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
                         .filter(Unidades.situacaoUnidadeId == 1)\
                         .order_by(Unidades.undSigla).all()
    lista_pais = [(int(p.unidadeId),p.undSigla) for p in pais]
    lista_pais.insert(0,(0,''))

    chefes = db.session.query(Pessoas.pessoaId, Pessoas.pesNome)\
                         .filter(Pessoas.tipoFuncaoId != None)\
                         .order_by(Pessoas.pesNome).all()
    lista_chefes = [(int(c.pessoaId),c.pesNome) for c in chefes]
    lista_chefes.insert(0,(0,''))

    lista_tipo_unidade = [(1,'Instituição'),(2,'Diretoria'),(3,'Coordenação-Geral'),(4,'Coordenação'),(5,'Serviço'),(6,'Outro')]

    lista_situ_unidade = [(1,'Ativa'),(2,'Inativa')]

    form = UnidadeForm()

    form.pai.choices = lista_pais
    form.chefe.choices = lista_chefes
    form.subs.choices = lista_chefes
    form.tipo.choices = lista_tipo_unidade
    form.situ.choices = lista_situ_unidade


    if form.validate_on_submit():

        if current_user.userAtivo:

            # conferir sigla da unidade com a que está sendo colocada como pai
            verifica_pai = dict(form.pai.choices).get(int(form.pai.data))
            if verifica_pai == form.sigla.data:
                flash('Unidade não pode ser pai de si mesma!','erro')
                return render_template('atu_unidade.html', form=form,
                                               id = None,
                                               sigla = None)

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

            return redirect(url_for('unidades.lista_unidades',lista='ativas'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('unidades.lista_unidades',lista='ativas'))


    return render_template('atu_unidade.html', form=form,
                                               id = None,
                                               sigla = None)


## lista atividades de uma unidade

@unidades.route('/<int:unid_id>/lista_atividades_unidade')

def lista_atividades_unidade(unid_id):
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista das atividades de uma unidade.                                     |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """   

    unid = db.session.query(Unidades.unidadeId, Unidades.undSigla).filter(Unidades.unidadeId == unid_id).first() 

    ativs_lista = db.session.query(Atividades.titulo,
                                   Atividades.itemCatalogoId, 
                                   cat_item_cat.catalogoId,
                                   unidade_ativ.unidadeId)\
                            .join(cat_item_cat, cat_item_cat.itemCatalogoId == Atividades.itemCatalogoId)\
                            .join(unidade_ativ, unidade_ativ.catalogoId == cat_item_cat.catalogoId)\
                            .filter(unidade_ativ.unidadeId == unid_id)\
                            .order_by(Atividades.titulo)\
                            .all() 


    quantidade = len(ativs_lista)

    return render_template('lista_atividades_unidade.html', unid=unid, quantidade = quantidade,
                                                ativs_lista = ativs_lista)


## desassocia atividade de uma unidade

@unidades.route('/<item_cat_id>/<cat_id>/<int:unid_id>/desassocia_ativ', methods=['GET', 'POST'])
@login_required

def desassocia_ativ(item_cat_id,cat_id,unid_id):
    """
    +---------------------------------------------------------------------------------------+
    |Desassocia atividades de uma unidade.                                                  |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    unid = db.session.query(Unidades.undSigla).filter(Unidades.unidadeId == unid_id).first() 

    #deleta registro na tabela Catalogo_Item_Catalogo

    db.session.query(cat_item_cat)\
              .filter(cat_item_cat.catalogoId == cat_id, cat_item_cat.itemCatalogoId == item_cat_id)\
              .delete()

    db.session.commit()


    registra_log_auto(current_user.id,'Uma atividade foi desassociada da unidade ' + unid.undSigla + '.')

    flash('Uma atividade foi desassociada com sucesso.','sucesso')

    return redirect(url_for('unidades.lista_atividades_unidade',unid_id=unid_id)) 