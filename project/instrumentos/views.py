"""
.. topic:: Instrumentos (views)

    Os Instrumentos são objetos que a coordenação necessita de um registro mínimo para referência em demandas.

    Um instrumento tem atributos que são registrados no momento de sua criação. Todos são obrigatórios:

    * Título
    * Contraparte
    * Número do processo SEI
    * Data de início
    * Data de término
    * Valor associado
    * Descrição

.. topic:: Ações relacionadas aos instrumentos

    * Listar instrumentos por edição do programa: lista_instrumentos
    * Atualizar/visualizar dados de um instrumento: update
    * Registrar um instrumento no sistema: cria_instrumento
    * Listar demandas de um determinado instrumento: instrumento_demandas

"""

# views.py na pasta instrumentos

from flask import render_template,url_for,flash, redirect,request,Blueprint
from flask_login import current_user,login_required
from sqlalchemy import func, distinct
from sqlalchemy.sql import label
from project import db
from project.models import User, Demanda, Coords, Instrumento
from project.instrumentos.forms import InstrumentoForm, ListaForm
from project.demandas.views import registra_log_auto

import locale
import datetime
from datetime import datetime as dt
from dateutil.rrule import rrule, MONTHLY

instrumentos = Blueprint('instrumentos',__name__,
                            template_folder='templates/instrumentos')

#
def none_0(a):
    '''
    DOCSTRING: Transforma None em 0.
    INPUT: campo a ser trandormado.
    OUTPUT: 0, se a entrada for None, caso contrário, a entrada.
    '''
    if a == None:
        a = 0
    return a


