"""
.. topic:: Envio (views)

    Procedimentos relacionados ao envio de dados (planos e atividades) ao orgão superior.


.. topic:: Funções

    * planos_enviados_LOG: Identifica no LOG os planos já enviados
    * planos_n_enviados_LOG: Identifica, conferindo no LOG, planos nunca 
    * envia_API: Faz o envio, ou reenvio, de planos em lote



.. topic:: Ações relacionadas ao envio

    * lista_a_enviar: Lista planos que estão aptos ao envio 
    * lista_enviados: Lista planos que já foram enviados 
    * enviar_planos: Envia, ou reenvia, planos em lote nas telas de listas (desativado)
    * enviar_um_plano: Envia, ou reenvia, um plano individual
    * lista_enviados: Lista planos que já foram enviados
    * agenda_envio: Agendamento de envios
    * envio_i: Auxiliar para montagem do menu em cascata


"""

# views.py na pasta envio

from flask import render_template,url_for,flash, redirect, request, Blueprint, abort
from flask_login import current_user, login_required

from sqlalchemy.sql import label
from sqlalchemy import func, literal

from project import db, sched
from project.models import Unidades, VW_Pactos, VW_Atividades_Pactos, users, Log_Auto

from project.usuarios.views import registra_log_auto                           

from project.envio.forms import AgendamentoForm

import requests
import json
from datetime import datetime, timedelta, date
import os
import re

envio = Blueprint('envio',__name__, template_folder='templates')


# funções

def pega_data_ref():
    
    ref_envios   = os.environ.get('REF_ENVIOS')
    
    if ref_envios != None and ref_envios != '':
        return (datetime.strptime(ref_envios,'%Y-%m-%d').date())
    else:
        return (date.today())
    

# pega token de acesso à API de envio de dados
def pega_token(inst): 

    #pega credenciais do usuário logado
    credenciais = db.session.query(users.user_api,
                                   users.senha_api)\
                            .filter(users.instituicaoId == inst,
                                    users.user_api != None,
                                    users.senha_api != None,
                                    users.user_api != '',
                                    users.senha_api != '')\
                            .first()              
    
    if credenciais == None:
        user_api   = os.getenv('APIPGDME_AUTH_USER')
        senha_api  = os.getenv('APIPGDME_AUTH_PASSWORD')
    else:
        user_api   = credenciais.user_api
        senha_api  = credenciais.senha_api

    if user_api == None:
        user_api  = ''
        print ('** Não há user_api configurado para acesso à API. ***')
    if senha_api == None:    
        senha_api = ''
        print ('** Não há senha_api configurada para acesso à API. ***')
    
    string = 'grant_type=&username='+user_api+'&password='+senha_api+'&scope=&client_id=&client_secret='

    headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/json"}
    
    if os.getenv('APIPGDME_URL')[-1] == '/': 
        api_url_login = os.getenv('APIPGDME_URL') + 'auth/jwt/login'
    else:
        api_url_login = os.getenv('APIPGDME_URL') + '/auth/jwt/login'

    response = requests.post(api_url_login, headers=headers ,data=json.dumps(string))

    rlogin_json = response.json()
        
    try:
        token = rlogin_json['access_token']
        # tipo =  rlogin_json['token_type'] 
    except:
         retorno_API = rlogin_json['detail']  
         print ('** RETORNO DA API: ',retorno_API)
         print ('** API URL login: ', api_url_login)
         print ('** User API: ', user_api)
         print ('** Senha API: ', senha_api)
         abort(403)  
        
    return(token)


# função que gera lista com ids dos planos que já foram enviados previamente, consultando o log
def planos_enviados_LOG():
    
    data_ref = pega_data_ref()
    
    ## Pegar usuarios que são da mesma instituição do usuario logado
    # quando a função é chamada pelo agendamento, current_user está vazio, pega então o usuário que fez o últinmo agendamento 
    if current_user == None or current_user.get_id() == None:
        user_agenda = db.session.query(Log_Auto.user_id)\
                                .filter(Log_Auto.msg.like('* Agendamento de envio:%'))\
                                .order_by(Log_Auto.id.desc())\
                                .first()
        id_user = user_agenda.user_id
        id_inst = db.session.query(users.instituicaoId).filter(users.id == id_user).first()
        usuarios = db.session.query(users.id).filter(users.instituicaoId == id_inst.instituicaoId).all()
        lista_users = [u.id for u in usuarios]
    elif current_user.instituicaoId != None:
        usuarios = db.session.query(users.id).filter(users.instituicaoId == current_user.instituicaoId).all()
        lista_users = [u.id for u in usuarios]
    else:
        abort(401)
    ##

    # pesquisa log de users da instituição do usuário
    enviados_log = db.session.query(Log_Auto.msg)\
                            .filter(Log_Auto.msg.like(' * PACTO ENVIADO:'+'%'),
                                    Log_Auto.data_hora >= data_ref,
                                    Log_Auto.user_id.in_(lista_users))\
                            .distinct()  
    
    enviados = [e.msg[18:54].split()[0] for e in enviados_log]
   
    # quebrando enviados em listas com 1000 ou menos elementos
    listas = []
    tamanho = len(enviados)
    if tamanho > 1000:
        qtd_listas = tamanho // 10
        resto = tamanho % 10
        if resto > 0:
            qtd_listas += 1
        listas = [enviados[i:i+1000] for i in range(0,len(enviados),1000)] 
    else:
        listas.append(enviados)    
    
    # print ('*** A lista de enviados tem: ',len(enviados),' items. Será quebrada em : ',len(listas),' sub-listas.')      

    return listas        
   

