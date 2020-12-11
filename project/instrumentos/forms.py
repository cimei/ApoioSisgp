"""

.. topic:: Instrumentos (formulários)

   O formulário do módulo *Instrumentos* recebe dados informados pelo usuário para o registro
   de um novo instrumento e é o mesmo utilizado quando da atualização de dados de um instrumento já existente.

   * InstrumentoForm: registrar ou atualizar dados de um instrumento.
   * ListaForm: escolher coordenação

**Campos definidos no formulário (todos são obrigatórios):**

"""

# forms.py dentro de instrumentos

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Regexp
from project import db
from project.models import Coords

# form para inclusão ou alteração de um instrumento
class InstrumentoForm(FlaskForm):

    coords = db.session.query(Coords.sigla)\
                      .order_by(Coords.sigla).all()
    lista_coords = [(c[0],c[0]) for c in coords]
    lista_coords.insert(0,('',''))

    coord        = SelectField('Coordenação:',choices= lista_coords)
    nome         = StringField('Título:',validators=[DataRequired(message="Informe um título para o instrumento!")])
    contraparte  = StringField('Contraparte:',validators=[DataRequired(message="Informe a contraparte!")])
    sei          = StringField('Número SEI:',validators=[DataRequired(message="Informe o Programa!")]) # incluir regex para sei
    data_inicio  = DateField('Data de início do Instrumento:',format='%d/%m/%Y',validators=[DataRequired(message="Informe data do início!")])
    data_fim     = DateField('Data de término do Instrumento:',format='%d/%m/%Y',validators=[DataRequired(message="Informe data do término!")])
    descri       = TextAreaField('Descrição:',validators=[DataRequired(message="Informe a descrição!")])
    valor        = StringField('Valor relacionado ao instrumento:',validators=[DataRequired(message="Informe o valor!")])

    submit       = SubmitField('Registrar')

#
# form para escolher a coordenação na lista de instrumentos
class ListaForm(FlaskForm):

    coords = db.session.query(Coords.sigla)\
                      .order_by(Coords.sigla).all()
    lista_coords = [(c[0],c[0]) for c in coords]
    lista_coords.insert(0,('',''))

    coord        = SelectField('Coordenação:',choices= lista_coords)
    submit       = SubmitField('Filtrar coordenação')
