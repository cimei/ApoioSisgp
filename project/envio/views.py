"""
.. topic:: Envio (views)

    Procedimentos relacionados ao envio de dados (planos e atividades) ao orgão superior.


.. topic:: Ações relacionadas ao envio

    * lista_a_enviar: Lista planos que estão aptos ao envio 

"""

# views.py na pasta envio

from flask import render_template,url_for,flash, redirect, request, Blueprint, send_from_directory
from flask_login import current_user

from sqlalchemy.sql import label
from sqlalchemy import func, distinct, or_

from project import db
from project.models import Pactos_de_Trabalho, Pessoas, Unidades, catdom,\
                           Pactos_de_Trabalho_Atividades, VW_Pactos, VW_Atividades_Pactos

from project.usuarios.views import registra_log_auto                           

from project.consultas.forms import PeriodoForm

from werkzeug.utils import secure_filename

import requests
import json
from datetime import datetime, date, timedelta, time
import os

envio = Blueprint('envio',__name__, template_folder='templates')

## lista planos avaliados que não foram enviados ainda 

@envio.route('/lista_a_enviar')
def lista_a_enviar():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos planos que estão aptos ao envio.                               |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    if os.getenv('APIPGDME_URL') != None and os.getenv('APIPGDME_URL') != "" and \
       os.getenv('APIPGDME_AUTH_USER') != None and os.getenv('APIPGDME_AUTH_USER') != "" and \
       os.getenv('APIPGDME_AUTH_PASSWORD') != None and os.getenv('APIPGDME_AUTH_PASSWORD') != "":   

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

        demandas = db.session.query(Pactos_de_Trabalho.pactoTrabalhoId,
                                    catdom_1.c.descricao,
                                    Pactos_de_Trabalho.situacaoId,
                                    ativs.c.qtd_ativs,
                                    ativs_com_nota.c.qtd_com_nota)\
                                .filter(catdom_1.c.descricao == 'Executado',
                                        ativs_com_nota.c.qtd_com_nota != None,
                                        ativs_com_nota.c.qtd_com_nota ==  ativs.c.qtd_ativs)\
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

        n_enviados = []

        for d in demandas:

            r = requests.get(os.getenv('APIPGDME_URL') + '/plano_trabalho/' + d.pactoTrabalhoId.urn[9:], headers= head)

            if r.ok == False:
                n_enviados.append(d.pactoTrabalhoId.urn[9:])

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
                                .filter(Pactos_de_Trabalho.pactoTrabalhoId.in_(n_enviados))\
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
                                            n_enviados = n_enviados,
                                            enviados = len(demandas) - planos_count,
                                            lista = lista)

    else:

        flash ('Credenciais de envio não informadas no deploy do aplicativo!','erro') 

        return render_template('index.html')                                 

## enviar planos 

