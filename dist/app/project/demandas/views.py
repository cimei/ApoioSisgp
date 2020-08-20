"""
.. topic:: Demandas (views)

    Compõe o trabalho diário da coordenação. Surgem na medida que as tarefas são executadas na coordenação.
    O técnico cria a demanda para si em função de uma solicitação superior, de um colega, vinda de fora ou até mesmo
    por iniciativa própria, quando se tratar de necessidade de trabalho.

    Uma demanda tem atributos que são registrados no momento de sua criação:

    * Processo SEI relacionado (obrigatório)
    * Convênio e ano do convênio (quando for o caso)
    * Tipo (obrigatório e conforme atividades específicas da coordenação)
    * Título
    * Descrição
    * Se necessita despacho/apreciação superior
    * Se está concluída ou em andamento

.. topic:: Ações relacionadas às demandas

    * Listar tipos de demanda: lista_tipos
    * Atualizar tipos de demandas: tipos_update
    * Inserir novo tipo de demanda: cria_tipo_demanda
    * Criar demandas: cria_demanda
    * Confirma criação de demanda: confirma_cria_demanda
    * Criar demamanda a partir de um acordo ou convênio: acordo_convenio_demanda
    * Confirma criação de demanda a partir de acordo ou convênio: confirma_acordo_convenio_demanda
    * Ler demandas: demanda
    * Listar demandas: list_demandas
    * Lista demandas não concluídas - lista RDU: prioriza
    * Atualizar demandas: update_demanda
    * Transferir demanda: transfer_demanda
    * Avocar demanda: avocar_demanda
    * Remover demandas: delete_demanda
    * Procurar demandas: pesquisa_demanda
    * Lista resultado da procura: list_pesquisa
    * Registrar despachos: cria_despacho
    * Registrar providências: cria_providencia
    * Resumo e estatísticas das demandas: demandas_resumo (em construção...)

"""

# views.py dentro da pasta demandas

from flask import render_template, url_for, flash, request, redirect, Blueprint, abort
from flask_login import current_user, login_required
from sqlalchemy import or_, and_, func
from sqlalchemy.sql import label
from project import db
from project.models import Demanda, Providencia, Despacho, User, Tipos_Demanda, DadosSEI, Acordo
from project.demandas.forms import DemandaForm1, DemandaForm, Demanda_ATU_Form, DespachoForm, ProvidenciaForm, PesquisaForm,\
                                   Tipos_DemandaForm, TransferDemandaForm, Admin_Altera_Demanda_Form, PesosForm
from datetime import datetime, date
#from sys

demandas = Blueprint("demandas",__name__,
                        template_folder='templates/demandas')

#
## lista tipos de demanda

@demandas.route('/lista_tipos')
def lista_tipos():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos tipos de demanda.                                              |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    form = Tipos_DemandaForm()
    ## lê tabela tipos_demanda
    tipos = db.session.query(Tipos_Demanda.id,
                             Tipos_Demanda.tipo,
                             Tipos_Demanda.relevancia)\
                      .order_by(Tipos_Demanda.relevancia,Tipos_Demanda.tipo).all()

    quantidade = len(tipos)

    tipos_s = []

    for tipo in tipos:
        tipo_s = list(tipo)
        tipo_s.append(dict(form.relevancia.choices)[str(tipo.relevancia)])
        tipos_s.append(tipo_s)

    return render_template('lista_tipos.html', tipos = tipos_s, quantidade=quantidade)

### atualiza lista de tipos de demanda

@demandas.route("/<int:id>/update_tipo", methods=['GET', 'POST'])
@login_required
def tipos_update(id):
    """
    +----------------------------------------------------------------------------------------------+
    |Permite atualizar os tipos de demanda.                                                        |
    |                                                                                              |
    |Recebe o id do tipo de demanda como parâmetro.                                                |
    +----------------------------------------------------------------------------------------------+
    """

    tipo = Tipos_Demanda.query.get_or_404(id)

    tipo_ant = tipo.tipo

    form = Tipos_DemandaForm()

    if form.validate_on_submit():

        tipo.tipo       = form.tipo.data
        tipo.relevancia = form.relevancia.data

        db.session.commit()

        if form.tipo.data != tipo_ant:
            demandas_alterar_tipo = db.session.query(Demanda).filter(Demanda.tipo == tipo_ant).all()
            for demanda in demandas_alterar_tipo:
                demanda.tipo = form.tipo.data
            db.session.commit()

        flash('Tipo de demanda atualizado!')
        return redirect(url_for('demandas.lista_tipos'))
    # traz a informação atual do programa
    elif request.method == 'GET':
        form.tipo.data = tipo.tipo
        form.relevancia.data = str(tipo.relevancia)

    return render_template('add_tipo.html',
                           form=form)

### inserir tipo de demanda

@demandas.route("/cria_tipo_demanda", methods=['GET', 'POST'])
@login_required
def cria_tipo_demanda():
    """
    +---------------------------------------------------------------------------------------+
    |Permite inseir tipo na lista de tipos de demanda.                                      |
    +---------------------------------------------------------------------------------------+
    """

    form = Tipos_DemandaForm()

    if form.validate_on_submit():
        tipo = Tipos_Demanda(tipo       = form.tipo.data,
                             relevancia = form.relevancia.data)
        db.session.add(tipo)
        db.session.commit()
        flash('Tipo de demanda inserido!')
        return redirect(url_for('demandas.lista_tipos'))

    return render_template('add_tipo.html', form=form)

######################
# CRIANDO uma demanda
##############################

# Verificando se já existe demanda semelhante

