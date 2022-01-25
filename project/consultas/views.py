"""
.. topic:: Consultas (views)

    As consultas trazem informações úteis para a gestão do SISGP.


.. topic:: Ações relacionadas às pessoas

    * Lista quantidades de pessoas em programas de gestão por unidade: pessoas_qtd_pg_unidade
    * Lista o Catálogo de Domínios: catalogo_dominio 


"""

# views.py na pasta consultas

from flask import render_template,url_for,flash, redirect,request,Blueprint
from sqlalchemy.sql import label
from sqlalchemy import func, distinct
from sqlalchemy.orm import aliased
from project import db
from project.models import Pactos_de_Trabalho, Pessoas, Unidades, Planos_de_Trabalho, catdom

import locale
import datetime
from datetime import date

consultas = Blueprint('consultas',__name__, template_folder='templates')


## lista quatidade de pessoas no plano de gestão por unidade 

@consultas.route('/pessoas_qtd_pg_unidade')
def pessoas_qtd_pg_unidade():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista com as quatidades de pessoas no plano de gestão por unidade.       |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    hoje = date.today()

    qtd_unidades = Unidades.query.count()

    qtd_pessoas = Pessoas.query.count()

    planos = db.session.query(Planos_de_Trabalho.unidadeId,
                              Planos_de_Trabalho.totalServidoresSetor,  
                              label('qtd_pg',func.count(Planos_de_Trabalho.unidadeId)))\
                       .group_by(Planos_de_Trabalho.unidadeId,Planos_de_Trabalho.totalServidoresSetor)\
                       .subquery()

    pactos = db.session.query(Pactos_de_Trabalho.unidadeId,
                              label('qtd_pactos',func.count(Pactos_de_Trabalho.unidadeId)))\
                       .filter(Pactos_de_Trabalho.dataFim > hoje, Pactos_de_Trabalho.situacaoId == 405)\
                       .group_by(Pactos_de_Trabalho.unidadeId)\
                       .subquery()                 

    pt = db.session.query(Unidades.unidadeId,
                          Unidades.undSigla,
                          Unidades.undDescricao,
                          planos.c.qtd_pg,
                          planos.c.totalServidoresSetor,
                          pactos.c.qtd_pactos)\
                   .join(planos, planos.c.unidadeId == Unidades.unidadeId)\
                   .outerjoin(pactos, pactos.c.unidadeId == Unidades.unidadeId)\
                   .order_by(Unidades.undDescricao)\
                   .all()

    qtd_pt_unidade = len(pt)

    qtd_pactos_unidade = Pactos_de_Trabalho.query.filter(Pactos_de_Trabalho.dataFim > hoje,
                                                         Pactos_de_Trabalho.situacaoId == 405).count()

## buscando detalhes dos programas de gestão das unidades e das pessoas com pacto vigente

    dados_pt = db.session.query(Planos_de_Trabalho.planoTrabalhoId,
                                Planos_de_Trabalho.unidadeId,
                                Planos_de_Trabalho.dataInicio,
                                Planos_de_Trabalho.dataFim,
                                catdom.descricao)\
                          .join(catdom, Planos_de_Trabalho.situacaoId == catdom.catalogoDominioId)\
                          .all() 

    dados_pessoa_pacto = db.session.query(Pactos_de_Trabalho.pessoaId,
                                          Pessoas.pesNome,
                                          Pactos_de_Trabalho.unidadeId,
                                          Pactos_de_Trabalho.dataInicio,
                                          Pactos_de_Trabalho.dataFim)\
                                   .join(Pessoas, Pessoas.pessoaId == Pactos_de_Trabalho.pessoaId)\
                                   .all()                                          


    return render_template('lista_pessoas_qtd_pg_unidade.html', qtd_unidades=qtd_unidades, pt=pt,
                           qtd_pessoas = qtd_pessoas, qtd_pt_unidade = qtd_pt_unidade,
                           qtd_pactos_unidade = qtd_pactos_unidade,
                           dados_pt = dados_pt, dados_pessoa_pacto = dados_pessoa_pacto)

#

## lista Catálogo de Domínio

@consultas.route('/catalogo_dominio')
def catalogo_dominio():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista do catálogo de dominio, que consiste das várias situações,         |
    |tipos, critérios etc que são utilizados pelo SISGP.                                    |
    +---------------------------------------------------------------------------------------+
    """

    cat = db.session.query(catdom).all()

    qtd_itens = len(cat)

    return render_template('lista_catalogo_dominio.html', qtd_itens = qtd_itens, cat = cat)