# função que gera lista de planos que nunca foram enviados, consultando o LOG
def planos_n_enviados_LOG(): 
    
    data_ref = pega_data_ref()
    
    # Pegar instituição do usuário logado e definir filtro na busca por pactos
    # quando a função é chamada pelo agendamento, current_user está vazio, pega então o usuário que fez o últinmo agendamento 
    if current_user == None or current_user.get_id() == None:
        user_agenda = db.session.query(Log_Auto.user_id)\
                                .filter(Log_Auto.msg.like('* Agendamento de envio:%'))\
                                .order_by(Log_Auto.id.desc())\
                                .first()
        id_user = users.query.filter_by(id = user_agenda.user_id).first()
        instituicao = db.session.query(Unidades.Sigla)\
                                .filter(Unidades.IdUnidade == id_user.instituicaoId)\
                                .first()
    elif current_user.instituicaoId != None:
        instituicao = db.session.query(Unidades.Sigla)\
                                .filter(Unidades.IdUnidade == current_user.instituicaoId)\
                                .first()
    else:
        abort(401)                            
  
    limite_unid = '%' + instituicao.Sigla + '%'

    # todos os planos executados e com horas homologadas > 0 de unidades de uma institução específica
    # planos_avaliados = db.session.query(VW_Pactos.id_pacto)\
    #                             .filter(VW_Pactos.desc_situacao_pacto == 'Executado',
    #                                     VW_Pactos.horas_homologadas > 0,
    #                                     VW_Pactos.data_fim >= data_ref,
    #                                     VW_Pactos.sigla_unidade_exercicio.like(limite_unid))\
    #                             .all()   
    
    # todos os planos de vw_pacto que terminam depois da data de referência
    planos_avaliados = db.session.query(VW_Pactos.id_pacto)\
                                .filter(VW_Pactos.data_fim >= data_ref)\
                                .all()                                                                  


    ## Pegar usuarios que são da mesma instituição do usuario logado
    # quando a função é chamada pelo agendamento, current_user está vazio, pega então o usuário que fez o últinmo agendamento 
    if current_user == None or current_user.get_id() == None:
        user_agenda = db.session.query(Log_Auto.user_id)\
                                .filter(Log_Auto.msg.like('* Agendamento de envio:%'))\
                                .order_by(Log_Auto.id.desc())\
                                .first()
        id_user = user_agenda.user_id
        id_inst = db.session.query(users.instituicaoId).filter(users.id == id_user).first()
        usuarios = db.session.query(users.id).filter(users.instituicaoId == id_inst.instituicaoId).all()
        lista_users = [u.id for u in usuarios]
    elif current_user.instituicaoId != None:
        usuarios = db.session.query(users.id).filter(users.instituicaoId == current_user.instituicaoId).all()
        lista_users = [u.id for u in usuarios]
    else:
        abort(401)
    ##

    # identifica envios na tabela do log para users da instituição selecionada
    enviados_log = db.session.query(Log_Auto.msg)\
                            .filter(Log_Auto.msg.like(' * PACTO ENVIADO:'+'%'),
                                    Log_Auto.data_hora >= data_ref,
                                    Log_Auto.user_id.in_(lista_users))\
                            .distinct()
    
    log = [e.msg[18:54] for e in enviados_log]

    n_enviados = []
    
    # adiciona em uma lista planos que NÃO constam do log como enviados
    for pa in planos_avaliados:

        if pa.id_pacto not in log:
            n_enviados.append(pa.id_pacto)   

    # quebrando n_enviados em listas com 1000 ou menos elementos
    listas = []
    tamanho = len(n_enviados)
    if tamanho > 1000:
        qtd_listas = tamanho // 10
        resto = tamanho % 10
        if resto > 0:
            qtd_listas += 1
        listas = [n_enviados[i:i+1000] for i in range(0,len(n_enviados),1000)] 
    else:
        listas.append(n_enviados)    
    
    # print ('*** A lista de não enviados tem: ',len(n_enviados),' items. Será quebrada em : ',len(listas),' sub-listas.')      
    
    return listas        
    
    
