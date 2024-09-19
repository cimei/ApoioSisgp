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

from datetime import datetime

from project.core.forms import  RefEnvioForm
from project import db, sched
from project.models import users, Log_Auto

from project.usuarios.views import registra_log_auto

from project.envio.views import envia_API


core = Blueprint("core",__name__)



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

    if instituicoes != None:

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

    return render_template ('index.html')

@core.route('/info')
def info():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta a tela de informações do aplicativo.                                         |
    +---------------------------------------------------------------------------------------+
    """

    return render_template('info.html')


@core.route('/ref_envios', methods=['GET', 'POST'])
@login_required

def ref_envios():
    """
    +---------------------------------------------------------------------------------------+
    |Define dada de referência para envio de planos                                         |
    +---------------------------------------------------------------------------------------+

    """
    
    referencia = os.environ.get('REF_ENVIOS')
        
    form = RefEnvioForm()
    
    if form.validate_on_submit():
        
        os.environ["REF_ENVIOS"] = form.data_ref.data.strftime('%Y-%m-%d')
        
        flash('Data de referência para envios atualizada para '+form.data_ref.data.strftime('%d/%m/%Y'),'sucesso')
        
        registra_log_auto(current_user.id,'* Data de referência para envios atualizada para '+form.data_ref.data.strftime('%d/%m/%Y'))
        
        return render_template('registra_ref_envios.html', form=form)
    
    if referencia:
        form.data_ref.data = datetime.strptime(referencia,'%Y-%m-%d').date()
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

