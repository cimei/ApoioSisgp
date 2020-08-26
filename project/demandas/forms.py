"""
.. topic:: **Demandas (formulários)**

    Os formulários do módulo *Demandas* recebem dados informados pelo usuário para
    registro, atualização, procura e deleção de demandas.

    Uma demanda, após criada, só pode ser alterda e removida pelo seu autor.

    Para o tratamento de demandas, foram definidos 4 formulários:

    * Plano_TrabalhoForm: iserir ou alterar atividade no plano de trabalho.
    * Tipos_DemandaForm: criação ou atualização de tipos de demanda.
    * Admin_Altera_Demanda_Form: admin altera data de conclusão de uma demanda.
    * DemandaForm1: triagem antes da criação de uma demanda.
    * DemandaForm: criação ou atualização de uma demanda.
    * Demanda_ATU_Form: atualizar demanda.
    * TransferDemandaForm: passar demanda para outra pessoa.
    * DespachoForm: criação de um despacho relativo a uma demanda existente.
    * ProvidenciaForm: criação de uma providência relativa a uma demanda existente.
    * PesquisaForm: localizar demandas conforme os campos informados.
    * PesosForm: atribuição de pesos para os critérios de priorização de demandas.
    * Afere_Demanda_Form: atribuir nota a uma demanda
    * Pdf_Demanda_Form: para gerar pdf da demanda em tela
    * CoordForm: escolher uma coordeação específica


**Campos definidos em cada formulário de *Demandas*:**

"""

# forms.py na pasta demandas

import datetime
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SelectField, BooleanField, DecimalField,\
                    DateField, DateTimeField, TextAreaField, SubmitField, RadioField
from wtforms.validators import DataRequired, Regexp
from project import db
from project.models import Tipos_Demanda, Coords, User, Plano_Trabalho


class Plano_TrabalhoForm(FlaskForm):

    pessoas = db.session.query(User.username, User.id)\
                      .order_by(User.username).all()
    lista_pessoas = [(str(p[1]),p[0]) for p in pessoas]
    lista_pessoas.insert(0,('',''))

    atividade_sigla = StringField('Sigla:',validators=[DataRequired(message="Informe a sigla!")])
    atividade_desc  = TextAreaField('Descrição:',validators=[DataRequired(message="Informe a descrição!")])
    natureza        = StringField('Natureza:',validators=[DataRequired(message="Informe a natureza!")])
    horas_semana    = DecimalField('Meta (h/sem):',validators=[DataRequired(message="Informe a meta!")], places=1)
    respon_1        = SelectField('1º respon.:',choices= lista_pessoas, validators=[DataRequired(message="Escolha alguém!")])
    respon_2        = SelectField('2º respon.:',choices= lista_pessoas, validators=[DataRequired(message="Escolha alguém!")])

    submit     = SubmitField('Registrar')

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

    atividades = db.session.query(Plano_Trabalho.atividade_sigla, Plano_Trabalho.id)\
                      .order_by(Plano_Trabalho.atividade_sigla).all()
    lista_atividades = [(str(a[1]),a[0]) for a in atividades]
    lista_atividades.insert(0,('',''))

    # programa            = StringField('Programa:',validators=[DataRequired(message="Escolha um Programa!")])
    atividade             = SelectField('Atividade:',choices= lista_atividades, validators=[DataRequired(message="Escolha uma atividade do plano de trabalho!")])
    convênio              = StringField('Convênio:')
    ano_convênio          = StringField('Ano do Convênio:')
    titulo                = StringField('Título:', validators=[DataRequired(message="Defina um Título!")])
    desc                  = TextAreaField('Descrição:',validators=[DataRequired(message="Descreva a Demanda!")])
    necessita_despacho    = BooleanField('Necessita despacho?')
    necessita_despacho_cg = BooleanField('Necessita despacho da CG ou sup.?')
    conclu                = BooleanField('Concluída?')
    urgencia              = SelectField('Urgência:',choices=[('3','Baixa'),('2','Média'),('1','Alta')],
                                       validators=[DataRequired(message="Defina a urgência!")])
    submit                = SubmitField('Registrar')