@instrumentos.route('/<lista>/<coord>/lista_instrumentos', methods=['GET', 'POST'])
def lista_instrumentos(lista,coord):
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos instrumentos por edição do programa.                           |
    |                                                                                       |
    |O instrumento é algo tratado pela área técnica que justifica um registro específico.   |
    |e que não pode ser caracterizado como convênio ou acordo.                              |
    |Um contratao é um exemplo de instrumento.                                              |
    |                                                                                       |
    |No topo da tela há a opção de se inserir um novo instrumento e o número sequencial     |
    |de cada instrumento (#), ao ser clicado, permite que seus dados possam ser editados.   |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    form = ListaForm()

    if form.validate_on_submit():

        coord = form.coord.data

        if coord == '' or coord == None:
            coord = '*'

        return redirect(url_for('instrumentos.lista_instrumentos',lista=lista,coord=coord))

    else:

        if coord == '*':

            form.coord.data = ''

            coordenacao = db.session.query(Coords.id,
                                           Coords.sigla)\
                                    .subquery()

        else:

            form.coord.data = coord

            coordenacao = db.session.query(Coords.id,
                                           Coords.sigla)\
                                    .filter(Coords.sigla == coord)\
                                    .subquery()

        if lista == 'todos':
            instrumentos_v = db.session.query(Instrumento.id,
                                              Instrumento.coord,
                                              Instrumento.nome,
                                              Instrumento.contraparte,
                                              Instrumento.sei,
                                              Instrumento.descri,
                                              Instrumento.data_inicio,
                                              Instrumento.data_fim,
                                              Instrumento.valor,
                                              coordenacao.c.sigla)\
                                       .join(coordenacao, coordenacao.c.sigla == Instrumento.coord)\
                                       .order_by(Instrumento.nome).all()

        elif lista == 'em execução':
            instrumentos_v = db.session.query(Instrumento.id,
                                              Instrumento.coord,
                                              Instrumento.nome,
                                              Instrumento.contraparte,
                                              Instrumento.sei,
                                              Instrumento.descri,
                                              Instrumento.data_inicio,
                                              Instrumento.data_fim,
                                              Instrumento.valor,
                                              coordenacao.c.sigla)\
                                       .join(coordenacao, coordenacao.c.sigla == Instrumento.coord)\
                                       .filter(Instrumento.data_fim >= datetime.date.today())\
                                       .order_by(Instrumento.data_fim,Instrumento.nome).all()

        quantidade = len(instrumentos_v)

        instrumentos = []

        for instrumento in instrumentos_v:
            # ajusta formatos para data e dinheiro
            if instrumento.data_inicio is not None:
                início = instrumento.data_inicio.strftime('%x')
            else:
                início = None

            if instrumento.data_fim is not None:
                fim = instrumento.data_fim.strftime('%x')
                dias = (instrumento.data_fim - datetime.date.today()).days
            else:
                fim = None
                dias = 999

            valor = locale.currency(instrumento.valor, symbol=False, grouping = True)

            instrumentos.append([instrumento.id,
                                 instrumento.sigla,
                                 instrumento.nome,
                                 instrumento.contraparte,
                                 instrumento.sei,
                                 início,
                                 fim,
                                 valor,
                                 dias,
                                 instrumento.descri])

        return render_template('lista_instrumentos.html', instrumentos=instrumentos,quantidade=quantidade,lista=lista,form=form)


### ATUALIZAR Instrumento

@instrumentos.route("/<int:instrumento_id>/update", methods=['GET', 'POST'])
@login_required
def update(instrumento_id):
    """
    +---------------------------------------------------------------------------------------+
    |Permite atualizar os dados de um instrumento selecionado na tela de consulta.          |
    |                                                                                       |
    |Recebe o ID do instrumento como parâmetro.                                             |
    +---------------------------------------------------------------------------------------+
    """

    instrumento = Instrumento.query.get_or_404(instrumento_id)

    form = InstrumentoForm()

    if form.validate_on_submit():

        instrumento.coord       = form.coord.data
        instrumento.nome        = form.nome.data
        instrumento.sei         = form.sei.data
        instrumento.contraparte = form.contraparte.data
        instrumento.data_inicio = form.data_inicio.data
        instrumento.data_fim    = form.data_fim.data
        instrumento.valor       = float(form.valor.data.replace('.','').replace(',','.'))
        instrumento.descri      = form.descri.data

        db.session.commit()

        registra_log_auto(current_user.id,None,'itm')

        flash('Instrumento atualizado!')
        return redirect(url_for('instrumentos.lista_instrumentos',lista='todos',coord = '*'))
    # traz a informação atual do instrumento
    elif request.method == 'GET':
        form.coord.data        = instrumento.coord
        form.nome.data         = instrumento.nome
        form.sei.data          = instrumento.sei
        form.contraparte.data  = instrumento.contraparte
        form.data_inicio.data  = instrumento.data_inicio
        form.data_fim.data     = instrumento.data_fim
        form.valor.data        = locale.currency( instrumento.valor, symbol=False, grouping = True )
        form.descri.data       = instrumento.descri

    return render_template('add_instrumento.html', title='Update',
                           form=form, id=instrumento_id)

### CRIAR Instrumento

@instrumentos.route("/criar", methods=['GET', 'POST'])
@login_required
def cria_instrumento():
    """
    +---------------------------------------------------------------------------------------+
    |Permite registrar os dados de um instrumento.                                               |
    +---------------------------------------------------------------------------------------+
    """

    form = InstrumentoForm()

    if form.validate_on_submit():
        instrumento = Instrumento(coord       = form.coord.data,
                                  nome        = form.nome.data,
                                  contraparte = form.contraparte.data,
                                  sei         = form.sei.data,
                                  data_inicio = form.data_inicio.data,
                                  data_fim    = form.data_fim.data,
                                  valor       = float(form.valor.data.replace('.','').replace(',','.')),
                                  descri      = form.descri.data)

        db.session.add(instrumento)
        db.session.commit()

        registra_log_auto(current_user.id,None,'itm')

        flash('Instrumento criado!')
        return redirect(url_for('instrumentos.lista_instrumentos',lista='todos',coord = '*'))


    return render_template('add_instrumento.html', form=form, id=0 )


# lista das demandas relacionadas a um instrumento

@instrumentos.route('/<instrumento_id>/instrumento_demandas')
def instrumento_demandas (instrumento_id):
    """+--------------------------------------------------------------------------------------+
       |Mostra as demandas relacionadas a um instrumento quando seu NUP é selecionado em uma  |
       |lista de instrumentos.                                                                |
       |Recebe o id do instrumento como parâmetro.                                            |
       +--------------------------------------------------------------------------------------+
    """

    instrumento_SEI = db.session.query(Instrumento.sei,Instrumento.nome).filter_by(id=instrumento_id).first()

    SEI = instrumento_SEI.sei
    SEI_s = str(SEI).split('/')[0]+'_'+str(SEI).split('/')[1]

    demandas_count = Demanda.query.filter(Demanda.sei.like('%'+SEI+'%')).count()

    demandas = Demanda.query.filter(Demanda.sei.like('%'+SEI+'%'))\
                            .order_by(Demanda.data.desc()).all()

    autores=[]
    for demanda in demandas:
        autores.append(str(User.query.filter_by(id=demanda.user_id).first()).split(';')[0])

    dados = [instrumento_SEI.nome,SEI_s,'0','0']

    return render_template('SEI_demandas.html',demandas_count=demandas_count,demandas=demandas,sei=SEI, autores=autores,dados=dados)

#
#removendo uma atividade do plano de trabalho

@instrumentos.route('/<int:instrumento_id>/delete', methods=['GET','POST'])
@login_required
def delete_instrumento(instrumento_id):
    """+----------------------------------------------------------------------+
       |Permite que o chefe, se logado, a remova um um instrumento.           |
       |                                                                      |
       |Recebe o ID do instrumento como parâmetro.                            |
       +----------------------------------------------------------------------+

    """
    if not current_user.ativo or (not current_user.despacha0 and not current_user.despacha and not current_user.despacha2):
        abort(403)

    instrumento = Instrumento.query.get_or_404(instrumento_id)

    db.session.delete(instrumento)
    db.session.commit()

    registra_log_auto(current_user.id,None,'xtm')

    flash ('Instrumento excluído!','sucesso')

    return redirect(url_for('instrumentos.lista_instrumentos',lista='todos',coord = '*'))
