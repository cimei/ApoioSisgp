"""
.. topic:: Consultas (views)

    As consultas trazem informações úteis para a gestão do SISGP.

.. topic:: Funções

    * allowed_file: atesta se nome de arquivo tem . e restringe seu tipo (sem uso)

.. topic:: Ações relacionadas às pessoas

    * pessoas_qtd_pg_unidade: Lista quantidades de pessoas em programas de gestão por unidade
    * catalogo_dominio: Lista o Catálogo de Domínios 
    * pactos: Dados de planos de trabalho
    * pactos_irregulares: Planos cuja situação não é adequada à vigência
    * pacto_atividades: Atividades de um plano
    * deleta_pg: Permite remover PGs em rascunho
    * relatorioPG: Relatório de PGs no formato xlsx
    * hierarquia: Relatório da estrutura hierárquica da instituição no formato xlsx
    * lista_ativs_planos: Lista das atividades em planos por situação
    * estatisticas: Alguns números
    * periodo: Quantidades de PGs e PTs em um perídodo informado
    * candidatos_sem_plano: Pessoas com candidatura aprovada, ma sem plano
    * consultas_i: Auxiliar para o menu em cascata de Consultas

"""

# views.py na pasta consultas

from flask import render_template,url_for,flash, redirect, request, Blueprint, send_from_directory
from flask_login import current_user, login_required

from sqlalchemy.sql import label, literal
from sqlalchemy import and_, func, distinct, or_
from sqlalchemy.orm import aliased

from project import db
from project.models import Pactos_de_Trabalho, Pessoas, Unidades, Planos_de_Trabalho, catdom,\
                           Pactos_de_Trabalho_Atividades, Atividades, Planos_de_Trabalho_Ativs,\
                           Planos_de_Trabalho_Hist, Planos_de_Trabalho_Ativs_Items, Pactos_de_Trabalho_Solic,\
                           VW_Unidades, Atividade_Candidato, VW_Pactos,VW_Unidades_Ativas
from project.usuarios.views import registra_log_auto                           

from project.consultas.forms import PeriodoForm

from werkzeug.utils import secure_filename

import requests
from datetime import datetime, date, timedelta, time
import os.path
import xlsxwriter

consultas = Blueprint('consultas',__name__, template_folder='templates')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['xlsx']

## lista quatidade de pessoas no plano de gestão por unidade 

@consultas.route('/pessoas_qtd_pg_unidade')
def pessoas_qtd_pg_unidade():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista com as quatidades de pessoas no plano de gestão por unidade.       |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    qtd_unidades = Unidades.query.count()

    qtd_pessoas = Pessoas.query.count()

    planos = db.session.query(Planos_de_Trabalho.unidadeId,
                              label('qtd_pg',func.count(Planos_de_Trabalho.unidadeId)))\
                       .group_by(Planos_de_Trabalho.unidadeId)\
                       .subquery()

    pactos = db.session.query(Pactos_de_Trabalho.unidadeId,
                              label('qtd_pactos',func.count(Pactos_de_Trabalho.unidadeId)))\
                       .filter(Pactos_de_Trabalho.situacaoId == 405)\
                       .group_by(Pactos_de_Trabalho.unidadeId)\
                       .subquery()

    pessoas_unid = db.session.query(Pessoas.unidadeId,
                                    label('qtd_pes',func.count(Pessoas.unidadeId)))\
                             .group_by(Pessoas.unidadeId)\
                             .subquery()    

    pt = db.session.query(Unidades.unidadeId,
                          Unidades.unidadeIdPai,
                          Unidades.undSigla,
                          Unidades.undDescricao,
                          planos.c.qtd_pg,
                          pactos.c.qtd_pactos,
                          pessoas_unid.c.qtd_pes)\
                   .join(planos, planos.c.unidadeId == Unidades.unidadeId)\
                   .outerjoin(pactos, pactos.c.unidadeId == Unidades.unidadeId)\
                   .outerjoin(pessoas_unid, pessoas_unid.c.unidadeId == Unidades.unidadeId)\
                   .order_by(Unidades.unidadeId)\
                   .all()

    qtd_pt_unidade = len(pt)

    qtd_pactos_unidade = Pactos_de_Trabalho.query.filter(Pactos_de_Trabalho.situacaoId == 405).count()

    ## buscando detalhes dos programas de gestão das unidades e das pessoas com pacto vigente

    dados_pt = db.session.query(Planos_de_Trabalho.planoTrabalhoId,
                                Planos_de_Trabalho.unidadeId,
                                Planos_de_Trabalho.dataInicio,
                                Planos_de_Trabalho.dataFim,
                                catdom.descricao,
                                Planos_de_Trabalho.totalServidoresSetor)\
                          .join(catdom, Planos_de_Trabalho.situacaoId == catdom.catalogoDominioId)\
                          .all() 

    dados_pessoa_pacto = db.session.query(Pactos_de_Trabalho.pessoaId,
                                          Pessoas.pesNome,
                                          Pactos_de_Trabalho.unidadeId,
                                          Pactos_de_Trabalho.dataInicio,
                                          Pactos_de_Trabalho.dataFim)\
                                   .join(Pessoas, Pessoas.pessoaId == Pactos_de_Trabalho.pessoaId)\
                                   .filter(Pactos_de_Trabalho.situacaoId == 405)\
                                   .all()                                          

    # montando estrutura hierárquica de cada unidade com pg
    tree = {}

    for item in pt:
        sigla = item.undSigla
        pai = item.unidadeIdPai
        while pai != None:
            sup = Unidades.query.filter(Unidades.unidadeId==pai).first()
            sigla = sup.undSigla + '/' + sigla
            pai = sup.unidadeIdPai
        tree[item.unidadeId]=sigla

    return render_template('lista_pessoas_qtd_pg_unidade.html', qtd_unidades=qtd_unidades, pt=pt,
                           qtd_pessoas = qtd_pessoas, qtd_pt_unidade = qtd_pt_unidade,
                           qtd_pactos_unidade = qtd_pactos_unidade,
                           dados_pt = dados_pt, dados_pessoa_pacto = dados_pessoa_pacto, tree=tree)

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