@demandas.route('/criar',methods=['GET','POST'])
@login_required
def cria_demanda():
    """+--------------------------------------------------------------------------------------+
       |Inicia o procedimento de registro de uma demanda.                                     |
       +--------------------------------------------------------------------------------------+
    """
    if current_user.ativo == False:
        abort(403)

    # o choices do campo tipo são definidos aqui e não no form
    tipos = db.session.query(Tipos_Demanda.tipo)\
                      .order_by(Tipos_Demanda.tipo).all()
    lista_tipos = [(t[0],t[0]) for t in tipos]
    lista_tipos.insert(0,('',''))
    form = DemandaForm1()
    form.tipo.choices = lista_tipos

    if form.validate_on_submit():

        verif_demanda = db.session.query(Demanda)\
                                  .filter(Demanda.sei == form.sei.data,
                                          Demanda.tipo == form.tipo.data,
                                          Demanda.conclu == False).first()

        if verif_demanda == None:
            mensagem = 'OK'
        else:
            mensagem = 'KO'+str(verif_demanda.id)

        return redirect(url_for('demandas.confirma_cria_demanda',sei=str(form.sei.data).split('/')[0]+'_'+str(form.sei.data).split('/')[1],
                                                                 tipo=form.tipo.data,
                                                                 mensagem=mensagem))

    return render_template('add_demanda1.html', form = form)

# CONFIRMANDO CRIAÇÃO DE demanda

@demandas.route('/<sei>/<tipo>/<mensagem>/confirma_criar',methods=['GET','POST'])
@login_required
def confirma_cria_demanda(sei,tipo,mensagem):
    """+--------------------------------------------------------------------------------------+
       |Confirma criação de demanda com os dados inseridos no respectivo formulário.          |
       |O título tem no máximo 140 caracteres.                                                |
       +--------------------------------------------------------------------------------------+
    """
    form = DemandaForm()

    if form.validate_on_submit():

        verif_sei = db.session.query(DadosSEI.id).filter(DadosSEI.sei == str(sei).split('_')[0]+'/'+str(sei).split('_')[1]).first()

        if verif_sei == None and form.convênio.data != '':
            dadosSEI = DadosSEI(nr_convenio = form.convênio.data,
                                ano         = form.ano_convênio.data,
                                sei         = str(sei).split('_')[0]+'/'+str(sei).split('_')[1],
                                epe         = '*',
                                uf          = '*',
                                programa    = form.programa.data,
                               )
            db.session.add(dadosSEI)
            db.session.commit()
            flash('Registro SEI criado a partir desta demanda!','sucesso')

        data_conclu = None
        data_env_despacho = None

        if form.conclu.data == True:
            form.necessita_despacho.data = False
            data_conclu = datetime.now()

        if form.convênio.data == '':
            ano = ''
        else:
            ano = form.ano_convênio.data

        if form.necessita_despacho.data == True:
            data_env_despacho = datetime.now()

        demanda = Demanda(programa              = form.programa.data,
                          sei                   = str(sei).split('_')[0]+'/'+str(sei).split('_')[1],
                          convênio              = form.convênio.data,
                          ano_convênio          = ano,
                          tipo                  = tipo,
                          data                  = datetime.now(),
                          user_id               = current_user.id,
                          titulo                = form.titulo.data,
                          desc                  = form.desc.data,
                          necessita_despacho    = form.necessita_despacho.data,
                          necessita_despacho_cg = False,
                          conclu                = form.conclu.data,
                          data_conclu           = data_conclu,
                          urgencia              = form.urgencia.data,
                          data_env_despacho     = data_env_despacho)

        db.session.add(demanda)
        db.session.commit()
        flash ('Demanda criada!','sucesso')
        return redirect(url_for('demandas.list_demandas'))

    if mensagem != 'OK':
        flash ('ATENÇÃO: Existe uma demanda não concluída para este processo sob o mesmo tipo. Verifique demanda '+mensagem[2:],'perigo')
    else:
        flash ('OK, favor preencher os demais campos.','sucesso')

    return render_template('add_demanda.html', form = form, sei=sei, tipo=tipo)



#CRIANDO uma demanda a partir de um acordo ou convênio

# VERIFICANDO
@demandas.route('/<prog>/<sei>/<conv>/<ano>/criar',methods=['GET','POST'])
@login_required
def acordo_convenio_demanda(prog,sei,conv,ano):
    """+--------------------------------------------------------------------------------------+
       |Inicia o procedimento de registro de uma demanda a partir de um acordo ou convênio.   |
       +--------------------------------------------------------------------------------------+
    """
    if current_user.ativo == False:
        abort(403)

    # o choices do campo tipo são definidos aqui e não no form
    tipos = db.session.query(Tipos_Demanda.tipo)\
                      .order_by(Tipos_Demanda.tipo).all()
    lista_tipos = [(t[0],t[0]) for t in tipos]
    lista_tipos.insert(0,('',''))
    form = DemandaForm1()
    form.tipo.choices = lista_tipos

    if form.validate_on_submit():

        verif_demanda = db.session.query(Demanda)\
                                  .filter(Demanda.sei == form.sei.data,
                                          Demanda.tipo == form.tipo.data,
                                          Demanda.conclu == False).first()

        if verif_demanda == None:
            mensagem = 'OK'
        else:
            mensagem = 'KO'+str(verif_demanda.id)

        return redirect(url_for('demandas.confirma_acordo_convenio_demanda',
                                                        prog=prog,
                                                        sei=str(form.sei.data).split('/')[0]+'_'+str(form.sei.data).split('/')[1],
                                                        conv=conv,
                                                        ano=ano,
                                                        tipo=form.tipo.data,
                                                        mensagem=mensagem))

    form.sei.data = str(sei).split('_')[0]+'/'+str(sei).split('_')[1]

    return render_template('add_demanda1.html', form = form)


# CONFIRMANDO

