"""
.. topic:: Envio (views)

    Procedimentos relacionados ao envio de dados (planos e atividades) ao orgão superior.


.. topic:: Ações relacionadas ao envio

    * lista_a_enviar: Lista planos que estão aptos ao envio 
    * enviar_planos: Envia planos não enviados previamente
    * enviar_um_plano: Envia, ou reenvia, um plano individual
    * lista_enviados: Lista planos que já foram enviados
    * agenda_envio: Agendamento de envios

"""

# views.py na pasta envio

from flask import render_template,url_for,flash, redirect, request, Blueprint
from flask_login import current_user, login_required

from sqlalchemy.sql import label
from sqlalchemy import func, literal

from project import db, sched
from project.models import Pactos_de_Trabalho, Pessoas, Unidades, catdom,\
                           Pactos_de_Trabalho_Atividades, VW_Pactos, VW_Atividades_Pactos, jobs, users

from project.usuarios.views import registra_log_auto                           

from project.envio.forms import AgendamentoForm

import requests
import json
from datetime import datetime
import os
import re

envio = Blueprint('envio',__name__, template_folder='templates')


# funções

# função que gera lista de planos que já foram enviados previamente
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
                                        ativs_com_nota.c.qtd_com_nota != None,
                                        ativs_com_nota.c.qtd_com_nota > 0)\
                                .join(catdom_1, catdom_1.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                .outerjoin(ativs_com_nota, ativs_com_nota.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .outerjoin(ativs, ativs.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .all() 

        # pega token de acesso à API de envio de dados

        string = 'grant_type=&username='+os.getenv('APIPGDME_AUTH_USER')+'&password='+os.getenv('APIPGDME_AUTH_PASSWORD')+'&scope=&client_id=&client_secret='

        headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/json"}

        api_url_login = os.getenv('APIPGDME_URL') + '/auth/jwt/login'

        response = requests.post(api_url_login, headers=headers ,data=json.dumps(string))

        rlogin_json = response.json()

        token = rlogin_json['access_token']
        tipo =  rlogin_json['token_type']       

        head = {'Authorization': 'Bearer {}'.format(token)}

        enviados = []

        for d in planos_avaliados:

            r = requests.get(os.getenv('APIPGDME_URL') + '/plano_trabalho/' + d.pactoTrabalhoId, headers= head)

            if r.ok:
                enviados.append(d.pactoTrabalhoId)

        return enviados        
                
    else:
        return ('erro_credenciais')      


# função que gera lista de planos que nunca foram enviados
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
                                        ativs_com_nota.c.qtd_com_nota != None,
                                        ativs_com_nota.c.qtd_com_nota > 0)\
                                .join(catdom_1, catdom_1.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                .outerjoin(ativs_com_nota, ativs_com_nota.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .outerjoin(ativs, ativs.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .all() 
        
        # pega token de acesso à API de envio de dados

        string = 'grant_type=&username='+os.getenv('APIPGDME_AUTH_USER')+'&password='+os.getenv('APIPGDME_AUTH_PASSWORD')+'&scope=&client_id=&client_secret='

        headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/json"}

        api_url_login = os.getenv('APIPGDME_URL') + '/auth/jwt/login'

        response = requests.post(api_url_login, headers=headers ,data=json.dumps(string))

        rlogin_json = response.json()

        # print('** Retorno do pedido de token: ',rlogin_json)

        token = rlogin_json['access_token']
        tipo =  rlogin_json['token_type']       

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


# função para envio de planos já enviados anteriormente
def envia_planos_novamente():

    enviados = planos_enviados_API()

    # quando o envio for feito pelo agendamento, current_user está vazio, pega então o primeiro usuário para registro do envio no diário 
    if current_user == None:
        primeiro = db.session.query(users.id).first()
        id = primeiro.id
        modo = 'agenda'
    else:
        id = current_user.id 
        modo = 'manual'

    registra_log_auto(id, 'Início do reenvio de Planos para API.') 

    if enviados != 'erro_credenciais':      
    
        # pega token de acesso à API de envio de dados

        string = 'grant_type=&username='+os.getenv('APIPGDME_AUTH_USER')+'&password='+os.getenv('APIPGDME_AUTH_PASSWORD')+'&scope=&client_id=&client_secret='

        headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/json"}

        api_url_login = os.getenv('APIPGDME_URL') + '/auth/jwt/login'

        response = requests.post(api_url_login, headers=headers ,data=json.dumps(string))

        rlogin_json = response.json()

        token = rlogin_json['access_token']
        tipo =  rlogin_json['token_type']       

        # indicador de planos enviados com sucesso 
        sucesso = 0

        # pega todos os planos que deverão ser enviados via query da aplicação API/CADE
        # l = n_enviados.replace('[','').replace(']','').replace("'","").replace(',','').split()
        l = enviados
        planos = db.session.query(VW_Pactos).filter(VW_Pactos.id_pacto.in_(l)).all()
        qtd_planos = len(planos)

        # para cada plano, monta o dados do dicionário 
        for p in planos:

            dic_envio = {}

            dic_envio['cod_plano']       = p.id_pacto
            dic_envio['situacao']        = p.situacao
            dic_envio['matricula_siape'] = int(p.matricula_siape)
            dic_envio['cpf']             = p.cpf
            dic_envio['nome_participante']      = p.nome_participante
            dic_envio['cod_unidade_exercicio']  = p.cod_unidade_exercicio
            dic_envio['nome_unidade_exercicio'] = p.nome_unidade_exercicio
            dic_envio['modalidade_execucao']    = p.modalidade_execucao
            dic_envio['carga_horaria_semanal']  = p.carga_horaria_semanal
            dic_envio['data_inicio']         = p.data_inicio.strftime('%Y-%m-%d')
            dic_envio['data_fim']            = p.data_fim.strftime('%Y-%m-%d')
            dic_envio['carga_horaria_total'] = p.carga_horaria_total
            dic_envio['data_interrupcao']    = p.data_interrupcao
            dic_envio['entregue_no_prazo']   = p.entregue_no_prazo
            dic_envio['horas_homologadas']   = p.horas_homologadas
            dic_envio['atividades'] = []

            # pega as atividades de cada plano
            ativs = db.session.query(VW_Atividades_Pactos)\
                            .filter(VW_Atividades_Pactos.id_pacto == p.id_pacto)\
                            .all()

            # para cada atividade, monta o resto do dicionário (key 'atividades')
            for a in ativs:

                dic_envio['atividades'].append({'id_atividade': a.id_produto,
                                                'nome_grupo_atividade': a.nome_grupo_atividade,
                                                'nome_atividade': a.nome_atividade,
                                                'faixa_complexidade': a.faixa_complexidade,
                                                'parametros_complexidade': a.parametros_complexidade,
                                                'tempo_presencial_estimado': a.tempo_presencial_estimado,
                                                'tempo_presencial_programado': a.tempo_presencial_programado,
                                                'tempo_presencial_executado': a.tempo_presencial_programado,
                                                'tempo_teletrabalho_estimado': a.tempo_teletrabalho_estimado,
                                                'tempo_teletrabalho_programado': a.tempo_teletrabalho_estimado,
                                                'tempo_teletrabalho_executado': a.tempo_teletrabalho_estimado,
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
                registra_log_auto(id, 'PACTO REENVIADO: ' + str(plano_id))

            retorno_API = re.search(r'\bmsg[\W|w]+[\w+\s]+',r_put.text) 

            if retorno_API:
                retorno_API_msg = retorno_API.group()[6:]
                registra_log_auto(id, 'Retorno API sobre falha no reenvio do Plano: ' + str(plano_id) + ' - ' + str(retorno_API_msg))
            else:
                retorno_API_msg = 'Sem registro de erro.'

        # quando o reenvio for feito pelo agendamento, personaliza msg no log com dados do agendamento

        if modo == 'agenda':
            agenda = db.session.query(jobs).first()
            run_time = datetime.fromtimestamp(agenda.next_run_time)
            msg = 'Reenvio programado: ' + run_time.strftime('%d/%m/%Y - %H:%M') +'. '
        else:
            msg = ''    

        if sucesso == qtd_planos:
            registra_log_auto(id, msg + str(qtd_planos) + ' Plano(s) reenviado(s) com sucesso.')
            if modo == 'manual':
                flash(str(qtd_planos) + ' Planos reenviados com sucesso','sucesso') # todos os planos enviados com sucesso
        else:
            registra_log_auto(id, msg + 'Na tentativa de reenvio de ' + str(qtd_planos) + ' Planos,' + str(sucesso) + ' foram reenviados.')
            if modo == 'manual':
                flash('Houve problema no reenvio dos Planos: Dos ' + str(qtd_planos) + ' Planos,' + str(sucesso) + ' foram reenviados.','erro') # alguma coisa deu errado

    else:
        return 'erro_credenciais'


# função para envio de planos nunca enviados
def envia_planos():  
      
    n_enviados = planos_n_enviados_API()

    # quando o envio for feito pelo agendamento, current_user está vazio, pega então o primeiro usuário para registro do envio no diário 
    if current_user == None:
        primeiro = db.session.query(users.id).first()
        id = primeiro.id
        modo = 'agenda'
    else:
        id = current_user.id 
        modo = 'manual'

    registra_log_auto(id, 'Início do envio de Planos para API.')       
    
    if n_enviados != 'erro_credenciais':
    
        # pega token de acesso à API de envio de dados

        string = 'grant_type=&username='+os.getenv('APIPGDME_AUTH_USER')+'&password='+os.getenv('APIPGDME_AUTH_PASSWORD')+'&scope=&client_id=&client_secret='

        headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/json"}

        api_url_login = os.getenv('APIPGDME_URL') + '/auth/jwt/login'

        response = requests.post(api_url_login, headers=headers ,data=json.dumps(string))

        rlogin_json = response.json()

        token = rlogin_json['access_token']
        tipo =  rlogin_json['token_type']       

        # indicador de planos enviados com sucesso 
        sucesso = 0

        # pega todos os planos que deverão ser enviados via query da aplicação API/CADE
        # l = n_enviados.replace('[','').replace(']','').replace("'","").replace(',','').split()
        l = n_enviados
        planos = db.session.query(VW_Pactos).filter(VW_Pactos.id_pacto.in_(l)).all()
        qtd_planos = len(planos)

        # para cada plano, monta o dados do dicionário 
        for p in planos:

            dic_envio = {}

            dic_envio['cod_plano']       = p.id_pacto
            dic_envio['situacao']        = p.situacao
            dic_envio['matricula_siape'] = int(p.matricula_siape)
            dic_envio['cpf']             = p.cpf
            dic_envio['nome_participante']      = p.nome_participante
            dic_envio['cod_unidade_exercicio']  = p.cod_unidade_exercicio
            dic_envio['nome_unidade_exercicio'] = p.nome_unidade_exercicio
            dic_envio['modalidade_execucao']    = p.modalidade_execucao
            dic_envio['carga_horaria_semanal']  = p.carga_horaria_semanal
            dic_envio['data_inicio']         = p.data_inicio.strftime('%Y-%m-%d')
            dic_envio['data_fim']            = p.data_fim.strftime('%Y-%m-%d')
            dic_envio['carga_horaria_total'] = p.carga_horaria_total
            dic_envio['data_interrupcao']    = p.data_interrupcao
            dic_envio['entregue_no_prazo']   = p.entregue_no_prazo
            dic_envio['horas_homologadas']   = p.horas_homologadas
            dic_envio['atividades'] = []

            # pega as atividades de cada plano
            ativs = db.session.query(VW_Atividades_Pactos)\
                            .filter(VW_Atividades_Pactos.id_pacto == p.id_pacto)\
                            .all()

            # para cada atividade, monta o resto do dicionário (key 'atividades')
            for a in ativs:

                dic_envio['atividades'].append({'id_atividade': a.id_produto,
                                                'nome_grupo_atividade': a.nome_grupo_atividade,
                                                'nome_atividade': a.nome_atividade,
                                                'faixa_complexidade': a.faixa_complexidade,
                                                'parametros_complexidade': a.parametros_complexidade,
                                                'tempo_presencial_estimado': a.tempo_presencial_estimado,
                                                'tempo_presencial_programado': a.tempo_presencial_programado,
                                                'tempo_presencial_executado': a.tempo_presencial_programado,
                                                'tempo_teletrabalho_estimado': a.tempo_teletrabalho_estimado,
                                                'tempo_teletrabalho_programado': a.tempo_teletrabalho_estimado,
                                                'tempo_teletrabalho_executado': a.tempo_teletrabalho_estimado,
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
                registra_log_auto(id, 'PACTO ENVIADO: ' + str(plano_id))

            retorno_API = re.search(r'\bmsg[\W|w]+[\w+\s]+',r_put.text) 

            if retorno_API:
                retorno_API_msg = retorno_API.group()[6:]
                registra_log_auto(id, 'Retorno API sobre falha no envio do Plano: ' + str(plano_id) + ' - ' + str(retorno_API_msg))
            else:
                retorno_API_msg = 'Sem registro de erro.'

        # quando o envio for feito pelo agendamento, personaliza msg no log com dados do agendamento

        if modo == 'agenda':
            agenda = db.session.query(jobs).first()
            run_time = datetime.fromtimestamp(agenda.next_run_time)
            msg = 'Envio programado: ' + run_time.strftime('%d/%m/%Y - %H:%M') +'. '
        else:
            msg = ''    

        if sucesso == qtd_planos:
            registra_log_auto(id, msg + str(qtd_planos) + ' Plano(s) enviado(s) com sucesso.')
            if modo == 'manual':
                flash(str(qtd_planos) + ' Planos enviados com sucesso','sucesso') # todos os planos enviados com sucesso
        else:
            registra_log_auto(id, msg + 'Na tentativa de envio de ' + str(qtd_planos) + ' Planos,' + str(sucesso) + ' foram enviados.')
            if modo == 'manual':
                flash('Houve problema no envio dos Planos: Dos ' + str(qtd_planos) + ' Planos,' + str(sucesso) + ' foram enviados.','erro') # alguma coisa deu errado 
    
    else:
        return 'erro_credenciais'


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

    n_enviados = planos_n_enviados_API()

    if n_enviados != 'erro_credenciais':

        lista = 'n_enviados'

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

        # todos os planos executados em com pelo menos uma atividade avaliada
        planos_avaliados = db.session.query(Pactos_de_Trabalho.pactoTrabalhoId,
                                            catdom_1.c.descricao,
                                            Pactos_de_Trabalho.situacaoId,
                                            ativs.c.qtd_ativs,
                                            ativs_com_nota.c.qtd_com_nota)\
                                     .filter(catdom_1.c.descricao == 'Executado',
                                             ativs_com_nota.c.qtd_com_nota != None,
                                             ativs_com_nota.c.qtd_com_nota > 0)\
                                     .join(catdom_1, catdom_1.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                     .outerjoin(ativs_com_nota, ativs_com_nota.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                     .outerjoin(ativs, ativs.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                     .all()                             

        planos_nao_env = db.session.query(Pactos_de_Trabalho.pactoTrabalhoId,
                                  Pactos_de_Trabalho.planoTrabalhoId,
                                  Pactos_de_Trabalho.dataInicio,
                                  Pactos_de_Trabalho.dataFim,
                                  Pactos_de_Trabalho.percentualExecucao,
                                  Pactos_de_Trabalho.relacaoPrevistoRealizado,
                                  Pessoas.pesNome,
                                  Unidades.unidadeId,
                                  Unidades.undSigla,
                                  catdom_1.c.descricao,
                                  label('forma',catdom.descricao),
                                  Pactos_de_Trabalho.situacaoId,
                                  ativs.c.qtd_ativs,
                                  ativs_com_nota.c.qtd_com_nota,
                                  literal(False).label('situ_envio_previo'))\
                            .filter(Pactos_de_Trabalho.pactoTrabalhoId.in_(n_enviados))\
                            .join(Pessoas, Pessoas.pessoaId == Pactos_de_Trabalho.pessoaId)\
                            .join(Unidades, Unidades.unidadeId == Pactos_de_Trabalho.unidadeId)\
                            .join(catdom_1, catdom_1.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                            .join(catdom, catdom.catalogoDominioId == Pactos_de_Trabalho.formaExecucaoId)\
                            .order_by(Unidades.unidadeId,Pessoas.pesNome,Pactos_de_Trabalho.dataInicio.desc())\
                            .outerjoin(ativs_com_nota, ativs_com_nota.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                            .outerjoin(ativs, ativs.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                            .all() 

        planos = planos_nao_env
        
        planos_count = len(planos)        

        return render_template('planos.html', demandas = planos, 
                                              demandas_count = planos_count,
                                              enviados = len(planos_avaliados) - planos_count,
                                              lista = lista)

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

    enviados = planos_enviados_API()

    if enviados != 'erro_credenciais':

        lista = 'enviados'

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
                                        ativs_com_nota.c.qtd_com_nota != None,
                                        ativs_com_nota.c.qtd_com_nota > 0)\
                                .join(catdom_1, catdom_1.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                .outerjoin(ativs_com_nota, ativs_com_nota.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .outerjoin(ativs, ativs.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .all()
    
        planos = db.session.query(Pactos_de_Trabalho.pactoTrabalhoId,
                                        Pactos_de_Trabalho.planoTrabalhoId,
                                        Pactos_de_Trabalho.dataInicio,
                                        Pactos_de_Trabalho.dataFim,
                                        Pactos_de_Trabalho.percentualExecucao,
                                        Pactos_de_Trabalho.relacaoPrevistoRealizado,
                                        Pessoas.pesNome,
                                        Unidades.unidadeId,
                                        Unidades.undSigla,
                                        catdom_1.c.descricao,
                                        label('forma',catdom.descricao),
                                        Pactos_de_Trabalho.situacaoId,
                                        ativs.c.qtd_ativs,
                                        ativs_com_nota.c.qtd_com_nota)\
                                .filter(Pactos_de_Trabalho.pactoTrabalhoId.in_(enviados))\
                                .join(Pessoas, Pessoas.pessoaId == Pactos_de_Trabalho.pessoaId)\
                                .join(Unidades, Unidades.unidadeId == Pactos_de_Trabalho.unidadeId)\
                                .join(catdom_1, catdom_1.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                .join(catdom, catdom.catalogoDominioId == Pactos_de_Trabalho.formaExecucaoId)\
                                .order_by(Unidades.unidadeId,Pessoas.pesNome,Pactos_de_Trabalho.dataInicio.desc())\
                                .outerjoin(ativs_com_nota, ativs_com_nota.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .outerjoin(ativs, ativs.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .all() 
        
        planos_count = len(planos)        

        return render_template('planos.html', demandas = planos, 
                                            demandas_count = planos_count,
                                            n_enviados = len(planos_avaliados) - planos_count,
                                            enviados = enviados,
                                            lista = lista)

    else:

        flash ('Credenciais de envio não informadas no deploy do aplicativo!','erro') 

        return render_template('index.html')                                          


## enviar planos 

@envio.route('<tipo>/enviar_planos', methods = ['GET', 'POST'])
@login_required

def enviar_planos(tipo):
    """
    +---------------------------------------------------------------------------------------+
    |Envia planos que não tenham de acordo com o tipo escolhido.                            |
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

    # pega token de acesso à API de envio de dados

    string = 'grant_type=&username='+os.getenv('APIPGDME_AUTH_USER')+'&password='+os.getenv('APIPGDME_AUTH_PASSWORD')+'&scope=&client_id=&client_secret='

    headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/json"}

    api_url_login = os.getenv('APIPGDME_URL') + '/auth/jwt/login'

    response = requests.post(api_url_login, headers=headers ,data=json.dumps(string))

    rlogin_json = response.json()

    token = rlogin_json['access_token']
    tipo =  rlogin_json['token_type']       

    # indicador de plano enviado com sucesso 
    sucesso = False

    # pega o plano informado via query da aplicação API/CADE
    plano = db.session.query(VW_Pactos).filter(VW_Pactos.id_pacto == plano_id).first()

    # para o plano, monta dados no dicionário 

    dic_envio = {}

    dic_envio['cod_plano']       = plano.id_pacto
    dic_envio['situacao']        = plano.situacao
    dic_envio['matricula_siape'] = int(plano.matricula_siape)
    dic_envio['cpf']             = plano.cpf
    dic_envio['nome_participante']      = plano.nome_participante
    dic_envio['cod_unidade_exercicio']  = plano.cod_unidade_exercicio
    dic_envio['nome_unidade_exercicio'] = plano.nome_unidade_exercicio
    dic_envio['modalidade_execucao']    = plano.modalidade_execucao
    dic_envio['carga_horaria_semanal']  = plano.carga_horaria_semanal
    dic_envio['data_inicio']         = plano.data_inicio.strftime('%Y-%m-%d')
    dic_envio['data_fim']            = plano.data_fim.strftime('%Y-%m-%d')
    dic_envio['carga_horaria_total'] = plano.carga_horaria_total
    dic_envio['data_interrupcao']    = plano.data_interrupcao
    dic_envio['entregue_no_prazo']   = plano.entregue_no_prazo
    dic_envio['horas_homologadas']   = plano.horas_homologadas
    dic_envio['atividades'] = []

    # pega as atividades do plano
    ativs = db.session.query(VW_Atividades_Pactos)\
                        .filter(VW_Atividades_Pactos.id_pacto == plano.id_pacto)\
                        .all()

    # para cada atividade, monta o resto do dicionário (key 'atividades')
    for a in ativs:

        dic_envio['atividades'].append({'id_atividade': a.id_produto,
                                        'nome_grupo_atividade': a.nome_grupo_atividade,
                                        'nome_atividade': a.nome_atividade,
                                        'faixa_complexidade': a.faixa_complexidade,
                                        'parametros_complexidade': a.parametros_complexidade,
                                        'tempo_presencial_estimado': a.tempo_presencial_estimado,
                                        'tempo_presencial_programado': a.tempo_presencial_programado,
                                        'tempo_presencial_executado': a.tempo_presencial_programado,
                                        'tempo_teletrabalho_estimado': a.tempo_teletrabalho_estimado,
                                        'tempo_teletrabalho_programado': a.tempo_teletrabalho_estimado,
                                        'tempo_teletrabalho_executado': a.tempo_teletrabalho_estimado,
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
            registra_log_auto(current_user.id, 'Plano reenviado manualmente com sucesso: ' + str(plano_id))
            flash('Plano reenviado manualmente com sucesso!','sucesso')
        elif lista == 'n_enviados':
            registra_log_auto(current_user.id, 'Plano enviado manualmente com sucesso: ' + str(plano_id))
            flash('Plano enviado manualmente com sucesso!','sucesso')   
    else:
        if lista == 'enviados':
            registra_log_auto(current_user.id, 'Erro na tentativa de reenvio do Plano: ' + str(plano_id)  + ' - ' + str(retorno_API_msg))
            flash('Erro na tentativa de reenvio manual do Plano: ' + str(plano_id) + ' - ' + str(retorno_API_msg),'erro') 
        elif lista == 'n_enviados':
            registra_log_auto(current_user.id, 'Erro na tentativa de envio do Plano: ' + str(plano_id)  + ' - ' + str(retorno_API_msg))
            flash('Erro na tentativa de envio manual do Plano: ' + str(plano_id) + ' - ' + str(retorno_API_msg),'erro')   

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

    form = AgendamentoForm()

    if form.validate_on_submit():

        tipo          = form.tipo.data
        periodicidade = form.periodicidade.data
        hora          = form.hora.data
        minuto        = form.minuto.data
        
        # verifica agendamentos existentes

        id='job_envia_planos'

        job_agendado = db.session.query(jobs).filter(jobs.id==id).first()

        if job_agendado:
            
            # altera job existente com os novos parâmetros informados pelo usuário
            if periodicidade == 'Diária':
                msg = ('*** O '+id+' será REAGENDADO para DIÁRIO, rodando de segunda a sexta-feira, às '+str(hora)+':'+str(minuto)+' ***')
                print(msg)
                dia_semana = 'mon-fri'
                try:
                    sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                except:
                    limpa_apscheduler_regs = db.session.query(jobs).delete()
                    db.session.commit()
                    print('** Tentativa de reagendamento falhou. Limpando tabela do APScheduler e tentando novamente.')
                    sched.add_job(trigger='cron', id=id, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                    sched.start()
            elif periodicidade == 'Semanal':
                msg =  ('*** O '+id+' será REAGENDADO para SEMANAL, rodando toda sexta-feira, às '+str(hora)+':'+str(minuto)+' ***')
                print(msg)
                dia_semana = 'fri'
                try:
                    sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)   
                except:
                    limpa_apscheduler_regs = db.session.query(jobs).delete()
                    db.session.commit()
                    print('** Tentativa de agendamento falhou. Limpando tabela do APScheduler e tentando novamente.')   
                    sched.add_job(trigger='cron', id=id, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
                    sched.start()   
            elif periodicidade == 'Mensal':
                msg =  ('*** O '+id+' será REAGENDADO para MENSAL,  rodando na primeira sexta-feira de cada mês, às '+str(hora)+':'+str(minuto)+' ***')
                print(msg)
                dia = '1st fri'
                try:
                    sched.reschedule_job(id, trigger='cron', day=dia, hour=hora, minute=minuto)
                except:
                    limpa_apscheduler_regs = db.session.query(jobs).delete()
                    db.session.commit()
                    print('** Tentativa de agendamento falhou. Limpando tabela do APScheduler e tentando novamente.')   
                    sched.add_job(trigger='cron', id=id, func=envia_planos, day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                    sched.start() 
            elif periodicidade == 'Nenhuma':
                msg =  ('*** O '+id+' será CANCELADO. Não haverá envios automáticos. ***')
                print(msg)
                sched.remove_job(id)    

        else:
           
            # como não enconcontrou job agendado, cria um job com os parãmetros informados pelo usuário
            if periodicidade == 'Diária':
                msg = ('*** O '+id+' será AGENDADO como DIÁRIO, rodando de segunda a sexta-feira, às '+str(hora)+':'+str(minuto)+' ***')
                print(msg)
                dia_semana = 'mon-fri'
                sched.add_job(trigger='cron', id=id, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                sched.start()
            elif periodicidade == 'Semanal':
                msg = ('*** O '+id+' será AGENDADO para SEMANAL, rodando toda sexta-feira, às '+str(hora)+':'+str(minuto)+' ***')
                print(msg)
                dia_semana = 'fri'
                sched.add_job(trigger='cron', id=id, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
                sched.start()
            elif periodicidade == 'Mensal':
                msg = ('*** O '+id+' será AGENDADO para MENSAL,  rodando na primeira sexta-feira de cada mês, às '+str(hora)+':'+str(minuto)+' ***')
                print(msg)
                dia = '1st fri'
                sched.add_job(trigger='cron', id=id, func=envia_planos, day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                sched.start()
            elif periodicidade == 'Nenhuma':
                msg =  ('*** Não há '+id+' para cancelar. Comando ignorado. ***')
                print(msg)

            registra_log_auto(current_user.id, 'Agendamento de envio: '+ str(periodicidade) +' - '+ str(hora) +':'+ str(minuto))
            flash(msg,'sucesso')    

        
        if tipo == 'todos':

            id='job_envia_planos_novamente'

            hora += 1

            job_agendado = db.session.query(jobs).filter(jobs.id==id).first()

            if job_agendado:
                
                # altera job existente com os novos parâmetros informados pelo usuário
                if periodicidade == 'Diária':
                    msg = ('*** O '+id+' será REAGENDADO para DIÁRIO, rodando de segunda a sexta-feira, às '+str(hora)+':'+str(minuto)+' ***')
                    print(msg)
                    dia_semana = 'mon-fri'
                    try:
                        sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)
                    except:
                        limpa_apscheduler_regs = db.session.query(jobs).delete()
                        db.session.commit()
                        print('** Tentativa de reagendamento falhou. Limpando tabela do APScheduler e tentando novamente.')
                        sched.add_job(trigger='cron', id=id, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                        sched.start()
                elif periodicidade == 'Semanal':
                    msg =  ('*** O '+id+' será REAGENDADO para SEMANAL, rodando toda sexta-feira, às '+str(hora)+':'+str(minuto)+' ***')
                    print(msg)
                    dia_semana = 'fri'
                    try:
                        sched.reschedule_job(id, trigger='cron', day_of_week=dia_semana, hour=hora, minute=minuto)   
                    except:
                        limpa_apscheduler_regs = db.session.query(jobs).delete()
                        db.session.commit()
                        print('** Tentativa de agendamento falhou. Limpando tabela do APScheduler e tentando novamente.')   
                        sched.add_job(trigger='cron', id=id, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
                        sched.start()   
                elif periodicidade == 'Mensal':
                    msg =  ('*** O '+id+' será REAGENDADO para MENSAL,  rodando na primeira sexta-feira de cada mês, às '+str(hora)+':'+str(minuto)+' ***')
                    print(msg)
                    dia = '1st fri'
                    try:
                        sched.reschedule_job(id, trigger='cron', day=dia, hour=hora, minute=minuto)
                    except:
                        limpa_apscheduler_regs = db.session.query(jobs).delete()
                        db.session.commit()
                        print('** Tentativa de agendamento falhou. Limpando tabela do APScheduler e tentando novamente.')   
                        sched.add_job(trigger='cron', id=id, func=envia_planos, day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                        sched.start() 
                elif periodicidade == 'Nenhuma':
                    msg =  ('*** O '+id+' será CANCELADO. Não haverá envios automáticos. ***')
                    print(msg)
                    sched.remove_job(id)    

            else:
            
                # como não enconcontrou job agendado, cria um job com os parãmetros informados pelo usuário
                if periodicidade == 'Diária':
                    msg = ('*** O '+id+' será AGENDADO como DIÁRIO, rodando de segunda a sexta-feira, às '+str(hora)+':'+str(minuto)+' ***')
                    print(msg)
                    dia_semana = 'mon-fri'
                    sched.add_job(trigger='cron', id=id, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                    sched.start()
                elif periodicidade == 'Semanal':
                    msg = ('*** O '+id+' será AGENDADO para SEMANAL, rodando toda sexta-feira, às '+str(hora)+':'+str(minuto)+' ***')
                    print(msg)
                    dia_semana = 'fri'
                    sched.add_job(trigger='cron', id=id, func=envia_planos, day_of_week=dia_semana, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)  
                    sched.start()
                elif periodicidade == 'Mensal':
                    msg = ('*** O '+id+' será AGENDADO para MENSAL,  rodando na primeira sexta-feira de cada mês, às '+str(hora)+':'+str(minuto)+' ***')
                    print(msg)
                    dia = '1st fri'
                    sched.add_job(trigger='cron', id=id, func=envia_planos, day=dia, hour=hora, minute=minuto, misfire_grace_time=3600, coalesce=True)
                    sched.start()
                elif periodicidade == 'Nenhuma':
                    msg =  ('*** Não há '+id+' para cancelar. Comando ignorado. ***')
                    print(msg)

                registra_log_auto(current_user.id, 'Agendamento de reenvio: '+ str(periodicidade) +' - '+ str(hora) +':'+ str(minuto))
                flash(msg,'sucesso')    

        return render_template('index.html')  

    # verifica agendamentos existentes
    job_agendado_envio   = db.session.query(jobs).filter(jobs.id=='job_envia_planos').first()
    job_agendado_reenvio = db.session.query(jobs).filter(jobs.id=='job_envia_planos_novamente').first()
    prox_exec_envio = ''
    if job_agendado_envio:
        prox_exec_envio = datetime.fromtimestamp(job_agendado.next_run_time)
    prox_exec_reenvio = ''
    if job_agendado_reenvio:
        prox_exec_reenvio = datetime.fromtimestamp(job_agendado.next_run_time)    

    # joga dados, caso existam, para a tela
    
    return render_template('jobs.html', job_agendado_envio=job_agendado_envio, 
                                        job_agendado_reenvio=job_agendado_reenvio, 
                                        prox_exec_envio=prox_exec_envio, 
                                        prox_exec_reenvio=prox_exec_reenvio, 
                                        form=form)        