# função para envio e reenvio de planos para a API
def envia_API(tipo,inst):  

    limita_horario = True
    
    if tipo == 'enviar':
      
        n_enviados = planos_n_enviados_LOG()

        print('**')
        print('*** Iniciando o envio de planos conforme agendamento ***')    
        
        # quando o envio for feito pelo agendamento, current_user está vazio, pega então o usuário que fez o últinmo agendamento 
        if current_user == None or current_user.get_id() == None:
            user_agenda = db.session.query(Log_Auto.user_id)\
                                    .filter(Log_Auto.msg.like('* Agendamento de envio:%'))\
                                    .order_by(Log_Auto.id.desc())\
                                    .first()
            id_user = user_agenda.user_id
            modo = 'agenda'
        else:
            id_user = current_user.id 
            modo = 'manual'

        registra_log_auto(id_user, '* Início do envio de Planos para API.')       
        
        if n_enviados != 'erro_credenciais':   
            
            token = pega_token(inst) 
            print('** Peguei o primeiro token para enviar planos **') 
            # 55 minutos para pegar novo token
            hora_token = datetime.now() + timedelta(seconds=(60*55))  

            # indicadores de planos enviados com sucesso e de quantidade total de planos a serem enviados 
            sucesso = 0
            qtd_planos = 0
            
            for l in n_enviados:
            
                planos = db.session.query(VW_Pactos).filter(VW_Pactos.id_pacto.in_(l)).all()
                qtd_planos += len(planos)

                # para cada plano, monta o dados do dicionário 
                for p in planos:
                    
                    # parar o envio caso extrapole o horário limite
                    if limita_horario:
                        if datetime.now().time() > datetime.strptime('06:00:00','%H:%M:%S').time() and \
                        datetime.now().time() < datetime.strptime('20:00:00','%H:%M:%S').time():
                            break
                    
                    # se estorar 55 minutos, pega novo token
                    if datetime.now() > hora_token:
                        token = pega_token(inst)   
                        print('** Peguei novo token **') 
                        hora_token = datetime.now() + timedelta(seconds=(60*55)) 
                        print ('** Hora para pegar próximo token: ',hora_token)

                    dic_envio = {}

                    dic_envio['cod_plano']              = p.id_pacto
                    dic_envio['situacao']               = p.situacao
                    dic_envio['matricula_siape']        = int(p.matricula_siape)
                    dic_envio['cpf']                    = p.cpf
                    dic_envio['nome_participante']      = p.nome_participante
                    dic_envio['cod_unidade_exercicio']  = p.cod_unidade_exercicio
                    dic_envio['nome_unidade_exercicio'] = p.nome_unidade_exercicio
                    dic_envio['modalidade_execucao']    = p.modalidade_execucao
                    dic_envio['carga_horaria_semanal']  = p.carga_horaria_semanal
                    dic_envio['data_inicio']            = p.data_inicio.strftime('%Y-%m-%d')
                    dic_envio['data_fim']               = p.data_fim.strftime('%Y-%m-%d')
                    dic_envio['carga_horaria_total']    = p.carga_horaria_total
                    dic_envio['data_interrupcao']       = p.data_interrupcao
                    dic_envio['entregue_no_prazo']      = p.entregue_no_prazo
                    dic_envio['horas_homologadas']      = p.horas_homologadas
                    dic_envio['atividades']             = []

                    # pega as atividades de cada plano
                    ativs = db.session.query(VW_Atividades_Pactos)\
                                    .filter(VW_Atividades_Pactos.id_pacto == p.id_pacto)\
                                    .all()

                    # para cada atividade, monta o resto do dicionário (key 'atividades')
                    for a in ativs:
                        
                        if a.tempo_presencial_estimado != None and a.tempo_presencial_programado != None and \
                           a.tempo_teletrabalho_estimado != None and a.tempo_teletrabalho_programado != None and \
                           (a.tempo_presencial_executado > 0 or a.tempo_teletrabalho_executado > 0):

                            dic_envio['atividades'].append({'id_atividade': a.id_produto,
                                                            'nome_grupo_atividade': a.nome_grupo_atividade,
                                                            'nome_atividade': a.nome_atividade,
                                                            'faixa_complexidade': a.faixa_complexidade,
                                                            'parametros_complexidade': a.parametros_complexidade,
                                                            'tempo_presencial_estimado': a.tempo_presencial_estimado,
                                                            'tempo_presencial_programado': a.tempo_presencial_programado,
                                                            'tempo_presencial_executado': a.tempo_presencial_executado,
                                                            'tempo_teletrabalho_estimado': a.tempo_teletrabalho_estimado,
                                                            'tempo_teletrabalho_programado': a.tempo_teletrabalho_programado,
                                                            'tempo_teletrabalho_executado': a.tempo_teletrabalho_executado,
                                                            'entrega_esperada': a.entrega_esperada,
                                                            'qtde_entregas': a.qtde_entregas,
                                                            'qtde_entregas_efetivas': a.qtde_entregas_efetivas,
                                                            'avaliacao': a.avaliacao,
                                                            'data_avaliacao': a.data_avaliacao,
                                                            'justificativa': a.justificativa}) 

                    # prepara headers do put
                    plano_id = p.id_pacto
                    headers = {'Content-Type': "application/json", 'Accept': "application/json", 'Authorization': 'Bearer {}'.format(token)}
                    
                    # faz o put na API via dumps json do dicionário    
                    r_put = requests.put(os.getenv('APIPGDME_URL') + '/plano_trabalho/'+plano_id, headers= headers, data=json.dumps(dic_envio))

                    # para cada put com sucesso (status_code < 400) acumula 1 no sucesso e registra envio no log
                    if r_put.ok:
                        sucesso += 1
                        registra_log_auto(id_user, ' * PACTO ENVIADO: ' + str(plano_id)+' de '+p.nome_participante)
                    else:
                        retorno_API = re.search(r'\bmsg[\W|w]+[\w+\s]+',r_put.text) 

                        if retorno_API:
                            retorno_API_msg = retorno_API.group()[6:]
                            print ('*** Erro envio do Plano: '+str(plano_id)+' de '+p.nome_participante+' - '+str(retorno_API_msg))
                            registra_log_auto(id_user, '* Retorno API sobre falha  no  envio do Plano: '+str(plano_id)+' de '+p.nome_participante+' - '+str(retorno_API_msg))
                        else:
                            retorno_API_msg = 'Sem retorno da API.'
                            print ('*** Erro envio do Plano: '+str(plano_id)+' de '+p.nome_participante+' - '+str(retorno_API_msg))
                            print ('*** Texto API: ',str(r_put.text),type(r_put.text))
                            registra_log_auto(id_user, '* Retorno API sobre falha  no  envio do Plano: '+str(plano_id)+' de '+p.nome_participante+' - '+str(retorno_API_msg))
                            if str(r_put.text) == '{"detail":"Unauthorized"}':
                                abort(401)

                # parar o envio caso extrapole o horário limite
                if limita_horario:
                    if datetime.now().time() > datetime.strptime('06:00:00','%H:%M:%S').time() and \
                    datetime.now().time() < datetime.strptime('20:00:00','%H:%M:%S').time():
                        print ('** Intervalo de tempo para o envio de planos esgotado para hoje **')
                        registra_log_auto(id_user, '* Intervalo de tempo para o envio de planos esgotado para hoje.') 
                        break
                
            # quando o envio for feito pelo agendamento, personaliza msg no log com dados do agendamento

            if modo == 'agenda':
                msg = 'Envio programado. ' 
            else:
                msg = ''    

            if sucesso == qtd_planos:
                if sucesso == 0:
                    registra_log_auto(id_user, '*' + msg + 'Não havia planos para enviar...')
                else:    
                    registra_log_auto(id_user, '*' + msg + str(qtd_planos) + ' Plano(s) enviado(s) com sucesso.')
                if modo == 'manual':
                    flash(str(qtd_planos) + ' Planos enviados com sucesso','sucesso') # todos os planos enviados com sucesso
            else:
                registra_log_auto(id_user, '*' + msg + 'Na tentativa de envio de ' + str(qtd_planos) + ' Planos, ' + str(sucesso) + ' foram enviados.')
                if modo == 'manual':
                    flash('Houve problema no envio dos Planos: Dos ' + str(qtd_planos) + ' Planos, ' + str(sucesso) + ' foram enviados.','erro') # alguma coisa deu errado 

        else:
            return 'erro_credenciais'

        registra_log_auto(id_user, '* Término do envio de Planos para API.')    

        print('*** Finalizando o envio de planos conforme agendamento ***')
        print('**')
    
    else:

        enviados = planos_enviados_LOG()
            
        print('**')
        print('*** Iniciando o reenvio de planos conforme agendamento ***')    

        # quando o envio for feito pelo agendamento, current_user está vazio, pega então o usuário que fez o últinmo agendamento 
        if current_user == None or current_user.get_id() == None:
            user_agenda = db.session.query(Log_Auto.user_id)\
                                    .filter(Log_Auto.msg.like('* Agendamento de reenvio:%'))\
                                    .order_by(Log_Auto.id.desc())\
                                    .first()
            id_user = user_agenda.user_id
            modo = 'agenda'
        else:
            id_user = current_user.id 
            modo = 'manual'

        registra_log_auto(id_user, '* Início do reenvio de Planos para API.') 

        if enviados != 'erro_credenciais':       
            
            token = pega_token(inst)   
            # 55 minutos para pegar novo token
            hora_token = datetime.now() + timedelta(seconds=(60*55))  

            # indicadores de planos enviados com sucesso e de quantidade total de planos a serem enviados 
            sucesso = 0
            qtd_planos = 0

            for l in enviados:
                
                planos = db.session.query(VW_Pactos).filter(VW_Pactos.id_pacto.in_(l)).all()
                qtd_planos += len(planos)

                # para cada plano, monta o dados do dicionário 
                for p in planos:
                    
                    # parar o envio caso extrapole o horário limite
                    if limita_horario:
                        if datetime.now().time() > datetime.strptime('06:00:00','%H:%M:%S').time() and \
                        datetime.now().time() < datetime.strptime('20:00:00','%H:%M:%S').time():
                            break
                    
                    # se estourar 55 minutos, pega novo token
                    if datetime.now() > hora_token:
                        token = pega_token(inst)
                        hora_token = datetime.now() + timedelta(seconds=(60*55))

                    dic_envio = {}

                    dic_envio['cod_plano']              = p.id_pacto
                    dic_envio['situacao']               = p.situacao
                    dic_envio['matricula_siape']        = int(p.matricula_siape)
                    dic_envio['cpf']                    = p.cpf
                    dic_envio['nome_participante']      = p.nome_participante
                    dic_envio['cod_unidade_exercicio']  = p.cod_unidade_exercicio
                    dic_envio['nome_unidade_exercicio'] = p.nome_unidade_exercicio
                    dic_envio['modalidade_execucao']    = p.modalidade_execucao
                    dic_envio['carga_horaria_semanal']  = p.carga_horaria_semanal
                    dic_envio['data_inicio']            = p.data_inicio.strftime('%Y-%m-%d')
                    dic_envio['data_fim']               = p.data_fim.strftime('%Y-%m-%d')
                    dic_envio['carga_horaria_total']    = p.carga_horaria_total
                    dic_envio['data_interrupcao']       = p.data_interrupcao
                    dic_envio['entregue_no_prazo']      = p.entregue_no_prazo
                    dic_envio['horas_homologadas']      = p.horas_homologadas
                    dic_envio['atividades']             = []

                    # pega as atividades de cada plano
                    ativs = db.session.query(VW_Atividades_Pactos)\
                                    .filter(VW_Atividades_Pactos.id_pacto == p.id_pacto)\
                                    .all()

                    # para cada atividade, monta o resto do dicionário (key 'atividades')
                    for a in ativs:
                        
                        if a.tempo_presencial_estimado != None and a.tempo_presencial_programado != None and \
                           a.tempo_teletrabalho_estimado != None and a.tempo_teletrabalho_programado != None and \
                           (a.tempo_presencial_executado > 0 or a.tempo_teletrabalho_executado > 0):

                            dic_envio['atividades'].append({'id_atividade': a.id_produto,
                                                            'nome_grupo_atividade': a.nome_grupo_atividade,
                                                            'nome_atividade': a.nome_atividade,
                                                            'faixa_complexidade': a.faixa_complexidade,
                                                            'parametros_complexidade': a.parametros_complexidade,
                                                            'tempo_presencial_estimado': a.tempo_presencial_estimado,
                                                            'tempo_presencial_programado': a.tempo_presencial_programado,
                                                            'tempo_presencial_executado': a.tempo_presencial_executado,
                                                            'tempo_teletrabalho_estimado': a.tempo_teletrabalho_estimado,
                                                            'tempo_teletrabalho_programado': a.tempo_teletrabalho_programado,
                                                            'tempo_teletrabalho_executado': a.tempo_teletrabalho_executado,
                                                            'entrega_esperada': a.entrega_esperada,
                                                            'qtde_entregas': a.qtde_entregas,
                                                            'qtde_entregas_efetivas': a.qtde_entregas_efetivas,
                                                            'avaliacao': a.avaliacao,
                                                            'data_avaliacao': a.data_avaliacao,
                                                            'justificativa': a.justificativa}) 

                    # prepara headers do put
                    plano_id = p.id_pacto
                    headers = {'Content-Type': "application/json", 'Accept': "application/json", 'Authorization': 'Bearer {}'.format(token)}
                    
                    # faz o put na API via dumps json do dicionário    
                    r_put = requests.put(os.getenv('APIPGDME_URL') + '/plano_trabalho/'+plano_id, headers= headers, data=json.dumps(dic_envio))

                    # para cada put com sucesso (status_code < 400) acumula 1 no sucesso e registra envio no log
                    if r_put.ok:
                        sucesso += 1
                        registra_log_auto(id_user, ' * PACTO REENVIADO: '+str(plano_id)+' de '+p.nome_participante)
                    else:
                        retorno_API = re.search(r'\bmsg[\W|w]+[\w+\s]+',r_put.text) 

                        if retorno_API:
                            retorno_API_msg = retorno_API.group()[6:]
                            print ('*** Erro reenvio do Plano: '+str(plano_id)+' de '+p.nome_participante+' - '+str(retorno_API_msg))
                            registra_log_auto(id_user, '* Retorno API sobre falha no reenvio do Plano: '+str(plano_id)+' de '+p.nome_participante+' - '+str(retorno_API_msg))
                        else:
                            retorno_API_msg = 'Sem retorno da API.'
                            print ('*** Erro reenvio do Plano: '+str(plano_id)+' de '+p.nome_participante+' - '+str(retorno_API_msg))
                            print ('*** Texto API: ',str(r_put.text))
                            registra_log_auto(id_user, '* Retorno API sobre falha no reenvio do Plano: '+str(plano_id)+' de '+p.nome_participante+' - '+str(retorno_API_msg))
                            if str(r_put.text) == '{"detail":"Unauthorized"}':
                                abort(401)
            
                # parar o envio caso extrapole o horário limite
                if limita_horario:
                    if datetime.now().time() > datetime.strptime('06:00:00','%H:%M:%S').time() and \
                    datetime.now().time() < datetime.strptime('20:00:00','%H:%M:%S').time():
                        print ('** Intervalo de tempo para o envio de planos esgotado para hoje **')
                        registra_log_auto(id_user, '* Intervalo de tempo para o envio de planos esgotado para hoje.') 
                        break
            
            # quando o reenvio for feito pelo agendamento, personaliza msg no log com dados do agendamento

            if modo == 'agenda':
                msg = 'Envio programado. ' 
            else:
                msg = ''    

            if sucesso == qtd_planos:
                registra_log_auto(id_user, '*' + msg + str(qtd_planos) + ' Plano(s) reenviado(s) com sucesso.')
                if modo == 'manual':
                    flash(str(qtd_planos) + ' Planos reenviados com sucesso','sucesso') # todos os planos enviados com sucesso
            else:
                registra_log_auto(id_user, '*' + msg + 'Na tentativa de reenvio de ' + str(qtd_planos) + ' Planos,' + str(sucesso) + ' foram reenviados.')
                if modo == 'manual':
                    flash('Houve problema no reenvio dos Planos: Dos ' + str(qtd_planos) + ' Planos,' + str(sucesso) + ' foram reenviados.','erro') # alguma coisa deu errado

        else:
            return 'erro_credenciais'

        registra_log_auto(id_user, '* Término do reenvio de Planos para API.')    

        print('*** Finalizando o reenvio de planos conforme agendamento ***')
        print('**')    



