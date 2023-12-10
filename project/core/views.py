"""
.. topic:: Core (views)

    Este é o módulo inicial do sistema.

    Apresenta as telas de início, informação e procedimentos de carga de dados em lote.

.. topic:: Funções

    * PegaArquivo: Faz o upload do arquivo desejado

.. topic:: Ações relacionadas aos bolsistas

    * index: Primeiro template chamado na inicialização do sistema. Reprograma agendamentos.
    * inicio: Tela inicial do sistema
    * info: Tela de informações
    * CarregaUnidades: Carrega dados de unidade em lote
    * CarregaPessoas: Carrega dados de pessoa em lote
    * CarregaAtividades: Carrega daddos de atividaes e lote
    * apoio_i: Auxiliar para o menu em cascata de Funções de apoio
    * cargas_i: Auxiliar para o menu em cascata de Carga de dados
    * interno_i: Auxiliar para o menu em cascata de Funções internas

"""

# core/views.py

from flask import render_template,url_for,flash, redirect, request, Blueprint, send_from_directory
from flask_login import current_user, login_required

import os
from datetime import datetime as dt, date
import tempfile
from werkzeug.utils import secure_filename
import csv
import uuid

from sqlalchemy import distinct

from datetime import datetime

from project.core.forms import ArquivoForm, RefEnvioForm
from project import db, sched
from project.models import Unidades, Pessoas, Atividades, Planos_de_Trabalho,\
                           Pactos_de_Trabalho, cat_item_cat, unidade_ativ, users, catdom, Log_Auto

from project.usuarios.views import registra_log_auto

from project.envio.views import envia_API


core = Blueprint("core",__name__)


## função para abrir arquivo csv

def PegaArquivo(form):

    '''
        DOCSTRING: solicita arquivo do usuário e salva em diretório temporário para ser utilizado
        INPUT: formulário de entrada
        OUTPUT: arquivo de trabalho
    '''

    tempdirectory = tempfile.gettempdir()

    print ('### tempdir: ',tempdirectory )

    f = form.arquivo.data
    fname = secure_filename(f.filename)
    arquivo = os.path.join(tempdirectory, fname)
    f.save(arquivo)

    print ('***  ARQUIVO ***',arquivo)

    pasta = os.path.normpath(tempdirectory)

    if not os.path.exists(pasta):
        os.makedirs(os.path.normpath(pasta))

    arq = fname
    arq = os.path.normpath(pasta+'/'+arq)

    return arq