## dados dos pactos de trabalho

@consultas.route('/pactos')
def pactos():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos planos de trabalho e dados relevantes.                         |
    +---------------------------------------------------------------------------------------+
    """

    page = request.args.get('page', 1, type=int)

    tipo = 'todos'

    situacao = db.session.query(catdom.catalogoDominioId,
                                catdom.descricao)\
                         .filter(catdom.classificacao == 'SituacaoPactoTrabalho')\
                         .subquery()

    pactos_trabalho = db.session.query(Pactos_de_Trabalho.pactoTrabalhoId,
                                       Pactos_de_Trabalho.unidadeId,
                                       Pactos_de_Trabalho.pessoaId,
                                       Pactos_de_Trabalho.dataInicio,
                                       Pactos_de_Trabalho.dataFim,
                                       Pactos_de_Trabalho.formaExecucaoId,
                                       Pactos_de_Trabalho.situacaoId,
                                       Pactos_de_Trabalho.percentualExecucao,
                                       Pactos_de_Trabalho.relacaoPrevistoRealizado,
                                       Pactos_de_Trabalho.avaliacaoId,
                                       VW_Unidades.undSiglaCompleta,
                                       Unidades.situacaoUnidadeId,
                                       Pessoas.pesNome,
                                       label('descricao1',catdom.descricao),
                                       label('descricao2',situacao.c.descricao))\
                                 .join(Unidades, Unidades.unidadeId == Pactos_de_Trabalho.unidadeId)\
                                 .join(VW_Unidades, VW_Unidades.unidadeId == Pactos_de_Trabalho.unidadeId)\
                                 .join(Pessoas, Pessoas.pessoaId == Pactos_de_Trabalho.pessoaId)\
                                 .join(catdom, catdom.catalogoDominioId == Pactos_de_Trabalho.formaExecucaoId)\
                                 .join(situacao, situacao.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                 .filter(Unidades.situacaoUnidadeId == 1)\
                                 .order_by(Pessoas.pesNome)\
                                 .paginate(page=page,per_page=1000)

    qtd_itens = pactos_trabalho.total

    return render_template('lista_pactos.html', qtd_itens = qtd_itens, pactos_trabalho = pactos_trabalho, tipo = tipo)    


## dados dos pactos de trabalho

@consultas.route('/pactos_executados')
def pactos_executados():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos planos de trabalho executados.                                 |
    +---------------------------------------------------------------------------------------+
    """

    page = request.args.get('page', 1, type=int)

    tipo = 'executados'

    avaliados = db.session.query(VW_Pactos.id_pacto).all()

    avaliados_l = [a.id_pacto for a in avaliados]

    pactos_trabalho = db.session.query(Pactos_de_Trabalho.pactoTrabalhoId,
                                       Pactos_de_Trabalho.unidadeId,
                                       Pactos_de_Trabalho.pessoaId,
                                       Pactos_de_Trabalho.dataInicio,
                                       Pactos_de_Trabalho.dataFim,
                                       Pactos_de_Trabalho.formaExecucaoId,
                                       VW_Unidades_Ativas.undSiglaCompleta,
                                       Pessoas.pesNome,
                                       label('descricao1',catdom.descricao),
                                       literal(None).label('qtd_hom'))\
                                 .join(VW_Unidades_Ativas, VW_Unidades_Ativas.id_unidade == Pactos_de_Trabalho.unidadeId)\
                                 .join(Pessoas, Pessoas.pessoaId == Pactos_de_Trabalho.pessoaId)\
                                 .join(catdom, catdom.catalogoDominioId == Pactos_de_Trabalho.formaExecucaoId)\
                                 .filter(Pactos_de_Trabalho.situacaoId == 406, Pactos_de_Trabalho.pactoTrabalhoId.not_in(avaliados_l))\
                                 .order_by(Pessoas.pesNome)\
                                 .paginate(page=page,per_page=1000)


    qtd_itens = pactos_trabalho.total

    return render_template('lista_pactos.html', qtd_itens = qtd_itens, pactos_trabalho = pactos_trabalho, tipo = tipo) 

## pactos em situação irregular