@demandas.route('/<prog>/<sei>/<conv>/<ano>/<tipo>/<mensagem>/criar',methods=['GET','POST'])
@login_required
def confirma_acordo_convenio_demanda(prog,sei,conv,ano,tipo,mensagem):
    """+--------------------------------------------------------------------------------------+
       |Registra uma demanda a partir de um acordo ou convênio.                               |
       |                                                                                      |
       |Atenção para o Título da Demanda que não pode passar de 140 caracteres.               |
       +--------------------------------------------------------------------------------------+
    """
    form = DemandaForm()

    if form.validate_on_submit():

        data_conclu = None
        data_env_despacho = None

        if form.conclu.data == True:
            form.necessita_despacho.data = False
            data_conclu = datetime.now()

        if form.convênio.data == '':
            ano = ''
        else:
            ano = form.ano_convênio.data

        if form.necessita_despacho.data == True:
            data_env_despacho = datetime.now()

        demanda = Demanda(programa              = form.programa.data,
                          sei                   = str(sei).split('_')[0]+'/'+str(sei).split('_')[1],
                          convênio              = form.convênio.data,
                          ano_convênio          = ano,
                          tipo                  = tipo,
                          data                  = datetime.now(),
                          user_id               = current_user.id,
                          titulo                = form.titulo.data,
                          desc                  = form.desc.data,
                          necessita_despacho    = form.necessita_despacho.data,
                          necessita_despacho_cg = False,
                          conclu                = form.conclu.data,
                          data_conclu           = data_conclu,
                          urgencia              = form.urgencia.data,
                          data_env_despacho     = data_env_despacho)

        db.session.add(demanda)
        db.session.commit()
        flash ('Demanda criada!','sucesso')
        return redirect(url_for('demandas.list_demandas'))
        #return redirect(url_for('demandas.demandas'))

    form.programa.data       = prog
    #form.tipo.data           = tipo
    #form.sei.data            = str(sei).split('_')[0]+'/'+str(sei).split('_')[1]

    if conv == '0':
        form.convênio.data   = ''
    else:
        form.convênio.data   = conv
    if ano == '0':
        form.ano_convênio.data   = ''
    else:
        form.ano_convênio.data   = ano

    if mensagem != 'OK':
        flash ('ATENÇÃO: Existe uma demanda não concluída para este processo sob o mesmo tipo. Verifique demanda '+mensagem[2:],'perigo')
    else:
        flash ('OK, favor preencher os demais campos.','sucesso')

    return render_template('add_demanda.html', form = form, sei = sei, tipo = tipo)


#lendo uma demanda

@demandas.route('/<int:demanda_id>')
def demanda(demanda_id):
    """+---------------------------------------------------------------------------------+
       |Resgata, para leitura, uma demanda, bem como providências e despachos associados.|
       |                                                                                 |
       |Recebe o ID da demanda como parâmetro.                                           |
       +---------------------------------------------------------------------------------+
    """
    #page = request.args.get('page', 1, type=int)

    demanda = Demanda.query.get_or_404(demanda_id)

    providencias = db.session.query(Providencia.demanda_id,
                                    Providencia.texto,
                                    Providencia.data,
                                    Providencia.user_id,
                                    label('username',User.username),
                                    User.despacha,
                                    User.despacha2)\
                                    .outerjoin(User, Providencia.user_id == User.id)\
                                    .filter(Providencia.demanda_id == demanda_id)\
                                    .order_by(Providencia.data.desc()).all()

    despachos = db.session.query(Despacho.demanda_id,
                                 Despacho.texto,
                                 Despacho.data,
                                 Despacho.user_id,
                                 label('username',User.username +' - DESPACHO'),
                                 User.despacha,
                                 User.despacha2)\
                                .filter_by(demanda_id=demanda_id)\
                                .outerjoin(User, Despacho.user_id == User.id)\
                                .order_by(Despacho.data.desc()).all()

    pro_des = providencias + despachos
    pro_des.sort(key=lambda ordem: ordem.data,reverse=True)

    if current_user.is_anonymous:
        leitor_despacha = 'False'
    else:
        if str(current_user).split(';')[1] == 'True' or str(current_user).split(';')[2] == 'True':
            leitor_despacha = 'True'
        else:
            leitor_despacha = 'False'

    if demanda.data_conclu != None:
        data_conclu = demanda.data_conclu.strftime('%x')
    else:
        data_conclu = ''

    return render_template('ver_demanda.html',
                            id                 = demanda.id,
                            programa           = demanda.programa,
                            sei                = demanda.sei,
                            convênio           = demanda.convênio,
                            ano_convênio       = demanda.ano_convênio,
                            data               = demanda.data,
                            tipo               = demanda.tipo,
                            titulo             = demanda.titulo,
                            desc               = demanda.desc,
                            necessita_despacho = demanda.necessita_despacho,
                            necessita_despacho_cg = demanda.necessita_despacho_cg,
                            conclu             = demanda.conclu,
                            data_conclu        = data_conclu,
                            post               = demanda,
                            leitor_despacha    = leitor_despacha,
                            pro_des            = pro_des)

#vendo ultimas demandas

@demandas.route('/demandas')
def list_demandas():
    """
        +----------------------------------------------------------------------+
        |Lista todas as demandas, bem como providências e despachos associados.|
        +----------------------------------------------------------------------+
    """
    pesquisa = False

    page = request.args.get('page', 1, type=int)

    providencias = db.session.query(Providencia.demanda_id,
                                    Providencia.texto,
                                    Providencia.data,
                                    Providencia.user_id,
                                    label('username',User.username))\
                                    .outerjoin(User, Providencia.user_id == User.id)\
                                    .order_by(Providencia.data.desc()).all()

    despachos = db.session.query(Despacho.demanda_id,
                                 Despacho.texto,
                                 Despacho.data,
                                 Despacho.user_id,
                                 label('username',User.username +' - DESPACHO'),
                                 User.despacha,
                                 User.despacha2)\
                                .outerjoin(User, Despacho.user_id == User.id)\
                                .order_by(Despacho.data.desc()).all()

    pro_des = providencias + despachos
    pro_des.sort(key=lambda ordem: ordem.data,reverse=True)

    demandas_count = Demanda.query.count()

    demandas       = Demanda.query.order_by(Demanda.data.desc()).paginate(page=page,per_page=8)


    return render_template ('demandas.html',pesquisa=pesquisa,demandas=demandas,
                            pro_des = pro_des, demandas_count = demandas_count)

#
#lista das demandas que aguardam despacho seguindo ordem de prioridades