@envio.route('<n_enviados>/enviar_planos', methods = ['GET', 'POST'])
def enviar_planos(n_enviados):
    """
    +---------------------------------------------------------------------------------------+
    |Envia planos.                                                                          |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
 
    # pega token de acesso à API de envio de dados

    string = 'grant_type=&username='+os.getenv('APIPGDME_AUTH_USER')+'&password='+os.getenv('APIPGDME_AUTH_PASSWORD')+'&scope=&client_id=&client_secret='

    headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/json"}

    api_url_login = os.getenv('APIPGDME_URL') + '/auth/jwt/login'

    response = requests.post(api_url_login, headers=headers, data=json.dumps(string))

    rlogin_json = response.json()

    token = rlogin_json['access_token']
    tipo =  rlogin_json['token_type']       

    # indicador de planos enviados com sucesso 
    sucesso = 0

    # pega todos os planos via query da aplicação API/CADE
    #l = n_enviados.replace('[','').replace(']','').replace("'","").replace(',','').split()
    l = n_enviados.replace("['","").replace("']",'').split()

    planos = db.session.query(VW_Pactos).filter(VW_Pactos.id_pacto.in_(l)).all()
    qtd_planos = len(planos)

    # para cada plano, monta o dados do dicionário 
    for p in planos:

        dic_envio = {}

        dic_envio['cod_plano']       = p.id_pacto.urn[9:].upper()
        dic_envio['situacao']        = p.situacao
        dic_envio['matricula_siape'] = int(p.matricula_siape)
        dic_envio['cpf']             = p.cpf
        dic_envio['nome_participante']      = p.nome_participante
        dic_envio['cod_unidade_exercicio']  = p.cod_unidade_exercicio if p.cod_unidade_exercicio is not None else 0
        dic_envio['nome_unidade_exercicio'] = p.nome_unidade_exercicio
        dic_envio['modalidade_execucao']    = p.modalidade_execucao
        dic_envio['carga_horaria_semanal']  = p.carga_horaria_semanal
        dic_envio['data_inicio']         = p.data_inicio.strftime('%Y-%m-%d')
        dic_envio['data_fim']            = p.data_fim.strftime('%Y-%m-%d')
        dic_envio['carga_horaria_total'] = p.carga_horaria_total 
        dic_envio['data_interrupcao']    = p.data_interrupcao if p.data_interrupcao is None else p.data_interrupcao.strftime('%Y-%m-%d')
        dic_envio['entregue_no_prazo']   = bool(p.entregue_no_prazo)
        dic_envio['horas_homologadas']   = p.horas_homologadas
        dic_envio['atividades'] = []

        # pega as atividades de cada plano
        ativs = db.session.query(VW_Atividades_Pactos)\
                        .filter(VW_Atividades_Pactos.id_pacto == p.id_pacto)\
                        .all()

        # para cada atividade, monta o resto do dicionário (key 'atividades')
        for a in ativs:

            dic_envio['atividades'].append({'id_atividade': a.id_produto.urn[9:].upper(),
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
                                            'data_avaliacao': a.data_avaliacao if a.data_avaliacao is None else a.data_avaliacao.strftime('%Y-%m-%d'),
                                            'justificativa': a.justificativa}) 

        # prepara headers do put
        plano_id = p.id_pacto
        headers = {'Content-Type': "application/json", 'Accept': "application/json", 'Authorization': 'Bearer {}'.format(token)}
        
        # gravando dicionário com dados de cada plano em um arquivo
        # with open('plano_body_dict.json', 'w', encoding='utf-8') as f:
        #     json.dump(dic_envio, f, ensure_ascii=False, indent=4)
        # # lendo arquivo gerado com dados de um plano
        # with open('plano_body_dict.json', 'rb') as f:
        #     r_put = requests.put(os.getenv('APIPGDME_URL') + '/plano_trabalho/'+plano_id, headers=headers, data=f)      

        # faz o put na API via dumps json do dicionário    
        r_put = requests.put(os.getenv('APIPGDME_URL') + '/plano_trabalho/'+ plano_id.urn[9:].upper(), headers= headers, data=json.dumps(dic_envio, allow_nan=True, indent=4))

        # para cada put com sucesso (status_code < 400) acumula 1 no sucesso
        if r_put.ok:
            sucesso += 1

    if sucesso == qtd_planos:
        registra_log_auto(current_user.id, str(qtd_planos) + ' Plano(s) enviado(s) com sucesso: ' + n_enviados)
        flash(str(qtd_planos) + ' Planos enviados com sucesso','sucesso') # todos os planos enviados com sucesso
    else:
        registra_log_auto(current_user.id, 'Na tentativa de envio de ' + str(qtd_planos) + ' Planos,' + str(sucesso) + ' foram enviados.')
        flash('Houve problema no envio dos Planos: Dos ' + str(qtd_planos) + ' Planos,' + str(sucesso) + ' foram enviados.','erro') # alguma coisa deu errado

    return redirect (url_for('envio.lista_a_enviar'))


## enviar plano específico 

@envio.route('<plano_id>/<lista>/enviar_um_plano', methods = ['GET', 'POST'])
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

    response = requests.post(api_url_login, headers=headers, data=json.dumps(string))

    rlogin_json = response.json()

    token = rlogin_json['access_token']
    tipo =  rlogin_json['token_type']    

    # indicador de plano enviado com sucesso 
    sucesso = False

    # pega o plano informado via query da aplicação API/CADE
    plano = db.session.query(VW_Pactos).filter(VW_Pactos.id_pacto == plano_id).first()

    # para o plano, monta dados no dicionário 

    dic_envio = {}

    dic_envio['cod_plano']       = plano.id_pacto.urn[9:].upper()
    dic_envio['situacao']        = plano.situacao
    dic_envio['matricula_siape'] = int(plano.matricula_siape)
    dic_envio['cpf']             = plano.cpf
    dic_envio['nome_participante']      = plano.nome_participante
    dic_envio['cod_unidade_exercicio']  = plano.cod_unidade_exercicio if plano.cod_unidade_exercicio is not None else 0
    dic_envio['nome_unidade_exercicio'] = plano.nome_unidade_exercicio
    dic_envio['modalidade_execucao']    = plano.modalidade_execucao
    dic_envio['carga_horaria_semanal']  = plano.carga_horaria_semanal
    dic_envio['data_inicio']         = plano.data_inicio.strftime('%Y-%m-%d')
    dic_envio['data_fim']            = plano.data_fim.strftime('%Y-%m-%d')
    dic_envio['carga_horaria_total'] = plano.carga_horaria_total
    dic_envio['data_interrupcao']    = plano.data_interrupcao if plano.data_interrupcao is None else plano.data_interrupcao.strftime('%Y-%m-%d')
    dic_envio['entregue_no_prazo']   = bool(plano.entregue_no_prazo)
    dic_envio['horas_homologadas']   = plano.horas_homologadas
    dic_envio['atividades'] = []

    # pega as atividades do plano
    ativs = db.session.query(VW_Atividades_Pactos)\
                        .filter(VW_Atividades_Pactos.id_pacto == plano.id_pacto)\
                        .all()

    # para cada atividade, monta o resto do dicionário (key 'atividades')
    for a in ativs:

        dic_envio['atividades'].append({'id_atividade': a.id_produto.urn[9:].upper(),
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
                                        'data_avaliacao': a.data_avaliacao if a.data_avaliacao is None else a.data_avaliacao.strftime('%Y-%m-%d'),
                                        'justificativa': a.justificativa}) 

    # prepara headers do put
    headers = {'Content-Type': "application/json", 'Accept': "application/json", 'Authorization': 'Bearer {}'.format(token)}
    
    # gravando dicionário com dados de cada plano em um arquivo
    # with open('plano_body_dict.json', 'w', encoding='utf-8') as f:
    #     json.dump(dic_envio, f, ensure_ascii=False, indent=4)
    # # lendo arquivo gerado com dados de um plano
    # with open('plano_body_dict.json', 'rb') as f:
    #     r_put = requests.put(os.getenv('APIPGDME_URL') + '/plano_trabalho/'+plano_id, headers=headers, data=f)      

    # faz o put na API via dumps json do dicionário    
    r_put = requests.put(os.getenv('APIPGDME_URL') + '/plano_trabalho/'+ plano_id.upper(), headers=headers, data=json.dumps(dic_envio))

    # para put com sucesso (status_code < 400) passa true no sucesso
    if r_put.ok:
        sucesso = True

    if sucesso:
        if lista == 'enviados':
            registra_log_auto(current_user.id, 'Plano reenviado com sucesso: ' + str(plano_id))
            flash('Plano reenviado com sucesso!','sucesso')
        elif lista == 'n_enviados':
            registra_log_auto(current_user.id, 'Plano enviado com sucesso: ' + str(plano_id))
            flash('Plano enviado com sucesso!','sucesso')   
    else:
        if lista == 'enviados':
            registra_log_auto(current_user.id, 'Erro na tentativa de reenvio do Plano: ' + str(plano_id))
            flash('Erro na tentativa de reenvio do Plano: ' + str(plano_id),'erro') 
        elif lista == 'n_enviados':
            registra_log_auto(current_user.id, 'Erro na tentativa de envio do Plano: ' + str(plano_id))
            flash('Erro na tentativa de envio do Plano: ' + str(plano_id),'erro')     

    if lista == 'n_enviados':
        return redirect (url_for('envio.lista_a_enviar'))
    elif lista == 'enviados':
        return redirect (url_for('envio.lista_enviados'))    


## lista planos enviados 

@envio.route('/lista_enviados')
def lista_enviados():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos planos que constam da API.                                     |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    
    if os.getenv('APIPGDME_URL') != None and os.getenv('APIPGDME_URL') != "" and \
       os.getenv('APIPGDME_AUTH_USER') != None and os.getenv('APIPGDME_AUTH_USER') != "" and \
       os.getenv('APIPGDME_AUTH_PASSWORD') != None and os.getenv('APIPGDME_AUTH_PASSWORD') != "":  

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

        demandas = db.session.query(Pactos_de_Trabalho.pactoTrabalhoId,
                                    catdom_1.c.descricao,
                                    Pactos_de_Trabalho.situacaoId,
                                    ativs.c.qtd_ativs,
                                    ativs_com_nota.c.qtd_com_nota)\
                                .filter(catdom_1.c.descricao == 'Executado',
                                        ativs_com_nota.c.qtd_com_nota != None,
                                        ativs_com_nota.c.qtd_com_nota ==  ativs.c.qtd_ativs)\
                                .join(catdom_1, catdom_1.c.catalogoDominioId == Pactos_de_Trabalho.situacaoId)\
                                .outerjoin(ativs_com_nota, ativs_com_nota.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .outerjoin(ativs, ativs.c.pactoTrabalhoId == Pactos_de_Trabalho.pactoTrabalhoId)\
                                .all() 

        # pega token de acesso à API de envio de dados

        string = 'grant_type=&username='+os.getenv('APIPGDME_AUTH_USER')+'&password='+os.getenv('APIPGDME_AUTH_PASSWORD')+'&scope=&client_id=&client_secret='

        headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/json"}

        api_url_login = os.getenv('APIPGDME_URL') + '/auth/jwt/login'

        response = requests.post(api_url_login, headers=headers, data=json.dumps(string))

        rlogin_json = response.json()

        token = rlogin_json['access_token']
        tipo =  rlogin_json['token_type']       

        head = {'Authorization': 'Bearer {}'.format(token)}

        enviados = []

        for d in demandas:

            r = requests.get(os.getenv('APIPGDME_URL') + '/plano_trabalho/' + d.pactoTrabalhoId.urn[9:].upper(), headers= head)

            if r.ok:
                enviados.append(d.pactoTrabalhoId)

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
                                            n_enviados = len(demandas) - planos_count,
                                            enviados = enviados,
                                            lista = lista)

    else:

        flash ('Credenciais de envio não informadas no deploy do aplicativo!','erro') 

        return render_template('index.html')                                          