@consultas.route('/pactos_irregulares')
def pactos_irregulares():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos pactos de trabalho em situação irregular.                      |
    +---------------------------------------------------------------------------------------+
    """

    page = request.args.get('page', 1, type=int)

    tipo = 'irregulares'

    hoje = date.today()

    # subquery das situações de pacto de trabalho
    catdom_1 = aliased(catdom)

    pactos_irregulares = db.session.query(Pactos_de_Trabalho.pactoTrabalhoId,
                                       Pactos_de_Trabalho.unidadeId,
                                       Pactos_de_Trabalho.pessoaId,
                                       Pactos_de_Trabalho.dataInicio,
                                       Pactos_de_Trabalho.dataFim,
                                       Pactos_de_Trabalho.formaExecucaoId,
                                       Pactos_de_Trabalho.situacaoId,
                                       Pactos_de_Trabalho.percentualExecucao,
                                       Pactos_de_Trabalho.relacaoPrevistoRealizado,
                                       Pactos_de_Trabalho.avaliacaoId,
                                       VW_Unidades.undSiglaCompleta,
                                       Unidades.situacaoUnidadeId,
                                       Pessoas.pesNome,
                                       label('descricao1',catdom.descricao),
                                       label('descricao2',catdom_1.descricao))\
                                 .join(Unidades, Unidades.unidadeId == Pactos_de_Trabalho.unidadeId)\
                                 .join(VW_Unidades, VW_Unidades.unidadeId == Pactos_de_Trabalho.unidadeId)\
                                 .join(Pessoas, Pessoas.pessoaId == Pactos_de_Trabalho.pessoaId)\
                                 .join(catdom, catdom.catalogoDominioId == Pactos_de_Trabalho.formaExecucaoId)\
                                 .join(catdom_1, catdom_1.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                 .filter(Pactos_de_Trabalho.dataFim < hoje,
                                         Pactos_de_Trabalho.situacaoId != 404,
                                         Pactos_de_Trabalho.situacaoId != 406,
                                         Pactos_de_Trabalho.situacaoId != 407,
                                         Unidades.situacaoUnidadeId == 1)\
                                 .order_by(Pessoas.pesNome)\
                                 .paginate(page=page,per_page=1000)

    qtd_itens = pactos_irregulares.total

    return render_template('lista_pactos.html', qtd_itens = qtd_itens, pactos_trabalho = pactos_irregulares, tipo = tipo)                                 


## lista atividades de um pacto de trabalho

@consultas.route('/<pactoId>/<nome>/pacto_atividades')
def pacto_atividades(pactoId,nome):
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista de dados básicos das atividades relacionadas a um pacto de trabaho.|
    +---------------------------------------------------------------------------------------+
    """

    pacto_ativ = db.session.query(Pactos_de_Trabalho_Atividades.pactoTrabalhoAtividadeId,
                                  Pactos_de_Trabalho_Atividades.pactoTrabalhoId,
                                  Pactos_de_Trabalho_Atividades.itemCatalogoId,
                                  Pactos_de_Trabalho_Atividades.quantidade,
                                  Pactos_de_Trabalho_Atividades.tempoPrevistoPorItem,
                                  Pactos_de_Trabalho_Atividades.tempoPrevistoTotal,
                                  Pactos_de_Trabalho_Atividades.dataInicio,
                                  Pactos_de_Trabalho_Atividades.dataFim,
                                  Pactos_de_Trabalho_Atividades.tempoRealizado,
                                  Pactos_de_Trabalho_Atividades.situacaoId,
                                  Pactos_de_Trabalho_Atividades.tempoHomologado,
                                  Pactos_de_Trabalho_Atividades.nota,
                                  Atividades.titulo,
                                  catdom.descricao)\
                           .join(Atividades, Atividades.itemCatalogoId == Pactos_de_Trabalho_Atividades.itemCatalogoId)\
                           .join(catdom, catdom.catalogoDominioId == Pactos_de_Trabalho_Atividades.situacaoId)\
                           .filter(Pactos_de_Trabalho_Atividades.pactoTrabalhoId == pactoId)\
                           .order_by(Atividades.titulo,Pactos_de_Trabalho_Atividades.situacaoId)\
                           .all()

    qtd_itens = len(pacto_ativ)

    pacto_ativ_unic = db.session.query(distinct(Pactos_de_Trabalho_Atividades.itemCatalogoId))\
                                .filter(Pactos_de_Trabalho_Atividades.pactoTrabalhoId == pactoId)\
                                .group_by(Pactos_de_Trabalho_Atividades,Pactos_de_Trabalho_Atividades.itemCatalogoId)\
                                .count()


    return render_template('lista_pacto_atividades.html', qtd_itens = qtd_itens, pacto_ativ = pacto_ativ,
                                                          nome=nome,pacto_ativ_unic = pacto_ativ_unic)


## deletar programa de gestão (plano de tragalho e relacionamentos) em rascunho

@consultas.route('/<pgId>/deleta_pg', methods=['GET', 'POST'])
@login_required

def deleta_pg(pgId):
    """
    +---------------------------------------------------------------------------------------+
    |Deleta um PG que esteja em rascunho e suas relaçõe próximas:  PlanoTrabalhoAtividade,  |
    |planoTrabalhoHistorico e PlanoTrabalhoAtividadeItem.                                   |
    +---------------------------------------------------------------------------------------+
    """  

    pg_sit = db.session.query(Planos_de_Trabalho.situacaoId,
                              Planos_de_Trabalho.unidadeId)\
                       .filter(Planos_de_Trabalho.planoTrabalhoId == pgId)\
                       .first()

    if pg_sit.situacaoId == 301:

        #deleta histórico

        try:
            db.session.query(Planos_de_Trabalho_Hist).filter(Planos_de_Trabalho_Hist.planoTrabalhoId == pgId).delete()
            db.session.commit()
        except: 
            print("Não foi possível excluir registro do histórico de planos de trabalho!")    

        #deleta items de atividades do pg

        ativs = db.session.query(Planos_de_Trabalho_Ativs.planoTrabalhoAtividadeId)\
                        .filter(Planos_de_Trabalho_Ativs.planoTrabalhoId == pgId)\
                        .all()

        for ativ in ativs:

            db.session.query(Planos_de_Trabalho_Ativs_Items).filter(Planos_de_Trabalho_Ativs_Items.planoTrabalhoAtividadeId == ativ.planoTrabalhoAtividadeId).delete()
            db.session.commit()

        #deleta atividades do pg

        db.session.query(Planos_de_Trabalho_Ativs).filter(Planos_de_Trabalho_Ativs.planoTrabalhoId == pgId).delete()
        db.session.commit()

        #deleta pg

        db.session.query(Planos_de_Trabalho).filter(Planos_de_Trabalho.planoTrabalhoId == pgId).delete()
        db.session.commit()

        registra_log_auto(current_user.id,'Um Programa de Gestão da unidade '+ str(pg_sit.unidadeId) +' foi deletado.')

        flash('Um Programa de Gestão da unidade '+ str(pg_sit.unidadeId) +' foi deletado.','sucesso')

    else:

        flash('PG escolhido não está como rascunho!','erro')

    return redirect(url_for('consultas.pessoas_qtd_pg_unidade'))

