"""
.. topic:: Core (views)

    Este é o módulo inicial do sistema.

    Apresenta as telas de início, informação, o procedimento para carga de dados de pagamento de bolsistas: planilha COSAO
    e carga dos dados do SICONV (convênios). Aqui também estão os procedimentos das Chamadas.

.. topic:: Ações relacionadas aos bolsistas

    * Tela inicial: index
    * Tela de informações: info
    * Carregar dados PDCTR: carregaPDCTR
    * Carregar dados SICONV: carregaSICONV
    * Inserir dados de chamadas homologadas: cria_chamada
    * Atualizar dados de chamada homologada: update_chamada
    * Carregar mensagens do SICONV: carregaMSG


"""

# core/views.py

from flask import render_template,url_for,flash, redirect,request,Blueprint
from flask_login import login_required, current_user
from sqlalchemy import func, distinct
from sqlalchemy.sql import label
from project import db
from project.models import PagamentosPDCTR, RefCargaPDCTR, Programa, Proposta, Convenio,\
                           Programa_Interesse, Pagamento, Empenho, Desembolso, RefSICONV,\
                           DadosSEI, Chamadas, MSG_Siconv, Acordo, Bolsa, Processo_Mae,\
                           Processo_Filho, Sistema

from project.demandas.views import registra_log_auto
from project.convenios.forms import ChamadaForm
from project.acordos.forms import ArquivoForm

import os
import re
import datetime
from datetime import datetime as dt
import xlrd
import shutil
import urllib.request
import csv
import locale
from threading import Thread
from werkzeug.utils import secure_filename
import tempfile

core = Blueprint("core",__name__)


# função que executa carga de dados PDCTR

def cargaPDCTR(entrada):

    data_referência = ''

    campos_bolsistas_para_db = ['Processo','Nome','Sexo Proc. Filho','CPF','Sit Filho','Data da Situação Filho', 'Inicio Filho',
                                'Termino Filho','Processo Mãe','Inicio Mãe','Termino Mãe','Titulo do Processo Filho', 'Nome Chamada',
                                'Modalidade','Cat Nivel','Cod Programa','Grande Área','Área de Conhecimento','Sigla Instituição',
                                'UF Instituição','Cidade Instituição','Data do Pagamento','Tipo de Pagamento','Valor Pago']

    print ('<<',dt.now().isoformat(timespec='minutes'),'>> ',' Carga PDCTR iniciada...')

    # abre arquivo (book), planilha (sheet) e linha com os nomes dos campos (linha_cabeçalho)

    book = xlrd.open_workbook(filename=entrada,ragged_rows=True)
    planilha = book.sheet_by_index(0)

    procura_cabeçalho = 0

    while planilha.row_len(procura_cabeçalho) < len(campos_bolsistas_para_db):

        procura_cabeçalho += 1

    linha_cabeçalho = planilha.row_values(procura_cabeçalho, start_colx=0, end_colx=None)

    for campo in campos_bolsistas_para_db:
        if campo not in linha_cabeçalho:
            print ('** ATENÇÃO: o campo ',campo,' não existe na planinha original, verifique o parâmetro inserido. **')
            exit()

    try:
        data_referência = planilha.cell_value(3,1)[-10:]
        data_referência = datetime.date(int(data_referência[-4:]),int(data_referência[-7:-5]),
                                         int(data_referência[0:2]))
    except:

        try:
            data_referência = planilha.cell_value(3,0)[-10:]
            data_referência = datetime.date(int(data_referência[-4:]),int(data_referência[-7:-5]),
                                             int(data_referência[0:2]))
        except:
            print ('** Erro ao tentar pegar a data de referência do arquivo. Usarei a data de hoje **')
            data_referência = datetime.date.today()

    print ('Planilha: CNPq')
    print (f'Cabeçalho original: {len(linha_cabeçalho)} campos')
    print (f'Cabeçalho após extração: {len(campos_bolsistas_para_db)} campos')
    print (f'Quantidade de registros na planilha: {planilha.nrows - procura_cabeçalho - 1 }')
    print ('Começará a extração com o cabeçalho na linha ',procura_cabeçalho + 1)
    print ('Data de referência: ', data_referência)
    print ('\n')

    qtd_linhas = planilha.nrows - procura_cabeçalho - 1

    # varre linha por linha da planilha de entrada

    print ('<<',dt.now().isoformat(timespec='minutes'),'>> ',' Gravando dados no banco...')

    for i in range(qtd_linhas):

        linha_base = planilha.row_values(i + procura_cabeçalho + 1 , start_colx=0, end_colx=None)

        linha = []
        iter  = 0

        # pega os campos de interess na planilha conforme o defindo em campos_bolsistas_para_db

        for campo in campos_bolsistas_para_db:

            dado_célula = planilha.cell_value(i + procura_cabeçalho + 1,
                                                               linha_cabeçalho.index(campo))
            tipo_célula = planilha.cell_type (i + procura_cabeçalho + 1,
                                                               linha_cabeçalho.index(campo))

            if str(dado_célula) == '':  # células vazias recebem None
                dado_célula = None

            if re.search('\d{2}/\d{2}/\d{4}', str(dado_célula)) != None: # identifica campos de texto, mas que contém data dd/mm/aaaa
                                                                         # e coloca no formado de data para o banco aaaa-mm-dd
                dado_célula = datetime.datetime.strptime(str(dado_célula), '%d/%m/%Y').date()

            if tipo_célula == 3:  # identifica células que tem formato de data no excell e coloca como aaaa-mm-dd

                ano_mes_dia = (str(xlrd.xldate.xldate_as_datetime(dado_célula, 0))[0:10])
                dia_mes_ano = ano_mes_dia[8:10] + '/' + ano_mes_dia[5:7] + '/' + ano_mes_dia[0:4]

                dado_célula = datetime.datetime.strptime(str(dia_mes_ano), '%d/%m/%Y').date()

            linha.append(dado_célula)

        # verifica se o registro a ser inserido já não existe no banco, identificado por processo, data pagamento e tipo pagamento
        #bolsista_pagamento = PagamentosPDCTR.query.filter_by(processo = linha[0], data_pagamento = linha[21], tipo_pagamento = linha[22]).first()
        bolsista_pagamento = db.session.query(PagamentosPDCTR)\
                                       .filter_by(processo = linha[0], data_pagamento = linha[21], tipo_pagamento = linha[22])\
                                       .first()

        # não existindo, grava:
        if bolsista_pagamento == None:

            pagamento = PagamentosPDCTR(processo          = linha[0],
                                        nome              = linha[1],
                                        sexo_proc_filho   = linha[2],
                                        cpf               = linha[3],
                                        situ_filho        = linha[4],
                                        data_situ_filho   = linha[5],
                                        inic_filho        = linha[6],
                                        term_filho        = linha[7],
                                        proc_mae          = linha[8],
                                        inic_mae          = linha[9],
                                        term_mae          = linha[10],
                                        titu_proc_filho   = linha[11],
                                        nome_chamada      = linha[12],
                                        modalidade        = linha[13],
                                        nivel             = linha[14],
                                        cod_programa      = linha[15],
                                        grande_area       = linha[16],
                                        area_conhecimento = linha[17],
                                        sigla_inst        = linha[18],
                                        uf_inst           = linha[19],
                                        cidade_inst       = linha[20],
                                        data_pagamento    = linha[21],
                                        tipo_pagamento    = linha[22],
                                        valor_pago        = linha[23])

            db.session.add(pagamento)


    db.session.commit()

    # grava em tabela própria a data de referência da tabela gerada pela COSAO
    refer = RefCargaPDCTR(data_ref = data_referência)
    db.session.add(refer)
    db.session.commit()

    print ('<<',dt.now().isoformat(timespec='minutes'),'>> ',' Dados de pagamento carregados. Iniciando criação de tabelas...')

    # pega processos filho da tabela dos dados de folha de pagamento (PagamentosPDCTR)


    processos_filho = db.session.query(PagamentosPDCTR.cod_programa,
                                       PagamentosPDCTR.nome_chamada,
                                       PagamentosPDCTR.proc_mae,
                                       PagamentosPDCTR.processo,
                                       PagamentosPDCTR.nome,
                                       PagamentosPDCTR.cpf,
                                       PagamentosPDCTR.modalidade,
                                       PagamentosPDCTR.nivel,
                                       PagamentosPDCTR.situ_filho,
                                       PagamentosPDCTR.inic_filho,
                                       label('max_term_filho',func.max(PagamentosPDCTR.term_filho)),
                                       label('mens_pagas', func.count(PagamentosPDCTR.processo)),
                                       label('pago_total', func.sum(PagamentosPDCTR.valor_pago)),
                                       label('valor_apagar', Bolsa.mensalidade),
                                       label('max_dt_ult_pag', func.max(PagamentosPDCTR.data_pagamento)))\
                                       .outerjoin(Bolsa, (PagamentosPDCTR.modalidade+'-'+PagamentosPDCTR.nivel)==Bolsa.mod_niv)\
                                       .group_by(PagamentosPDCTR.proc_mae,PagamentosPDCTR.processo).all()