## lista planos avaliados que não foram enviados ainda 

@envio.route('/lista_a_enviar')
@login_required

def lista_a_enviar():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos planos que estão aptos ao envio.                               |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    page = request.args.get('page', 1, type=int)
       
    data_ref = pega_data_ref()
    
    n_enviados = planos_n_enviados_LOG()
    fonte = 'LOG'

    if n_enviados != 'erro_credenciais':

        lista = 'n_enviados'
        
        l = n_enviados[0]  ## pega até o limite de 1000 planos 
            
        qtd_total = 0    
        for grupo in n_enviados:
            qtd_total += len(grupo)

        #query que resgata erros em tentativas de envios de planos   
        log_erro_envio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                .filter(Log_Auto.msg.like('* Retorno API sobre falha'+'%'),
                                        Log_Auto.data_hora >= data_ref)\
                                .order_by(Log_Auto.id.desc())\
                                .all() 
        l_log_erro_envio = [[p.msg[47:83],p.msg] for p in log_erro_envio]  
                                               
                            
        # todos os planos executados e com horas homologadas > 0
        # planos_nao_env = db.session.query(VW_Pactos.id_pacto,
        #                                   VW_Pactos.situacao,
        #                                   VW_Pactos.data_inicio,
        #                                   VW_Pactos.data_fim,
        #                                   VW_Pactos.nome_participante,
        #                                   VW_Pactos.sigla_unidade_exercicio,
        #                                   VW_Pactos.modalidade_execucao)\
        #                            .order_by(VW_Pactos.data_fim.desc(),VW_Pactos.sigla_unidade_exercicio,VW_Pactos.nome_participante)\
        #                            .filter(VW_Pactos.desc_situacao_pacto == 'Executado',
        #                                     VW_Pactos.horas_homologadas > 0,
        #                                     VW_Pactos.id_pacto.in_(l))\
        #                            .paginate(page=page,per_page=500) 
        
        # todos os planos de vw_pacto
        planos_nao_env = db.session.query(VW_Pactos.id_pacto,
                                          VW_Pactos.situacao,
                                          VW_Pactos.data_inicio,
                                          VW_Pactos.data_fim,
                                          VW_Pactos.nome_participante,
                                          VW_Pactos.sigla_unidade_exercicio,
                                          VW_Pactos.modalidade_execucao)\
                                   .order_by(VW_Pactos.data_fim.desc(),VW_Pactos.sigla_unidade_exercicio,VW_Pactos.nome_participante)\
                                   .filter(VW_Pactos.id_pacto.in_(l))\
                                   .paginate(page=page,per_page=500)                                              

        planos = planos_nao_env
        planos_count = planos.total      

        return render_template('planos.html', demandas = planos, 
                                              demandas_count = planos_count,
                                              qtd_total = qtd_total,
                                              lista = lista,
                                              fonte = fonte,
                                              l_log_erro_envio = l_log_erro_envio,
                                              data_ref = data_ref)

    else:

        flash ('Credenciais de acesso à API não estão completas!','erro') 

        return render_template('index.html')   