## gera xlsx com dados dos plano de gestão nas unidades 

@consultas.route('/relatorioPG', methods = ['GET', 'POST'])
@login_required

def relatorioPG():
    """
    +---------------------------------------------------------------------------------------+
    |Monta um relatório (planilha xlsx) com dados dos planos de gestão nas unidades.        |
    +---------------------------------------------------------------------------------------+
    """

    hoje = date.today()

    catdom_2 = aliased(catdom)

    dados_pt = db.session.query(Planos_de_Trabalho.planoTrabalhoId,
                                Planos_de_Trabalho.unidadeId,
                                Planos_de_Trabalho.totalServidoresSetor,
                                Planos_de_Trabalho.dataInicio,
                                Planos_de_Trabalho.dataFim,
                                catdom.descricao)\
                         .join(catdom, Planos_de_Trabalho.situacaoId == catdom.catalogoDominioId)\
                         .subquery()                  
                    
    pactos = db.session.query(Pactos_de_Trabalho.planoTrabalhoId,
                              Pactos_de_Trabalho.pessoaId,
                              Pessoas.pesNome,
                              Pactos_de_Trabalho.unidadeId,
                              label('pactoIni',Pactos_de_Trabalho.dataInicio),
                              label('pactoFim',Pactos_de_Trabalho.dataFim),
                              label('pactoDesc',catdom.descricao),
                              label('formaExec',catdom_2.descricao))\
                       .join(Pessoas, Pessoas.pessoaId == Pactos_de_Trabalho.pessoaId)\
                       .join(catdom, Pactos_de_Trabalho.situacaoId == catdom.catalogoDominioId)\
                       .join(catdom_2, Pactos_de_Trabalho.formaExecucaoId == catdom_2.catalogoDominioId)\
                       .subquery()

    pt = db.session.query(VW_Unidades.unidadeId,
                          VW_Unidades.undSiglaCompleta,
                          VW_Unidades.undDescricao,
                          dados_pt.c.totalServidoresSetor,
                          dados_pt.c.dataInicio,
                          dados_pt.c.dataFim,
                          dados_pt.c.descricao,
                          pactos.c.pesNome,
                          pactos.c.pactoIni,
                          pactos.c.pactoFim,
                          pactos.c.pactoDesc,
                          pactos.c.formaExec)\
                   .join(dados_pt, dados_pt.c.unidadeId == VW_Unidades.unidadeId)\
                   .outerjoin(pactos, pactos.c.planoTrabalhoId == dados_pt.c.planoTrabalhoId)\
                   .filter(VW_Unidades.situacaoUnidadeId == 1)\
                   .order_by(VW_Unidades.unidadeId)\
                   .all()

    # Criando o workbook e adicionando a worksheet.

    pasta_rel = os.path.normpath('/app/project/static/Rel_PG.xlsx')

    workbook = xlsxwriter.Workbook(pasta_rel)
    worksheet = workbook.add_worksheet('Lista')

    bold = workbook.add_format({'bold': True})

    worksheet.write('A1', 'Dados de:', bold)
    worksheet.write('B1', hoje.strftime('%x'), bold)

    # Começando da primeira célula. Linhas e colunas são "zero indexed".
    row = 3
    col = 0

    # A view VW_Unidades traz a hierarquia da unidade, o que dispensa a consulta comentada acima
    col_cab = col

    worksheet.write(row-1, col_cab+1, 'Programas de Gestão', bold)
    worksheet.write(row-1, col_cab + 5, 'Planos de Trabalho', bold)

    worksheet.write(row, col, 'Sigla Completa', bold)
    worksheet.write(row, col_cab + 1, 'Nome', bold)
    worksheet.write(row, col_cab + 2, 'Pessoas', bold)
    worksheet.write(row, col_cab + 3, 'Início PG', bold)
    worksheet.write(row, col_cab + 4, 'Fim PG', bold)
    worksheet.write(row, col_cab + 5, 'Situação PG', bold)
    worksheet.write(row, col_cab + 6, 'Pessoa', bold)
    worksheet.write(row, col_cab + 7, 'Início Plano', bold)
    worksheet.write(row, col_cab + 8, 'Fim Plano', bold)
    worksheet.write(row, col_cab + 9, 'Situação Plano', bold)
    worksheet.write(row, col_cab + 10, 'Forma Execução', bold)

    row = 4

    for item in pt:

        # preenche demais colunas de detalhe, sem a necessidade de montar a hierarquia (código comentado acima)
        col_det = col

        worksheet.write(row, col_det, item.undSiglaCompleta)

        worksheet.write(row, col_det + 1, item.undDescricao)

        worksheet.write(row, col_det + 2, item.totalServidoresSetor)
        
        if item.dataInicio != None:
            worksheet.write(row, col_det + 3, item.dataInicio.strftime('%d/%m/%Y'))
        else:
            worksheet.write(row, col_det + 3, 'N.I.')
        
        if item.dataFim != None:    
            worksheet.write(row, col_det + 4, item.dataFim.strftime('%d/%m/%Y'))
        else:
            worksheet.write(row, col_det + 4, 'N.I.')

        worksheet.write(row, col_det + 5, item.descricao)

        worksheet.write(row, col_det + 6, item.pesNome)

        if item.pactoIni != None:
            worksheet.write(row, col_det + 7, item.pactoIni.strftime('%d/%m/%Y'))
        else:
            worksheet.write(row, col_det + 7, 'N.I.')

        if item.pactoFim != None:    
            worksheet.write(row, col_det + 8, item.pactoFim.strftime('%d/%m/%Y'))
        else:
            worksheet.write(row, col_det + 8, 'N.I.')

        worksheet.write(row, col_det + 9, item.pactoDesc)

        worksheet.write(row, col_det + 10, item.formaExec)

        row += 1

    workbook.close()

    # o comandinho mágico que permite fazer o download de um arquivo
    send_from_directory('/app/project/static', 'Rel_PG.xlsx')

    registra_log_auto(current_user.id,'Consulta à Relatório de PGs e PTs.')


    # return render_template('download.html')
    return render_template('lista_relatorio.html', pt=pt)