#
    quantidade_filho = len(processos_filho)

    #
    ## deletar linhas da tabela processo_filho e carregá-la com novos dados
    db.session.query(Processo_Filho).delete()
    db.session.commit()
    # Gera tabela  Processo_Filho totalizando mensalidades e valores a pagar

    situ_filho_retirados = [17,18,40,41,61,62,63,66,71,74,83]
    """
    +---------------------------------------------------------------------------------------+
    |                                                                                       |
    |Situações para as quais não se calcula mensalidades e valores a pagar                  |
    | - 17 - CANCELADO POR MOTIVO DE SaúDE                                                  |
    | - 18 - ENCERRADO COM DEVOLUçãO DE RECURSOS                                            |
    | - 40 - CANCELADO POR AQUISIçãO DE VíNCULO EMPREGATíCIO                                |
    | - 41 - CANCELADO POR ACUMULO DE CONCESSõES (OUTRA AgêNCIA/CNPQ)                       |
    | - 61 - CANCELADO PELO CNPQ                                                            |
    | - 62 - CANCELADO A PEDIDO DO BOLSISTA/PESQUISADOR                                     |
    | - 63 - CANCELADO A PEDIDO DO COORDENADOR                                              |
    | - 66 - CANCELADO COM DéBITO                                                           |
    | - 71 - ENCERRADO                                                                      |
    | - 74 - ENCERRADO COM DÉBITO                                                           |
    | - 83 - ENCERRADO POR VIGÊNCIA EXPIRADA                                                |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    for filho in processos_filho:

        filho_s = list(filho)

        # aqui calcula-se a quantidade de meses entre o último pagamento e o final da vigencia do filho
        # esta quandidade é inserida ao final da lista para ser gravada na tabela ao final
        if filho_s[8] not in situ_filho_retirados and filho.max_term_filho >= data_referência:
            filho_s.append((filho.max_term_filho.year  - filho.max_dt_ult_pag.year) * 12 +\
                           (filho.max_term_filho.month - filho.max_dt_ult_pag.month))
            if filho_s[15] < 0:
                filho_s[15] = 0
        else:
            filho_s.append(0)

        if filho.valor_apagar != None:
            filho_s[13] = filho.valor_apagar * filho_s[15]
        else:
            filho_s[13] = 0

        filho_gravar = Processo_Filho(cod_programa      = filho_s[0],
                                      nome_chamada      = filho_s[1],
                                      proc_mae          = filho_s[2],
                                      processo          = filho_s[3],
                                      nome              = filho_s[4],
                                      cpf               = filho_s[5],
                                      modalidade        = filho_s[6],
                                      nivel             = filho_s[7],
                                      situ_filho        = filho_s[8],
                                      inic_filho        = filho_s[9],
                                      term_filho        = filho_s[10],
                                      mens_pagas        = filho_s[11],
                                      pago_total        = filho_s[12],
                                      valor_apagar      = filho_s[13],
                                      mens_apagar       = filho_s[15],
                                      dt_ult_pag        = filho_s[14])
        db.session.add(filho_gravar)

    db.session.commit()

    print ('<<',dt.now().isoformat(timespec='minutes'),'>> ',' Tabela dos processos-filho criada.')



    #
    # pega processos mãe da planilha de folha de pagamento

    processos_mae = db.session.query(PagamentosPDCTR.proc_mae,
                                     PagamentosPDCTR.cod_programa,
                                     PagamentosPDCTR.nome_chamada,
                                     PagamentosPDCTR.inic_mae,
                                     PagamentosPDCTR.term_mae,
                                     label('max_id',func.max(PagamentosPDCTR.id)))\
                                     .group_by(PagamentosPDCTR.proc_mae).all()
                                     #label('max_term_mae',func.max(PagamentosPDCTR.term_mae)))\

#
    quantidade_mae = len(processos_mae)

    # Atualiza tabela  Processo_Mae
    for mae in processos_mae:

        mae_atual = db.session.query(Processo_Mae).filter(Processo_Mae.proc_mae==mae.proc_mae).first()

        if mae_atual == None:

            print('*** Novo processo mãe inserido: ',mae.proc_mae,' ***')
            mae_gravar = Processo_Mae(cod_programa  = mae.cod_programa,
                                      nome_chamada  = mae.nome_chamada,
                                      proc_mae      = mae.proc_mae,
                                      inic_mae      = mae.inic_mae,
                                      term_mae      = mae.term_mae)
            db.session.add(mae_gravar)
            db.session.commit()

        else:

            mae_atual.term_mae = mae.term_mae
            db.session.commit()


    print ('<<',dt.now().isoformat(timespec='minutes'),'>> ',' Tabela dos processos-mae atualizada.')
    print ('<<',dt.now().isoformat(timespec='minutes'),'>> ',' Procedimento finalizado!')


###########################################################################################################

# função que executa carga de dados SICONV - é executada de forma assíncrona

def cargaSICONV():
    ## parâmetros internos de download e carga: default 'sim' (colocar 'não' quando quiser pular fase)
    pega_e_descompacta  = 'sim'
    carrega_programas   = 'sim'
    carrega_propostas   = 'sim'
    carrega_convenios   = 'sim'
    carrega_pagamentos  = 'sim'
    carrega_empenhos    = 'sim'
    carrega_desembolsos = 'sim'

    ## pega arquivos do portal siconv e os descompacta, gerando os respectivos .csv
    print ('*****************************************************************')
    print ('<<',dt.now().isoformat(timespec='minutes'),'>> ','Downloading and unpacking SICONV files...')
    print ('*****************************************************************')

    #url_base = 'http://portal.convenios.gov.br/images/docs/CGSIS/csv/'
    url_base = 'http://plataformamaisbrasil.gov.br/images/docs/CGSIS/csv/'
    pasta_compactados = os.path.normpath('c:/temp/arqs_siconv')
    #pasta_compactados = 'arqs_siconv'
    if not os.path.exists(pasta_compactados):
        os.makedirs(os.path.normpath(pasta_compactados))

    # SEM 'siconv_prorroga_oficio.csv' e 'siconv_termo_aditivo.csv'
    arquivos = ['siconv_programa.csv','siconv_programa_proposta.csv','siconv_proposta.csv',
                'siconv_convenio.csv','siconv_empenho.csv','siconv_desembolso.csv','siconv_pagamento.csv',
                'siconv_empenho_desembolso.csv','data_carga_siconv.csv']

    ## usando o urlretrieve para pegar os arquivos e o shutil para descompactar
    if pega_e_descompacta == 'sim':

        print ('*****************************************************************')

        for arquivo in arquivos:

            url = url_base + arquivo + '.zip'
            arq = os.path.normpath(pasta_compactados+'/'+arquivo+'.zip')

            #urllib.request.urlretrieve (url,arquivo+'.zip')
            urllib.request.urlretrieve (url,arq)
            print ('<<',dt.now().isoformat(timespec='minutes'),'>> ','Pegou ' + arquivo + '.zip')

            #shutil.unpack_archive(arquivo+'.zip',pasta_compactados,'zip')
            shutil.unpack_archive(arq,pasta_compactados,'zip')
            print ('<<',dt.now().isoformat(timespec='minutes'),'>> ','Descompactou ' + arquivo)

        print ('*****************************************************************')

        ## caso o urlretrieve seja deprecado, usar o urlopen e gravar o arquivo de destino
        #for arquivo in arquivos:
        #    url = url_base + arquivo + '.zip'
        #    response = urllib.request.urlopen(url)
        #    f = open(arquivo+'.zip', 'wb')
        #    f.write(response.read())
        #    f.close()
        #    shutil.unpack_archive(arquivo+'.zip',pasta_compactados,'zip')

        ## OBS: esta lista deve ser adquida do banco acordos_conv, tabela conv_programas_a_pegar
        ## os cod_programas vem do banco com uma lista de tuplas (vírcula no final e entre parenteses)
        ## tive que criar uma lista para pegar só o valor do cod_programa

    #funções internas

    def data_banco (dia):
        '''
        DOCSTRING: coloca data no padrao dd/mm/aaaa para aaaa-mm-dd
        INPUT: string - data dd/mm/aaaa
        OUTPUT: date - data aaaa-mm-dd
        '''
        return datetime.date(int(dia[-4:]),int(dia[3:5]),int(dia[0:2]))

    def valor_banco (valor):
        '''
        DOCSTRING: coloca valor no padrao 999,99 para 999.99
        INPUT: string - valor com , como separador decimal
        OUTPUT: float - valor com . como separador decimal
        '''
        if valor == None or valor == '':
            valor = '0'

        return float(valor.replace(',','.'))

    ## gera lista com os programas de interesse da coordenação conforme registrado no na tabela Programa_Interesse

    #l_programas = db.session.query(Programa_Interesse.cod_programa).all()

    #lista_programas = [str(l[0]) for l in l_programas]

    ##################################################
    ##             pegar dados de programas         ##
    ##################################################
    if carrega_programas == 'sim':

        arq = 'siconv_programa'
        arq = os.path.normpath(pasta_compactados+'/'+arq+'.csv')

        print ('*****************************************************************')
        print ('<<',dt.now().isoformat(timespec='minutes'),'>> ','Carregando dados de programas...')

        # abre csv dos programas e gera a lista data_lines
        with open(arq, newline='',encoding = 'utf-8') as data:
            data_lines = csv.DictReader(data,delimiter=';')
            programas = []

        # gera a lista programas pegando somente os cujo código começa com 20501 (CNPq)
            for line in data_lines:

                if str(line['COD_PROGRAMA'][0:5]) == '20501':

                    programas.append([line['ID_PROGRAMA'],line['COD_PROGRAMA'],line['NOME_PROGRAMA']])

            # classifica a lista programas pelo id_programa e gera a lista programas_unic retirando as repetições
            programas.sort(key=lambda x: x[0])

            ## deletar linhas da tabela programa e carregá-la com programas sem repetições
            id_programa = ''
            programas_unic = []

            db.session.query(Programa).delete()
            db.session.commit()

            for programa in programas:
                if programa[0] != id_programa:
                    programas_unic.append(programa)
                    programa_gravar = Programa(ID_PROGRAMA   = programa[0],
                                               COD_PROGRAMA  = programa[1],
                                               NOME_PROGRAMA = programa[2])
                    db.session.add(programa_gravar)

                id_programa = programa[0]

            db.session.commit()

        if os.path.exists(arq):
            os.remove(arq + '.zip')
            os.remove(arq)

    ##################################################
    ##             pegar dados de propostas         ##
    ##################################################
    if carrega_propostas == 'sim':

        print ('<<',dt.now().isoformat(timespec='minutes'),'>> ','Carregando dados de propostas...')
        #lista dos identificadores de programas
        ids_programas = [id[0] for id in programas_unic]

        # abre csv do programa_proposta e gera a lista data_lines
        programa_proposta = []

        arq1 = 'siconv_programa_proposta'
        arq1 = os.path.normpath(pasta_compactados+'/'+arq1+'.csv')

        with open(arq1, newline='',encoding = 'utf-8') as data:
            data_lines = csv.DictReader(data,delimiter=';')

            id_programa_campo = data_lines.fieldnames[0]

            # gera a lista programa_proposta pegando somente os que tem id_programa na lista ids_programas
            for line in data_lines:
                if line[id_programa_campo] in ids_programas:
                    programa_proposta.append(line)

        # abre csv de propostas e gera a lista data_lines
        propostas = []

        arq2 = 'siconv_proposta'
        arq2 = os.path.normpath(pasta_compactados+'/'+arq2+'.csv')

        with open(arq2, newline='',encoding = 'utf-8') as data:
            data_lines = csv.DictReader(data,delimiter=';')

            # indica campos de interesse
            # tira lixo que vem no início do nome do primeiro campo

            campos_proposta = ['ID_PROPOSTA','UF_PROPONENTE','NM_PROPONENTE','OBJETO_PROPOSTA']

            id_proposta_campo = data_lines.fieldnames[0]

            # gera a lista propostas pegando somente os que coincidem com a programa_proposta,
            # incluindo o id_programa na primeira posição
            for line in data_lines:
                if line[id_proposta_campo] in [item['ID_PROPOSTA'] for item in programa_proposta]:
                    propostas.append([line[id_proposta_campo],line[campos_proposta[1]],line[campos_proposta[2]],line[campos_proposta[3]]])

            db.session.query(Proposta).delete()
            db.session.commit()

            for proposta in propostas:

                for item in programa_proposta:
                    if item['ID_PROPOSTA'] == proposta[0]:
                        proposta.insert(0,item[id_programa_campo])

                proposta_gravar = Proposta(ID_PROGRAMA      = proposta[0],
                                           ID_PROPOSTA      = proposta[1],
                                           UF_PROPONENTE    = proposta[2],
                                           NM_PROPONENTE    = proposta[3],
                                           OBJETO_PROPOSTA  = proposta[4])
                db.session.add(proposta_gravar)

            db.session.commit()

        if os.path.exists(arq1):
            os.remove(arq1 + '.zip')
            os.remove(arq1)

        if os.path.exists(arq2):
            os.remove(arq2 + '.zip')
            os.remove(arq2)

    ##################################################
    ##             pegar dados de convenios         ##
    ##################################################
    if carrega_convenios == 'sim':

        print ('<<',dt.now().isoformat(timespec='minutes'),'>> ','Carregando dados de convênios...')
        # abre csv de propostas e gera a lista data_lines
        arq = 'siconv_convenio'
        arq = os.path.normpath(pasta_compactados+'/'+arq+'.csv')

        with open(arq, newline='',encoding = 'utf-8') as data:
            data_lines = csv.DictReader(data,delimiter=';')

            convenios = []

            # PEGA NOME DO PRIMEIRO CAMPO, POIS COSTUAM VIR COM CARACTER ESTRANHO NO INÍCIO (?)

            nr_convenio_campo = data_lines.fieldnames[0]

            # grava convenios pegando somente os que coincidem com a programa_proposta

            db.session.query(Convenio).delete()
            db.session.commit()

            for line in data_lines:
                if line['ID_PROPOSTA'] in [item['ID_PROPOSTA'] for item in programa_proposta]:

                    convenios.append(line)

                    convenio_gravar = Convenio(NR_CONVENIO                   = line[nr_convenio_campo],
                                               ID_PROPOSTA                   = line['ID_PROPOSTA'],
                                               DIA                           = line['DIA'],
                                               MES                           = line['MES'],
                                               ANO                           = line['ANO'],
                                               DIA_ASSIN_CONV                = line['DIA_ASSIN_CONV'],
                                               SIT_CONVENIO                  = line['SIT_CONVENIO'],
                                               SUBSITUACAO_CONV              = line['SUBSITUACAO_CONV'],
                                               SITUACAO_PUBLICACAO           = line['SITUACAO_PUBLICACAO'],
                                               INSTRUMENTO_ATIVO             = line['INSTRUMENTO_ATIVO'],
                                               IND_OPERA_OBTV                = line['IND_OPERA_OBTV'],
                                               NR_PROCESSO                   = line['NR_PROCESSO'],
                                               UG_EMITENTE                   = line['UG_EMITENTE'],
                                               DIA_PUBL_CONV                 = line['DIA_PUBL_CONV'],
                                               DIA_INIC_VIGENC_CONV          = line['DIA_INIC_VIGENC_CONV'],
                                               DIA_FIM_VIGENC_CONV           = data_banco(line['DIA_FIM_VIGENC_CONV']),
                                               DIA_FIM_VIGENC_ORIGINAL_CONV  = line['DIA_FIM_VIGENC_ORIGINAL_CONV'],
                                               DIAS_PREST_CONTAS             = line['DIAS_PREST_CONTAS'],
                                               DIA_LIMITE_PREST_CONTAS       = line['DIA_LIMITE_PREST_CONTAS'],
                                               SITUACAO_CONTRATACAO          = line['SITUACAO_CONTRATACAO'],
                                               IND_ASSINADO                  = line['IND_ASSINADO'],
                                               MOTIVO_SUSPENSAO              = line['MOTIVO_SUSPENSAO'],
                                               IND_FOTO                      = line['IND_FOTO'],
                                               QTDE_CONVENIOS                = line['QTDE_CONVENIOS'],
                                               QTD_TA                        = line['QTD_TA'],
                                               QTD_PRORROGA                  = line['QTD_PRORROGA'],
                                               VL_GLOBAL_CONV                = valor_banco(line['VL_GLOBAL_CONV']),
                                               VL_REPASSE_CONV               = valor_banco(line['VL_REPASSE_CONV']),
                                               VL_CONTRAPARTIDA_CONV         = valor_banco(line['VL_CONTRAPARTIDA_CONV']),
                                               VL_EMPENHADO_CONV             = valor_banco(line['VL_EMPENHADO_CONV']),
                                               VL_DESEMBOLSADO_CONV          = valor_banco(line['VL_DESEMBOLSADO_CONV']),
                                               VL_SALDO_REMAN_TESOURO        = valor_banco(line['VL_SALDO_REMAN_TESOURO']),
                                               VL_SALDO_REMAN_CONVENENTE     = valor_banco(line['VL_SALDO_REMAN_CONVENENTE']),
                                               VL_RENDIMENTO_APLICACAO       = valor_banco(line['VL_RENDIMENTO_APLICACAO']),
                                               VL_INGRESSO_CONTRAPARTIDA     = valor_banco(line['VL_INGRESSO_CONTRAPARTIDA']),
                                               VL_SALDO_CONTA                = valor_banco(line['VL_SALDO_CONTA']),
                                               VALOR_GLOBAL_ORIGINAL_CONV    = valor_banco(line['VALOR_GLOBAL_ORIGINAL_CONV']))

                    db.session.add(convenio_gravar)

            db.session.commit()

        if os.path.exists(arq):
            os.remove(arq + '.zip')
            os.remove(arq)


    ##
    ##################################################
    ##             pegar dados de empenho           ##
    ##################################################
    if carrega_empenhos == 'sim':

        print ('<<',dt.now().isoformat(timespec='minutes'),'>> ','Carregando dados de empenhos...')
        # abre csv de empenho e gera a lista data_lines
        empenhos = []
        arq = 'siconv_empenho'
        arq = os.path.normpath(pasta_compactados+'/'+arq+'.csv')

        with open(arq, newline='',encoding = 'utf-8') as data:
            data_lines = csv.DictReader(data,delimiter=';')

            # PEGA NOME DO PRIMEIRO CAMPO, POIS COSTUAM VIR COM CARACTER ESTRANHO NO INÍCIO (?)

            id_empenho_campo = data_lines.fieldnames[0]

            #
            db.session.query(Empenho).delete()
            db.session.commit()

            # gera a lista empenhos pegando somente os que coincidem com convenios
            for line in data_lines:

                if line['NR_CONVENIO'] in [convenio[nr_convenio_campo] for convenio in convenios]:

                    empenhos.append(line)

                    emp = Empenho(ID_EMPENHO              = line[id_empenho_campo],
                                  NR_CONVENIO             = line['NR_CONVENIO'],
                                  NR_EMPENHO              = line['NR_EMPENHO'],
                                  TIPO_NOTA               = line['TIPO_NOTA'],
                                  DESC_TIPO_NOTA          = line['DESC_TIPO_NOTA'],
                                  DATA_EMISSAO            = data_banco(line['DATA_EMISSAO']),
                                  COD_SITUACAO_EMPENHO    = line['COD_SITUACAO_EMPENHO'],
                                  DESC_SITUACAO_EMPENHO   = line['DESC_SITUACAO_EMPENHO'],
                                  VALOR_EMPENHO           = valor_banco(line['VALOR_EMPENHO']))
                    db.session.add(emp)

            db.session.commit()

        if os.path.exists(arq):
            os.remove(arq + '.zip')
            os.remove(arq)

    ##
    ##################################################
    ##             pegar dados de desembolso        ##
    ##################################################
    if carrega_desembolsos == 'sim':

        print ('<<',dt.now().isoformat(timespec='minutes'),'>> ','Carregando dados de desembolso...')
        # abre csv do empenho_desembolso e gera a lista data_lines
        empenho_desembolso = []
        arq1 = 'siconv_empenho_desembolso'
        arq1 = os.path.normpath(pasta_compactados+'/'+arq1+'.csv')

        with open(arq1, newline='',encoding = 'utf-8') as data:
            data_lines = csv.DictReader(data,delimiter=';')

            # gera a lista empenho_desembolso pegando somente os que tem id_empenho na lista empenhos
            for line in data_lines:
                if line['ID_EMPENHO'] in [empenho[id_empenho_campo] for empenho in empenhos]:
                    empenho_desembolso.append(line)

        # abre csv de desembolso e gera a lista data_lines
        desembolsos = []
        arq2 = 'siconv_desembolso'
        arq2 = os.path.normpath(pasta_compactados+'/'+arq2+'.csv')

        #
        db.session.query(Desembolso).delete()
        db.session.commit()

        with open(arq2, newline='',encoding = 'utf-8') as data:
            data_lines = csv.DictReader(data,delimiter=';')

            id_desembolso_campo = data_lines.fieldnames[0]

            # gera a lista desembolsos pegando somente os que coincidem com a empenhos
            for line in data_lines:
                if line[id_desembolso_campo] in [desembolso[id_desembolso_campo] for desembolso in empenho_desembolso]:

                    for item in empenho_desembolso:
                        if item[id_desembolso_campo] == line[id_desembolso_campo]:
                            line['ID_EMPENHO'] = item['ID_EMPENHO']

                    des = Desembolso(ID_DESEMBOLSO           = line[id_desembolso_campo],
                                     NR_CONVENIO             = line['NR_CONVENIO'],
                                     DT_ULT_DESEMBOLSO       = data_banco(line['DT_ULT_DESEMBOLSO']),
                                     QTD_DIAS_SEM_DESEMBOLSO = line['QTD_DIAS_SEM_DESEMBOLSO'],
                                     DATA_DESEMBOLSO         = data_banco(line['DATA_DESEMBOLSO']),
                                     ANO_DESEMBOLSO          = line['ANO_DESEMBOLSO'],
                                     MES_DESEMBOLSO          = line['MES_DESEMBOLSO'],
                                     NR_SIAFI                = line['NR_SIAFI'],
                                     VL_DESEMBOLSADO         = valor_banco(line['VL_DESEMBOLSADO']),
                                     ID_EMPENHO              = line['ID_EMPENHO'])
                    db.session.add(des)

            db.session.commit()

        if os.path.exists(arq1):
            os.remove(arq1 + '.zip')
            os.remove(arq1)

        if os.path.exists(arq2):
            os.remove(arq2 + '.zip')
            os.remove(arq2)

    #
    ##################################################
    ##             pegar dados de pagamento         ##
    ##################################################
    if carrega_pagamentos == 'sim':

        print ('<<',dt.now().isoformat(timespec='minutes'),'>> ','Carregando dados de pagamentos...')
        # abre csv de pagamento e gera a lista data_lines
        pagamentos = []

        db.session.query(Pagamento).delete()
        db.session.commit()

        arq = 'siconv_pagamento'
        arq = os.path.normpath(pasta_compactados+'/'+arq+'.csv')

        with open(arq, newline='',encoding = 'utf-8') as data:
            data_lines = csv.DictReader(data,delimiter=';')

            i = 0
            # gera a lista pagamentos pegando somente os que coincidem com convenios
            for line in data_lines:

                if line['NR_CONVENIO'] in [convenio[nr_convenio_campo] for convenio in convenios]:

                    pag = Pagamento(NR_CONVENIO          = line['NR_CONVENIO'],
                                    IDENTIF_FORNECEDOR   = line['IDENTIF_FORNECEDOR'],
                                    NOME_FORNECEDOR      = line['NOME_FORNECEDOR'],
                                    VL_PAGO              = float(valor_banco(line['VL_PAGO'])))

                    db.session.add(pag)

            db.session.commit()

        if os.path.exists(arq):
            os.remove(arq + '.zip')
            os.remove(arq)

    ##
    ################################################################################################
    ##       ainda decidindo se vale a pena pegar dados de prorroga_oficio e termo_aditivo        ##
    ################################################################################################

    ##
    ############################################################
    ##             pegar data de referência SICONV           ##
    ##########################################################
    print ('<<',dt.now().isoformat(timespec='minutes'),'>> ','Carregando data dos dados...')
    # abre csv de com data da carga e gera a lista data_lines
    arq = 'data_carga_siconv'
    arq = os.path.normpath(pasta_compactados+'/'+arq+'.csv')

    with open(arq, newline='',encoding = 'utf-8') as data:

        data_lines = csv.DictReader(data,delimiter=';')

        nome_campo = data_lines.fieldnames[0]

        for line in data_lines:
            data_ref = dt.strptime(str(line[nome_campo][:10]), '%d/%m/%Y').date()

        db.session.query(RefSICONV).delete()
        db.session.commit()

        ref = RefSICONV(data_ref = data_ref)
        db.session.add(ref)
        db.session.commit()

    if os.path.exists(arq):
        os.remove(arq + '.zip')
        os.remove(arq)

    print ('<<',dt.now().isoformat(timespec='minutes'),'>> ','Carga SICONV finalizada!')
    print ('*****************************************************************')

# função que executa thread de carga dos dados SICONV
def thread_cargaSICONV():
    thr = Thread(target=cargaSICONV)
    thr.start()

## função que executa thread de carga dos dados PDCTR
#def thread_cargaPDCTR(arq):
#    thr = Thread(target=cargaPDCTR,args=(arq,))
#    thr.start()


@core.route('/')
def index():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta a tela inicial do aplicativo.                                                |
    +---------------------------------------------------------------------------------------+
    """
    sistema = db.session.query(Sistema).first()

    return render_template ('index.html',sistema=sistema)

