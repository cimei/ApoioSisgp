"""
.. topic:: Envio (views)

    Procedimentos relacionados ao envio de dados (planos e atividades) ao orgão superior.


.. topic:: Funções

    * planos_enviados_API: Identifica API os planos já enviados (demorado)
    * planos_enviados_LOG: Identifica no LOG os planos já enviados
    * planos_n_enviados_API: Identifica, conferindo na API, planos nunca enviados
    * planos_n_enviados_LOG: Identifica, conferindo no LOG, planos nunca 
    * envia_planos_novamente: Faz o reenvio de planos em lote
    * envia_planos: Faz o envio de planos em lote



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
from project.models import Pactos_de_Trabalho, Pessoas, Unidades, catdom,\
                           Pactos_de_Trabalho_Atividades, VW_Pactos, VW_Atividades_Pactos,\
                           jobs, users, Log_Auto

from project.usuarios.views import registra_log_auto                           

from project.envio.forms import AgendamentoForm, PesquisaPlanoForm

import requests
import json
from datetime import datetime, timedelta, date
import os
import re

envio = Blueprint('envio',__name__, template_folder='templates')


# funções

def pega_data_ref():
    
    ref_envios = db.session.query(catdom).filter(catdom.classificacao=='DataBaseEnvioPlanos').first()
    if ref_envios:
        return (datetime.strptime(ref_envios.descricao,'%Y-%m-%d').date())
    else:
        return (date.today())
    

# pega token de acesso à API de envio de dados
def pega_token():        

    string = 'grant_type=&username='+os.getenv('APIPGDME_AUTH_USER')+'&password='+os.getenv('APIPGDME_AUTH_PASSWORD')+'&scope=&client_id=&client_secret='

    headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/json"}

    api_url_login = os.getenv('APIPGDME_URL') + '/auth/jwt/login'

    response = requests.post(api_url_login, headers=headers ,data=json.dumps(string))

    rlogin_json = response.json()

    token = rlogin_json['access_token']
    tipo =  rlogin_json['token_type']  
    
    return(token)


# função que gera lista de planos que já foram enviados previamente, consultando a API
def planos_enviados_API():
    
    if os.getenv('APIPGDME_URL') != None and os.getenv('APIPGDME_URL') != "" and \
       os.getenv('APIPGDME_AUTH_USER') != None and os.getenv('APIPGDME_AUTH_USER') != "" and \
       os.getenv('APIPGDME_AUTH_PASSWORD') != None and os.getenv('APIPGDME_AUTH_PASSWORD') != "":  

        #subquery para pegar situações dos planos de trabalho (pactos)
        catdom_1 = db.session.query(catdom.catalogoDominioId,
                                    catdom.descricao)\
                            .filter(catdom.classificacao == 'SituacaoPactoTrabalho')\
                            .subquery()

        #subquery que conta atividades em cada plano de trabalho (pacto)
        ativs = db.session.query(Pactos_de_Trabalho_Atividades.pactoTrabalhoId,
                                label('qtd_ativs',func.count(Pactos_de_Trabalho_Atividades.pactoTrabalhoAtividadeId)))\
                        .group_by(Pactos_de_Trabalho_Atividades.pactoTrabalhoId)\
                        .subquery()
        
        #subquery que conta atividades com nota em cada plano de trabalho (pacto)
        ativs_com_nota = db.session.query(Pactos_de_Trabalho_Atividades.pactoTrabalhoId,
                                        label('qtd_com_nota',func.count(Pactos_de_Trabalho_Atividades.pactoTrabalhoAtividadeId)))\
                                .filter(Pactos_de_Trabalho_Atividades.nota != None)\
                                .group_by(Pactos_de_Trabalho_Atividades.pactoTrabalhoId)\
                                .subquery()  

        # todos os planos executados e com todas as atividades avaliadas
        planos_avaliados = db.session.query(Pactos_de_Trabalho.pactoTrabalhoId,
                                    catdom_1.c.descricao,
                                    Pactos_de_Trabalho.situacaoId,
                                    ativs.c.qtd_ativs,
                                    ativs_com_nota.c.qtd_com_nota)\
                                .filter(catdom_1.c.descricao == 'Executado',
                                        ativs.c.qtd_ativs != None,
                                        ativs_com_nota.c.qtd_com_nota != None,
                                        ativs_com_nota.c.qtd_com_nota > 0)\
                                .join(catdom_1, catdom_1.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                .outerjoin(ativs_com_nota, ativs_com_nota.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .outerjoin(ativs, ativs.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .all() 
        
        token = pega_token()     

        head = {'Authorization': 'Bearer {}'.format(token)}

        enviados = []

        for d in planos_avaliados:

            r = requests.get(os.getenv('APIPGDME_URL') + '/plano_trabalho/' + d.pactoTrabalhoId, headers= head)

            if r.ok:
                enviados.append(d.pactoTrabalhoId)

        return enviados        
                
    else:
        return ('erro_credenciais')      



# função que gera lista com ids dos planos que já foram enviados previamente, consultando o log
def planos_enviados_LOG():
    
    data_ref = pega_data_ref()
    
    enviados_log = db.session.query(Log_Auto.msg)\
                             .filter(Log_Auto.msg.like(' * PACTO ENVIADO:'+'%'),
                                     Log_Auto.data_hora >= data_ref)\
                             .distinct()                        
    
    enviados = [e.msg[18:54] for e in enviados_log]
   
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
   



# função que gera lista de planos que nunca foram enviados, consultando API
def planos_n_enviados_API():

    if os.getenv('APIPGDME_URL') != None and os.getenv('APIPGDME_URL') != "" and \
       os.getenv('APIPGDME_AUTH_USER') != None and os.getenv('APIPGDME_AUTH_USER') != "" and \
       os.getenv('APIPGDME_AUTH_PASSWORD') != None and os.getenv('APIPGDME_AUTH_PASSWORD') != "":   

        #subquery para pegar situações dos planos de trabalho (pactos)
        catdom_1 = db.session.query(catdom.catalogoDominioId,
                                    catdom.descricao)\
                            .filter(catdom.classificacao == 'SituacaoPactoTrabalho')\
                            .subquery()

        #subquery que conta atividades em cada plano de trabalho (pacto)
        ativs = db.session.query(Pactos_de_Trabalho_Atividades.pactoTrabalhoId,
                                 label('qtd_ativs',func.count(Pactos_de_Trabalho_Atividades.pactoTrabalhoAtividadeId)))\
                          .group_by(Pactos_de_Trabalho_Atividades.pactoTrabalhoId)\
                          .subquery()
        
        #subquery que conta atividades com nota em cada plano de trabalho (pacto)
        ativs_com_nota = db.session.query(Pactos_de_Trabalho_Atividades.pactoTrabalhoId,
                                        label('qtd_com_nota',func.count(Pactos_de_Trabalho_Atividades.pactoTrabalhoAtividadeId)))\
                                .filter(Pactos_de_Trabalho_Atividades.nota != None)\
                                .group_by(Pactos_de_Trabalho_Atividades.pactoTrabalhoId)\
                                .subquery() 
                                                                                     
        # resgata todos os planos executados com pelo menos uma atividade avaliada
        planos_avaliados = db.session.query(Pactos_de_Trabalho.pactoTrabalhoId,
                                            catdom_1.c.descricao,
                                            Pactos_de_Trabalho.situacaoId,
                                            ativs.c.qtd_ativs,
                                            ativs_com_nota.c.qtd_com_nota)\
                                    .filter(catdom_1.c.descricao == 'Executado',
                                            ativs.c.qtd_ativs != None,
                                            ativs_com_nota.c.qtd_com_nota != None,
                                            ativs_com_nota.c.qtd_com_nota > 0)\
                                    .join(catdom_1, catdom_1.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                    .outerjoin(ativs_com_nota, ativs_com_nota.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                    .outerjoin(ativs, ativs.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                    .all()  
        
        token = pega_token()   

        head = {'Authorization': 'Bearer {}'.format(token)}

        n_enviados = []

        # o get na API é utilizado para identificar planos avaliados, mas não enviados ainda
        # a lista n_enviados é então um subgrupo da query planos avaliados, que foi executada mais acima
        
        for d in planos_avaliados:

            r = requests.get(os.getenv('APIPGDME_URL') + '/plano_trabalho/' + d.pactoTrabalhoId, headers= head)

            if r.ok == False:
                n_enviados.append(d.pactoTrabalhoId)
        
        return n_enviados        
                
    else:
        return ('erro_credenciais') 

# função que gera lista de planos que nunca foram enviados, consultando o LOG
def planos_n_enviados_LOG(): 
    
    data_ref = pega_data_ref()
              
    # todos os planos executados e com horas homologadas > 0
    planos_avaliados = db.session.query(VW_Pactos.id_pacto)\
                                 .filter(VW_Pactos.desc_situacao_pacto == 'Executado',
                                        VW_Pactos.horas_homologadas > 0,
                                        VW_Pactos.data_fim >= data_ref)\
                                 .all()                                            
    
    # identifica envios na tabela do log
    
    enviados_log = db.session.query(Log_Auto.msg)\
                             .filter(Log_Auto.msg.like(' * PACTO ENVIADO:'+'%'),
                                     Log_Auto.data_hora >= data_ref)\
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


# função para envio de planos já enviados anteriormente
def envia_planos_novamente():
    
    if os.getenv('CONSULTA_API') == 'S':
        enviados = planos_enviados_API()
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
        
        token = pega_token()   
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
                if datetime.now().time() > datetime.strptime('06:00:00','%H:%M:%S').time() and \
                   datetime.now().time() < datetime.strptime('20:00:00','%H:%M:%S').time():
                    break
                
                # se estourar 55 minutos, pega novo token
                if datetime.now() > hora_token:
                    token = pega_token()
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

                    if a.tempo_presencial_estimado and a.tempo_presencial_programado and \
                       a.tempo_teletrabalho_estimado and a.tempo_teletrabalho_programado and \
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


# função para envio de planos nunca enviados
def envia_planos():  
      
    if os.getenv('CONSULTA_API') == 'S':
        n_enviados = planos_n_enviados_API()
    else:
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
        
        token = pega_token() 
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
                if datetime.now().time() > datetime.strptime('06:00:00','%H:%M:%S').time() and \
                   datetime.now().time() < datetime.strptime('20:00:00','%H:%M:%S').time():
                    break
                
                # se estorar 55 minutos, pega novo token
                if datetime.now() > hora_token:
                    token = pega_token()   
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
                    
                    # # consulta a tabela de atividades do pacto para ver situação. Serão enviadas somente atividades concluídas (503)
                    # situ_ativ = db.session.query(Pactos_de_Trabalho_Atividades.situacaoId)\
                    #                     .filter(Pactos_de_Trabalho_Atividades.pactoTrabalhoAtividadeId == a.id_produto)\
                    #                     .first()

                    if a.tempo_presencial_estimado and a.tempo_presencial_programado and \
                       a.tempo_teletrabalho_estimado and a.tempo_teletrabalho_programado and \
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
    
    
    
# função para envio e reenvio de planos para a API
def envia_API(tipo):  
    
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
            
            token = pega_token() 
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
                    if datetime.now().time() > datetime.strptime('06:00:00','%H:%M:%S').time() and \
                    datetime.now().time() < datetime.strptime('20:00:00','%H:%M:%S').time():
                        break
                    
                    # se estorar 55 minutos, pega novo token
                    if datetime.now() > hora_token:
                        token = pega_token()   
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
                        
                        if a.tempo_presencial_estimado and a.tempo_presencial_programado and \
                        a.tempo_teletrabalho_estimado and a.tempo_teletrabalho_programado and \
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
            
            token = pega_token()   
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
                    if datetime.now().time() > datetime.strptime('06:00:00','%H:%M:%S').time() and \
                    datetime.now().time() < datetime.strptime('20:00:00','%H:%M:%S').time():
                        break
                    
                    # se estourar 55 minutos, pega novo token
                    if datetime.now() > hora_token:
                        token = pega_token()
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
                        
                        if a.tempo_presencial_estimado and a.tempo_presencial_programado and \
                        a.tempo_teletrabalho_estimado and a.tempo_teletrabalho_programado and \
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
    
    if os.getenv('CONSULTA_API') == 'S':
        n_enviados = planos_n_enviados_API()
        fonte = 'API'
    else:
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
        
        formas = db.session.query(catdom.catalogoDominioId,
                                  catdom.descricao)\
                            .filter(catdom.classificacao == 'ModalidadeExecucao')\
                            .all()                                          
                            
        # todos os planos executados e com horas homologadas > 0
        planos_nao_env = db.session.query(VW_Pactos.id_pacto,
                                          VW_Pactos.situacao,
                                          VW_Pactos.data_inicio,
                                          VW_Pactos.data_fim,
                                          VW_Pactos.nome_participante,
                                          VW_Pactos.sigla_unidade_exercicio,
                                          VW_Pactos.modalidade_execucao)\
                                   .order_by(VW_Pactos.data_fim.desc(),VW_Pactos.sigla_unidade_exercicio,VW_Pactos.nome_participante)\
                                   .filter(VW_Pactos.desc_situacao_pacto == 'Executado',
                                            VW_Pactos.horas_homologadas > 0,
                                            VW_Pactos.id_pacto.in_(l))\
                                   .paginate(page=page,per_page=100)                    

        planos = planos_nao_env
        planos_count = planos.total      

        return render_template('planos.html', demandas = planos, 
                                              demandas_count = planos_count,
                                              qtd_total = qtd_total,
                                              lista = lista,
                                              fonte = fonte,
                                              l_log_erro_envio = l_log_erro_envio,
                                              formas = formas,
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

    if os.getenv('CONSULTA_API') == 'S':
        enviados = planos_enviados_API()
        fonte = 'API'
    else:
        enviados = planos_enviados_LOG()
        fonte = 'LOG'

    if enviados != 'erro_credenciais':

        lista = 'enviados'
        
        l = enviados[0]  ## pega até o limite de 1000 planos 
        
        qtd_total = 0    
        for grupo in enviados:
            qtd_total += len(grupo)
            
        formas = db.session.query(catdom.catalogoDominioId,
                                  catdom.descricao)\
                            .filter(catdom.classificacao == 'ModalidadeExecucao')\
                            .all()    
                                
        planos = db.session.query(VW_Pactos.id_pacto,
                                  VW_Pactos.situacao,
                                  VW_Pactos.data_inicio,
                                  VW_Pactos.data_fim,
                                  VW_Pactos.nome_participante,
                                  VW_Pactos.sigla_unidade_exercicio,
                                  VW_Pactos.modalidade_execucao)\
                           .order_by(VW_Pactos.data_fim.desc(),VW_Pactos.sigla_unidade_exercicio,VW_Pactos.nome_participante)\
                           .filter(VW_Pactos.desc_situacao_pacto == 'Executado',
                                   VW_Pactos.horas_homologadas > 0,
                                   VW_Pactos.id_pacto.in_(l))\
                           .paginate(page=page,per_page=100)                         
       
        planos_count = planos.total 
        
        return render_template('planos.html', demandas = planos, 
                                              demandas_count = planos_count,
                                              qtd_total = qtd_total,
                                              lista = lista,
                                              fonte = fonte,
                                              formas = formas,
                                              data_ref = data_ref)

    else:

        flash ('Credenciais de envio não informadas no deploy do aplicativo!','erro') 

        return render_template('index.html')                                          


## pesquisa planos 

@envio.route('/pesquisa_planos', methods = ['GET', 'POST'])
@login_required

def pesquisa_planos():
    """
    +---------------------------------------------------------------------------------------+
    |Pesquisa planos a partir de critérios informados.                                      |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    form = PesquisaPlanoForm()
    
    unids = db.session.query(Unidades.unidadeId, Unidades.undSigla).order_by(Unidades.undSigla).filter(Unidades.situacaoUnidadeId==1).all()
    lista_unids = [(u.undSigla,u.undSigla) for u in unids]
    lista_unids.insert(0,('','Todas')) 
    
    form.unidade.choices = lista_unids
    
    if form.validate_on_submit():
        
        formas = db.session.query(catdom.catalogoDominioId,
                                  catdom.descricao)\
                            .filter(catdom.classificacao == 'ModalidadeExecucao')\
                            .all()
                            
        #query que resgata erros em tentativas de envios de planos   
        log_erro_envio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                .filter(Log_Auto.msg.like('* Retorno API sobre falha'+'%') )\
                                .order_by(Log_Auto.id.desc())\
                                .all() 
        l_log_erro_envio = [[p.msg[47:83],p.msg] for p in log_erro_envio]                    
                            
        enviados = planos_enviados_LOG()                    
        
        for l in enviados:
        
            planos_avaliados = db.session.query(VW_Pactos.id_pacto,
                                                VW_Pactos.situacao,
                                                VW_Pactos.data_inicio,
                                                VW_Pactos.data_fim,
                                                VW_Pactos.nome_participante,
                                                VW_Pactos.sigla_unidade_exercicio,
                                                VW_Pactos.modalidade_execucao,
                                                literal('enviado').label('sit_envio'))\
                                .order_by(VW_Pactos.data_fim.desc(),VW_Pactos.sigla_unidade_exercicio,VW_Pactos.nome_participante)\
                                .filter(VW_Pactos.desc_situacao_pacto == 'Executado',
                                        VW_Pactos.horas_homologadas > 0,
                                        VW_Pactos.nome_participante.like('%'+form.pessoa.data+'%'),
                                        VW_Pactos.sigla_unidade_exercicio.like('%'+form.unidade.data+'%'),
                                        VW_Pactos.id_pacto.in_(l))\
                                .all()
                                
            if enviados.index(l) == 0:
                demandas = planos_avaliados
                demandas_count = len(planos_avaliados)
            else:    
                demandas += planos_avaliados 
                demandas_count += len(planos_avaliados)                    
        
        
        n_enviados = planos_n_enviados_LOG()                    
        
        for l in n_enviados:
        
            planos_avaliados = db.session.query(VW_Pactos.id_pacto,
                                                VW_Pactos.situacao,
                                                VW_Pactos.data_inicio,
                                                VW_Pactos.data_fim,
                                                VW_Pactos.nome_participante,
                                                VW_Pactos.sigla_unidade_exercicio,
                                                VW_Pactos.modalidade_execucao,
                                                literal('n_enviado').label('sit_envio'))\
                                .order_by(VW_Pactos.data_fim.desc(),VW_Pactos.sigla_unidade_exercicio,VW_Pactos.nome_participante)\
                                .filter(VW_Pactos.desc_situacao_pacto == 'Executado',
                                        VW_Pactos.horas_homologadas > 0,
                                        VW_Pactos.nome_participante.like('%'+form.pessoa.data+'%'),
                                        VW_Pactos.sigla_unidade_exercicio.like('%'+form.unidade.data+'%'),
                                        VW_Pactos.id_pacto.in_(l))\
                                .all()
                                
            if n_enviados.index(l) == 0 and demandas == None:
                demandas = planos_avaliados
                demandas_count = len(planos_avaliados)
            else:    
                demandas += planos_avaliados 
                demandas_count += len(planos_avaliados)    
                                     
        
        return render_template('planos_pesq.html', demandas = demandas, 
                                                   demandas_count = demandas_count,
                                                   formas = formas,
                                                   l_log_erro_envio = l_log_erro_envio)                            

    return render_template('pesquisa.html', form = form)