## gera xlsx com estrutura hierárquica das unidades 

@consultas.route('/hierarquia')
def hierarquia():
    """
    +---------------------------------------------------------------------------------------+
    |Monta um relatório (planilha xlsx) com a estrutura hierárquica das unidades.           |
    +---------------------------------------------------------------------------------------+
    """

    hoje = date.today()  

    unids = db.session.query(Unidades.undDescricao,
                             Unidades.undSigla,
                             Unidades.unidadeIdPai)\
                      .all()

    # Create a workbook and add a worksheet.

    pasta_rel = os.path.normpath('c:/temp/hierarquia.xlsx')

    if not os.path.exists(os.path.normpath('c:/temp/')):
        os.makedirs(os.path.normpath('c:/temp/'))

    workbook = xlsxwriter.Workbook(pasta_rel)
    worksheet = workbook.add_worksheet('Lista')

    bold = workbook.add_format({'bold': True})

    worksheet.write('A1', 'Dados de:', bold)
    worksheet.write('B1', hoje.strftime('%x'), bold)

    # Start from the first cell. Rows and columns are zero indexed.
    row = 2
    col = 1

    for item in unids:

        sigla = item.undSigla
        pai = item.unidadeIdPai
        
        # monta colunas com hierarquia da unidade no registro

        worksheet.write(row,0,item.undDescricao)

        hier = []
        hier.append(sigla)
        while pai != None:
            sup = Unidades.query.filter(Unidades.unidadeId==pai).first()
            hier.append(sup.undSigla)
            pai = sup.unidadeIdPai

        for i in range(len(hier)-1, -1, -1):
            worksheet.write(row, col-i+len(hier)-1, hier[i])  

        row += 1

    workbook.close()

    registra_log_auto(current_user.id,'Gerado hierarquia.xlsx.')

    flash('Gerado hierarquia.xlsx. Verifique na sua pasta c:/temp/','sucesso')

    return redirect(url_for('core.index'))    

## atividades em planos de trabalho

