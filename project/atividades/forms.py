"""

.. topic:: Atividades (formulários)

   Formulários de alteração da dados de atividades.

   * AtividadeForm: utilizado registrar ou atualizar dados de uma atividade.
   * UnidForm: utilizado para associar uma atividade a uma unidade.

"""

# forms.py dentro de atividades

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField, DecimalField
from wtforms.validators import DataRequired, Optional

class AtividadeForm(FlaskForm):

    titulo      = StringField('Título:', validators=[DataRequired(message="Informe o Título!")])
    calc_temp   = SelectField('Cálculo do tempo:',coerce=int, validators=[DataRequired(message="Informe a forma do cálculo do tempo!")])
    remoto      = BooleanField('Permite remoto:')
    tempo_pres  = StringField('Tempo Presencial:')
    tempo_rem   = StringField('Tempo Remoto:')
    descricao   = StringField('Descrição:')
    complex     = StringField('Complexidade:')
    def_complex = StringField('Definição da Complexidade:')
    entregas    = StringField('Entregas:')
    
    submit  = SubmitField('Submeter')

class UnidForm(FlaskForm):

   unid = SelectField('Unidade:',coerce=int, validators=[DataRequired(message="Escolha uma unidade!")])

   submit  = SubmitField('Submeter')