@core.route('/')
def index():
    """
    +---------------------------------------------------------------------------------------+
    |Ações quando o aplicativo é colocado no ar.                                            |
    |Inicia jobs de envio e de reenvio conforme ultimo registro de agendamento no log.      |
    +---------------------------------------------------------------------------------------+
    """

    # pegar unidades de todos os usuários para conferir a existência de jobs de envio para cada uma
    instituicoes = db.session.query(users.instituicaoId).filter(users.instituicaoId != None).all()
    instituicoes_lista = [i.instituicaoId for i in instituicoes]
   
    for i in instituicoes_lista:
    
        # pega últimos registros de agendamento no log
        log_agenda_ant_envio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                        .filter(Log_Auto.msg.like('* Agendamento de envio:'+'%'+str(i)))\
                                        .order_by(Log_Auto.id.desc())\
                                        .first()
        log_agenda_canc_envio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                            .filter(Log_Auto.msg.like('* Agendamento cancelado.'+'%'+str(i)))\
                                            .order_by(Log_Auto.id.desc())\
                                            .first()

        if log_agenda_ant_envio != None:

            if log_agenda_canc_envio != None and log_agenda_canc_envio.id > log_agenda_ant_envio.id:
                pass
            
            else:  #não há cancelamento de agendamento

                # pega dados do último agendamento e se certifica que não há job_envia_planos na memória
                periodicidade = (log_agenda_ant_envio.msg[24:].split())[0]
                hora_min      = (log_agenda_ant_envio.msg[24:].split())[2]
                inst          = i

                try:
                    job_existente = sched.get_job('job_envia_planos_'+str(inst))
                    if job_existente:
                        executa = False
                    else:
                        executa = True      
                except:
                    executa = True

                if executa:  # não achou nada na memória, coloca agenda job_envia_planos_<id da instituição>

                    print ('*** Agendamento inicial: '+ periodicidade + ' - ' + hora_min)

                    id = 'job_envia_planos_'+str(inst)
                    
                    tipo_envio = 'enviar'

                    if hora_min[1] == ':':
                        hora_min = '0'+ hora_min
                    s_hora   = hora_min[0:2]    
                    hora     = int(s_hora)
                    s_minuto = hora_min[3:5]
                    minuto   = int(s_minuto)

                    if periodicidade == 'Diária':
                        msg = ('*** Agendamento inicial de '+id+' como DIÁRIO, rodando de segunda a sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                        print(msg)
                        dia_semana = 'mon-fri'
                        try:
                            sched.add_job(trigger='cron', id=id, func=lambda:envia_API(tipo_envio, inst), day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                            sched.start()
                        except:
                            sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                    elif periodicidade == 'Semanal':
                        msg = ('*** Agendamento inicial de '+id+' como SEMANAL, rodando toda sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                        print(msg)
                        dia_semana = 'fri'
                        try:
                            sched.add_job(trigger='cron', id=id, func=lambda:envia_API(tipo_envio, inst), day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
                            sched.start()
                        except:
                            sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                    elif periodicidade == 'Mensal':
                        msg = ('*** Agendamento inicial de '+id+' com MENSAL,  rodando na primeira sexta-feira de cada mês, às '+s_hora+':'+s_minuto+' ***')
                        print(msg)
                        dia = '1st fri'
                        try:
                            sched.add_job(trigger='cron', id=id, func=lambda:envia_API(tipo_envio, inst), day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                            sched.start()
                        except:
                            sched.reschedule_job(id, trigger='cron', day=dia, hour=hora, minute=minuto)   

                    # agendanto também o job_envia_planos_novamente, caso necessário
                    log_agenda_ant_reenvio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                            .filter(Log_Auto.msg.like('* Agendamento de reenvio:'+'%'+str(i)))\
                                            .order_by(Log_Auto.id.desc())\
                                            .first()

                    if log_agenda_ant_reenvio and log_agenda_ant_reenvio.id > log_agenda_ant_envio.id:

                        id='job_envia_planos_novamente_'+str(inst)
                        
                        tipo_envio = 'reenviar'

                        hora += 1
                        s_hora = str(hora)
                        # minuto += 2
                        # s_minuto = str(minuto)
                            
                        if periodicidade == 'Diária':
                            msg = ('*** Agendamento inicial de '+id+' como DIÁRIO, rodando de segunda a sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                            print(msg)
                            dia_semana = 'mon-fri'
                            try:
                                sched.add_job(trigger='cron', id=id, func=lambda:envia_API(tipo_envio, inst), day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                            except:   
                                sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                        elif periodicidade == 'Semanal':
                            msg =  ('*** Agendamento inicial de '+id+' como SEMANAL, rodando toda sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                            print(msg)
                            dia_semana = 'fri'
                            try:
                                sched.add_job(trigger='cron', id=id, func=lambda:envia_API(tipo_envio, inst), day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
                            except:  
                                sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)    
                        elif periodicidade == 'Mensal':
                            msg =  ('*** Agendamento inicial de '+id+' como MENSAL, rodando na primeira sexta-feira de cada mês, às '+s_hora+':'+s_minuto+' ***')
                            print(msg)
                            dia = '1st fri'
                            try:
                                sched.add_job(trigger='cron', id=id, func=lambda:envia_API(tipo_envio, inst), day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                            except:
                                sched.reschedule_job(id, trigger='cron', day=dia, hour=hora, minute=minuto)

    
    return render_template ('index.html')



@core.route('/inicio')
def inicio():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta a tela inicial do aplicativo.                                                |
    +---------------------------------------------------------------------------------------+
    """

    return render_template ('index.html',sistema='Apoio SISGP')

@core.route('/info')
def info():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta a tela de informações do aplicativo.                                         |
    +---------------------------------------------------------------------------------------+
    """

    # o comandinho mágico que permite fazer o download de um arquivo
    send_from_directory('/app/project/static', 'Cartilha_MEAG_PGD1.pdf')

    unids = db.session.query(Unidades).count()

    unids_com_pg = db.session.query(distinct(Planos_de_Trabalho.unidadeId)).count()

    pes = db.session.query(Pessoas).count()

    pes_pacto = db.session.query(distinct(Pactos_de_Trabalho.pessoaId)).filter(Pactos_de_Trabalho.situacaoId == 405).count()

    ativs = db.session.query(Atividades).count()

    pts = db.session.query(Planos_de_Trabalho).count()

    pts_exec = db.session.query(Planos_de_Trabalho).filter(Planos_de_Trabalho.situacaoId == 309).count()

    pactos = db.session.query(Pactos_de_Trabalho).count()

    pactos_exec = db.session.query(Pactos_de_Trabalho).filter(Pactos_de_Trabalho.situacaoId == 405).count()

    ativos = db.session.query(users).filter(users.userAtivo == True).count()

    return render_template('info.html',unids = unids, unids_com_pg = unids_com_pg, pes = pes, 
                                         pes_pacto = pes_pacto, ativs = ativs,
                                         pts = pts, pts_exec = pts_exec, pactos = pactos, pactos_exec = pactos_exec,
                                         ativos = ativos)

@core.route('/carregaUnidades', methods=['GET', 'POST'])
def CarregaUnidades():
    """
    +---------------------------------------------------------------------------------------+
    |Executa o procedimento de carga dos dados de Unidades                                  |
    +---------------------------------------------------------------------------------------+

    """

    tipo = "unid"

    form = ArquivoForm()

    if form.validate_on_submit():

        if current_user.userAtivo:

            arq = PegaArquivo(form)

            print ('*****************************************************************')
            print ('<<',dt.now().strftime("%x %X"),'>> ','Carregando dados de Unidades...')
            print ('*****************************************************************')

            qtd = 0
            qtd_exist = 0
            qtdLinhas = 0

            # pega siglas das unidades que já existem no banco
            siglaExistente = db.session.query(Unidades.undSigla).all()

            # monta uma lista com as siglas das unidades já existentes
            l_siglaExistente = [s[0] for s in siglaExistente]

            # primeira rodada, grava registros mas mantém Pais nulos
            # abre csv, gera a lista data_lines e grava registros no banco de dados
            with open(arq, newline='',encoding = 'utf-8-sig') as data:

                data_lines = csv.DictReader(data,delimiter=';')     
                for linha in data_lines:

                    qtdLinhas += 1

                    # Se a unidade (sigla) já existir, atualiza os registros (sobreescreve)
                    # Campos com ** serão ignorados

                    if linha['undSigla'] in l_siglaExistente:

                        qtd_exist += 1

                        unid_exist = db.session.query(Unidades).filter(Unidades.undSigla == linha['undSigla']).first()

                        unid_exist.undSigla = linha['undSigla']

                        if linha['undDescricao'] != '**':
                            unid_exist.undDescricao = linha['undDescricao']
                            
                        if linha['unidadeIdPai'] != '**':
                            unid_exist.unidadeIdPai = None
                            
                        if linha['tipoUnidadeId'] != '**':
                            unid_exist.tipoUnidadeId = linha['tipoUnidadeId']
                            
                        if linha['situacaoUnidadeId'] != '**':
                            unid_exist.situacaoUnidadeId = linha['situacaoUnidadeId']
                            
                        if linha['ufId'] != '**':
                            unid_exist.ufId = linha['ufId']

                        if linha['undNivel'] != '**':
                            if linha['undNivel'] == 'NULL' or linha['undNivel'] == '':
                                unid_exist.undNivel = None
                            else:
                                unid_exist.undNivel = linha['undNivel']

                        if linha['tipoFuncaoUnidadeId'] != '**':
                            if linha['tipoFuncaoUnidadeId'] == 'NULL' or linha['tipoFuncaoUnidadeId'] == '':
                                unid_exist.tipoFuncaoUnidadeId = None
                            else:
                                unid_exist.tipoFuncaoUnidadeId = linha['tipoFuncaoUnidadeId']

                        if linha['Email'] != '**':
                            if linha['Email'] == 'NULL' or linha['Email'] == '':
                                unid_exist.Email = None
                            else:
                                unid_exist.Email = linha['Email']

                        if linha['undCodigoSIORG'] != '**':
                            if linha['undCodigoSIORG'] == 'NULL' or linha['undCodigoSIORG'] == '':
                                unid_exist.undCodigoSIORG = 0
                            else:
                                unid_exist.undCodigoSIORG = linha['undCodigoSIORG']    
                        
                        if linha['pessoaIdChefe'] != '**':
                            if linha['pessoaIdChefe'] == 'NULL' or linha['pessoaIdChefe'] == '' or linha['pessoaIdChefe'] == 0:
                                unid_exist.pessoaIdChefe = None
                            else:
                                if len(str(linha['pessoaIdChefe'])) == 11: # deve ser um cpf neste campo, pega então id correspondente
                                    id_cpf = db.session.query(Pessoas.pessoaId).filter(Pessoas.pesCPF == str(linha['pessoaIdChefe'])).first()
                                    if id_cpf:
                                        unid_exist.pessoaIdChefe = id_cpf.pessoaId
                                    else:
                                        unid_exist.pessoaIdChefe = None    
                                else:
                                    confirma_id = db.session.query(Pessoas).filter(Pessoas.pessoaId == int(linha['pessoaIdChefe'])).first()
                                    if confirma_id:
                                        unid_exist.pessoaIdChefe = int(linha['pessoaIdChefe'])
                                    else:
                                        unid_exist.pessoaIdChefe = None

                        if linha['pessoaIdChefeSubstituto'] != '**':
                            if linha['pessoaIdChefeSubstituto'] == 'NULL' or linha['pessoaIdChefeSubstituto'] == '' or linha['pessoaIdChefeSubstituto'] == 0: 
                                unid_exist.pessoaIdChefeSubstituto = None
                            else:
                                if len(str(linha['pessoaIdChefeSubstituto'])) == 11: # deve ser um cpf neste campo, pega então id correspondente
                                    id_cpf = db.session.query(Pessoas.pessoaId).filter(Pessoas.pesCPF == str(linha['pessoaIdChefeSubstituto'])).first()
                                    if id_cpf:
                                        unid_exist.pessoaIdChefeSubstituto = id_cpf.pessoaId
                                    else:
                                        unid_exist.pessoaIdChefeSubstituto = None
                                else:
                                    confirma_id = db.session.query(Pessoas).filter(Pessoas.pessoaId == int(linha['pessoaIdChefeSubstituto'])).first()
                                    if confirma_id:
                                        unid_exist.pessoaIdChefeSubstituto = int(linha['pessoaIdChefeSubstituto'])
                                    else:
                                        unid_exist.pessoaIdChefeSubstituto = None

                        db.session.commit()
            
                    # Não encontrando a unidade(sigla) no banco, cria um novo registro

                    elif linha['undSigla'] != '' and linha['undSigla'] != None : # sigla não pode vir vazia em um registro novo

                        pai = None  # pai, se houver, será carregado posteriormente
                        
                        if linha['undDescricao'] == 'NULL' or linha['undDescricao'] == '' or linha['undDescricao'] == '**':
                            descricao = 'N.I. - **'
                        else:
                            descricao = linha['undDescricao']
                            
                        if linha['tipoUnidadeId'] == 'NULL' or linha['tipoUnidadeId'] == '' or linha['tipoUnidadeId'] == '**':
                            tipounidade = 0
                        else:
                            tipounidade = linha['tipoUnidadeId']   
                            
                        if linha['situacaoUnidadeId'] == 'NULL' or linha['situacaoUnidadeId'] == '' or linha['situacaoUnidadeId'] == '**':
                            situunidade = 0
                        else:
                            situunidade = linha['situacaoUnidadeId']    
                            
                        if linha['ufId'] == 'NULL' or linha['ufId'] == '' or linha['ufId'] == '**':
                            ufId = 'xx'
                        else:
                            ufId = linha['ufId']    
                        
                        if linha['undNivel'] == 'NULL' or linha['undNivel'] == '' or linha['undNivel'] == '**':
                            niv = None
                        else:
                            niv = linha['undNivel']

                        if linha['tipoFuncaoUnidadeId'] == 'NULL' or linha['tipoFuncaoUnidadeId'] == '' or linha['tipoFuncaoUnidadeId'] == '**':
                            func = None
                        else:
                            func = linha['tipoFuncaoUnidadeId']

                        if linha['Email'] == 'NULL' or linha['Email'] == '' or linha['Email'] == '**':
                            email = None
                        else:
                            email = linha['Email']

                        if linha['undCodigoSIORG'] == 'NULL' or linha['undCodigoSIORG'] == '' or linha['undCodigoSIORG'] == '**':
                            siorg = 0
                        else:
                            siorg = linha['undCodigoSIORG']     

                        if linha['pessoaIdChefe'] == 'NULL' or linha['pessoaIdChefe'] == '' or linha['pessoaIdChefe'] == 0 or linha['pessoaIdChefe'] == '**':
                            chefe = None
                        else:
                            if len(str(linha['pessoaIdChefe'])) == 11: # deve ser um cpf neste campo, pega então id correspondente
                                id_cpf = db.session.query(Pessoas.pessoaId).filter(Pessoas.pesCPF == str(linha['pessoaIdChefe'])).first()
                                if id_cpf:
                                    chefe = id_cpf.pessoaId
                                else:
                                    chefe = None    
                            else:
                                confirma_id = db.session.query(Pessoas).filter(Pessoas.pessoaId == int(linha['pessoaIdChefe'])).first()
                                if confirma_id:
                                    chefe = int(linha['pessoaIdChefe'])
                                else:
                                    chefe = None    

                        if linha['pessoaIdChefeSubstituto'] == 'NULL' or linha['pessoaIdChefeSubstituto'] == '' or linha['pessoaIdChefeSubstituto'] == 0 or linha['pessoaIdChefeSubstituto'] == '**':
                            subs = None
                        else:
                            if len(str(linha['pessoaIdChefeSubstituto'])) == 11: # deve ser um cpf neste campo, pega então id correspondente
                                id_cpf = db.session.query(Pessoas.pessoaId).filter(Pessoas.pesCPF == str(linha['pessoaIdChefeSubstituto'])).first()
                                if id_cpf:
                                    subs = id_cpf.pessoaId
                                else:
                                    subs = None
                            else:
                                confirma_id = db.session.query(Pessoas).filter(Pessoas.pessoaId == int(linha['pessoaIdChefeSubstituto'])).first()
                                if confirma_id:
                                    subs = int(linha['pessoaIdChefeSubstituto'])
                                else:
                                    subs = None    
                                
                                  

                        unidade_gravar = Unidades(undSigla                = linha['undSigla'],
                                                  undDescricao            = descricao,
                                                  unidadeIdPai            = pai,
                                                  tipoUnidadeId           = tipounidade,
                                                  situacaoUnidadeId       = situunidade,
                                                  ufId                    = ufId,
                                                  undNivel                = niv,
                                                  tipoFuncaoUnidadeId     = func,
                                                  Email                   = email,
                                                  undCodigoSIORG          = siorg,
                                                  pessoaIdChefe           = chefe,
                                                  pessoaIdChefeSubstituto = subs)

                        db.session.add(unidade_gravar)

                        qtd += 1

                        db.session.commit()

            # segunda rodada, para atualizar as unidades pai de cada registro
            # abre novamente o csv, gera a lista data_lines e grava registros no banco de dados
            with open(arq, newline='',encoding = 'utf-8-sig') as data:            
                
                erro_pai = 0
                erro_pai_de_si_mema = 0
                data_lines = csv.DictReader(data,delimiter=';')
                for linha in data_lines: 

                    unid_exist = db.session.query(Unidades).filter(Unidades.undSigla == linha['undSigla']).first()

                    if unid_exist:

                        if linha['unidadeIdPai'] == 'NULL' or linha['unidadeIdPai'] == '':
                            unid_exist.unidadeIdPai = None
                        else:
                            if linha['unidadeIdPai'].isnumeric():
                                cod_pai = db.session.query(Unidades.unidadeId).filter(Unidades.unidadeId==linha['unidadeIdPai']).first()
                                if not cod_pai:
                                    erro_pai += 1
                                    unid_exist.unidadeIdPai = None
                                else:
                                    if linha['unidadeIdPai'] == unid_exist.unidadeId:
                                        erro_pai_de_si_mema += 1
                                        unid_exist.unidadeIdPai = None
                                    else:
                                        unid_exist.unidadeIdPai = linha['unidadeIdPai']
                            else:   
                                
                                if linha['unidadeIdPai'] != '**':
                                    
                                    cod_pai = db.session.query(Unidades.unidadeId).filter(Unidades.undSigla==linha['unidadeIdPai']).first()
                                    if not cod_pai:
                                        erro_pai += 1
                                        unid_exist.unidadeIdPai = None
                                    else:
                                        if linha['unidadeIdPai'] == unid_exist.undSigla:
                                            erro_pai_de_si_mema += 1
                                            unid_exist.unidadeIdPai = None
                                        else:
                                            unid_exist.unidadeIdPai = cod_pai.unidadeId

                db.session.commit()                          

                print ('*** ',qtdLinhas,'linha(s) no arquivo de entrada.')
                print ('*** ',qtd,'linha(s) inserida(s) na tabela unidade -> Unidades novas.')
                print ('*** ',qtd_exist,'linha(s) com sigla(s) já existente(s) -> Unidade(s) alterada(s).')
                print ('*****************************************************************')

                if erro_pai > 0:
                    flash (str(erro_pai)+' ocorrência(s) de unidade pai sem correspondência na tabela de Unidades.','erro')
                
                if erro_pai_de_si_mema > 0:
                    flash (str(erro_pai_de_si_mema)+' ocorrência(s) de unidade com tentativa de registro como próprio pai. O campo unidadeIdPai foi ignorado.','erro')

                if qtd_exist == 0:

                    flash('Executada carga de unidades no DBSISGP. ' +\
                        str(qtdLinhas) +' linha(s) no arquivo de entrada, ' +\
                        str(qtd) + ' linha(s) inserida(s).','sucesso')

                else:

                    flash('Executada carga de unidades no DBSISGP. ' +\
                        str(qtdLinhas) +' linha(s) no arquivo de entrada, ' +\
                        str(qtd) + ' registro(s) inserido(s) e ' +\
                        str(qtd_exist) + ' registro(s) preexistente(s) alterado(s).','perigo')

                registra_log_auto(current_user.id,'Carga em Unidades: ' + str(qtdLinhas) +' linha(s) no arquivo. ' +\
                                                 str(qtd) + ' registro(s) inserido(s). ' + str(qtd_exist) + ' registro(s) alterado(s).')

            if os.path.exists(arq):
                os.remove(arq)

            return redirect(url_for('unidades.lista_unidades',lista='ativas'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('unidades.lista_unidades',lista='ativas'))

    return render_template('grab_file.html',form=form, tipo = tipo)


@core.route('/carregaPessoas', methods=['GET', 'POST'])
@login_required

def CarregaPessoas():
    """
    +---------------------------------------------------------------------------------------+
    |Executa o procedimento de carga dos dados de Pessoas                                   |
    +---------------------------------------------------------------------------------------+

    """

    tipo = "pes"

    form = ArquivoForm()

    if form.validate_on_submit():

        if current_user.userAtivo:

            arq = PegaArquivo(form)

            print ('*****************************************************************')
            print ('<<',dt.now().strftime("%x %X"),'>> ','Carregando dados de Pessoas...')
            print ('*****************************************************************')

            qtd = 0
            qtd_exist = 0
            qtdLinhas = 0
            qtd_sem_unid = 0

            # pega cpfs das pessoas que já existem no banco
            cpfExistente = db.session.query(Pessoas.pesCPF).all()

            # cria uma lista com os cpfs das pessoas que já existem no banco
            l_cpfExistente = [c[0] for c in cpfExistente]

            # abre csv e gera a lista data_lines
            with open(arq, newline='',encoding = 'utf-8-sig') as data:
                data_lines = csv.DictReader(data,delimiter=';')

                for linha in data_lines:

                    qtdLinhas += 1

                    unid = db.session.query(Unidades.unidadeId).filter(Unidades.undSigla == linha['undSigla']).first()

                    if unid != None:

                        if linha['pesCPF'] in l_cpfExistente:

                            # Se o cpf já existir no banco, atualiza registro
                            # Caso receba **, ignora o campo

                            qtd_exist += 1

                            pessoa_exist = db.session.query(Pessoas).filter(Pessoas.pesCPF == linha['pesCPF']).first()

                            pessoa_exist.unidadeId = unid.unidadeId

                            if linha['pesNome'] != '**':
                                pessoa_exist.pesNome = linha['pesNome']

                            if linha['pesDataNascimento'] != '**':    
                                pessoa_exist.pesDataNascimento    = linha['pesDataNascimento']

                            if linha['pesMatriculaSiape'] != '**':
                                if linha['pesMatriculaSiape'] == 'NULL':
                                    pessoa_exist.pesMatriculaSiape = None
                                else:
                                    pessoa_exist.pesMatriculaSiape = linha['pesMatriculaSiape']

                            if linha['pesEmail'] != '**':
                                if linha['pesEmail'] == 'NULL':
                                    pessoa_exist.pesEmail = None
                                else:
                                    pessoa_exist.pesEmail = linha['pesEmail']

                            if linha['tipoFuncaoId'] != '**':
                                if linha['tipoFuncaoId'] == 'NULL' or linha['tipoFuncaoId'] == '':
                                    pessoa_exist.tipoFuncaoId = None
                                else:
                                    pessoa_exist.tipoFuncaoId  = linha['tipoFuncaoId']

                            if linha['cargaHoraria'] != '**':
                                if linha['cargaHoraria'] == 'NULL':
                                    pessoa_exist.cargaHoraria = None
                                else:
                                    pessoa_exist.cargaHoraria = linha['cargaHoraria']

                            if linha['situacaoPessoaId'] != '**':
                                if linha['situacaoPessoaId'] == 'NULL':
                                    pessoa_exist.situacaoPessoaId = None
                                else:
                                    pessoa_exist.situacaoPessoaId = linha['situacaoPessoaId']

                            if linha['tipoVinculoId'] != '**':
                                if linha['tipoVinculoId'] == 'NULL':
                                    pessoa_exist.tipoVinculoId = None
                                else:
                                    pessoa_exist.tipoVinculoId = linha['tipoVinculoId']

                        elif linha['pesCPF'] != '' and linha['pesCPF'] != None:  # o cpf não pode vir vazio em um registro novo

                            if linha['pesNome'] == '**':
                                nome = 'N.I. - **'
                            else:
                                nome = linha['pesNome']

                            if linha['pesDataNascimento'] == '**':    
                                nasc = datetime.strptime('2001-01-01','%Y-%m-%d').date()
                            else:
                                nasc = linha['pesDataNascimento']
                            
                            if linha['pesMatriculaSiape'] == 'NULL' or linha['pesMatriculaSiape'] == '**':
                                siape = None
                            else:
                                siape = linha['pesMatriculaSiape']

                            if linha['pesEmail'] == 'NULL' or linha['pesEmail'] == '**':
                                email = None
                            else:
                                email = linha['pesEmail']

                            if linha['tipoFuncaoId'] == '' or linha['tipoFuncaoId'] == 0 or linha['tipoFuncaoId'] == 'NULL' or linha['tipoFuncaoId'] == '**':
                                func = None
                            else:
                                func = linha['tipoFuncaoId']
                                
                            if linha['cargaHoraria'] == 'NULL' or linha['cargaHoraria'] == '**':
                                cargaHoraria = None
                            else:
                                cargaHoraria = linha['cargaHoraria']   

                            if linha['situacaoPessoaId'] == '' or linha['situacaoPessoaId'] == 0 or linha['situacaoPessoaId'] == 'NULL' or linha['situacaoPessoaId'] == '**':
                                sit = None
                            else:
                                sit = linha['situacaoPessoaId']

                            if linha['tipoVinculoId'] == '' or linha['tipoVinculoId'] == 0 or linha['tipoVinculoId'] == 'NULL' or linha['tipoVinculoId'] == '**':
                                vinc = None
                            else:
                                vinc = linha['tipoVinculoId']   

                            pessoa_gravar = Pessoas(pesCPF            = linha['pesCPF'],
                                                    unidadeId         = unid.unidadeId,
                                                    pesNome           = nome,
                                                    pesDataNascimento = nasc,
                                                    pesMatriculaSiape = siape,
                                                    pesEmail          = email,
                                                    tipoFuncaoId      = func,
                                                    cargaHoraria      = cargaHoraria,
                                                    situacaoPessoaId  = sit,
                                                    tipoVinculoId     = vinc)

                            db.session.add(pessoa_gravar)
                                
                            qtd += 1

                        db.session.commit()

                    else:
                        qtd_sem_unid += 1

                print ('*** ',qtdLinhas,'linha(s) no arquivo de entrada.')
                print ('*** ',qtd,'linha(s) inserida(s) na tabela pessoa.')
                print ('*** ',qtd_exist,'registro(s) preexistente(s) alterado(s).')
                print ('*** ',qtd_sem_unid,'não inserida(s) por não encontrar undSigla correspondente na tabela Unidades.')
                print ('***********************************************************************************')

                if qtd_exist == 0:
                    if qtd_sem_unid == 0:
                        flash('Executada carga de Pessoas no DBSISGP: ' +\
                            str(qtdLinhas) +' linha(s) no arquivo de entrada, ' +\
                            str(qtd) +' linha(s) inserida(s).','sucesso')
                    else:
                        flash('Executada carga de Pessoas no DBSISGP: ' +\
                            str(qtdLinhas) +' linha(s) no arquivo de entrada, ' +\
                            str(qtd) +' linha(s) inserida(s). ' +\
                            str(qtd_sem_unid) +' pessoa(s) não inserida(s) por não encontrar undSigla correspondente na tabela Unidades.','sucesso')    
                else:
                    if qtd_sem_unid == 0:
                        flash('Executada carga de Pessoas no DBSISGP: ' +\
                            str(qtdLinhas) +' linha(s) no arquivo de entrada, ' +\
                            str(qtd) +' registro(s) inserido(s) e ' +\
                            str(qtd_exist) +' registros alterado(s).','perigo')
                    else:
                        flash('Executada carga de Pessoas no DBSISGP: ' +\
                            str(qtdLinhas) +' linha(s) no arquivo de entrada, ' +\
                            str(qtd) +' registro(s) inserido(s) e ' +\
                            str(qtd_exist) +' registros alterado(s). ' +\
                            str(qtd_sem_unid) +' pessoa(s) não inserida(s) por não encontrar undSigla correspondente na tabela Unidades.','perigo')    
            
                registra_log_auto(current_user.id,'Carga em Pessoas: ' + str(qtdLinhas) +' linha(s) no arquivo. ' +\
                                                 str(qtd) + ' registro(s) inserido(s). ' + str(qtd_exist) + ' registro(s) alterado(s).')


            if os.path.exists(arq):
                os.remove(arq)        

            return redirect(url_for('pessoas.lista_pessoas'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('pessoas.lista_pessoas'))

    return render_template('grab_file.html',form=form, tipo = tipo)


@core.route('/carregaAtividades', methods=['GET', 'POST'])
@login_required

def CarregaAtividades():
    """
    +---------------------------------------------------------------------------------------+
    |Executa o procedimento de carga dos dados de Atividades                                |
    +---------------------------------------------------------------------------------------+

    """

    tipo = "ati"

    form = ArquivoForm()

    if form.validate_on_submit():

        if current_user.userAtivo:

            arq = PegaArquivo(form)

            print ('*****************************************************************')
            print ('<<',dt.now().strftime("%x %X"),'>> ','Carregando dados de Atividades...')
            print ('*****************************************************************')

            qtd = 0
            qtd_atu = 0
            qtd_inval = 0
            qtdLinhas = 0
            qtd_sem_unid = 0

            # abre csv e gera a lista data_lines
            with open(arq, newline='',encoding = 'utf-8-sig') as data:
                data_lines = csv.DictReader(data,delimiter=';')

                for linha in data_lines:

                    qtdLinhas += 1

                    # a atividade contendo um título é gravada no banco    
                    if linha['titulo'] != '' and linha['titulo'] != None:
                        
                        if linha['calc_temp'] == 'Por atividade':
                            calculoTempoId = 202
                        else:
                            calculoTempoId = 201

                        if linha['permite_remoto'].lower() == 'sim':
                            remoto = True
                        else:
                            remoto = False

                        # se o título não existe no banco, grava, se sim, atualiza
                        verifica_ativ = db.session.query(Atividades).filter(Atividades.titulo==linha['titulo']).first()    

                        if not verifica_ativ:    
                            ativ_gravar = Atividades(itemCatalogoId        = uuid.uuid4(),
                                                    titulo                = linha['titulo'],
                                                    calculoTempoId        = calculoTempoId,
                                                    permiteRemoto         = remoto,
                                                    tempoPresencial       = linha['tempo_presencial'].replace(',','.'),
                                                    tempoRemoto           = linha['tempo_remoto'].replace(',','.'),
                                                    descricao             = linha['descricao'],
                                                    complexidade          = linha['complexidade'],
                                                    definicaoComplexidade = linha['def_complexidade'],
                                                    entregasEsperadas     = linha['entrega'])

                            db.session.add(ativ_gravar)
                                
                            qtd += 1

                        else:
                            verifica_ativ.calculoTempoId        = calculoTempoId
                            verifica_ativ.permiteRemoto         = remoto
                            verifica_ativ.tempoPresencial       = linha['tempo_presencial'].replace(',','.')
                            verifica_ativ.tempoRemoto           = linha['tempo_remoto'].replace(',','.')
                            verifica_ativ.descricao             = linha['descricao']
                            verifica_ativ.complexidade          = linha['complexidade']
                            verifica_ativ.definicaoComplexidade = linha['def_complexidade']
                            verifica_ativ.entregasEsperadas     = linha['entrega']

                            qtd_atu += 1

                        db.session.commit()

                        # verifica se a unidade que acompanha a atividade nova existe no banco
                        unid = db.session.query(Unidades.unidadeId).filter(Unidades.undSigla == linha['undSigla']).first()

                        if unid != None:
                            # faz o primeiro relacionamento atividade-unidade
                            unid_ativ = db.session.query(unidade_ativ).filter(unidade_ativ.unidadeId == unid.unidadeId).first()                    
                            if not unid_ativ:
                                rel1 = unidade_ativ(catalogoId = uuid.uuid4(),
                                                    unidadeId  = unid.unidadeId)
                                db.session.add(rel1)                    
                                db.session.commit()
                                catalogoId = rel1.catalogoId
                            else:
                                catalogoId = unid_ativ.catalogoId

                            # faz o segundo relacionamento atividade-unidade   
                            rel2 = cat_item_cat(catalogoItemCatalogoId = uuid.uuid4(),
                                                catalogoId             = catalogoId,
                                                itemCatalogoId         = ativ_gravar.itemCatalogoId)
                            db.session.add(rel2)                    
                            db.session.commit()     
                        else:
                            # adiciona 1 no contador de registros sem unidade válida
                            qtd_sem_unid += 1

                    else:
                        qtd_inval += 1

                print ('*** ',qtdLinhas,'linhas no arquivo de entrada.')
                print ('*** ',qtd_inval,'linhas no arquivo são inválidas (sem título).')
                print ('*** ',qtd_atu,'linhas atualizadas na tabela ItemCatalogo.')
                print ('*** ',qtd,'linhas inseridas na tabela ItemCatalogo.')
                print ('*** ',qtd_sem_unid,'das linhas inseridas não foram associadas a uma Unidade.')
                print ('***********************************************************************************')

                flash('Executada carga de Atividades no DBSISGP. ' +\
                        str(qtdLinhas) +' linha(s) no arquivo de entrada. ' +\
                        str(qtd_inval) +' linha(s) inválida(s) (sem título). ' +\
                        str(qtd_atu) +' linha(s) atualizada(s). ' +\
                        str(qtd) +' linha(s) efetivamente inserida(s). ' +\
                        str(qtd_sem_unid) +' da(s) atividade(s) inserida(s) não foram associadas a uma Unidade.','sucesso')

            
                registra_log_auto(current_user.id,'Carga em Atividades: ' + str(qtdLinhas) +' linhas no arquivo. ' +\
                                                   str(qtd) + ' registros inseridos.')

            if os.path.exists(arq):
                os.remove(arq)        

            return redirect(url_for('atividades.lista_atividades',lista='ativas'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('atividades.lista_atividades',lista='ativas'))

    return render_template('grab_file.html',form=form, tipo = tipo)


@core.route('/ref_envios', methods=['GET', 'POST'])
@login_required

def ref_envios():
    """
    +---------------------------------------------------------------------------------------+
    |Define dada de referência para envio de planos                                         |
    +---------------------------------------------------------------------------------------+

    """
    
    referencia = db.session.query(catdom).filter(catdom.classificacao == 'DataBaseEnvioPlanos').first()
        
    form = RefEnvioForm()
    
    if form.validate_on_submit():
        
        if referencia:
            referencia.descricao = form.data_ref.data.strftime('%Y-%m-%d')
        else:
            referencia = catdom(catalogoDominioId = 55555,
                                classificacao     = 'DataBaseEnvioPlanos',
                                descricao         = form.data_ref.data.strftime('%Y-%m-%d'),
                                ativo             = True)
            db.session.add(referencia)    
        
        db.session.commit()
        
        flash('Data de referência para envios atualizada para '+form.data_ref.data.strftime('%d/%m/%Y'),'sucesso')
        
        registra_log_auto(current_user.id,'* Data de referência para envios atualizada para '+form.data_ref.data.strftime('%d/%m/%Y'))
        
        return render_template('registra_ref_envios.html', form=form)
    
    if referencia:
        form.data_ref.data = datetime.strptime(referencia.descricao,'%Y-%m-%d').date()
    else:
        form.data_ref.data = None   
        flash('Ainda não foi definida uma data de referência para envio de planos!','perigo') 
    
    return render_template('registra_ref_envios.html', form=form)
        
        


## renderiza tela inicial do apoio

@core.route('/apoio_i')
@login_required

def apoio_i():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta tela inicial do apoio.                                                       |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    
    return render_template('apoio.html') 

## renderiza tela inicial de cargas

@core.route('/cargas_i')
@login_required

def cargas_i():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta tela inicial de cargas.                                                      |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    
    return render_template('cargas.html') 

## renderiza tela inicial funções internas

@core.route('/interno_i')
@login_required

def interno_i():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta tela inicial de funções internas.                                            |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    
    return render_template('interno.html') 