@consultas.route('/lista_ativs_planos')
def lista_ativs_planos():
    """
    +---------------------------------------------------------------------------------------+
    |Lista as atividades em planos por situação                                             |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    # quantidades de atividades em planos (pactos)
    ativs = db.session.query(catdom.descricao,
                             Atividades.titulo, 
                             label('qtd_ativs',func.count(Pactos_de_Trabalho_Atividades.pactoTrabalhoAtividadeId)))\
                      .join(Atividades, Atividades.itemCatalogoId == Pactos_de_Trabalho_Atividades.itemCatalogoId)\
                      .join(catdom,catdom.catalogoDominioId == Pactos_de_Trabalho_Atividades.situacaoId)\
                      .group_by(catdom.descricao, Atividades.titulo)\
                      .all()

    return render_template('lista_ativs_planos.html', ativs=ativs)                  



## alguns números

@consultas.route('/estatisticas')
def estatisticas():
    """
    +---------------------------------------------------------------------------------------+
    |Alguns números do SISGP.                                                               |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    hoje = date.today()

    catdom_sit = db.session.query(catdom).subquery()

    # quantidades de unidades, pessoas, atividades, atividades utilizadas em planos e atividades utilizadas em pgs
    qtd_unidades = Unidades.query.count()
    qtd_unidades_ativas = db.session.query(Unidades).filter(Unidades.situacaoUnidadeId == 1).count()


    qtd_pessoas = Pessoas.query.count()
    qtd_pessoas_ativas = Pessoas.query.filter(Pessoas.situacaoPessoaId == 1).count()

    qtd_ativs = db.session.query(Atividades).count()
    qtd_ativs_validas = db.session.query(Atividades).filter(Atividades.titulo.notlike('x%'),
                                                            Atividades.titulo.notlike('z%')).count()

    ativs_utilizadas = db.session.query(distinct(Pactos_de_Trabalho_Atividades.itemCatalogoId)).count()
    ativs_utilizadas_validas = db.session.query(distinct(Pactos_de_Trabalho_Atividades.itemCatalogoId))\
                                         .join(Atividades, Atividades.itemCatalogoId == Pactos_de_Trabalho_Atividades.itemCatalogoId)\
                                         .filter(Atividades.titulo.notlike('x%'),
                                                 Atividades.titulo.notlike('z%'))\
                                         .count()

    ativs_utilizadas_pgs = db.session.query(distinct(Planos_de_Trabalho_Ativs_Items.itemCatalogoId))\
                                     .join(Planos_de_Trabalho_Ativs, Planos_de_Trabalho_Ativs.planoTrabalhoAtividadeId == Planos_de_Trabalho_Ativs_Items.planoTrabalhoAtividadeId)\
                                     .join(Planos_de_Trabalho,Planos_de_Trabalho.planoTrabalhoId == Planos_de_Trabalho_Ativs.planoTrabalhoId)\
                                     .count()
    ativs_utilizadas_pgs_validas = db.session.query(distinct(Planos_de_Trabalho_Ativs_Items.itemCatalogoId))\
                                     .join(Planos_de_Trabalho_Ativs, Planos_de_Trabalho_Ativs.planoTrabalhoAtividadeId == Planos_de_Trabalho_Ativs_Items.planoTrabalhoAtividadeId)\
                                     .join(Planos_de_Trabalho,Planos_de_Trabalho.planoTrabalhoId == Planos_de_Trabalho_Ativs.planoTrabalhoId)\
                                     .join(Atividades, Atividades.itemCatalogoId == Planos_de_Trabalho_Ativs_Items.itemCatalogoId)\
                                     .filter(Atividades.titulo.notlike('x%'),
                                             Atividades.titulo.notlike('z%'))\
                                     .count()                                 

    # o primeiro pg
    primeiro_pg = db.session.query(Planos_de_Trabalho.dataInicio).order_by(Planos_de_Trabalho.dataInicio).limit(1)
    # meses desde o primeito pg
    if primeiro_pg.first():
        vida_pgd = (hoje.year - primeiro_pg[0].dataInicio.year) * 12 + hoje.month - primeiro_pg[0].dataInicio.month
    else:
        vida_pgd = 0    

    # o primeiro plano
    primeiro_plano = db.session.query(Pactos_de_Trabalho.dataInicio).order_by(Pactos_de_Trabalho.dataInicio).limit(1)
    # meses desde o primeito plano
    if primeiro_plano.first():
        vida_plano = (hoje.year - primeiro_plano[0].dataInicio.year) * 12 + hoje.month - primeiro_plano[0].dataInicio.month
    else:
        vida_plano = 0

    # quantidade de atividades em pgs (planos)
    ativs_pgs = db.session.query(catdom.descricao, 
                             label('qtd_ativs',func.count(Planos_de_Trabalho_Ativs_Items.planoTrabalhoAtividadeItemId)))\
                      .join(Planos_de_Trabalho_Ativs,Planos_de_Trabalho_Ativs.planoTrabalhoAtividadeId==Planos_de_Trabalho_Ativs_Items.planoTrabalhoAtividadeId)\
                      .join(catdom,catdom.catalogoDominioId == Planos_de_Trabalho_Ativs.modalidadeExecucaoId)\
                      .group_by(catdom.descricao)\
                      .all()

    # quantidades de atividades em planos (pactos)
    ativs = db.session.query(catdom.descricao, 
                             label('qtd_ativs',func.count(Pactos_de_Trabalho_Atividades.pactoTrabalhoAtividadeId)))\
                      .join(Pactos_de_Trabalho,Pactos_de_Trabalho.pactoTrabalhoId == Pactos_de_Trabalho_Atividades.pactoTrabalhoId)\
                      .join(catdom,catdom.catalogoDominioId == Pactos_de_Trabalho_Atividades.situacaoId)\
                      .group_by(catdom.descricao)\
                      .all()

    # atividades top5 em planos de trabalho
    ativs_sub = db.session.query(Atividades.titulo,
                                 func.count(Pactos_de_Trabalho_Atividades.itemCatalogoId).label('qtd_ativs'))\
                            .join(Pactos_de_Trabalho_Atividades,Atividades.itemCatalogoId == Pactos_de_Trabalho_Atividades.itemCatalogoId)\
                            .group_by(Atividades.titulo)\
                            .subquery()
    ativs_top = db.session.query(ativs_sub.c.titulo,
                                   ativs_sub.c.qtd_ativs)\
                             .order_by(ativs_sub.c.qtd_ativs.desc())\
                             .limit(5)

    # quantitativos de programas de gestão
    programas_de_gestao = db.session.query(catdom.descricao, 
                                           label('qtd_pg',func.count(Planos_de_Trabalho.planoTrabalhoId)))\
                                    .join(catdom,catdom.catalogoDominioId == Planos_de_Trabalho.situacaoId)\
                                    .group_by(catdom.descricao)\
                                    .all()

    # quantidades de planos de trabalho por forma e situação
    planos_de_trabalho_fs = db.session.query(label('forma',catdom.descricao),
                                             label('sit',catdom_sit.c.descricao),   
                                             label('qtd_planos',func.count(Pactos_de_Trabalho.pactoTrabalhoId)))\
                                    .join(catdom,catdom.catalogoDominioId == Pactos_de_Trabalho.formaExecucaoId)\
                                    .join(catdom_sit,catdom_sit.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                    .group_by(catdom.descricao,catdom_sit.c.descricao)\
                                    .order_by(catdom.descricao,catdom_sit.c.descricao)\
                                    .all()      

    # quantidades de solicitações
    solicit = db.session.query(Pactos_de_Trabalho_Solic.analisado,
                               Pactos_de_Trabalho_Solic.aprovado,
                               catdom.descricao,
                               label('qtd_solic',func.count(Pactos_de_Trabalho_Solic.pactoTrabalhoSolicitacaoId)))\
                        .join(Pactos_de_Trabalho,Pactos_de_Trabalho.pactoTrabalhoId == Pactos_de_Trabalho_Solic.pactoTrabalhoId)\
                        .join(catdom,catdom.catalogoDominioId == Pactos_de_Trabalho_Solic.tipoSolicitacaoId)\
                        .group_by(Pactos_de_Trabalho_Solic.analisado,Pactos_de_Trabalho_Solic.aprovado,catdom.descricao)\
                        .order_by(Pactos_de_Trabalho_Solic.analisado,Pactos_de_Trabalho_Solic.aprovado,catdom.descricao)\
                        .all()                                                          

    # pessoas: max, min e média nas unidades
    pessoas_unid = db.session.query(label('qtd_pes',func.count(Pessoas.pessoaId)))\
                             .join(Unidades, Unidades.unidadeIdPai == Pessoas.unidadeId)\
                             .filter(Unidades.situacaoUnidadeId == 1,
                                     Pessoas.situacaoPessoaId == 1)\
                             .group_by(Pessoas.unidadeId)\
                             .all()

    if len(pessoas_unid) > 0:
        qtd_pes_max = max(pessoas_unid)[0]
        qtd_pes_min = min(pessoas_unid)[0]
        qtd_pes_avg = round(qtd_pessoas_ativas/qtd_unidades_ativas)
    else:
        qtd_pes_max = 0
        qtd_pes_min = 0
        qtd_pes_avg = 0                             

    # unidades top5 em programas de gestão
    unids_sub = db.session.query(Unidades.undSigla,
                                 func.count(Planos_de_Trabalho.unidadeId).label('qtd_pgs'))\
                            .join(Planos_de_Trabalho,Unidades.unidadeId == Planos_de_Trabalho.unidadeId)\
                            .group_by(Unidades.undSigla)\
                            .subquery()
    unids_top = db.session.query(unids_sub.c.undSigla,
                                 unids_sub.c.qtd_pgs)\
                           .order_by(unids_sub.c.qtd_pgs.desc())\
                           .limit(5)

    # unidades top5 em planos de trabalho
    unids_pt_sub = db.session.query(Unidades.undSigla,
                                 func.count(Pactos_de_Trabalho.unidadeId).label('qtd_pts'))\
                             .join(Pactos_de_Trabalho,Unidades.unidadeId == Pactos_de_Trabalho.unidadeId)\
                             .group_by(Unidades.undSigla)\
                             .subquery()
    unids_pt_top = db.session.query(unids_pt_sub.c.undSigla,
                                    unids_pt_sub.c.qtd_pts)\
                             .order_by(unids_pt_sub.c.qtd_pts.desc())\
                             .limit(5)                       
              

    return render_template('estatisticas.html', programas_de_gestao=programas_de_gestao,
                                                planos_de_trabalho_fs=planos_de_trabalho_fs, 
                                                qtd_ativs=qtd_ativs, 
                                                qtd_pessoas=qtd_pessoas, qtd_pessoas_ativas=qtd_pessoas_ativas, 
                                                qtd_unidades=qtd_unidades,
                                                qtd_unidades_ativas=qtd_unidades_ativas,
                                                qtd_pes_max=qtd_pes_max, qtd_pes_min=qtd_pes_min, qtd_pes_avg=qtd_pes_avg,
                                                ativs_utilizadas=ativs_utilizadas,
                                                ativs_utilizadas_pgs=ativs_utilizadas_pgs,
                                                hoje=hoje,
                                                ativs_top=ativs_top,
                                                unids_top=unids_top,
                                                unids_pt_top=unids_pt_top,
                                                vida_pgd=vida_pgd,
                                                vida_plano=vida_plano,
                                                ativs=ativs,
                                                solicit=solicit,
                                                ativs_pgs=ativs_pgs,
                                                qtd_ativs_validas=qtd_ativs_validas,
                                                ativs_utilizadas_validas=ativs_utilizadas_validas,
                                                ativs_utilizadas_pgs_validas=ativs_utilizadas_pgs_validas)


# qtd pgs e pts em um período log

@consultas.route("/periodo", methods=['GET', 'POST'])
def periodo():
    """+--------------------------------------------------------------------------------------+
       |Mostra quantidades de PGs e PTs em um perídodo informado.                             |
       |                                                                                      |
       +--------------------------------------------------------------------------------------+
    """

    catdom_sit = db.session.query(catdom).subquery()

    form = PeriodoForm()

    if form.validate_on_submit():

        data_ini = form.data_ini.data
        data_fim = form.data_fim.data

        # quantitativos de programas de gestão iniciados e finalizados no período
        programas_de_gestao_d = db.session.query(catdom.descricao, 
                                            label('qtd_pg',func.count(Planos_de_Trabalho.planoTrabalhoId)))\
                                        .join(catdom,catdom.catalogoDominioId == Planos_de_Trabalho.situacaoId)\
                                        .filter(Planos_de_Trabalho.dataInicio > datetime.combine(data_ini,time.min),
                                                Planos_de_Trabalho.dataFim < datetime.combine(data_fim,time.max))\
                                        .group_by(catdom.descricao)\
                                        .all()

        # quantidades de planos de trabalho iniciados e finalizados no período
        planos_de_trabalho_d = db.session.query(label('forma',catdom.descricao),
                                                 label('sit',catdom_sit.c.descricao),   
                                                 label('qtd_planos',func.count(Pactos_de_Trabalho.pactoTrabalhoId)))\
                                          .join(catdom,catdom.catalogoDominioId == Pactos_de_Trabalho.formaExecucaoId)\
                                          .join(catdom_sit,catdom_sit.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                          .filter(Pactos_de_Trabalho.dataInicio > datetime.combine(data_ini,time.min),
                                                  Pactos_de_Trabalho.dataFim < datetime.combine(data_fim,time.max))\
                                          .group_by(catdom.descricao,catdom_sit.c.descricao)\
                                          .order_by(catdom.descricao,catdom_sit.c.descricao)\
                                          .all()

        #################

        # quantitativos de programas de gestão com vigêntes no período
        programas_de_gestao_v = db.session.query(catdom.descricao, 
                                                 label('qtd_pg',func.count(Planos_de_Trabalho.planoTrabalhoId)))\
                                          .join(catdom,catdom.catalogoDominioId == Planos_de_Trabalho.situacaoId)\
                                          .filter(Planos_de_Trabalho.dataInicio <= datetime.combine(data_fim,time.min),
                                                  Planos_de_Trabalho.dataFim >= datetime.combine(data_ini,time.max))\
                                          .group_by(catdom.descricao)\
                                          .all()

        # quantidades de planos de trabalho vigentes no período
        planos_de_trabalho_v = db.session.query(label('forma',catdom.descricao),
                                                   label('sit',catdom_sit.c.descricao),   
                                                   label('qtd_planos',func.count(Pactos_de_Trabalho.pactoTrabalhoId)))\
                                            .join(catdom,catdom.catalogoDominioId == Pactos_de_Trabalho.formaExecucaoId)\
                                            .join(catdom_sit,catdom_sit.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                            .filter(Pactos_de_Trabalho.dataInicio <= datetime.combine(data_fim,time.min),
                                                    Pactos_de_Trabalho.dataFim >= datetime.combine(data_ini,time.max))\
                                            .group_by(catdom.descricao,catdom_sit.c.descricao)\
                                            .order_by(catdom.descricao,catdom_sit.c.descricao)\
                                            .all()   

        ###############

        # quantitativos de programas de gestão com vigência fora do período
        programas_de_gestao_f = db.session.query(catdom.descricao, 
                                            label('qtd_pg',func.count(Planos_de_Trabalho.planoTrabalhoId)))\
                                        .join(catdom,catdom.catalogoDominioId == Planos_de_Trabalho.situacaoId)\
                                        .filter(or_(and_(Planos_de_Trabalho.dataInicio < datetime.combine(data_ini,time.min),\
                                                         Planos_de_Trabalho.dataFim    < datetime.combine(data_ini,time.max)),\
                                                    and_(Planos_de_Trabalho.dataInicio > datetime.combine(data_fim,time.min),\
                                                         Planos_de_Trabalho.dataFim    > datetime.combine(data_fim,time.max))))\
                                        .group_by(catdom.descricao)\
                                        .all()

        # quantidades de planos de trabalho com vigência fora do período
        planos_de_trabalho_f = db.session.query(label('forma',catdom.descricao),
                                                 label('sit',catdom_sit.c.descricao),   
                                                 label('qtd_planos',func.count(Pactos_de_Trabalho.pactoTrabalhoId)))\
                                          .join(catdom,catdom.catalogoDominioId == Pactos_de_Trabalho.formaExecucaoId)\
                                          .join(catdom_sit,catdom_sit.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                          .filter(or_(and_(Pactos_de_Trabalho.dataInicio < datetime.combine(data_ini,time.min),\
                                                           Pactos_de_Trabalho.dataFim    < datetime.combine(data_ini,time.max)),\
                                                      and_(Pactos_de_Trabalho.dataInicio > datetime.combine(data_fim,time.min),\
                                                           Pactos_de_Trabalho.dataFim    > datetime.combine(data_fim,time.max))))\
                                          .group_by(catdom.descricao,catdom_sit.c.descricao)\
                                          .order_by(catdom.descricao,catdom_sit.c.descricao)\
                                          .all()                                                                             

        return render_template('pg_pt_por_periodo.html', form=form, 
                                                         programas_de_gestao_f = programas_de_gestao_f,
                                                         planos_de_trabalho_f  = planos_de_trabalho_f,
                                                         programas_de_gestao_d = programas_de_gestao_d,
                                                         planos_de_trabalho_d  = planos_de_trabalho_d,
                                                         programas_de_gestao_v = programas_de_gestao_v,
                                                         planos_de_trabalho_v  = planos_de_trabalho_v)


    return render_template('pg_pt_por_periodo.html', form=form)


# Candidaturas aprovadas mas sem plano

@consultas.route("/candidatos_sem_plano")
def candidatos_sem_plano():
    """+--------------------------------------------------------------------------------------+
       |Mostra pessoas que tiveram candidatura aprovada em um PG, mas que não um plano.       |
       |                                                                                      |
       +--------------------------------------------------------------------------------------+
    """


    candidatos_sem_plano = db.session.query(Atividade_Candidato.pessoaId,
                                            Atividade_Candidato.situacaoId,
                                            Pessoas.pesNome,
                                            Unidades.undSigla,
                                            VW_Unidades.undSiglaCompleta,
                                            Planos_de_Trabalho_Ativs.planoTrabalhoId,
                                            Planos_de_Trabalho.situacaoId,
                                            Planos_de_Trabalho.dataInicio,
                                            Planos_de_Trabalho.dataFim,
                                            catdom.descricao)\
                             .join(Pessoas, Pessoas.pessoaId == Atividade_Candidato.pessoaId)\
                             .join(Unidades,Unidades.unidadeId == Pessoas.unidadeId)\
                             .outerjoin(VW_Unidades, VW_Unidades.unidadeId == Pessoas.unidadeId)\
                             .join(Planos_de_Trabalho_Ativs, Planos_de_Trabalho_Ativs.planoTrabalhoAtividadeId == Atividade_Candidato.planoTrabalhoAtividadeId)\
                             .join(Planos_de_Trabalho, Planos_de_Trabalho.planoTrabalhoId == Planos_de_Trabalho_Ativs.planoTrabalhoId)\
                             .join(catdom, catdom.catalogoDominioId == Planos_de_Trabalho.situacaoId)\
                             .outerjoin(Pactos_de_Trabalho, and_(Pactos_de_Trabalho.planoTrabalhoId == Planos_de_Trabalho.planoTrabalhoId,
                                                                 Pactos_de_Trabalho.pessoaId == Atividade_Candidato.pessoaId))\
                             .filter(Atividade_Candidato.situacaoId == 804,
                                     Pactos_de_Trabalho.pactoTrabalhoId == None,
                                     Unidades.situacaoUnidadeId == 1,
                                     Planos_de_Trabalho.situacaoId == 309)\
                             .order_by(VW_Unidades.undSiglaCompleta,Pessoas.pesNome)\
                             .all()

    quantidade = len(candidatos_sem_plano)  

    return render_template('lista_candidatos_sem_plano.html', candidatos_sem_plano=candidatos_sem_plano, quantidade=quantidade)

## renderiza tela inicial de consultas

@consultas.route('/consultas_i')
@login_required

def consultas_i():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta tela inicial de consultas.                                                   |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    
    return render_template('consultas.html') 