@demandas.route('/<peso_R>/<peso_D>/<peso_U>/<coord>/prioriza', methods=['GET', 'POST'])
def prioriza(peso_R,peso_D,peso_U,coord):
    """
        +---------------------------------------------------------------------------+
        |Lista as demandas não concluídas em uma ordem de prioridades - lista RDU.  |
        +---------------------------------------------------------------------------+
    """

    #
    form = PesosForm()

    if form.validate_on_submit():

        peso_R = form.peso_R.data
        peso_D = form.peso_D.data
        peso_U = form.peso_U.data
        if form.coord.data != '':
            coord  = form.coord.data
        else:
            coord = '*'

        return redirect(url_for('demandas.prioriza',peso_R=peso_R,peso_D=peso_D,peso_U=peso_U,coord=coord))

    else:

        form.peso_R.data = peso_R
        form.peso_D.data = peso_D
        form.peso_U.data = peso_U
        form.coord.data  = coord

        hoje = datetime.today()

        ## calcula vida média por tipo de demanda

        demandas_conclu_por_tipo = db.session.query(Demanda.tipo,label('qtd',func.count(Demanda.id)))\
                                      .filter(Demanda.conclu == True)\
                                      .order_by(Demanda.tipo)\
                                      .group_by(Demanda.tipo)

        vida_m_por_tipo_dict = {}

        for tipo in demandas_conclu_por_tipo:
            demandas_datas = db.session.query(Demanda.data,Demanda.data_conclu)\
                                        .filter(Demanda.tipo == tipo.tipo, Demanda.data_conclu != None)

            vida = 0
            vida_m = 0

            for dia in demandas_datas:

                vida += (dia.data_conclu - dia.data).days

            if len(list(demandas_datas)) > 0:
                vida_m = round(vida/len(list(demandas_datas)))
            else:
                vida_m = 0

            vida_m_por_tipo_dict[tipo.tipo] = vida_m

        ##

        demandas_s = []

        ufs = db.session.query(DadosSEI.sei, DadosSEI.uf).all()

        if coord == '*':
            demandas       = db.session.query(Demanda.id,
                                              Demanda.programa,
                                              Demanda.sei,
                                              Demanda.tipo,
                                              Demanda.data,
                                              Demanda.necessita_despacho,
                                              Demanda.necessita_despacho_cg,
                                              Demanda.urgencia,
                                              Demanda.convênio,
                                              User.username)\
                            .join(User, Demanda.user_id == User.id)\
                            .order_by(Demanda.data)\
                            .filter(Demanda.conclu == False)\
                            .all()
        else:
            demandas       = db.session.query(Demanda.id,
                                              Demanda.programa,
                                              Demanda.sei,
                                              Demanda.tipo,
                                              Demanda.data,
                                              Demanda.necessita_despacho,
                                              Demanda.necessita_despacho_cg,
                                              Demanda.urgencia,
                                              Demanda.convênio,
                                              User.username)\
                            .join(User, Demanda.user_id == User.id)\
                            .order_by(Demanda.data)\
                            .filter(Demanda.conclu == False, User.coord == coord)\
                            .all()


        quantidade = len(demandas)

        for demanda in demandas:
            # identifica UF
            if demanda.convênio != 0 and demanda.convênio != '':
                uf = db.session.query(DadosSEI.uf).filter_by(sei=demanda.sei).first()
            else:
                uf = db.session.query(Acordo.uf).filter_by(sei=demanda.sei).first()
            if uf == None:
                uf = ('*',)

            # identifica relevância
            relev = db.session.query(Tipos_Demanda.relevancia).filter_by(tipo=demanda.tipo).first()

            # calcula distância (momento)
            try:
                alvo = vida_m_por_tipo_dict[demanda.tipo]
            except KeyError:
                alvo = 999

            vigencia = (hoje - demanda.data).days

            if alvo == 0:
                distancia = 1
            else:
                if vigencia/alvo > 1.50:
                    distancia = 1
                elif vigencia/alvo < 0.5:
                    distancia = 3
                else:
                    distancia = 2

            # identifica urgência
            # --> constante no campo demanda.urgencia

            demanda_s = list(demanda)
            demanda_s.append(float(peso_R)*relev.relevancia + float(peso_D)*distancia + float(peso_U)*demanda.urgencia)
            demanda_s.append(str(relev.relevancia)+','+str(distancia)+','+str(demanda.urgencia))
            demanda_s.append(uf)

            demandas_s.append(demanda_s)

        # ordenar lista de demanda
        demandas_s.sort(key=lambda x: x[10])

        return render_template ('prioriza.html',demandas=demandas_s,quantidade=quantidade,form=form)

#atualizando uma demanda

@demandas.route("/<int:demanda_id>/update_demanda", methods=['GET','POST'])
@login_required
def update_demanda(demanda_id):
    """
    +---------------------------------------------------------------------------------------+
    |Permite que o autor da demanda, se logado, altere dados desta.                         |
    |                                                                                       |
    |Recebe o ID da demanda como parâmetro.                                                 |
    |                                                                                       |
    |Uma vez que a demanda é marcada como concluída, a necessidade de despacho é desmarcada.|
    +---------------------------------------------------------------------------------------+
    """
    demanda = Demanda.query.get_or_404(demanda_id)

    if demanda.author != current_user:
        abort(403)

    if current_user.ativo == False:
        abort(403)

    # o choices do campo tipo são definidos aqui e não no form
    tipos = db.session.query(Tipos_Demanda.tipo)\
                      .order_by(Tipos_Demanda.tipo).all()
    lista_tipos = [(t[0],t[0]) for t in tipos]
    lista_tipos.insert(0,('',''))
    form = Demanda_ATU_Form()
    form.tipo.choices = lista_tipos

    if form.validate_on_submit():

        demanda.programa              = form.programa.data
        demanda.sei                   = form.sei.data
        demanda.convênio              = form.convênio.data

        if form.ano_convênio.data == '':
            demanda.ano_convênio      = ''
        else:
            demanda.ano_convênio      = form.ano_convênio.data

        demanda.tipo                  = form.tipo.data
        demanda.titulo                = form.titulo.data
        demanda.desc                  = form.desc.data
        demanda.necessita_despacho    = form.necessita_despacho.data
        demanda.necessita_despacho_cg = form.necessita_despacho_cg.data

        if form.necessita_despacho.data == True:
            demanda.necessita_despacho_cg = False

        if form.necessita_despacho_cg.data == True:
            demanda.necessita_despacho = False

        if form.conclu.data == True:
            demanda.necessita_despacho    = False
            demanda.necessita_despacho_cg = False
            if demanda.conclu == False:
                demanda.data_conclu = datetime.now()
        else:
            data_conclu = None

        if form.necessita_despacho.data != form.necessita_despacho_cg.data:
            if demanda.data_env_despacho == None:
                demanda.data_env_despacho = datetime.now()

        demanda.conclu                = form.conclu.data
        demanda.urgencia              = form.urgencia.data

        db.session.commit()
        flash ('Demanda atualizada!','sucesso')
        return redirect(url_for('demandas.demanda',demanda_id=demanda.id))

    elif request.method == 'GET':
        form.programa.data              = demanda.programa
        form.sei.data                   = demanda.sei
        form.convênio.data              = demanda.convênio
        form.ano_convênio.data          = demanda.ano_convênio
        form.tipo.data                  = demanda.tipo
        form.titulo.data                = demanda.titulo
        form.desc.data                  = demanda.desc
        form.necessita_despacho.data    = demanda.necessita_despacho
        form.necessita_despacho_cg.data = demanda.necessita_despacho_cg
        form.conclu.data                = demanda.conclu
        form.urgencia.data              = str(demanda.urgencia)

    return render_template('atualiza_demanda.html', title='Update',form = form, demanda_id=demanda_id)