## lista planos enviados 

@envio.route('/lista_enviados')
@login_required

def lista_enviados():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos planos que constam da API.                                     |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    page = request.args.get('page', 1, type=int)
    
    data_ref = pega_data_ref()

    enviados = planos_enviados_LOG()
    fonte = 'LOG'

    if enviados != 'erro_credenciais':

        lista = 'enviados'
        
        l = enviados[0]  ## pega até o limite de 1000 planos 
        
        qtd_total = 0    
        for grupo in enviados:
            qtd_total += len(grupo)   
                                
        # planos = db.session.query(VW_Pactos.id_pacto,
        #                           VW_Pactos.situacao,
        #                           VW_Pactos.data_inicio,
        #                           VW_Pactos.data_fim,
        #                           VW_Pactos.nome_participante,
        #                           VW_Pactos.sigla_unidade_exercicio,
        #                           VW_Pactos.modalidade_execucao)\
        #                    .order_by(VW_Pactos.data_fim.desc(),VW_Pactos.sigla_unidade_exercicio,VW_Pactos.nome_participante)\
        #                    .filter(VW_Pactos.desc_situacao_pacto == 'Executado',
        #                            VW_Pactos.horas_homologadas > 0,
        #                            VW_Pactos.id_pacto.in_(l))\
        #                    .paginate(page=page,per_page=500)   
        planos = db.session.query(VW_Pactos.id_pacto,
                                  VW_Pactos.situacao,
                                  VW_Pactos.data_inicio,
                                  VW_Pactos.data_fim,
                                  VW_Pactos.nome_participante,
                                  VW_Pactos.sigla_unidade_exercicio,
                                  VW_Pactos.modalidade_execucao)\
                           .order_by(VW_Pactos.data_fim.desc(),VW_Pactos.sigla_unidade_exercicio,VW_Pactos.nome_participante)\
                           .filter(VW_Pactos.id_pacto.in_(l))\
                           .paginate(page=page,per_page=500)                                         
       
        planos_count = planos.total 
        
        return render_template('planos.html', demandas = planos, 
                                              demandas_count = planos_count,
                                              qtd_total = qtd_total,
                                              lista = lista,
                                              fonte = fonte,
                                              data_ref = data_ref)

    else:

        flash ('Credenciais de envio não informadas no deploy do aplicativo!','erro') 

        return render_template('index.html')                                          


