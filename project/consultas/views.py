"""
.. topic:: Consultas (views)

    As consultas trazem informações úteis para a gestão do SISGP.


.. topic:: Ações relacionadas às pessoas

    * Lista quantidades de pessoas em programas de gestão por unidade: pessoas_qtd_pg_unidade
    * Lista o Catálogo de Domínios: catalogo_dominio 
    * Dados de Pactos de trabalho: pactos
    * Atividades de um pacto: pacto_atividades


"""

# views.py na pasta consultas

from flask import render_template,url_for,flash, redirect,request,Blueprint
from flask_login import current_user
from sqlalchemy.sql import label
from sqlalchemy import func, distinct
from sqlalchemy.orm import aliased
from project import db
from project.models import Pactos_de_Trabalho, Pessoas, Unidades, Planos_de_Trabalho, catdom,\
                           Pactos_de_Trabalho_Atividades, Atividades, Planos_de_Trabalho_Ativs,\
                           Planos_de_Trabalho_Hist, Planos_de_Trabalho_Ativs_Items
from project.usuarios.views import registra_log_auto                           

import locale
import datetime
from datetime import date
import os.path
import xlsxwriter

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
                          Unidades.unidadeIdPai,
                          Unidades.undSigla,
                          Unidades.undDescricao,
                          planos.c.qtd_pg,
                          planos.c.totalServidoresSetor,
                          pactos.c.qtd_pactos)\
                   .join(planos, planos.c.unidadeId == Unidades.unidadeId)\
                   .outerjoin(pactos, pactos.c.unidadeId == Unidades.unidadeId)\
                   .order_by(Unidades.unidadeId)\
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
    |Apresenta uma lista dos pactos de trabalho e dados relevantes.                         |
    +---------------------------------------------------------------------------------------+
    """

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
                                       Unidades.undSigla,
                                       Pessoas.pesNome,
                                       label('descricao1',catdom.descricao),
                                       label('descricao2',situacao.c.descricao))\
                                 .join(Unidades, Unidades.unidadeId == Pactos_de_Trabalho.unidadeId)\
                                 .join(Pessoas, Pessoas.pessoaId == Pactos_de_Trabalho.pessoaId)\
                                 .join(catdom, catdom.catalogoDominioId == Pactos_de_Trabalho.formaExecucaoId)\
                                 .join(situacao, situacao.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                 .order_by(Pessoas.pesNome)\
                                 .all()

    qtd_itens = len(pactos_trabalho)

    return render_template('lista_pactos.html', qtd_itens = qtd_itens, pactos_trabalho = pactos_trabalho)    


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

    ##### para conferir cálculo de %execucao (conta por fora não bate com os valores registrados no banco)
    # pactos = db.session.query(Pessoas.pesNome,  
    #                           func.sum(Pactos_de_Trabalho_Atividades.tempoPrevistoPorItem).label("total_tempo_item"),
    #                           func.sum(Pactos_de_Trabalho_Atividades.tempoPrevistoTotal).label("total_tempo_total"),
    #                           func.sum(Pactos_de_Trabalho_Atividades.tempoRealizado).label("total_tempo_realizado"))\
    #                    .join(Pactos_de_Trabalho, Pactos_de_Trabalho.pactoTrabalhoId == Pactos_de_Trabalho_Atividades.pactoTrabalhoId)\
    #                    .join(Pessoas,Pessoas.pessoaId == Pactos_de_Trabalho.pessoaId)\
    #                    .group_by(Pactos_de_Trabalho_Atividades.pactoTrabalhoId,Pactos_de_Trabalho.pessoaId,Pessoas.pesNome)\
    #                    .all()           
    
    # workbook = xlsxwriter.Workbook('totais_pactos.xlsx')
    # worksheet = workbook.add_worksheet('Lista')
    # col = 0
    # row = 0
    # for p in pactos:
    #     worksheet.write(row, col, p.pesNome)
    #     worksheet.write(row, col + 1, p.total_tempo_item)
    #     worksheet.write(row, col + 2, p.total_tempo_total)
    #     worksheet.write(row, col + 3, p.total_tempo_realizado)
    #     row += 1
    # workbook.close()


    pacto_ativ_unic = db.session.query(distinct(Pactos_de_Trabalho_Atividades.itemCatalogoId))\
                                .filter(Pactos_de_Trabalho_Atividades.pactoTrabalhoId == pactoId)\
                                .group_by(Pactos_de_Trabalho_Atividades,Pactos_de_Trabalho_Atividades.itemCatalogoId)\
                                .count()


    return render_template('lista_pacto_atividades.html', qtd_itens = qtd_itens, pacto_ativ = pacto_ativ,
                                                          nome=nome,pacto_ativ_unic = pacto_ativ_unic)


## deletar programa de gestão (plano de tragalho e relacionamentos) em rascunho

@consultas.route('/<pgId>/deleta_pg', methods=['GET', 'POST'])
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

@consultas.route('/relatorioPG')
def relatorioPG():
    """
    +---------------------------------------------------------------------------------------+
    |Monta um relatório (planilha xlsx) com dados dos planos de gestão nas unidades.        |
    +---------------------------------------------------------------------------------------+
    """

    hoje = date.today()

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
                              label('pactoDesc',catdom.descricao))\
                       .join(Pessoas, Pessoas.pessoaId == Pactos_de_Trabalho.pessoaId)\
                       .join(catdom, Pactos_de_Trabalho.situacaoId == catdom.catalogoDominioId)\
                       .subquery()                                    

    pt = db.session.query(Unidades.unidadeId,
                          Unidades.unidadeIdPai,
                          Unidades.undSigla,
                          Unidades.undDescricao,
                          dados_pt.c.totalServidoresSetor,
                          dados_pt.c.dataInicio,
                          dados_pt.c.dataFim,
                          dados_pt.c.descricao,
                          pactos.c.pesNome,
                          pactos.c.pactoIni,
                          pactos.c.pactoFim,
                          pactos.c.pactoDesc)\
                   .join(dados_pt, dados_pt.c.unidadeId == Unidades.unidadeId)\
                   .outerjoin(pactos, pactos.c.planoTrabalhoId == dados_pt.c.planoTrabalhoId)\
                   .order_by(Unidades.unidadeId)\
                   .all()

    # montando estrutura hierárquica de cada unidade com pg e gravando tudo num xlsx

    # Create a workbook and add a worksheet.

    pasta_rel = os.path.normpath('c:/temp/Rel_PG.xlsx')
    if not os.path.exists(os.path.normpath('c:/temp/')):
        os.makedirs(os.path.normpath('c:/temp/'))

    workbook = xlsxwriter.Workbook(pasta_rel)
    worksheet = workbook.add_worksheet('Lista')

    bold = workbook.add_format({'bold': True})

    worksheet.write('A1', 'Dados extraidos em:', bold)
    worksheet.write('B1', hoje.strftime('%x'), bold)

    # Start from the first cell. Rows and columns are zero indexed.
    row = 3
    col = 0

    # Monta linha de cabeçalho do xlsx. Descobre o maior nível hierárquico das unidades
 
    niv_max = db.session.query(label('niv',func.max(Unidades.undNivel))).first()
    col_cab = col + niv_max.niv

    worksheet.write(row-1, col_cab+1, 'Sobre Programa de Gestão', bold)
    worksheet.write(row-1, col_cab + 5, 'Sobre Pactos de Trabalho', bold)

    worksheet.write(row, col, 'Hierarquia', bold)
    worksheet.write(row, col_cab, 'Nome', bold)
    worksheet.write(row, col_cab + 1, 'Pessoas', bold)
    worksheet.write(row, col_cab + 2, 'Início PG', bold)
    worksheet.write(row, col_cab + 3, 'Fim PG', bold)
    worksheet.write(row, col_cab + 4, 'Situação PG', bold)
    worksheet.write(row, col_cab + 5, 'Pessoa', bold)
    worksheet.write(row, col_cab + 6, 'Início Pacto', bold)
    worksheet.write(row, col_cab + 7, 'Fim Pacto', bold)
    worksheet.write(row, col_cab + 8, 'Situação Pacto', bold)

    row = 4
 
    for item in pt:

        sigla = item.undSigla
        pai = item.unidadeIdPai
        
        # monta colunas com hierarquia da unidade no registro
        worksheet.write(row, niv_max.niv, sigla)

        hier = []
        hier.append(sigla)
        while pai != None:
            sup = Unidades.query.filter(Unidades.unidadeId==pai).first()
            hier.append(sup.undSigla)
            pai = sup.unidadeIdPai

        for i in range(len(hier)-1, -1, -1):
            worksheet.write(row, col-i+len(hier)-1, hier[i])

        # preenche demais colunas de detalhe
        col_det = col_cab - 1

        worksheet.write(row, col_det + 1, item.undDescricao)

        worksheet.write(row, col_det + 2, item.totalServidoresSetor)
        
        if item.dataInicio != None:
            worksheet.write(row, col_det + 3, item.dataInicio.strftime('%x'))
        else:
            worksheet.write(row, col_det + 3, 'N.I.')
        
        if item.dataFim != None:    
            worksheet.write(row, col_det + 4, item.dataFim.strftime('%x'))
        else:
            worksheet.write(row, col_det + 4, 'N.I.')

        worksheet.write(row, col_det + 5, item.descricao)

        worksheet.write(row, col_det + 6, item.pesNome)

        if item.pactoIni != None:
            worksheet.write(row, col_det + 7, item.pactoIni.strftime('%x'))
        else:
            worksheet.write(row, col_det + 7, 'N.I.')

        if item.pactoFim != None:    
            worksheet.write(row, col_det + 8, item.pactoFim.strftime('%x'))
        else:
            worksheet.write(row, col_det + 8, 'N.I.')

        worksheet.write(row, col_det + 9, item.pactoDesc)

        row += 1

    workbook.close()

    flash('Gerado Rel_PG.xlsx. Verifique na sua pasta c:/temp/','sucesso')

    return redirect(url_for('consultas.pessoas_qtd_pg_unidade'))


