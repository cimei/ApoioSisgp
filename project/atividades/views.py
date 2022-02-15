"""
.. topic:: Atividades (views)

    Atividades da institição.


.. topic:: Ações relacionadas às Atividades

    * Lista atividades: lista_atividades
    * Atualiza unidade: unidade_update
    * Acrescenta unidade: cria_unidade

"""

# views.py na pasta atividades

from flask import render_template,url_for,flash, redirect,request,Blueprint
from flask_login import current_user, login_required

from sqlalchemy import func
from sqlalchemy.sql import label
from sqlalchemy.orm import aliased
from project import db
from project.models import Unidades, Pessoas, unidade_ativ, cat_item_cat, Atividades, catdom
from project.atividades.forms import AtividadeForm, UnidForm

import locale

from project.usuarios.views import registra_log_auto

atividades = Blueprint('atividades',__name__, template_folder='templates')


## lista atividades da instituição

@atividades.route('/lista_atividades')

def lista_atividades():
    """
    +-----------------------------------------------------------------------------------------------+
    |Apresenta uma lista das atividades da instituição.                                             |
    |                                                                                               |
    |Aqui há uma gambiarra. Os valores de tempo presencial e remoto, no banco, estão como           | 
    |number(4,1), contudo eles chegam para o aplicativo sem a posição decimal definida.             | 
    |A solução foi dividir os valores por 10 no template que apresenta a lista.                     |    
    +-----------------------------------------------------------------------------------------------+
    """
# Lê tabela atividades

    unids = db.session.query(cat_item_cat.itemCatalogoId,
                             label('qtd_unids',func.count(cat_item_cat.catalogoId)))\
                       .join(Atividades, Atividades.itemCatalogoId == cat_item_cat.itemCatalogoId)\
                       .group_by(cat_item_cat.itemCatalogoId)\
                       .subquery()

    ativs = db.session.query(Atividades.itemCatalogoId,
                             Atividades.titulo,
                             catdom.descricao,
                             Atividades.permiteRemoto,
                             Atividades.tempoPresencial,
                             Atividades.tempoRemoto,
                             Atividades.complexidade,
                             Atividades.definicaoComplexidade,
                             Atividades.entregasEsperadas,
                             unids.c.qtd_unids)\
                       .join(catdom,catdom.catalogoDominioId == Atividades.calculoTempoId)\
                       .outerjoin(unids,unids.c.itemCatalogoId == Atividades.itemCatalogoId)\
                       .order_by(Atividades.titulo).all()


    quantidade = len(ativs)


    return render_template('lista_atividades.html', ativs=ativs, quantidade=quantidade)

#
### atualiza dados de uma atividade

@atividades.route("/<cod_ativ>/update", methods=['GET', 'POST'])
@login_required