## enviar planos (DESATIVADO)

@envio.route('<tipo>/enviar_planos', methods = ['GET', 'POST'])
@login_required

def enviar_planos(tipo):
    """
    +---------------------------------------------------------------------------------------+
    |Envia manualmente planos de uma lista. (desativado)                                    |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    if tipo == 'n_enviados':
        # executa função que envia planos não enviados
        envio = envia_planos()
        if envio == 'erro_credenciais': 
            flash ('Credenciais de acesso à API não estão completas!','erro') 
        return redirect (url_for('envio.lista_a_enviar'))
    elif tipo == 'enviados':
        # executa função que reenvia planos
        envio = envia_planos_novamente()
        if envio == 'erro_credenciais': 
            flash ('Credenciais de acesso à API não estão completas!','erro') 
        return redirect (url_for('envio.lista_enviados'))
    else:
        flash ('Opção inválida!','erro') 
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
    
    token = pega_token()

    # indicador de plano enviado com sucesso 
    sucesso = False

    # pega o plano informado via query da aplicação API/CADE
    plano = db.session.query(VW_Pactos).filter(VW_Pactos.id_pacto == plano_id).first()

    # para o plano, monta dados no dicionário 

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
    dic_envio['data_interrupcao']       = plano.data_interrupcao
    dic_envio['entregue_no_prazo']      = plano.entregue_no_prazo
    dic_envio['horas_homologadas']      = plano.horas_homologadas
    dic_envio['atividades']             = []

    # pega as atividades do plano
    ativs = db.session.query(VW_Atividades_Pactos)\
                        .filter(VW_Atividades_Pactos.id_pacto == plano.id_pacto)\
                        .all()

    # para cada atividade, monta o resto do dicionário (key 'atividades')
    for a in ativs:
        
        # # consulta a tabela de atividades do pacto para ver situação. Serão enviadas somente atividades concluídas (503)
        # situ_ativ = db.session.query(Pactos_de_Trabalho_Atividades.situacaoId)\
        #                       .filter(Pactos_de_Trabalho_Atividades.pactoTrabalhoAtividadeId == a.id_produto)\
        #                       .first()

        if a.tempo_presencial_estimado and a.tempo_presencial_programado and \
           a.tempo_teletrabalho_estimado and a.tempo_teletrabalho_programado and \
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

@envio.route('/agenda_envio', methods = ['GET', 'POST'])
@login_required

def agenda_envio():
    """
    +---------------------------------------------------------------------------------------+
    |Faz agendamento de envio de planos.                                                    |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    
    def agendador(id_job, periodicidade, tipo_agendamento, tipo_envio, s_hora, s_minuto):
        """Prepara sched com os parámetros informados.

        Keyword arguments:
        job -- identificador do job
        periodicidade -- intervalo de tempo entre envios (Diária, Semanal ou Mensal)
        tipo_agendamento -- se agendamento ou reagendamento
        tipo_envio -- se envio ou reenvio
        s_hora -- hora de execução do job
        s_minuto -- mintuo de execução do job
        """
        
        if periodicidade == 'Diária':
            msg = ('*** '+tipo_agendamento+' '+id_job+' como DIÁRIO, rodando de segunda a sexta-feira, às '+s_hora+':'+s_minuto+' ***')
            print(msg)
            dia_semana = '*'
            if tipo_agendamento == 'AGENDAR':
                try:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio), day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)
                    sched.start()
                except:
                    sched.reschedule_job(id_job, trigger='cron', day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto))
            else:
                try:
                    sched.reschedule_job(id_job, trigger='cron', day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto))
                except:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio), day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)
                    sched.start()
        elif periodicidade == 'Semanal':
            msg =  ('*** '+tipo_agendamento+' '+id_job+' como SEMANAL, rodando toda sexta-feira, às '+s_hora+':'+s_minuto+' ***')
            print(msg)
            dia_semana = 'fri'
            if tipo_agendamento == 'AGENDAR':
                try:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio), day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)  
                    sched.start()
                except:
                    sched.reschedule_job(id_job, trigger='cron', day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto))
            else:
                try:
                    sched.reschedule_job(id_job, trigger='cron', day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto))   
                except:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio), day_of_week=dia_semana, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)  
                    sched.start()   
        elif periodicidade == 'Mensal':
            msg =  ('*** '+tipo_agendamento+' '+id_job+' como MENSAL,  rodando na primeira sexta-feira de cada mês, às '+s_hora+':'+s_minuto+' ***')
            print(msg)
            dia = '1st fri'
            if tipo_agendamento == 'AGENDAR':
                try:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio), day=dia, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)
                    sched.start()
                except:
                    sched.reschedule_job(id_job, trigger='cron', day=dia, hour=int(s_hora), minute=int(s_minuto))
            else:
                try:
                    sched.reschedule_job(id_job, trigger='cron', day=dia, hour=int(s_hora), minute=int(s_minuto))
                except:
                    sched.add_job(trigger='cron', id=id_job, func=lambda:envia_API(tipo_envio), day=dia, hour=int(s_hora), minute=int(s_minuto), misfire_grace_time=3600, coalesce=True)
                    sched.start() 

    

    form = AgendamentoForm()

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

        id_1='job_envia_planos'
        id_2='job_envia_planos_novamente'
        
        # no caso de cancelamento de envios
        if periodicidade == 'Nenhuma':
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
            registra_log_auto(current_user.id, '* Agendamento cancelado.')    
            flash(msg,'sucesso')
        
        else:    

            try:
                job_existente = sched.get_job(id_1)
                if job_existente:
                    print ('*** Job encontrado: ',job_existente)
                    job_agendado = True
                else:
                    print ('*** Não encontrei job '+id_1+' ***')
                    job_agendado = None      
            except:
                print ('*** Não encontrei job '+id_1+' ***')
                job_agendado = None

            if job_agendado:
                
                agendador(id_1, periodicidade, 'REAGENDAR', 'enviar', s_hora, s_minuto)
                flash(str(id_1)+' reagendado para periodicidade '+str(periodicidade)+' ('+s_hora+':'+s_minuto+')','sucesso')
                
                # # altera job existente com os novos parâmetros informados pelo usuário
                # if periodicidade == 'Diária':
                #     msg = ('*** O '+id_1+' será REAGENDADO para DIÁRIO, rodando de segunda a sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                #     print(msg)
                #     dia_semana = '*'
                #     try:
                #         sched.reschedule_job(id_1, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                #     except:
                #         sched.add_job(trigger='cron', id=id_1, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                #         sched.start()
                # elif periodicidade == 'Semanal':
                #     msg =  ('*** O '+id_1+' será REAGENDADO para SEMANAL, rodando toda sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                #     print(msg)
                #     dia_semana = 'fri'
                #     try:
                #         sched.reschedule_job(id_1, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)   
                #     except:
                #         sched.add_job(trigger='cron', id=id_1, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
                #         sched.start()   
                # elif periodicidade == 'Mensal':
                #     msg =  ('*** O '+id_1+' será REAGENDADO para MENSAL,  rodando na primeira sexta-feira de cada mês, às '+s_hora+':'+s_minuto+' ***')
                #     print(msg)
                #     dia = '1st fri'
                #     try:
                #         sched.reschedule_job(id_1, trigger='cron', day=dia, hour=hora, minute=minuto)
                #     except:
                #         sched.add_job(trigger='cron', id=id_1, func=envia_planos, day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                #         sched.start() 
                # elif periodicidade == 'Nenhuma':
                #     msg =  ('*** Jobs serão CANCELADOS. Não haverá envios automáticos. ***')
                #     print(msg)
                #     sched.remove_job(id_1) 
                #     try:
                #         job_2 = sched.get_job(id_2)
                #         if job_2:
                #             sched.remove_job(id_2)
                #     except:
                #         pass  

            else:
                
                agendador(id_1, periodicidade, 'AGENDAR', 'enviar', s_hora, s_minuto)
                flash(str(id_1)+' agendado para periodicidade '+str(periodicidade)+' ('+s_hora+':'+s_minuto+')','sucesso')
            
            #     # como não enconcontrou job agendado, cria um job com os parãmetros informados pelo usuário
            #     if periodicidade == 'Diária':
            #         msg = ('*** O '+id_1+' será AGENDADO como DIÁRIO, rodando de segunda a sexta-feira, às '+s_hora+':'+s_minuto+' ***')
            #         print(msg)
            #         dia_semana = '*'
            #         try:
            #             sched.add_job(trigger='cron', id=id_1, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
            #             sched.start()
            #         except:
            #             sched.reschedule_job(id_1, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
            #     elif periodicidade == 'Semanal':
            #         msg = ('*** O '+id_1+' será AGENDADO para SEMANAL, rodando toda sexta-feira, às '+s_hora+':'+s_minuto+' ***')
            #         print(msg)
            #         dia_semana = 'fri'
            #         try:
            #             sched.add_job(trigger='cron', id=id_1, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
            #             sched.start()
            #         except:
            #             sched.reschedule_job(id_1, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
            #     elif periodicidade == 'Mensal':
            #         msg = ('*** O '+id_1+' será AGENDADO para MENSAL,  rodando na primeira sexta-feira de cada mês, às '+s_hora+':'+s_minuto+' ***')
            #         print(msg)
            #         dia = '1st fri'
            #         try:
            #             sched.add_job(trigger='cron', id=id_1, func=envia_planos, day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
            #             sched.start()
            #         except:
            #             sched.reschedule_job(id_1, trigger='cron', day=dia, hour=hora, minute=minuto)
            #     elif periodicidade == 'Nenhuma':
            #         msg =  ('*** Não jobs para cancelar. Comando ignorado. ***')
            #         print(msg)

            # if periodicidade != 'Nenhuma':
            #     registra_log_auto(current_user.id, '* Agendamento de envio: '+ str(periodicidade) +' - '+ s_hora +':'+ s_minuto)
            # else:
            #     registra_log_auto(current_user.id, '* Agendamento cancelado.')    
            # flash(msg,'sucesso')    

            registra_log_auto(current_user.id, '* Agendamento de envio: '+ str(periodicidade) +' - '+ s_hora +':'+ s_minuto)

            if tipo == 'todos':

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
                        job_agendado = None      
                except:
                    print ('*** Não encontrei job '+ id_2 +' ***')
                    job_agendado = None

                if job_agendado:
                    
                    agendador(id_2, periodicidade, 'REAGENDAR', 'reenviar', s_hora, s_minuto)
                    flash(str(id_2)+' reagendado para periodicidade '+str(periodicidade)+' ('+s_hora+':'+s_minuto+')','sucesso')
                    
                    # # altera job existente com os novos parâmetros informados pelo usuário
                    # if periodicidade == 'Diária':
                    #     msg = ('*** O '+id_2+' será REAGENDADO para DIÁRIO, rodando de segunda a sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                    #     print(msg)
                    #     dia_semana = '*'
                    #     try:
                    #         sched.reschedule_job(id_2, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                    #     except:   
                    #         sched.add_job(trigger='cron', id=id_2, func=envia_planos_novamente, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                    #         # sched.start()
                    # elif periodicidade == 'Semanal':
                    #     msg =  ('*** O '+id_2+' será REAGENDADO para SEMANAL, rodando toda sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                    #     print(msg)
                    #     dia_semana = 'fri'
                    #     try:
                    #         sched.reschedule_job(id_2, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)   
                    #     except:  
                    #         sched.add_job(trigger='cron', id=id_2, func=envia_planos_novamente, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
                    #         # sched.start()   
                    # elif periodicidade == 'Mensal':
                    #     msg =  ('*** O '+id_2+' será REAGENDADO para MENSAL,  rodando na primeira sexta-feira de cada mês, às '+s_hora+':'+s_minuto+' ***')
                    #     print(msg)
                    #     dia = '1st fri'
                    #     try:
                    #         sched.reschedule_job(id_2, trigger='cron', day=dia, hour=hora, minute=minuto)
                    #     except:
                    #         sched.add_job(trigger='cron', id=id_2, func=envia_planos_novamente, day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                    #         # sched.start()  

                else:
                    
                    agendador(id_2, periodicidade, 'AGENDAR', 'reenviar', s_hora, s_minuto)
                    flash(str(id_2)+' agendado para periodicidade '+str(periodicidade)+' ('+s_hora+':'+s_minuto+')','sucesso')
                
                    # # como não enconcontrou job agendado, cria um job com os parãmetros informados pelo usuário
                    # if periodicidade == 'Diária':
                    #     msg = ('*** O '+id_2+' será AGENDADO como DIÁRIO, rodando de segunda a sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                    #     print(msg)
                    #     dia_semana = '*'
                    #     try:
                    #         sched.add_job(trigger='cron', id=id_2, func=envia_planos_novamente, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                    #     except:
                    #         sched.reschedule_job(id_2, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                    #     # sched.start()
                    # elif periodicidade == 'Semanal':
                    #     msg = ('*** O '+id_2+' será AGENDADO para SEMANAL, rodando toda sexta-feira, às '+s_hora+':'+s_minuto+' ***')
                    #     print(msg)
                    #     dia_semana = 'fri'
                    #     try:
                    #         sched.add_job(trigger='cron', id=id_2, func=envia_planos_novamente, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
                    #     except:
                    #         sched.reschedule_job(id_2, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                    #     # sched.start()
                    # elif periodicidade == 'Mensal':
                    #     msg = ('*** O '+id_2+' será AGENDADO para MENSAL,  rodando na primeira sexta-feira de cada mês, às '+s_hora+':'+s_minuto+' ***')
                    #     print(msg)
                    #     dia = '1st fri'
                    #     try:
                    #         sched.add_job(trigger='cron', id=id_2, func=envia_planos_novamente, day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                    #     except:
                    #         sched.reschedule_job(id_2, trigger='cron', day=dia, hour=hora, minute=minuto)
                    #     # sched.start()

                registra_log_auto(current_user.id, '* Agendamento de reenvio: '+ str(periodicidade) +' - '+ s_hora +':'+ s_minuto)

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
                                     .filter(Log_Auto.msg.like('* Agendamento de envio:'+'%') )\
                                     .order_by(Log_Auto.id.desc())\
                                     .first()
    log_agenda_ant_reenvio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                       .filter(Log_Auto.msg.like('* Agendamento de reenvio:'+'%') )\
                                       .order_by(Log_Auto.id.desc())\
                                       .first()                                 

    log_agenda_canc_envio = db.session.query(Log_Auto.id, Log_Auto.msg)\
                                      .filter(Log_Auto.msg == '* Agendamento cancelado.')\
                                      .order_by(Log_Auto.id.desc())\
                                      .first()                                        

    
    try:
        job_envio_existente = sched.get_job('job_envia_planos')
        if job_envio_existente:
            txt_envio = ' (job de envio ativo)'
        else:
            txt_envio = ' (não há job de envio ativo)'      
    except:
        txt_envio = ' (não há job de envio ativo)' 

    try:
        job_reenvio_existente = sched.get_job('job_envia_planos_novamente')
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
            if log_agenda_ant_reenvio.id > log_agenda_ant_envio.id:
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