## enviar plano específico 

@envio.route('<plano_id>/<lista>/enviar_um_plano', methods = ['GET', 'POST'])
@login_required

def enviar_um_plano(plano_id,lista):
    """
    +---------------------------------------------------------------------------------------+
    |Envia um plano específico.                                                             |
    |Recebe o id do plano como parâmetro.                                                   |
    +---------------------------------------------------------------------------------------+
    """   

    # pega instituição do usuário logado
    instituicao = db.session.query(users.instituicaoId).filter(users.id == current_user.id).first()

    if instituicao == None:
        flash('Usuário não tem uma instiuição definida em seu registro!','erro')
        if lista == 'n_enviados':
            return redirect (url_for('envio.lista_a_enviar'))
        elif lista == 'enviados':
            return redirect (url_for('envio.lista_enviados'))
    
    token = pega_token(instituicao.instituicaoId)

    # indicador de plano enviado com sucesso 
    sucesso = False

    # pega o plano informado via query da aplicação API/CADE
    plano = db.session.query(VW_Pactos).filter(VW_Pactos.id_pacto == plano_id).first()

    # para o plano, monta dados no dicionário 
    
    if plano.data_interrupcao == None or plano.data_interrupcao == '':
        data_interrupcao = None
    else:
        data_interrupcao = plano.data_interrupcao.strftime('%Y-%m-%d')
        

    dic_envio = {}

    dic_envio['cod_plano']              = plano.id_pacto
    dic_envio['situacao']               = plano.situacao
    dic_envio['matricula_siape']        = int(plano.matricula_siape)
    dic_envio['cpf']                    = plano.cpf
    dic_envio['nome_participante']      = plano.nome_participante
    dic_envio['cod_unidade_exercicio']  = plano.cod_unidade_exercicio
    dic_envio['nome_unidade_exercicio'] = plano.nome_unidade_exercicio
    dic_envio['modalidade_execucao']    = plano.modalidade_execucao
    dic_envio['carga_horaria_semanal']  = plano.carga_horaria_semanal
    dic_envio['data_inicio']            = plano.data_inicio.strftime('%Y-%m-%d')
    dic_envio['data_fim']               = plano.data_fim.strftime('%Y-%m-%d')
    dic_envio['carga_horaria_total']    = plano.carga_horaria_total
    dic_envio['data_interrupcao']       = data_interrupcao
    dic_envio['entregue_no_prazo']      = plano.entregue_no_prazo
    dic_envio['horas_homologadas']      = plano.horas_homologadas
    dic_envio['atividades']             = []

    # pega as atividades do plano
    ativs = db.session.query(VW_Atividades_Pactos)\
                        .filter(VW_Atividades_Pactos.id_pacto == plano.id_pacto)\
                        .all()

    # para cada atividade, monta o resto do dicionário (key 'atividades')
    for a in ativs:

        if a.tempo_presencial_estimado != None and a.tempo_presencial_programado != None and \
           a.tempo_teletrabalho_estimado != None and a.tempo_teletrabalho_programado != None and \
          (a.tempo_presencial_executado > 0 or a.tempo_teletrabalho_executado > 0):
              
            if a.data_avaliacao == None or a.data_avaliacao == '':
                data_avaliacao = None
            else:
                data_avaliacao = a.data_avaliacao.strftime('%Y-%m-%d')  

                    

            dic_envio['atividades'].append({'id_atividade': a.id_produto,
                                            'nome_grupo_atividade': a.nome_grupo_atividade,
                                            'nome_atividade': a.nome_atividade,
                                            'faixa_complexidade': a.faixa_complexidade,
                                            'parametros_complexidade': a.parametros_complexidade,
                                            'tempo_presencial_estimado': a.tempo_presencial_estimado,
                                            'tempo_presencial_programado': a.tempo_presencial_programado,
                                            'tempo_presencial_executado': a.tempo_presencial_executado,
                                            'tempo_teletrabalho_estimado': a.tempo_teletrabalho_estimado,
                                            'tempo_teletrabalho_programado': a.tempo_teletrabalho_programado,
                                            'tempo_teletrabalho_executado': a.tempo_teletrabalho_executado,
                                            'entrega_esperada': a.entrega_esperada,
                                            'qtde_entregas': a.qtde_entregas,
                                            'qtde_entregas_efetivas': a.qtde_entregas_efetivas,
                                            'avaliacao': a.avaliacao,
                                            'data_avaliacao': data_avaliacao,
                                            'justificativa': a.justificativa}) 

   
    # prepara headers do put
    headers = {'Content-Type': "application/json", 'Accept': "application/json", 'Authorization': 'Bearer {}'.format(token)}
    
    # faz o put na API via dumps json do dicionário    
    r_put = requests.put(os.getenv('APIPGDME_URL') + '/plano_trabalho/'+plano_id, headers= headers, data=json.dumps(dic_envio))

    # put com sucesso (status_code < 400), seta sucesso como True
    if r_put.ok:
        sucesso = True

    retorno_API = re.search(r'\bmsg[\W|w]+[\w+\s]+',r_put.text) 

    if retorno_API:
        retorno_API_msg = retorno_API.group()[6:]
    else:
        retorno_API_msg = 'Sem retorno da API.'   

    if sucesso:
        if lista == 'enviados':
            # registra_log_auto(current_user.id, '* Plano reenviado manualmente com sucesso: '+str(plano_id)+' de '+plano.nome_participante)
            registra_log_auto(current_user.id, ' * PACTO REENVIADO: '+str(plano_id)+' de '+plano.nome_participante + ' (manualmente)')
            flash('Plano de '+plano.nome_participante+' reenviado manualmente com sucesso!','sucesso')
        elif lista == 'n_enviados':
            # registra_log_auto(current_user.id, '* Plano enviado manualmente com sucesso: '+str(plano_id)+' de '+plano.nome_participante)
            registra_log_auto(current_user.id, ' * PACTO ENVIADO: ' + str(plano_id)+' de '+plano.nome_participante + ' (manualmente)')
            flash('Plano de '+plano.nome_participante+' enviado manualmente com sucesso!','sucesso')   
    else:
        if lista == 'enviados':
            registra_log_auto(current_user.id, '* Retorno API sobre falha no reenvio do Plano: '+str(plano_id)+' de '+plano.nome_participante+' - '+str(retorno_API_msg))
            if str(retorno_API_msg) == 'Sem retorno da API.':
                flash('Erro na tentativa de reenvio manual do Plano: '+plano.nome_participante+' - '+r_put.text,'erro')
            else:
                flash('Erro na tentativa de reenvio manual do Plano: '+plano.nome_participante+' - '+str(retorno_API_msg),'erro') 
        elif lista == 'n_enviados':
            registra_log_auto(current_user.id, '* Retorno API sobre falha  no  envio do Plano: '+str(plano_id)+' de '+plano.nome_participante+' - '+str(retorno_API_msg))
            if str(retorno_API_msg) == 'Sem retorno da API.':
                flash('Erro na tentativa de envio manual do Plano: '+plano.nome_participante+' - '+r_put.text,'erro')
            else:
                flash('Erro na tentativa de envio manual do Plano: '+plano.nome_participante+' - '+str(retorno_API_msg),'erro')   

    # print(json.dumps(dic_envio, skipkeys=True, allow_nan=True, indent=4))          

    if lista == 'n_enviados':
        return redirect (url_for('envio.lista_a_enviar'))
    elif lista == 'enviados':
        return redirect (url_for('envio.lista_enviados'))    