def atividade_update(cod_ativ):
    """
    +----------------------------------------------------------------------------------------------+
    |Permite atualizar os dados de uma atividade                                                   |
    |                                                                                              |
    |Recebe o código da atividade como parâmetro.                                                  |
    |                                                                                              |
    |Aqui há uma gambiarra. Os valores de tempo presencial e remoto, no banco, estão como          | 
    |number(4,1), contudo eles chegam para o aplicativo sem a posição decimal definida.            | 
    |A solução foi dividir os valores por 10 ao resgatá-los para a tela de atualização.            | 
    +----------------------------------------------------------------------------------------------+
    """


    unids_lista = db.session.query(Unidades.undSigla,
                                   unidade_ativ.unidadeId,
                                   cat_item_cat.itemCatalogoId)\
                            .join(unidade_ativ, unidade_ativ.unidadeId == Unidades.unidadeId)\
                            .join(cat_item_cat, cat_item_cat.catalogoId == unidade_ativ.catalogoId)\
                            .order_by(Unidades.undSigla)\
                            .filter(cat_item_cat.itemCatalogoId == cod_ativ)\
                            .all()

    qtd_unids = len(unids_lista)                            

    calc_tempo_cat = db.session.query(catdom.catalogoDominioId, catdom.descricao)\
                               .filter(catdom.classificacao == 'FormaCalculoTempoItemCatalogo')\
                               .all()
    lista_calc_temp = [(int(c.catalogoDominioId),c.descricao) for c in calc_tempo_cat]


    ativ = Atividades.query.filter(Atividades.itemCatalogoId==cod_ativ).first_or_404()

    form = AtividadeForm()

    form.calc_temp.choices = lista_calc_temp

    if form.validate_on_submit():

        if current_user.userAtivo:

            ativ.titulo                = form.titulo.data
            ativ.calculoTempoId        = form.calc_temp.data
            ativ.permiteRemoto         = form.remoto.data
            ativ.tempoPresencial       = float(form.tempo_pres.data.replace('.','').replace(',','.'))
            ativ.tempoRemoto           = float(form.tempo_rem.data.replace('.','').replace(',','.'))
            ativ.descricao             = form.descricao.data
            ativ.complexidade          = form.complex.data
            ativ.definicaoComplexidade = form.def_complex.data
            ativ.entregasEsperadas     = form.entregas.data

            db.session.commit()

            registra_log_auto(current_user.id,'Atividade '+ str(ativ.titulo)[:12] +'... teve dados alterados.')

            flash('Atividade atualizada!','sucesso')

            return redirect(url_for('atividades.lista_atividades'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('atividades.lista_atividades'))


    # traz a informação atual da atividade

    elif request.method == 'GET':

        form.titulo.data      = ativ.titulo 
        form.calc_temp.data   = ativ.calculoTempoId
        form.remoto.data      = ativ.permiteRemoto
        form.tempo_pres.data  = locale.format_string('%.1f',ativ.tempoPresencial/10,grouping=True)
        form.tempo_rem.data   = locale.format_string('%.1f',ativ.tempoRemoto/10,grouping=True)
        form.descricao.data   = ativ.descricao   
        form.complex.data     = ativ.complexidade  
        form.def_complex.data = ativ.definicaoComplexidade
        form.entregas.data    = ativ.entregasEsperadas 

        return render_template('atu_atividade.html', form=form, unids_lista=unids_lista, 
                            qtd_unids=qtd_unids, titulo = form.titulo.data)

#
### insere nova atividade no banco de dados

@atividades.route("/cria_atividade", methods=['GET', 'POST'])
@login_required

def cria_atividade():
    """
    +----------------------------------------------------------------------------------------------+
    |Inserção de uma nova atividade no sistema.                                                    |
    |Aqui a iserção é feita com SQL, pois a chave da tabela é unique identifier, o que demanda o   |
    |NEWID() do SQL Server para um novo registro.                                                  |     
    +----------------------------------------------------------------------------------------------+
    """

    calc_tempo_cat = db.session.query(catdom.catalogoDominioId, catdom.descricao)\
                               .filter(catdom.classificacao == 'FormaCalculoTempoItemCatalogo')\
                               .all()
    lista_calc_temp = [(int(c.catalogoDominioId),c.descricao) for c in calc_tempo_cat]


    form = AtividadeForm()

    form.calc_temp.choices = lista_calc_temp

    if form.validate_on_submit():

        if current_user.userAtivo:

            if form.remoto.data:
                remoto = 1
            else:
                remoto = 0

            tabela = "[ProgramaGestao].[ItemCatalogo]"
            colunas = ["[itemCatalogoId]", "[titulo]", "[calculoTempoId]", "[permiteRemoto]",
                       "[tempoPresencial]", "[tempoRemoto]", "[descricao]", "[complexidade]",\
                       "[definicaoComplexidade]", "[entregasEsperadas]"]
            valores = ["(NEWID(), \'"+str(form.titulo.data) +"\', "+\
                             str(form.calc_temp.data) +", "+\
                             str(remoto) +", "+\
                             str(form.tempo_pres.data) +", "+\
                             str(form.tempo_rem.data) +", \'"+\
                             str(form.descricao.data) +"\', \'"+\
                             str(form.complex.data) +"\', \'"+\
                             str(form.def_complex.data) +"\', \'"+\
                             str(form.entregas.data) +"\')"]
            s_cols = ', '.join(colunas)
            s_vals = ', '.join(valores)

            ativ = db.session.execute(f"INSERT INTO {tabela} ({s_cols}) VALUES {s_vals}")                             

            db.session.commit()

            registra_log_auto(current_user.id,'Atividade '+ str(form.titulo.data)[:12] +'... inserida no banco de dados.')

            flash('Atividade inserida no banco!','sucesso')

            return redirect(url_for('atividades.lista_atividades'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('atividades.lista_atividades'))


    return render_template('atu_atividade.html', form=form)

    ### insere nova atividade no banco de dados

@atividades.route("/<cod_ativ>/associa_atividade_unidade", methods=['GET', 'POST'])
@login_required

def associa_atividade_unidade(cod_ativ):
    """
    +----------------------------------------------------------------------------------------------+
    |Associa uma atividade a uma unidade.                                                          |
    |Recebe id da atividade como parâmetro.                                                        | 
    +----------------------------------------------------------------------------------------------+
    """
    #pega o titulo da atividade
    ativ = db.session.query(Atividades.itemCatalogoId,
                            Atividades.titulo)\
                     .filter(Atividades.itemCatalogoId == cod_ativ)\
                     .first()

    #pega unidades com as quais a atividade já se relaciona
    unids_ativ = db.session.query(cat_item_cat.catalogoId,
                                  cat_item_cat.itemCatalogoId,
                                  unidade_ativ.unidadeId,
                                  Unidades.undSigla)\
                         .join(unidade_ativ, unidade_ativ.catalogoId == cat_item_cat.catalogoId)\
                         .join(Unidades, Unidades.unidadeId == unidade_ativ.unidadeId)\
                         .filter(cat_item_cat.itemCatalogoId == cod_ativ)\
                         .all()

    # opções do form.unid
    unids = db.session.query(Unidades.unidadeId, Unidades.undSigla)\
                      .order_by(Unidades.undSigla).all()
    lista_unids = [(int(u.unidadeId),u.undSigla) for u in unids]
    lista_unids.insert(0,(0,''))

    form = UnidForm()
    form.unid.choices = lista_unids


    if form.validate_on_submit():

        if current_user.userAtivo:
            # verifica relacionamento atividade unidade já existente
            ver_unid = db.session.query(cat_item_cat.catalogoId,
                                        cat_item_cat.itemCatalogoId,
                                        unidade_ativ.unidadeId)\
                         .join(unidade_ativ, unidade_ativ.catalogoId == cat_item_cat.catalogoId)\
                         .filter(cat_item_cat.itemCatalogoId == cod_ativ, unidade_ativ.unidadeId == form.unid.data)\
                         .all()

            # não existindo
            if ver_unid is None or len(ver_unid) == 0:

                # insere relacionamento na tabela Catalogo
                tab   = "[ProgramaGestao].[Catalogo]"
                cols1 = ["[catalogoId]", "[unidadeId]"]
                vals1 = ["(NEWID(), "+str(form.unid.data) +")"]
                s_cols = ', '.join(cols1)
                s_vals = ', '.join(vals1)

                ins1 = db.session.execute(f"INSERT INTO {tab} ({s_cols}) VALUES {s_vals}")

                db.session.commit()

                # pega na tabela Catalogo os relacionamentos já existes para a unidade
                rel1 = db.session.query(unidade_ativ.catalogoId).filter(unidade_ativ.unidadeId == form.unid.data).all()

                rel_criado = False
                # verifica nos relacionamentos em Catalogo o que já existe na tabela CatalogoItemCatalogo
                for i in rel1:
                    chk1 = db.session.query(cat_item_cat.itemCatalogoId).filter(cat_item_cat.catalogoId == i.catalogoId).all()

                    # o que não for achado, é porque precisa ser criado
                    if chk1 == None or len(chk1) == 0:

                        # pega então a chave catalogoId
                        pk1 = i.catalogoId
                        rel_criado = True

                        # insere relacionamento na tabela CatalogoItemCatalogo
                        tab   = "[ProgramaGestao].[CatalogoItemCatalogo]"
                        cols2 = ["[catalogoItemCatalogoId]","[catalogoId]", "[itemCatalogoId]"]
                        vals2 = ["(NEWID(), \'"+str(pk1) + "\', \'"+ str(ativ.itemCatalogoId) +"\')"]
                        s_cols = ', '.join(cols2)
                        s_vals = ', '.join(vals2)

                        ins2 = db.session.execute(f"INSERT INTO {tab} ({s_cols}) VALUES {s_vals}")

                        db.session.commit()

                        unid = db.session.query(Unidades.undSigla).filter(Unidades.unidadeId == form.unid.data).first()

                        registra_log_auto(current_user.id,'Atividade '+ str(ativ.titulo)[:12] +'... associada à unidade '+str(unid.undSigla)+'.')

                        flash('Associação Atividade-Unidade realizada!','sucesso')

                if not rel_criado:

                    flash('Esta associação já existe (catalogoId em CatalogItemCatalogo não pode ser criado)!','sucesso')

                return redirect(url_for('atividades.lista_atividades'))

            else:

                flash('Esta associação já existe!','erro')

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('atividades.lista_atividades'))


    return render_template('associa_unidade.html', form=form, atividade=ativ.titulo, unids_ativ=unids_ativ)