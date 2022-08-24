"""

.. topic:: Pessoas (formulários)

   Formulários de alteração da dados de pessoas da instituição.

   * PessoaForm: utilizado registrar ou atualizar dados de uma pessoa.

"""

# forms.py dentro de pessoas

from xmlrpc.client import Boolean
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Optional, Email
from wtforms.fields.html5 import EmailField, DateField


class PessoaForm(FlaskForm):

   nome    = StringField('Nome:', validators=[DataRequired(message="Informe o nome completo!")])
   cpf     = StringField('CPF:',validators=[DataRequired(message="Informe o CPF!")])
   nasc    = DateField('Dt Nasc.:',format='%Y-%m-%d',validators=[DataRequired(message="Informe a data de nascimento!")])
   siape   = StringField('Matrícula SIAPE:')
   email   = EmailField('E-mail:', validators = [Email('Informar um e-mail'), Optional()])
   unidade = SelectField('Unidade:',validators=[DataRequired(message="Escolha a unidade!")],coerce=int)
   func    = SelectField('Função:',coerce=int)
   carga   = IntegerField('Carga Horária:')
   situ    = SelectField('Situação:',coerce=int)
   vinculo = SelectField('Tipo vínculo:',coerce=int)
   gestor  = BooleanField('Gestor(a) SISGP?')
    
   submit  = SubmitField('Submeter')
