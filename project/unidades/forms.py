"""

.. topic:: Unidades (formulários)

   Formulários de alteração da dados de unidades da instituição.

   * UnidadeForm: utilizado registrar ou atualizar dados de uma unidade.

"""

# forms.py dentro de convenios

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional, Email
from wtforms.fields.html5 import EmailField

class UnidadeForm(FlaskForm):

    sigla   = StringField('Sigla:', validators=[DataRequired(message="Informe a Sigla!")])
    desc    = StringField('Nome:',validators=[DataRequired(message="Informe o nome por extenso!")])
    pai     = SelectField('Pai:',coerce=int)
    tipo    = SelectField('Tipo:',validators=[DataRequired(message="Escolha o tipo!")],coerce=int)
    situ    = SelectField('Situação:',validators=[DataRequired(message="Escolha a situação!")],coerce=int)
    uf      = StringField('UF:',validators=[DataRequired(message="Escolha a UF!")])
    nivel   = StringField('Nível:')
    tipoFun = StringField('Tipo Função:')
    email   = EmailField('E-mail:', validators = [Email('Informar um e-mail'), Optional()])
    siorg   = StringField('SIORG:')
    chefe   = SelectField('Chefe:',coerce=int)
    subs    = SelectField('Substituto:',coerce=int)
    
    submit  = SubmitField('Submeter')