#
class Demanda_ATU_Form(FlaskForm):

    atividades = db.session.query(Plano_Trabalho.atividade_sigla, Plano_Trabalho.id)\
                      .order_by(Plano_Trabalho.atividade_sigla).all()
    lista_atividades = [(str(a[1]),a[0]) for a in atividades]
    lista_atividades.insert(0,('',''))

    # programa            = StringField('Programa:',validators=[DataRequired(message="Escolha um Programa!")])
    atividade             = SelectField('Atividade:',choices= lista_atividades, validators=[DataRequired(message="Escolha uma atividade do plano de trabalho!")])
    sei                 = StringField('SEI:')
    tipo                = SelectField('Tipo:')
    convênio            = StringField('Convênio:')
    ano_convênio        = StringField('Ano do Convênio:')
    titulo              = StringField('Título:', validators=[DataRequired(message="Defina um Título!")])
    desc                = TextAreaField('Descrição:',validators=[DataRequired(message="Descreva a Demanda!")])
    tipo_despacho       = RadioField('Necessita despacho?',choices=[('0','Nenhum'),('1','Coord. Téc.'),('2','Coord. Geral')])
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

    data_hora           = DateTimeField('Momento:',format='%d/%m/%Y %H:%M:%S',validators=[DataRequired(message="O momento deve ser informado!")])
    duracao             = IntegerField('Duração:')
    agenda              = BooleanField("Marcar na agenda")
    texto               = TextAreaField('Descrição:',validators=[DataRequired(message="Insira uma descrição!")])
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

    atividades = db.session.query(Plano_Trabalho.atividade_sigla, Plano_Trabalho.id)\
                      .order_by(Plano_Trabalho.atividade_sigla).all()
    lista_atividades = [(str(a[1]),a[0]) for a in atividades]
    lista_atividades.insert(0,('',''))

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

    atividade           = SelectField('Atividade:',choices= lista_atividades)

    submit              = SubmitField('Pesquisar')

# form para definir o peso de cada componente RDU
class PesosForm(FlaskForm):

    coords = db.session.query(Coords.sigla)\
                      .order_by(Coords.sigla).all()
    lista_coords = [(c[0],c[0]) for c in coords]
    lista_coords.insert(0,('',''))

    pessoas = db.session.query(User.username, User.id)\
                      .order_by(User.username).all()
    lista_pessoas = [(str(p[1]),p[0]) for p in pessoas]
    lista_pessoas.insert(0,('',''))

    peso_R = SelectField('Relevância:',choices= [('0.5','Importante'),('1','Normal'),('1.5','Sem importância')],default='1')
    peso_D = SelectField('Momento:',choices= [('0.5','Importante'),('1','Normal'),('1.5','Sem importância')],default='1')
    peso_U = SelectField('Urgência:',choices= [('0.5','Importante'),('1','Normal'),('1.5','Sem importância')],default='1')
    coord  = SelectField('Coordenação:',choices= lista_coords)
    pessoa = SelectField('Responsável:',choices= lista_pessoas)
    submit = SubmitField('Aplicar')

# form para aferir demanda
class Afere_Demanda_Form(FlaskForm):

    nota = RadioField('Nota:',choices=[('0','0'),('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7'),('8','8'),('9','9'),('10','10')],
                              validators=[DataRequired(message="Escolha a nota!")])

    submit      = SubmitField('Registrar')

# form para gerar relatório pdf da demanda
class Pdf_Demanda_Form(FlaskForm):

    submit      = SubmitField('Gerar pdf')

# form para escolher coordenação
class CoordForm(FlaskForm):

    coords = db.session.query(Coords.sigla)\
                      .order_by(Coords.sigla).all()
    lista_coords = [(c[0],c[0]) for c in coords]
    lista_coords.insert(0,('',''))

    coord  = SelectField('Coordenação:',choices= lista_coords)

    submit = SubmitField('Aplicar')