@core.route('/info')
def info():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta a tela de informações do aplicativo.                                         |
    +---------------------------------------------------------------------------------------+
    """

    return render_template('info.html')

@core.route('/carregaPDCTR', methods=['GET', 'POST'])
@login_required
def carregaPDCTR():
    """
    +---------------------------------------------------------------------------------------+
    |Executa o procedimento de carga dos dados de folha de pagamento enviados via planilha  |
    |excel, pela COSAO: planilha COSAO.                                                     |
    |                                                                                       |
    |O módulo pede que seja informado o local onde a planilha COSAO foi salva e armazena os |
    |dados úteis ao aplicativo em tabela própria do banco de dados.                         |
    |                                                                                       |
    |Somente são gravados registros que não existam previamente no banco de dados, ou seja, |
    |caso a planilha COSAO tenha dados previamente carregados, não ocorre a duplicação.     |
    |                                                                                       |
    | *É muito importante que a planilha a ser carregada seja da folha de pagamento*        |
    | *imediatamente superior à da última carga de forma a não causar hiato na sequência*   |
    | *dos dados.*                                                                          |
    +---------------------------------------------------------------------------------------+

    .. warning:: A data de referência da tabela a ser carregada não pode ser distante mais do que um mês da data de referência da última carga!
    """

    form = ArquivoForm()

    if form.validate_on_submit():

        tempdirectory = tempfile.gettempdir()

        f = form.arquivo.data
        fname = secure_filename(f.filename)
        folha_pag = os.path.join(tempdirectory, fname)
        f.save(folha_pag)

        print ('***  ARQUIVO ***',folha_pag)
        cargaPDCTR(folha_pag)

        registra_log_auto(current_user.id,None,'car')

        return redirect(url_for('core.index'))

    data_ref = db.session.query(func.MAX(RefCargaPDCTR.data_ref)).first()

    return render_template('grab_file.html',form=form,data_ref=dt.strptime(data_ref[0],'%Y-%m-%d').date())

@core.route('/carregaSICONV', methods=['GET', 'POST'])
@login_required
def carregaSICONV():
    """
    +---------------------------------------------------------------------------------------+
    |Executa o procedimento de carga dos dados do SICONV.                                   |
    |                                                                                       |
    |Faz o dowload dos aquivos compactados diretamente do site do SICONV, descompacta e     |
    |carrega as respectivas tabelas do banco de dados.                                      |
    |                                                                                       |
    |Os dados anteriores são apagados e os novos inseridos nas tabelas.                     |
    |                                                                                       |
    | Para algumas tabelas, somente campos de interesse são carregados.                     |
    +---------------------------------------------------------------------------------------+
    """

   #síncrono
    thread_cargaSICONV()

   #assíncrono
   #cargaSICONV()

    registra_log_auto(current_user.id,None,'car')

    #return render_template('index.html')
    return redirect(url_for('core.index'))


#
### inserir dados sobre chamadas homologadas

@core.route("/<sei>/criar_chamada", methods=['GET', 'POST'])
@login_required
def cria_chamada(sei):
    """
    +---------------------------------------------------------------------------------------+
    |Permite registrar os dados de uma chamada homolada pelo CNPq.                          |
    |                                                                                       |
    |Recebe o número SEI como parâmetro.                                                    |
    +---------------------------------------------------------------------------------------+
    """

    form = ChamadaForm()

    if form.validate_on_submit():
        chamada = Chamadas( sei              = form.sei.data,
                            chamada          = form.chamada.data,
                            qtd_projetos     = form.qtd_projetos.data,
                            vl_total_chamada = float(form.vl_total_chamada.data.replace('.','').replace(',','.')),
                            doc_sei          = form.doc_sei.data,
                            obs              = form.obs.data)

        db.session.add(chamada)
        db.session.commit()

        registra_log_auto(current_user.id,None,'hom')

        sei = str(sei).split('_')[0]+'/'+str(sei).split('_')[1]
        conv = db.session.query(DadosSEI.nr_convenio).filter(DadosSEI.sei == sei).first()

        acordo_id = db.session.query(Acordo.id).filter(Acordo.sei == sei).first()

        flash('Chamada homologada registrada!','sucesso')
        if conv == None or conv == ':':
            return redirect(url_for('acordos.acordo_detalhe', acordo_id=acordo_id[0]))
        else:
            return redirect(url_for('convenios.convenio_detalhe', conv=conv[0]))
    #
    # traz a informação atual do registro SEI
    elif request.method == 'GET':
        form.sei.data = str(sei).split('_')[0]+'/'+str(sei).split('_')[1]

    return render_template('add_chamada.html', form=form)

#
### altera dados de chamada homologada

@core.route("/<int:id>/update_chamada", methods=['GET', 'POST'])
@login_required
def update_chamada(id):
    """
    +---------------------------------------------------------------------------------------+
    |Permite alterar os dados de uma chamada homolada pelo CNPq.                            |
    |                                                                                       |
    |Recebe o id da chamada como parâmetro.                                                 |
    +---------------------------------------------------------------------------------------+
    """

    chamada = Chamadas.query.get_or_404(id)

    form = ChamadaForm()

    if form.validate_on_submit():

        chamada.sei              = form.sei.data
        chamada.chamada          = form.chamada.data
        chamada.qtd_projetos     = form.qtd_projetos.data
        chamada.vl_total_chamada = float(form.vl_total_chamada.data.replace('.','').replace(',','.'))
        chamada.doc_sei          = form.doc_sei.data
        chamada.obs              = form.obs.data

        db.session.commit()

        registra_log_auto(current_user.id,None,'hom')

        conv = db.session.query(DadosSEI.nr_convenio).filter(DadosSEI.sei == form.sei.data).first()

        acordo_id = db.session.query(Acordo.id).filter(Acordo.sei == form.sei.data).first()

        flash('Chamada homologada atualizada!','sucesso')
        if conv == None or conv == ':':
            return redirect(url_for('acordos.acordo_detalhe', acordo_id=acordo_id[0]))
        else:
            return redirect(url_for('convenios.convenio_detalhe', conv=conv[0]))
    #
    # traz a informação atual do registro SEI
    elif request.method == 'GET':
        form.sei.data              = chamada.sei
        form.chamada.data          = chamada.chamada
        form.qtd_projetos.data     = chamada.qtd_projetos
        form.vl_total_chamada.data = locale.currency( chamada.vl_total_chamada, symbol=False, grouping = True )
        form.doc_sei.data          = chamada.doc_sei
        form.obs.data              = chamada.obs

    return render_template('add_chamada.html', form=form)

#
# função que executa carga de mensagens do SICONV
@core.route('/carregaMSG', methods=['GET', 'POST'])
@login_required
def carregaMSG():
    """
    +---------------------------------------------------------------------------------------+
    |Executa o procedimento de carga das mensagens emitidas pelo SICONV que indicam situa-  |
    |ções a verifica.                                                                       |
    |                                                                                       |
    |O módulo pede que seja informado o local onde a planilha de mensagens salva e armazena |
    |os em tabela própria do banco de dados.                                                |
    |                                                                                       |
    |Em cada carga, os dados anteriores são excluidos.                                      |
    +---------------------------------------------------------------------------------------+

    .. warning:: A data de referência é a data do dia da carga e não a data de criação da planilha de entrada!
    """
    #
    form = ArquivoForm()

    if form.validate_on_submit():

        tempdirectory = tempfile.gettempdir()

        f = form.arquivo.data
        fname = secure_filename(f.filename)
        msg_siconv = os.path.join(tempdirectory, fname)
        f.save(msg_siconv)

        print ('***  ARQUIVO ***',msg_siconv)

        print ('<<',dt.now().isoformat(timespec='minutes'),'>> ',' Carga de mensagens iniciada...')

        book = xlrd.open_workbook(filename=msg_siconv,ragged_rows=True)
        planilha = book.sheet_by_name('Plan1')

        print (f'Quantidade de registros na planilha: {planilha.nrows}')

        qtd_linhas = planilha.nrows

        # varre linha por linha da planilha de entrada e insere na tabela do banco

        print ('<<',dt.now().isoformat(timespec='minutes'),'>> ',' Gravando dados no banco...')

        reg_msg = []

        for i in range(qtd_linhas):

            linha_base = planilha.row_values(i, start_colx=0, end_colx=None)

            ano_mes_dia = (str(xlrd.xldate.xldate_as_datetime(linha_base[2], 0))[0:10])
            dia_mes_ano = ano_mes_dia[8:10] + '/' + ano_mes_dia[5:7] + '/' + ano_mes_dia[0:4]

            data_ref = datetime.datetime.strptime(str(dia_mes_ano), '%d/%m/%Y').date()

            msg_gravada = db.session.query(MSG_Siconv)\
                                    .filter(MSG_Siconv.nr_convenio == linha_base[0],
                                            MSG_Siconv.desc == linha_base[1]).first()

            if msg_gravada != None:
                sit = "v"
            else:
                sit = 'n'

            reg_msg.append([linha_base[0],linha_base[1],data_ref,sit])

        db.session.query(MSG_Siconv).delete()
        db.session.commit()

        for reg in reg_msg:

            msg = MSG_Siconv(nr_convenio = reg[0],
                             desc        = reg[1],
                             data_ref    = reg[2],
                             sit         = reg[3])

            db.session.add(msg)

        db.session.commit()

        registra_log_auto(current_user.id,None,'msg')

        print ('<<',dt.now().isoformat(timespec='minutes'),'>> ',' Carga de mensagens finalizada!')

        return redirect(url_for('core.index'))

    data_ref = ''

    return render_template('grab_file.html',form=form,data_ref=data_ref)