#
#transferir uma demanda para outro responsável

@demandas.route("/<int:demanda_id>/transfer_demanda", methods=['GET','POST'])
@login_required
def transfer_demanda(demanda_id):
    """
    +---------------------------------------------------------------------------------------+
    |Permite que o autor da demanda, se logado, passe sua demanda para outra pessoa.        |
    |                                                                                       |
    |Recebe o ID da demanda como parâmetro.                                                 |
    |                                                                                       |
    |É criada automaticamente uma providência, registrando a ação.                          |
    +---------------------------------------------------------------------------------------+
    """
    if current_user.ativo == False:
        abort(403)

    demanda = Demanda.query.get_or_404(demanda_id)

    if demanda.author != current_user:
        abort(403)

    form = TransferDemandaForm()

    if form.validate_on_submit():

        providencia = Providencia(demanda_id = demanda_id,
                                  data       = datetime.now(),
                                  texto      = 'DEMANDA TRANSFERIDA! Resp. anterior: ' + current_user.username + '.',
                                  user_id    = current_user.id)

        db.session.add(providencia)
        db.session.commit()

        demanda.user_id   = int(form.pessoa.data)

        db.session.commit()
        flash ('Demanda transferida!','sucesso')
        return redirect(url_for('demandas.demanda',demanda_id=demanda.id))

    return render_template('transfer_demanda.html', title='Update',form = form)

#
#avocar uma demanda

@demandas.route("/<int:demanda_id>/avocar_demanda", methods=['GET','POST'])
@login_required
def avocar_demanda(demanda_id):
    """
    +---------------------------------------------------------------------------------------+
    |Permite que o usuário corrente avoque uma demanda de outra pessoa                      |
    |                                                                                       |
    |Recebe o ID da demanda como parâmetro.                                                 |
    |                                                                                       |
    |É criada automaticamente uma providência, registrando a ação.                          |
    +---------------------------------------------------------------------------------------+
    """
    if current_user.ativo == False:
        abort(403)

    demanda = Demanda.query.get_or_404(demanda_id)

    providencia = Providencia(demanda_id = demanda_id,
                              data       = datetime.now(),
                              texto      = 'DEMANDA AVOCADA! Resp. anterior: ' + demanda.author.username + '.',
                              user_id    = current_user.id)

    db.session.add(providencia)
    db.session.commit()

    demanda.user_id   = current_user.id
    db.session.commit()

    flash ('Demanda avocada!','sucesso')

    return redirect(url_for('demandas.demanda',demanda_id=demanda.id))

#
#admin altera data de conclusão de uma demanda