## agendamento de envio 

@envio.route('/<int:inst>/agenda_envio', methods = ['GET', 'POST'])
@login_required

def agenda_envio(inst):
    """
    +---------------------------------------------------------------------------------------+
    |Faz agendamento de envio de planos.                                                    |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    
    def agendador(id_job, periodicidade, tipo_agendamento, tipo_envio, s_hora, s_minuto, inst):
        """Prepara sched com os parámetros informados.

        Keyword arguments:
        job -- identificador do job
        periodicidade -- intervalo de tempo entre envios (D, S ou M)
        tipo_agendamento -- se agendamento ou reagendamento
        tipo_envio -- se envio ou reenvio
        s_hora -- hora de execução do job
        s_minuto -- mintuo de execução do job
        inst -- a instituição 
        """
        
        if periodicidade == 'D':
            msg = ('*** '+tipo_agendamento+' '+id_job+' como DIÁRIO, rodando de segunda a sexta-feira, às '+s_hora+':'+s_minuto+' ***')
            print(msg)
            dia_semana = 'mon-fri'
            if tipo_agendamento == 'AGENDAR':
                try:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio, inst), day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)
                    sched.start()
                except:
                    sched.reschedule_job(id_job, trigger='cron', day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto))
            else:
                try:
                    sched.reschedule_job(id_job, trigger='cron', day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto))
                except:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio, inst), day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)
                    sched.start()
        elif periodicidade == 'S':
            msg =  ('*** '+tipo_agendamento+' '+id_job+' como SEMANAL, rodando toda sexta-feira, às '+s_hora+':'+s_minuto+' ***')
            print(msg)
            dia_semana = 'fri'
            if tipo_agendamento == 'AGENDAR':
                try:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio, inst), day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)  
                    sched.start()
                except:
                    sched.reschedule_job(id_job, trigger='cron', day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto))
            else:
                try:
                    sched.reschedule_job(id_job, trigger='cron', day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto))   
                except:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio, inst), day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)  
                    sched.start()   
        elif periodicidade == 'M':
            msg =  ('*** '+tipo_agendamento+' '+id_job+' como MENSAL,  rodando na primeira sexta-feira de cada mês, às '+s_hora+':'+s_minuto+' ***')
            print(msg)
            dia = '1st fri'
            if tipo_agendamento == 'AGENDAR':
                try:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio, inst), day=dia, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)
                    sched.start()
                except:
                    sched.reschedule_job(id_job, trigger='cron', day=dia, hour=int(s_hora), minute=int(s_minuto))
            else:
                try:
                    sched.reschedule_job(id_job, trigger='cron', day=dia, hour=int(s_hora), minute=int(s_minuto))
                except:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio, inst), day=dia, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)
                    sched.start() 

    

    form = AgendamentoForm()

    # pega instituição do usuário logado
    instituicao = db.session.query(users.instituicaoId).filter(users.id == current_user.id).first()

    if instituicao == None:
        flash('Usuário não tem uma instiuição definida em seu registro!','erro')
        return render_template('jobs.html', agenda_ant_envio='',
                                            agenda_ant_reenvio='', 
                                            form=form)

    if form.validate_on_submit():

        # pega dados informado no formulário, limitando minutos a 59
        tipo          = form.tipo.data
        periodicidade = form.periodicidade.data
        hora          = form.hora.data
        if form.minuto.data > 59:
            minuto = 59
        else:    
            minuto    = form.minuto.data
        
        # tornando minuto e hora strings de duas posições (0 anterior, quando for o caso)
        if len(str(minuto)) == 1:
            s_minuto = '0'+str(minuto)
        else: 
            s_minuto = str(minuto)

        if len(str(hora)) == 1:
            s_hora = '0'+str(hora)
        else: 
            s_hora = str(hora)    
        
        print ('*****')
        
        # verifica agendamentos existentes

        id_1='job_envia_planos_'+str(instituicao.instituicaoId)
        id_2='job_envia_planos_novamente_'+str(instituicao.instituicaoId)
        
        # no caso de cancelamento de envios
        if periodicidade == 'N':
            msg =  ('*** Jobs CANCELADOS. Não haverá envios automáticos. ***')
            print(msg)
            try:
                job_1 = sched.get_job(id_1)
                if job_1:
                    sched.remove_job(id_1)
            except:
                pass
            try:
                job_2 = sched.get_job(id_2)
                if job_2:
                    sched.remove_job(id_2)
            except:
                pass
            registra_log_auto(current_user.id, '* Agendamento cancelado. - '+str(instituicao.instituicaoId))    
            flash(msg,'sucesso')
        
        else:    

            try:
                job_existente = sched.get_job(id_1)
                if job_existente:
                    print ('*** Job encontrado: ',job_existente)
                    job_agendado = True
                else:
                    print ('*** Não encontrei job '+id_1+' ***')
                    job_agendado = False      
            except:
                print ('*** Não encontrei job '+id_1+' ***')
                job_agendado = False

            if job_agendado:
                
                agendador(id_1, periodicidade, 'REAGENDAR', 'enviar', s_hora, s_minuto, instituicao.instituicaoId)
                if periodicidade == 'S':
                    txt = 'todas as sextas-feiras'
                elif periodicidade == 'M':
                    txt = 'a primeira sexta-feira do mês'
                else:
                    txt = '' 
                flash(str(id_1)+' reagendado para '+txt+' ('+s_hora+':'+s_minuto+')','sucesso')
                
            else:
                
                agendador(id_1, periodicidade, 'AGENDAR', 'enviar', s_hora, s_minuto, instituicao.instituicaoId)
                if periodicidade == 'S':
                    txt = 'todas as sextas-feiras'
                elif periodicidade == 'M':
                    txt = 'a primeira sexta-feira do mês'
                else:
                    txt = ''
                flash(str(id_1)+' agendado para '+txt+' ('+s_hora+':'+s_minuto+')','sucesso')
            
            registra_log_auto(current_user.id, '* Agendamento de envio: '+ str(periodicidade) +' - '+ s_hora +':'+ s_minuto + ' - ' + str(instituicao.instituicaoId))

            if tipo == 'todos':

                if hora == 0:
                    hora = 1
                    s_hora = '0'+str(hora)
                else:    
                    hora += 1
                    s_hora = str(hora)
                # minuto += 2
                # s_minuto = str(minuto)

                try:
                    job_existente = sched.get_job(id_2)
                    if job_existente:
                        print ('*** Job encontrado: ',job_existente)
                        job_agendado = True
                    else:
                        print ('*** Não encontrei job '+ id_2 +' ***')
                        job_agendado = False      
                except:
                    print ('*** Não encontrei job '+ id_2 +' ***')
                    job_agendado = False

                if job_agendado:
                    
                    agendador(id_2, periodicidade, 'REAGENDAR', 'reenviar', s_hora, s_minuto, instituicao.instituicaoId)
                    if periodicidade == 'S':
                        txt = 'todas as sextas-feiras'
                    elif periodicidade == 'M':
                        txt = 'a primeira sexta-feira do mês'
                    else:
                        txt = ''
                    flash(str(id_2)+' reagendado para '+txt+' ('+s_hora+':'+s_minuto+')','sucesso')
                    
                else:
                    
                    agendador(id_2, periodicidade, 'AGENDAR', 'reenviar', s_hora, s_minuto, instituicao.instituicaoId)
                    if periodicidade == 'S':
                        txt = 'todas as sextas-feiras'
                    elif periodicidade == 'M':
                        txt = 'a primeira sexta-feira do mês'
                    else:
                        txt = ''
                    flash(str(id_2)+' agendado para '+txt+' ('+s_hora+':'+s_minuto+')','sucesso')
                
                registra_log_auto(current_user.id, '* Agendamento de reenvio: '+ str(periodicidade) +' - '+ s_hora +':'+ s_minuto + ' - ' + str(instituicao.instituicaoId))

            else:
                msg =  ('*** Agendamento só de inéditos. Job de reenvio, se houver, será CANCELADO. ***')
                print(msg)
                try:
                    job_2 = sched.get_job(id_2)
                    if job_2:
                        sched.remove_job(id_2)
                except:
                    pass
                
        
        return render_template('envio.html')  

    # verifica agendamentos anteriores via consulta ao log

    log_agenda_ant_envio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                     .filter(Log_Auto.msg.like('* Agendamento de envio:'+'%'+str(instituicao.instituicaoId)))\
                                     .order_by(Log_Auto.id.desc())\
                                     .first()
    
    log_agenda_ant_reenvio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                       .filter(Log_Auto.msg.like('* Agendamento de reenvio:'+'%'+str(instituicao.instituicaoId)))\
                                       .order_by(Log_Auto.id.desc())\
                                       .first()      

    log_agenda_canc_envio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                      .filter(Log_Auto.msg.like('* Agendamento cancelado.'+'%'+str(instituicao.instituicaoId)))\
                                      .order_by(Log_Auto.id.desc())\
                                      .first() 

    
    try:
        job_envio_existente = sched.get_job('job_envia_planos_'+str(instituicao.instituicaoId))
        if job_envio_existente:
            txt_envio = ' (job de envio ativo)'
        else:
            txt_envio = ' (não há job de envio ativo)'      
    except:
        txt_envio = ' (não há job de envio ativo)' 

    try:
        job_reenvio_existente = sched.get_job('job_envia_planos_novamente_'+str(instituicao.instituicaoId))
        if job_reenvio_existente:
            txt_reenvio = ' (job de reenvio ativo)'
        else:
            txt_reenvio = ' (não há job de reenvio ativo)'      
    except:
        txt_reenvio = ' (não há job de reenvio ativo)'    
    
    if log_agenda_ant_envio:
        if log_agenda_canc_envio and log_agenda_canc_envio.id > log_agenda_ant_envio.id:
            agenda_ant_envio = 'Não consta agendamento'
            agenda_ant_reenvio = None
        else:    
            agenda_ant_envio = log_agenda_ant_envio.msg[24:] + txt_envio
            if log_agenda_ant_reenvio and log_agenda_ant_reenvio.id > log_agenda_ant_envio.id:
                agenda_ant_reenvio = log_agenda_ant_reenvio.msg[26:] + txt_reenvio
            else:
                agenda_ant_reenvio = None
    else:
        agenda_ant_envio = None 
        agenda_ant_reenvio = None

    # joga dados, caso existam, para a tela
    
    return render_template('jobs.html', agenda_ant_envio=agenda_ant_envio,
                                        agenda_ant_reenvio=agenda_ant_reenvio, 
                                        form=form)   
    
    
## renderiza tela inicial dos envios 

@envio.route('/envio_i')
@login_required

def envio_i():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta tela inicial dos envios.                                                     |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    
    return render_template('envio.html')          
