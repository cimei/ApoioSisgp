"""

.. topic:: Padrões (formulários)

   Formulários de alteração tipos e situações específicos da instituição.

   * Situ_PessoasForm: registrar ou atualizar situações de uma pessoa.
   * Func_PessoasForm: registrar ou atualizar função.
   * Vinc_PessoasForm: registrar ou atualizar tipo de vínculo.
   * FeriadoForm: registrar ou atualizar feriado.

"""

# forms.py dentro de pessoas

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, BooleanField, DateField
from wtforms.validators import DataRequired

class Situ_PessoasForm(FlaskForm):

   id  = IntegerField('ID:', validators=[DataRequired(message="Informe um identificador para a situação!")])
   desc = StringField('Descrição:', validators=[DataRequired(message="Informe uma descrição para a situação!")])
       
   submit  = SubmitField('Submeter')

class Func_PessoasForm(FlaskForm):

   id   = IntegerField('ID:', validators=[DataRequired(message="Informe um identificador para a função!")])
   desc  = StringField('Descrição:', validators=[DataRequired(message="Informe a descrição da função!")])
   cod   = StringField('Código:')
   indic = BooleanField('Indicador Chefia:')

   submit  = SubmitField('Submeter')   

class Vinc_PessoasForm(FlaskForm):

   id  = IntegerField('ID:', validators=[DataRequired(message="Informe um identificador para vínculo!")])
   desc = StringField('Descrição:', validators=[DataRequired(message="Informe uma descrição para o vínculo!")])
       
   submit  = SubmitField('Submeter')

class FeriadoForm(FlaskForm):

   ferData      = DateField('Data:',format='%d/%m/%Y', validators=[DataRequired(message="Informe a data!")])
   ferDescricao = StringField('Descrição:', validators=[DataRequired(message="Informe a descrição!")])
   ferFixo      = BooleanField('Feriado é fixo?')
   ufId         = StringField('UF:')

   submit  = SubmitField('Submeter')  