@demandas.route("/<int:demanda_id>/admin_altera_demanda", methods=['GET','POST'])
@login_required
def admin_altera_demanda(demanda_id):
    """
    +---------------------------------------------------------------------------------------+
    |Permite que o admin altere a data de conclusão de uma demanda.                         |
    |                                                                                       |
    |Recebe o ID da demanda como parâmetro.                                                 |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    if current_user.ativo == False:
        abort(403)

    if current_user.role != 'admin':
        abort(403)

    demanda = Demanda.query.get_or_404(demanda_id)

    form = Admin_Altera_Demanda_Form()

    if form.validate_on_submit():

        demanda.data_conclu = form.data_conclu.data

        db.session.commit()

        flash ('Data de conclusão alterada!','sucesso')

        return redirect(url_for('demandas.demanda',demanda_id=demanda.id))

    elif request.method == 'GET':

        form.data_conclu.data = demanda.data_conclu

    return render_template('admin_altera_demanda.html', title='Update',form = form, demanda_id=demanda_id,conclu=demanda.conclu)

#removendo uma demanda

@demandas.route('/<int:demanda_id>/delete', methods=['GET','POST'])
@login_required
def delete_demanda(demanda_id):
    """+----------------------------------------------------------------------+
       |Permite que o autor da demanda, se logado, a remova do banco de dados.|
       |                                                                      |
       |Recebe o ID da demanda como parâmetro.                                |
       +----------------------------------------------------------------------+

    """
    if current_user.ativo == False:
        abort(403)

    demanda = Demanda.query.get_or_404(demanda_id)

    if demanda.author != current_user:
        abort(403)

    db.session.delete(demanda)
    db.session.commit()

    flash ('Demanda excluída!','sucesso')

    return redirect(url_for('demandas.list_demandas'))


# procurando uma demanda

@demandas.route('/pesquisa', methods=['GET','POST'])
def pesquisa_demanda():
    """+--------------------------------------------------------------------------------------+
       |Permite a procura por demandas conforme os campos informados no respectivo formulário.|
       |                                                                                      |
       |Envia a string pesq para a função list_pesquisa, que executa a busca.                 |
       +--------------------------------------------------------------------------------------+
    """

    pesquisa = True

    form = PesquisaForm()

    if form.validate_on_submit():
        # a / do campo sei precisou ser trocada por _ para poder ser passado no URL da pesquisa
        if form.sei.data != '':

            pesq = str(form.sei.data).split('/')[0]+'_'+str(form.sei.data).split('/')[1]+';'+\
                   str(form.titulo.data)+';'+\
                   str(form.tipo.data)+';'+\
                   str(form.necessita_despacho.data)+';'+\
                   str(form.conclu.data)+';'+\
                   str(form.convênio.data)+';'+\
                   str(form.autor.data)+';'+\
                   str(form.demanda_id.data)+';'+\
                   str(form.programa.data)+';'+\
                   str(form.coord.data)+';'+\
                   str(form.necessita_despacho_cg.data)

        else:

            pesq = ''+';'+\
                   str(form.titulo.data)+';'+\
                   str(form.tipo.data)+';'+\
                   str(form.necessita_despacho.data)+';'+\
                   str(form.conclu.data)+';'+\
                   str(form.convênio.data)+';'+\
                   str(form.autor.data)+';'+\
                   str(form.demanda_id.data)+';'+\
                   str(form.programa.data)+';'+\
                   str(form.coord.data)+';'+\
                   str(form.necessita_despacho_cg.data)

        return redirect(url_for('demandas.list_pesquisa',pesq = pesq))

    return render_template('pesquisa_demanda.html', form = form)

# lista as demandas com base em uma procura

@demandas.route('/<pesq>/list_pesquisa')
def list_pesquisa(pesq):
    """+--------------------------------------------------------------------------------------+
       |Com os dados recebidos da formulário de pesquisa, traz as demandas, bem como          |
       |providências e despachos, encontrados no banco de dados.                              |
       |                                                                                      |
       |Recebe a string pesq (dados para pesquisa) como parâmetro.                            |
       +--------------------------------------------------------------------------------------+
    """

    pesquisa = True

    page = request.args.get('page', 1, type=int)

    pesq_l = pesq.split(';')

    sei = pesq_l[0]
    if sei != '':
        sei = str(pesq_l[0]).split('_')[0]+'/'+str(pesq_l[0]).split('_')[1]

    if pesq_l[2] == 'Todos':
        p_tipo_pattern = ''
    else:
        p_tipo_pattern = pesq_l[2]

    p_n_d = 'Todos'
    if pesq_l[3] == 'Sim':
        p_n_d = True
    if pesq_l[3] == 'Não':
        p_n_d = False

    p_n_dcg = 'Todos'
    if pesq_l[10] == 'Sim':
        p_n_dcg = True
    if pesq_l[10] == 'Não':
        p_n_dcg = False

    p_conclu = 'Todos'
    if pesq_l[4] == 'Sim':
        p_conclu = True
    if pesq_l[4] == 'Não':
        p_conclu = False

    if pesq_l[6] != '':
        autor_id = pesq_l[6]
    else:
        autor_id = '%'

    if pesq_l[7] == '':
        pesq_l[7] = '%'+str(pesq_l[7])+'%'
    else:
        pesq_l[7] = str(pesq_l[7])

    if pesq_l[9] == '':
        pesq_l[9] = '%'
    else:
        pesq_l[9] = str(pesq_l[9])


    demandas  = Demanda.query.join(User).filter(Demanda.sei.like('%'+sei+'%'),
                                      Demanda.convênio.like('%'+pesq_l[5]+'%'),
                                      Demanda.titulo.like('%'+pesq_l[1]+'%'),
                                      Demanda.tipo.like('%'+p_tipo_pattern+'%'),
                                      Demanda.necessita_despacho != p_n_d,
                                      Demanda.necessita_despacho_cg != p_n_dcg,
                                      Demanda.conclu != p_conclu,
                                      Demanda.user_id.like (autor_id),
                                      Demanda.id.like (pesq_l[7]),
                                      Demanda.programa.like ('%'+str(pesq_l[8])+'%'),
                                      User.coord.like (pesq_l[9]))\
                                      .order_by(Demanda.data.desc())\
                                      .paginate(page=page,per_page=8)

    demandas_count  = demandas.total

    providencias = db.session.query(Providencia.demanda_id,
                                    Providencia.texto,
                                    Providencia.data,
                                    Providencia.user_id,
                                    label('username',User.username))\
                                    .outerjoin(User, Providencia.user_id == User.id)\
                                    .order_by(Providencia.data.desc()).all()

    despachos = db.session.query(Despacho.demanda_id,
                                 Despacho.texto,
                                 Despacho.data,
                                 Despacho.user_id,
                                 label('username',User.username +' - DESPACHO'),
                                 User.despacha,
                                 User.despacha2)\
                                .outerjoin(User, Despacho.user_id == User.id)\
                                .order_by(Despacho.data.desc()).all()

    pro_des = providencias + despachos
    pro_des.sort(key=lambda ordem: ordem.data,reverse=True)

    return render_template ('pesquisa.html', demandas_count = demandas_count, demandas = demandas,
                             pro_des = pro_des, pesq = pesq, pesq_l = pesq_l)

#################################################################

#CRIANDO um despacho

@demandas.route('/<int:demanda_id>/cria_despacho',methods=['GET','POST'])
@login_required
def cria_despacho(demanda_id):
    """+--------------------------------------------------------------------------------------+
       |Registra, para uma demanda, um despacho do chefe.                                     |
       |A opção de criar despacho só aparece para o usuário logado e que tem o                |
       |status de Chefe.                                                                      |
       |                                                                                      |
       |Inserido um despacho, a situação de necessidade de despacho da demanda é desmarcada.  |
       |                                                                                      |
       |Recebe o ID da demanda como parâmetro.                                                |
       +--------------------------------------------------------------------------------------+
    """

    demanda = Demanda.query.get_or_404(demanda_id)

    form = DespachoForm()

    if form.validate_on_submit():
        despacho = Despacho(data       = datetime.now(),
                            user_id    = current_user.id,
                            demanda_id = demanda_id,
                            texto      = form.texto.data)

        db.session.add(despacho)
        db.session.commit()

        # marca a demanda quanto à necessidade de despacho da CG
        # e desmarca, dependendo de quem deu o despacho.
        demanda.necessita_despacho_cg = form.necessita_despacho_cg.data

        if form.necessita_despacho_cg == True:
            demanda.data_env_despacho = datetime.now()

        if current_user.despacha:
            demanda.necessita_despacho = False

        if current_user.despacha2 and not current_user.despacha:
            demanda.necessita_despacho_cg = False

        db.session.commit()

        # registra data de conclusão da demanda, caso o despachante use desta prerrogativa
        if form.conclu.data:
            demanda.conclu      = True
            demanda.data_conclu = datetime.now()
            db.session.commit()

        flash ('Despacho criado!','sucesso')
        return redirect(url_for('demandas.demanda',demanda_id=demanda.id))

    return render_template('add_despacho.html', form               = form,
                                                sei                = demanda.sei,
                                                convênio           = demanda.convênio,
                                                ano_convênio       = demanda.ano_convênio,
                                                data               = demanda.data,
                                                tipo               = demanda.tipo,
                                                titulo             = demanda.titulo,
                                                desc               = demanda.desc,
                                                necessita_despacho = demanda.necessita_despacho,
                                                necessita_despacho_cg = demanda.necessita_despacho_cg,
                                                conclu             = demanda.conclu,
                                                post               = demanda)

#################################################################

#CRIANDO uma providência

@demandas.route('/<int:demanda_id>/cria_providencia',methods=['GET','POST'])
@login_required
def cria_providencia(demanda_id):
    """+--------------------------------------------------------------------------------------+
       |Registra, para uma demanda, uma providência tomada por um técnico.                    |
       |A opção de criar proviência aparece qualquer usuário logado, independemtemente de     |
       |ser, ou não, o autor da demanda consultada.                                           |
       |Este tem a opção de marcar a demanda com a necessidade de despacho.                   |
       |Inserido um despacho, a situação de necessidade de despacho da demanda é desmarcada.  |
       |                                                                                      |
       |Recebe o ID da demanda como parâmetro.                                                |
       +--------------------------------------------------------------------------------------+
    """
    if current_user.ativo == False:
        abort(403)

    demanda = Demanda.query.get_or_404(demanda_id)

    form = ProvidenciaForm()

    if form.validate_on_submit():
        providencia = Providencia(demanda_id = demanda_id,
                                  data       = datetime.now(),
                                  texto      = form.texto.data,
                                  user_id    = current_user.id)

        db.session.add(providencia)
        db.session.commit()

        if form.necessita_despacho.data == True:
            demanda.necessita_despacho = True
            demanda.necessita_despacho_cg = False
            demanda.conclu = False
            demanda.data_env_despacho = datetime.now()
            db.session.commit()
        else:
            demanda.necessita_despacho = False
            db.session.commit()

        flash ('Providência criada!','sucesso')
        return redirect(url_for('demandas.demanda',demanda_id=demanda.id))

    if demanda.necessita_despacho:
        form.necessita_despacho.data = True

    if current_user.despacha and demanda.user_id != current_user.id:
        flash ('Esta demanda não é sua. Não seria o caso de registrar um DESPACHO?','perigo')

    return render_template('add_providencia.html',
                            form               = form,
                            sei                = demanda.sei,
                            convênio           = demanda.convênio,
                            ano_convênio       = demanda.ano_convênio,
                            data               = demanda.data,
                            tipo               = demanda.tipo,
                            titulo             = demanda.titulo,
                            desc               = demanda.desc,
                            necessita_despacho = demanda.necessita_despacho,
                            conclu             = demanda.conclu,
                            post               = demanda)

#
#Um resumo das demandas

@demandas.route('/demandas_resumo')
def demandas_resumo():
    """
        +----------------------------------------------------------------------+
        |Agrega informações básicas de todas as demandas.                      |
        +----------------------------------------------------------------------+
    """

    hoje = date.today()

    ## conta demandas por tipo, destacando a quantidade concluída e a vida média
    demandas_count = Demanda.query.order_by(Demanda.data.desc()).count()

    demandas_por_tipo = db.session.query(Demanda.tipo,label('qtd_por_tipo',func.count(Demanda.id)))\
                                  .order_by(func.count(Demanda.id).desc())\
                                  .group_by(Demanda.tipo)

    demandas_por_tipo_ano_anterior = db.session.query(Demanda.tipo,label('qtd_por_tipo',func.count(Demanda.id)))\
                                    .filter(Demanda.data >= str(hoje.year - 1) + '-01-01',
                                            Demanda.data <= str(hoje.year - 1) + '-12-31')\
                                    .group_by(Demanda.tipo)

    demandas_por_tipo_ano_corrente = db.session.query(Demanda.tipo,label('qtd_por_tipo',func.count(Demanda.id)))\
                                    .filter(Demanda.data >= str(hoje.year) + '-01-01')\
                                    .group_by(Demanda.tipo)

    demandas_tipos = db.session.query(Tipos_Demanda.tipo).order_by(Tipos_Demanda.tipo).all()

    vida_m_por_tipo = []

    for demanda in demandas_por_tipo:
        demandas_datas = db.session.query(Demanda.data,Demanda.data_conclu)\
                                    .filter(Demanda.tipo == demanda.tipo,Demanda.conclu == '1', Demanda.data_conclu != None)

        demandas_conclu_por_tipo = db.session.query(Demanda.tipo,label('qtd_conclu',func.count(Demanda.id)))\
                                             .filter(Demanda.tipo == demanda.tipo,Demanda.conclu == '1')


        vida = 0
        vida_m = 0

        for dia in demandas_datas:

            vida += (dia.data_conclu - dia.data).days

        if len(list(demandas_datas)) > 0:
            vida_m = round(vida/len(list(demandas_datas)))
        else:
            vida_m = 0

        vida_m_por_tipo.append([demanda.tipo,demandas_conclu_por_tipo[0][1],vida_m])

    ## calcula a vida média das demandas (geral)
    demandas_datas = db.session.query(Demanda.data,Demanda.data_conclu)\
                                .filter(Demanda.conclu == '1', Demanda.data_conclu != None)

    vida = 0
    vida_m = 0

    for dia in demandas_datas:
        vida += (dia.data_conclu - dia.data).days

    if len(list(demandas_datas)) > 0:
        vida_m = round(vida/len(list(demandas_datas)))
    else:
        vida_m = 0

    ## calcula a vida média das demandas (ano corrente)

    inic_ano = str(hoje.year) + '-01-01'

    demandas_ano = db.session.query(Demanda.data,Demanda.data_conclu)\
                                .filter(Demanda.conclu == '1', Demanda.data > inic_ano)
    vida = 0
    vida_m_ano = 0

    for dia in demandas_ano:
        vida += (dia.data_conclu - dia.data).days

    if len(list(demandas_ano)) > 0:
        vida_m_ano = round(vida/len(list(demandas_ano)))
    else:
        vida_m_ano = 0


    ## calcula o prazo médio dos despachos
    despachos = db.session.query(label('c_data',Despacho.data), Despacho.demanda_id, Demanda.id, label('i_data',Demanda.data))\
                          .outerjoin(Demanda, Despacho.demanda_id == Demanda.id)\
                          .all()

    desp = 0
    desp_m = 0

    for despacho in despachos:
        desp += (despacho.c_data - despacho.i_data).days

    if len(list(despachos)) > 0:
        desp_m = round(desp/len(list(despachos)))
    else:
        desp_m = 0

    # porcentagem de conclusão das demandas

    demandas_total = Demanda.query.count()

    demandas_conclu = Demanda.query.filter(Demanda.conclu == '1').count()

    percent_conclu = round((demandas_conclu / demandas_total) * 100)

    # média, maior quantidade e menor quantidade de demandas por colaborador ativo.

    colaborador_demandas = db.session.query(Demanda.user_id,label('qtd',func.count(Demanda.user_id))).group_by(Demanda.user_id)

    pessoas = db.session.query(User.id,User.ativo).all()

    qtd_demandas = []
    for c_d in colaborador_demandas:
        for p in pessoas:
            if c_d.user_id == p.id:
                if p.ativo == True:
                    qtd_demandas.append(c_d.qtd)

    qtd_demandas_max = max(qtd_demandas)
    qtd_demandas_min = min(qtd_demandas)
    qtd_demandas_avg = round(sum(qtd_demandas)/len(qtd_demandas))

    # média de demandas, providêndcias e despachos por mês nos últimos 12 meses

    meses = []
    for i in range(12):
        m = hoje.month-i-1
        y = hoje.year
        if m < 1:
            m += 12
            y -= 1
        if m >= 0 and m < 10:
            m = '0' + str(m)
        meses.append((str(m),str(y)))

    demandas_12meses = [Demanda.query.filter(Demanda.data >= mes[1]+'-'+mes[0]+'-01',
                                             Demanda.data <= mes[1]+'-'+mes[0]+'-31').count()
                                             for mes in meses]

    med_dm = round(sum(demandas_12meses)/len(demandas_12meses))
    max_dm = max(demandas_12meses)
    mes_max_dm = meses[demandas_12meses.index(max_dm)]
    min_dm = min(demandas_12meses)
    mes_min_dm = meses[demandas_12meses.index(min_dm)]

    providencias_12meses = [Providencia.query.filter(Providencia.data >= mes[1]+'-'+mes[0]+'-01',
                                             Providencia.data <= mes[1]+'-'+mes[0]+'-31').count()
                                             for mes in meses]

    med_pr = round(sum(providencias_12meses)/len(providencias_12meses))
    max_pr = max(providencias_12meses)
    mes_max_pr = meses[providencias_12meses.index(max_pr)]
    min_pr = min(providencias_12meses)
    mes_min_pr = meses[providencias_12meses.index(min_pr)]

    despachos_12meses = [Despacho.query.filter(Despacho.data >= mes[1]+'-'+mes[0]+'-01',
                                             Despacho.data <= mes[1]+'-'+mes[0]+'-31').count()
                                             for mes in meses]

    med_dp = round(sum(despachos_12meses)/len(despachos_12meses))
    max_dp = max(despachos_12meses)
    mes_max_dp = meses[despachos_12meses.index(max_dp)]
    min_dp = min(despachos_12meses)
    mes_min_dp = meses[despachos_12meses.index(min_dp)]


    return render_template ('demandas_resumo.html', demandas_count = demandas_count,
                                                    demandas_por_tipo = demandas_por_tipo,
                                                    demandas_por_tipo_ano_anterior=demandas_por_tipo_ano_anterior,
                                                    demandas_por_tipo_ano_corrente=demandas_por_tipo_ano_corrente,
                                                    demandas_tipos=demandas_tipos,
                                                    vida_m_por_tipo = vida_m_por_tipo,
                                                    vida_m = vida_m,
                                                    desp_m = desp_m,
                                                    percent_conclu = percent_conclu,
                                                    vida_m_ano = vida_m_ano,
                                                    qtd_demandas_max=qtd_demandas_max,
                                                    qtd_demandas_min=qtd_demandas_min,
                                                    qtd_demandas_avg=qtd_demandas_avg,
                                                    med_dm=med_dm,
                                                    max_dm=max_dm,
                                                    mes_max_dm=mes_max_dm,
                                                    min_dm=min_dm,
                                                    mes_min_dm=mes_min_dm,
                                                    med_pr=med_pr,
                                                    max_pr=max_pr,
                                                    mes_max_pr=mes_max_pr,
                                                    min_pr=min_pr,
                                                    mes_min_pr=mes_min_pr,
                                                    med_dp=med_dp,
                                                    max_dp=max_dp,
                                                    mes_max_dp=mes_max_dp,
                                                    min_dp=min_dp,
                                                    mes_min_dp=mes_min_dp)
