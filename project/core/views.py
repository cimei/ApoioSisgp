"""
.. topic:: Core (views)

    Este é o módulo inicial do sistema.

    Apresenta as telas de início, informação e procedimentos de carda de dados em lote.

.. topic:: Ações relacionadas aos bolsistas

    * index: Tela inicial
    * info: Tela de informações
    * CarregaUnidades: Carrega dados de unidade em lote
    * CarregaPessoas: Carrega dados de pessoa em lote
    * CarregaAtividades: Carreg daddos de atividaes e lote

"""

# core/views.py

from flask import render_template,url_for,flash, redirect, request, Blueprint, send_from_directory
from flask_login import current_user, login_required

import os
from datetime import datetime as dt
import tempfile
from werkzeug.utils import secure_filename
import csv
import uuid

from sqlalchemy import distinct

from project.core.forms import ArquivoForm
from project import db, sched
from project.models import Unidades, Pessoas, Atividades, Planos_de_Trabalho,\
                           Pactos_de_Trabalho, cat_item_cat, unidade_ativ, users, jobs, Log_Auto

from project.usuarios.views import registra_log_auto

from project.envio.views import envia_planos, envia_planos_novamente


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
    
    # pega últimos registros de agendamento no log
    log_agenda_ant_envio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                     .filter(Log_Auto.msg.like('* Agendamento de envio:'+'%') )\
                                     .order_by(Log_Auto.id.desc())\
                                     .first()
    log_agenda_canc_envio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                        .filter(Log_Auto.msg == '* Agendamento cancelado.')\
                                        .order_by(Log_Auto.id.desc())\
                                        .first()

    if log_agenda_ant_envio:

        if log_agenda_canc_envio and log_agenda_canc_envio.id > log_agenda_ant_envio.id:
            return render_template ('index.html',sistema='Apoio SISGP')
        
        else:  #não há cancelamento de agendamento

            # pega dados do último agendamento e se certifica que não há job_envia_planos na memória
            periodicidade = (log_agenda_ant_envio.msg[24:].split())[0]
            hora_min      = (log_agenda_ant_envio.msg[24:].split())[2]

            try:
                job_existente = sched.get_job('job_envia_planos')
                if job_existente:
                    executa = False
                else:
                    executa = True      
            except:
                executa = True

            if executa:  # não achou nada na memória, coloca agenda job_envia_planos

                print ('*** Agendamento inicial: '+ periodicidade + ' - ' + hora_min)

                id = 'job_envia_planos'

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
                        sched.add_job(trigger='cron', id=id, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                        sched.start()
                    except:
                        sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                elif periodicidade == 'Semanal':
                    msg = ('*** Agendamento inicial de '+id+' como SEMANAL, rodando toda sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                    print(msg)
                    dia_semana = 'fri'
                    try:
                        sched.add_job(trigger='cron', id=id, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
                        sched.start()
                    except:
                        sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                elif periodicidade == 'Mensal':
                    msg = ('*** Agendamento inicial de '+id+' com MENSAL,  rodando na primeira sexta-feira de cada mês, às '+s_hora+':'+s_minuto+' ***')
                    print(msg)
                    dia = '1st fri'
                    try:
                        sched.add_job(trigger='cron', id=id, func=envia_planos, day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                        sched.start()
                    except:
                        sched.reschedule_job(id, trigger='cron', day=dia, hour=hora, minute=minuto)   

                # agendanto também o job_envia_planos_novamente, caso necessário
                log_agenda_ant_reenvio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                        .filter(Log_Auto.msg.like('* Agendamento de reenvio:'+'%') )\
                                        .order_by(Log_Auto.id.desc())\
                                        .first()

                if log_agenda_ant_reenvio and log_agenda_ant_reenvio.id > log_agenda_ant_envio.id:

                    id='job_envia_planos_novamente'

                    # hora += 1
                    # s_hora = str(hora)
                    minuto += 2
                    s_minuto = str(minuto)
                        
                    if periodicidade == 'Diária':
                        msg = ('*** Agendamento inicial de '+id+' como DIÁRIO, rodando de segunda a sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                        print(msg)
                        dia_semana = 'mon-fri'
                        try:
                            sched.add_job(trigger='cron', id=id, func=envia_planos_novamente, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                        except:   
                            sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                    elif periodicidade == 'Semanal':
                        msg =  ('*** Agendamento inicial de '+id+' como SEMANAL, rodando toda sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                        print(msg)
                        dia_semana = 'fri'
                        try:
                            sched.add_job(trigger='cron', id=id, func=envia_planos_novamente, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
                        except:  
                            sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)    
                    elif periodicidade == 'Mensal':
                        msg =  ('*** Agendamento inicial de '+id+' como MENSAL, rodando na primeira sexta-feira de cada mês, às '+s_hora+':'+s_minuto+' ***')
                        print(msg)
                        dia = '1st fri'
                        try:
                            sched.add_job(trigger='cron', id=id, func=envia_planos_novamente, day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                        except:
                            sched.reschedule_job(id, trigger='cron', day=dia, hour=hora, minute=minuto)

    
    return render_template ('index.html',sistema='Apoio SISGP')



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

                    # se a unidade (sigla) já existir, atualiza os registros (sobreescreve)
                    if linha['undSigla'] in l_siglaExistente:

                        qtd_exist += 1

                        unid_exist = db.session.query(Unidades).filter(Unidades.undSigla == linha['undSigla']).first()

                        unid_exist.undSigla          = linha['undSigla']
                        unid_exist.undDescricao      = linha['undDescricao']
                        unid_exist.unidadeIdPai      = None
                        unid_exist.tipoUnidadeId     = linha['tipoUnidadeId']
                        unid_exist.situacaoUnidadeId = linha['situacaoUnidadeId']
                        unid_exist.ufId              = linha['ufId']

                        if linha['undNivel'] == 'NULL' or linha['undNivel'] == '':
                            unid_exist.undNivel = None
                        else:
                            unid_exist.undNivel = linha['undNivel']

                        if linha['tipoFuncaoUnidadeId'] == 'NULL' or linha['tipoFuncaoUnidadeId'] == '':
                            unid_exist.tipoFuncaoUnidadeId = None
                        else:
                            unid_exist.tipoFuncaoUnidadeId = linha['tipoFuncaoUnidadeId']

                        if linha['Email'] == 'NULL' or linha['Email'] == '':
                            unid_exist.Email = None
                        else:
                            unid_exist.Email = linha['Email']

                        if linha['undCodigoSIORG'] == 'NULL' or linha['undCodigoSIORG'] == '':
                            unid_exist.undCodigoSIORG = 0
                        else:
                            unid_exist.undCodigoSIORG = linha['undCodigoSIORG']    

                        if linha['pessoaIdChefe'] == 'NULL' or linha['pessoaIdChefe'] == '':
                            unid_exist.pessoaIdChefe = None
                        else:
                            unid_exist.pessoaIdChefe = linha['pessoaIdChefe']

                        if linha['pessoaIdChefeSubstituto'] == 'NULL' or linha['pessoaIdChefeSubstituto'] == '': 
                            unid_exist.pessoaIdChefeSubstituto = None
                        else:
                            unid_exist.pessoaIdChefeSubstituto = linha['pessoaIdChefeSubstituto']

                        db.session.commit()
            
                    # não encontrando a unidade(sigla) no banco, cria um novo registro
                    elif linha['undSigla'] != '' and linha['undSigla'] != None :

                        pai = None
                        
                        if linha['undNivel'] == 'NULL' or linha['undNivel'] == '':
                            niv = None
                        else:
                            niv = linha['undNivel']

                        if linha['tipoFuncaoUnidadeId'] == 'NULL' or linha['tipoFuncaoUnidadeId'] == '':
                            func = None
                        else:
                            func = linha['tipoFuncaoUnidadeId']

                        if linha['Email'] == 'NULL' or linha['Email'] == '':
                            email = None
                        else:
                            email = linha['Email']

                        if linha['undCodigoSIORG'] == 'NULL' or linha['undCodigoSIORG'] == '':
                            siorg = 0
                        else:
                            siorg = linha['undCodigoSIORG']     

                        if linha['pessoaIdChefe'] == 'NULL' or linha['pessoaIdChefe'] == '' or linha['pessoaIdChefe'] == 0:
                            chefe = None
                        else:
                            chefe = linha['pessoaIdChefe']

                        if linha['pessoaIdChefeSubstituto'] == 'NULL' or linha['pessoaIdChefeSubstituto'] == '' or linha['pessoaIdChefeSubstituto'] == 0:
                            subs = None
                        else:
                            subs = linha['pessoaIdChefeSubstituto']    

                        unidade_gravar = Unidades(undSigla                = linha['undSigla'],
                                                  undDescricao            = linha['undDescricao'],
                                                  unidadeIdPai            = pai,
                                                  tipoUnidadeId           = linha['tipoUnidadeId'],
                                                  situacaoUnidadeId       = linha['situacaoUnidadeId'],
                                                  ufId                    = linha['ufId'],
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
                                    flash('Id informado como unidade pai inexistente no banco de dados: '+ linha['unidadeIdPai'],'erro' )
                                    unid_exist.unidadeIdPai = None
                                else:    
                                    unid_exist.unidadeIdPai = linha['unidadeIdPai']
                            else:    
                                cod_pai = db.session.query(Unidades.unidadeId).filter(Unidades.undSigla==linha['unidadeIdPai']).first()
                                if not cod_pai:
                                    flash('Sigla informada como unidade pai inexistente no banco de dados: '+ linha['unidadeIdPai'],'erro' )
                                    unid_exist.unidadeIdPai = None
                                else:    
                                    unid_exist.unidadeIdPai = cod_pai.unidadeId 
                db.session.commit()                          

                print ('*** ',qtdLinhas,'linhas no arquivo de entrada.')
                print ('*** ',qtd,'linhas inseridas na tabela unidade -> Unidades novas.')
                print ('*** ',qtd_exist,'linhas com siglas já existentes -> Unidades alteradas.')
                print ('*****************************************************************')

                if qtd_exist == 0:

                    flash('Executada carga de unidades no DBSISGP. ' +\
                        str(qtdLinhas) +' linhas no arquivo de entrada, ' +\
                        str(qtd) + ' linhas efetivamente inseridas.','sucesso')

                else:

                    flash('Executada carga de unidades no DBSISGP. ' +\
                        str(qtdLinhas) +' linhas no arquivo de entrada, ' +\
                        str(qtd) + ' registros efetivamente inseridos e ' +\
                        str(qtd_exist) + ' registros preexistentes alterados.','perigo')

                registra_log_auto(current_user.id,'Carga em Unidades: ' + str(qtdLinhas) +' linhas no arquivo. ' +\
                                                 str(qtd) + ' registros inseridos. ' + str(qtd_exist) + ' registros alterados.')

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

                            qtd_exist += 1

                            pessoa_exist = db.session.query(Pessoas).filter(Pessoas.pesCPF == linha['pesCPF']).first()

                            pessoa_exist.pesNome = linha['pesNome']
                            pessoa_exist.pesDataNascimento    = linha['pesDataNascimento']

                            if linha['pesMatriculaSiape'] == 'NULL':
                                pessoa_exist.pesMatriculaSiape = None
                            else:
                                pessoa_exist.pesMatriculaSiape = linha['pesMatriculaSiape']

                            if linha['pesEmail'] == 'NULL':
                                pessoa_exist.pesEmail = None
                            else:
                                pessoa_exist.pesEmail = linha['pesEmail']

                            pessoa_exist.unidadeId = unid.unidadeId

                            if linha['tipoFuncaoId'] == 'NULL' or linha['tipoFuncaoId'] == '':
                                pessoa_exist.tipoFuncaoId = None
                            else:
                                pessoa_exist.tipoFuncaoId  = linha['tipoFuncaoId']

                            if linha['cargaHoraria'] == 'NULL':
                                pessoa_exist.cargaHoraria = None
                            else:
                                pessoa_exist.cargaHoraria = linha['cargaHoraria']

                            if linha['situacaoPessoaId'] == 'NULL':
                                pessoa_exist.situacaoPessoaId = None
                            else:
                                pessoa_exist.situacaoPessoaId = linha['situacaoPessoaId']

                            if linha['tipoVinculoId'] == 'NULL':
                                pessoa_exist.tipoVinculoId = None
                            else:
                                pessoa_exist.tipoVinculoId = linha['tipoVinculoId']

                        elif linha['pesCPF'] != '' and linha['pesCPF'] != None:

                            if linha['pesMatriculaSiape'] == 'NULL':
                                siape = None
                            else:
                                siape = linha['pesMatriculaSiape']

                            if linha['pesEmail'] == 'NULL':
                                email = None
                            else:
                                email = linha['pesEmail']

                            if linha['tipoFuncaoId'] == '' or linha['tipoFuncaoId'] == 0 or linha['tipoFuncaoId'] == 'NULL':
                                func = None
                            else:
                                func = linha['tipoFuncaoId']

                            if linha['situacaoPessoaId'] == '' or linha['situacaoPessoaId'] == 0 or linha['situacaoPessoaId'] == 'NULL':
                                sit = None
                            else:
                                sit = linha['situacaoPessoaId']

                            if linha['tipoVinculoId'] == '' or linha['tipoVinculoId'] == 0 or linha['tipoVinculoId'] == 'NULL':
                                vinc = None
                            else:
                                vinc = linha['tipoVinculoId']   

                            pessoa_gravar = Pessoas(pesNome           = linha['pesNome'],
                                                    pesCPF            = linha['pesCPF'],
                                                    pesDataNascimento = linha['pesDataNascimento'],
                                                    pesMatriculaSiape = siape,
                                                    pesEmail          = email,
                                                    unidadeId         = unid.unidadeId,
                                                    tipoFuncaoId      = func,
                                                    cargaHoraria      = linha['cargaHoraria'],
                                                    situacaoPessoaId  = sit,
                                                    tipoVinculoId     = vinc)

                            db.session.add(pessoa_gravar)
                                
                            qtd += 1

                        db.session.commit()

                    else:
                        qtd_sem_unid += 1

                print ('*** ',qtdLinhas,'linhas no arquivo de entrada.')
                print ('*** ',qtd,'linhas inseridas na tabela pessoa.')
                print ('*** ',qtd_exist,'registros preexistentes alterados.')
                print ('*** ',qtd_sem_unid,'não inseridas por não encontrar undSigla correspondente na tabela Unidades.')
                print ('***********************************************************************************')

                if qtd_exist == 0:

                    flash('Executada carga de Pessoas no DBSISGP. ' +\
                        str(qtdLinhas) +' linha(s) no arquivo de entrada, ' +\
                        str(qtd) +' linha(s) efetivamente inserida(s). ' +\
                        str(qtd_sem_unid) +' pessoa(s) não inserida(s) por não encontrar undSigla correspondente na tabela Unidades.','sucesso')

                else:

                    flash('Executada carga de Pessoas no DBSISGP. ' +\
                        str(qtdLinhas) +' linha(s) no arquivo de entrada, ' +\
                        str(qtd) +' registro(s) efetivamente inserido(s) e ' +\
                        str(qtd_exist) +' registros alterado(s). ' +\
                        str(qtd_sem_unid) +' pessoa(s) não inserida(s) por não encontrar undSigla correspondente na tabela Unidades.','perigo')
            
                registra_log_auto(current_user.id,'Carga em Pessoas: ' + str(qtdLinhas) +' linhas no arquivo. ' +\
                                                 str(qtd) + ' registros inseridos. ' + str(qtd_exist) + ' registros alterados.')


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

## renderiza tela com template base do gov

@core.route('/base')
@login_required

def base():
    
    return render_template('template_gov.html') 
