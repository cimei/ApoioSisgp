"""

.. topic:: **Consultas (formulários)**

   Formulários:

   * PeriodoForm: para que o usuário informe o intervalo de datas para resgatar registros

"""

from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, IntegerField
from wtforms.fields.html5 import DateField

class PeriodoForm(FlaskForm):

    data_ini = DateField('Data Inicial: ', format='%Y-%m-%d')
    data_fim = DateField('Data Final: ', format='%Y-%m-%d')
    submit   = SubmitField('Procurar')

class AgendamentoForm(FlaskForm):

   tipo          = SelectField('Planos para envio:',choices=[('nunca_enviados','Nunca enviados'),('todos','Todos')])
   periodicidade = SelectField('Periodicidade',choices=[('Diária','Diária'),('Semanal','Semanal'),('Mensal','Mensal'),('Nenhuma','Nenhuma')])
   hora          = SelectField('Hora',choices=[(20,'20'),(21,'21'),(22,'22'),(23,'23'),(0,'00'),(1,'01'),(2,'02'),(3,'03')],coerce=int)
   minuto        = IntegerField('Minuto')    

   submit        = SubmitField('Agendar')