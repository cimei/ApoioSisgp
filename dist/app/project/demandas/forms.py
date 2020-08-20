"""
.. topic:: **Demandas (formulários)**

    Os formulários do módulo *Demandas* recebem dados informados pelo usuário para
    registro, atualização, procura e deleção de demandas.

    Uma demanda, após criada, só pode ser alterda e removida pelo seu autor.

    Para o tratamento de demandas, foram definidos 4 formulários:

    * Tipos_DemandaForm: criação ou atualização de tipos de demanda.
    * DemandaForm: criação ou atualização de uma demanda.
    * DespachoForm: criação de um despacho relativo a uma demanda existente.
    * ProvidenciaForm: criação de uma providência relativa a uma demanda existente.
    * PesquisaForm: localizar demandas conforme os campos informados.

**Campos definidos em cada formulário de *Demandas*:**

"""

# forms.py na pasta demandas

import datetime
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SelectField, BooleanField, DecimalField,\
                    DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Regexp
from project import db
from project.models import Tipos_Demanda, Coords, User

class Tipos_DemandaForm(FlaskForm):

    tipo       = StringField('Tipo de Demanda')
    relevancia = SelectField('Relevância:',choices=[('3','Baixa'),('2','Média'),('1','Alta')],
                              validators=[DataRequired(message="Defina a Relevância!")])

    submit     = SubmitField('Registrar')

class Admin_Altera_Demanda_Form(FlaskForm):

    data_conclu = DateField('Data de conclusão da demanda:',format='%d/%m/%Y',validators=[DataRequired(message="Informe data da conclusão!")])

    submit      = SubmitField('Registrar')

class DemandaForm1(FlaskForm):
    # choices do campo tipo são definido na view
    sei                 = StringField('SEI:',validators=[DataRequired(message="Informe o Processo!")]) # incluir regex para sei, talvez ?!?!
    tipo                = SelectField('Tipo:', validators=[DataRequired(message="Escolha um Tipo!")])
    submit              = SubmitField('Verificar')


class DemandaForm(FlaskForm):

    programa            = StringField('Programa:',validators=[DataRequired(message="Escolha um Programa!")])
    convênio            = StringField('Convênio:')
    ano_convênio        = StringField('Ano do Convênio:')
    titulo              = StringField('Título:', validators=[DataRequired(message="Defina um Título!")])
    desc                = TextAreaField('Descrição:',validators=[DataRequired(message="Descreva a Demanda!")])
    necessita_despacho  = BooleanField('Necessita despacho?')
    necessita_despacho_cg  = BooleanField('Necessita despacho da CG ou sup.?')
    conclu              = BooleanField('Concluída?')
    urgencia            = SelectField('Urgência:',choices=[('3','Baixa'),('2','Média'),('1','Alta')],
                                       validators=[DataRequired(message="Defina a urgência!")])
    submit              = SubmitField('Registrar')

#
class Demanda_ATU_Form(FlaskForm):

    programa            = StringField('Programa:',validators=[DataRequired(message="Escolha um Programa!")])
    sei                 = StringField('SEI:')
    tipo                = SelectField('Tipo:')
    convênio            = StringField('Convênio:')
    ano_convênio        = StringField('Ano do Convênio:')
    titulo              = StringField('Título:', validators=[DataRequired(message="Defina um Título!")])
    desc                = TextAreaField('Descrição:',validators=[DataRequired(message="Descreva a Demanda!")])
    necessita_despacho  = BooleanField('Necessita despacho?')
    necessita_despacho_cg  = BooleanField('Necessita despacho da CG ou sup.?')
    conclu              = BooleanField('Concluída?')
    urgencia            = SelectField('Urgência:',choices=[('3','Baixa'),('2','Média'),('1','Alta')],
                                       validators=[DataRequired(message="Defina a urgência!")])
    submit              = SubmitField('Registrar')

class TransferDemandaForm(FlaskForm):

    pessoas = db.session.query(User.username, User.id)\
                      .order_by(User.username).all()
    lista_pessoas = [(str(p[1]),p[0]) for p in pessoas]
    lista_pessoas.insert(0,('',''))

    pessoa = SelectField('Novo responsável:',choices= lista_pessoas, validators=[DataRequired(message="Escolha alguém!")])
    submit = SubmitField('Transferir')

class DespachoForm(FlaskForm):

    texto                  = TextAreaField('Descrição:',validators=[DataRequired(message="Descreva o Despacho!")])
    necessita_despacho_cg  = BooleanField('Necessita despacho CG ou sup.?')
    conclu                 = BooleanField('Concluir a Demanda?')
    submit                 = SubmitField('Registrar')

class ProvidenciaForm(FlaskForm):

    texto               = TextAreaField('Descrição:',validators=[DataRequired(message="Descreva a Providência!")])
    necessita_despacho  = BooleanField('Necessita despacho?')
    submit              = SubmitField('Registrar')

class PesquisaForm(FlaskForm):

    coords = db.session.query(Coords.sigla)\
                      .order_by(Coords.sigla).all()
    lista_coords = [(c[0],c[0]) for c in coords]
    lista_coords.insert(0,('',''))

    tipos = db.session.query(Tipos_Demanda.tipo)\
                      .order_by(Tipos_Demanda.tipo).all()
    lista_tipos = [(t[0],t[0]) for t in tipos]
    lista_tipos.insert(0,('',''))

    pessoas = db.session.query(User.username, User.id)\
                      .order_by(User.username).all()
    lista_pessoas = [(str(p[1]),p[0]) for p in pessoas]
    lista_pessoas.insert(0,('',''))

    coord               = SelectField('Coordenação:',choices= lista_coords)
    sei                 = StringField('SEI:')
    convênio            = StringField('Convênio:')
    tipo                = SelectField(choices= lista_tipos)
    titulo              = StringField('Título:')
    ## os valore nos dois campos a seguir vão ao contrário, pois na view a condição de pesquisa usa o !=
    necessita_despacho  = SelectField('Aguarda Despacho',choices=[('Todos','Todos'),
                                               ('Sim','Não'),
                                               ('Não','Sim')])
    necessita_despacho_cg  = SelectField('Aguarda Despacho CG ou sup.',choices=[('Todos','Todos'),
                                              ('Sim','Não'),
                                              ('Não','Sim')])
    conclu              = SelectField('Concluído',choices=[('Todos','Todos'),
                                               ('Sim','Não'),
                                               ('Não','Sim')])

    autor               = SelectField('Responsável:',choices= lista_pessoas)

    demanda_id          = StringField('Número da demanda:')

    programa            = StringField('Programa:')

    submit              = SubmitField('Pesquisar')

# form para definir o peso de cada componente RDU
class PesosForm(FlaskForm):

    coords = db.session.query(Coords.sigla)\
                      .order_by(Coords.sigla).all()
    lista_coords = [(c[0],c[0]) for c in coords]
    lista_coords.insert(0,('',''))

    peso_R       = SelectField('Relevância:',choices= [('0.5','Importante'),('1','Normal'),('1.5','Sem importância')],default='1')
    peso_D       = SelectField('Momento:',choices= [('0.5','Importante'),('1','Normal'),('1.5','Sem importância')],default='1')
    peso_U       = SelectField('Urgência:',choices= [('0.5','Importante'),('1','Normal'),('1.5','Sem importância')],default='1')
    coord        = SelectField('Coordenação:',choices= lista_coords)
    submit       = SubmitField('Aplicar')
