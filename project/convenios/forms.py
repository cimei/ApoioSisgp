"""

.. topic:: Convênios (formulários)

   O formulário do módulo *Convenios* recebe dados informados pelo usuário para o registro
   de dados SEI de um convênio e é o mesmo utilizado quando da atualização de dados já existente.

   * SEIForm: utilizado registrar ou atualizar dados SEI de um convênio.
   * ProgPrefForm: para registrar ou atualizar programas preferenciais, ou seja, aqueles a partir dos quais será feira extração no SICONV.
   * ChamadaForm: para registrar ou atualizar dados de chamadas públicas cujos resultados foram homologados pelo CNPq.
   * NDForm: para registrar naturezas de despesas em empenhos

**Campos definidos no formulário (todos são obrigatórios, exceto o "obs" do ChamadaForm):**

"""

# forms.py dentro de convenios

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, Regexp
from sqlalchemy import distinct

from project import db
from project.models import Programa_Interesse

class SEIForm(FlaskForm):

    nr_convenio = IntegerField('Nº Convênio SICONV:',validators=[DataRequired(message="Informe o número do convênio!")])
    ano         = IntegerField('Ano do Convênio:',validators=[DataRequired(message="Informe o ano!")])
    sei         = StringField('SEI do Convênio:',validators=[DataRequired(message="Informe o Processo!")]) # incluir regex para sei... um dia....
    epe         = StringField('Sigla da EPE:',validators=[DataRequired(message="Informe a instituição!")])
    uf          = StringField('UF (sigla):',validators=[DataRequired(message="Informe a sigla da UF!")])
    programa    = StringField('Sigla do Programa:',validators=[DataRequired(message="Informe o Programa!")])
    submit      = SubmitField('Registrar')

# form para inserir/atualizar programa preferencial
class ProgPrefForm(FlaskForm):

    #coords = db.session.query(Coords.sigla)\
    #                  .order_by(Coords.sigla).all()
    #lista_coords = [(c[0],c[0]) for c in coords]
    #lista_coords.insert(0,('',''))

    cod_programa = IntegerField('Código do Programa:',validators=[DataRequired(message="Informe o Código do Programa!")])
    desc         = StringField('Descrição:',validators=[DataRequired(message="Faça uma descrição!")])
    sigla        = StringField('Sigla:',validators=[DataRequired(message="Informe a Sigla do Programa!")])
    coord        = StringField('Coordenação:',validators=[DataRequired(message="Informa a Coordenação!")])
    #coord        = SelectField('Coordenação:',choices= lista_coords, validators=[DataRequired(message="Escolha uma Coordenção!")])
    submit       = SubmitField('Registrar')

#
## form para inserir dados de chamada homologadas
class ChamadaForm(FlaskForm):

    sei               = StringField('Número SEI:',validators=[DataRequired(message="Informe o Processo!")]) # incluir regex para sei... um dia....
    chamada           = StringField('Chamada:',validators=[DataRequired(message="Informe o nome da Chamada!")])
    qtd_projetos      = StringField('Quantidade de projetos:',validators=[DataRequired(message="Informe a quantidade de projetos!")])
    vl_total_chamada  = StringField('Valor total homologado:',validators=[DataRequired(message="Informe o valor!")])
    doc_sei           = StringField('Doc com a lista de projetos no SEI:',validators=[DataRequired(message="Informe o número do documento!")])
    obs               = StringField('Observações:')
    submit      = SubmitField('Registrar')

#
## form para inserir dados de natureza de despesa em empenho
class NDForm(FlaskForm):

    nd      = StringField('Código da Natureza de Despesa:',validators=[DataRequired(message="Informe a ND!")])
    submit  = SubmitField('Registrar')
#
# form para escolher a coordenação na lista de convênios
class ListaForm(FlaskForm):

    coords = db.session.query(distinct(Programa_Interesse.coord))\
                      .order_by(Programa_Interesse.coord).all()
    lista_coords = [(c[0],c[0]) for c in coords]

    lista_coords.insert(0,('inst','Instituição'))
    lista_coords.insert(0,('',''))

    coord        = SelectField('Coordenação:',choices= lista_coords)
    submit       = SubmitField('Filtrar coordenação')
