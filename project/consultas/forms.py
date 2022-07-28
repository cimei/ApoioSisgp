"""

.. topic:: **Consultas (formulários)**

   Formulários:

   * PeriodoForm: para que o usuário informe o intervalo de datas para resgatar registros

"""

from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms.fields.html5 import DateField

class PeriodoForm(FlaskForm):

    data_ini = DateField('Data Inicial: ', format='%Y-%m-%d')
    data_fim = DateField('Data Final: ', format='%Y-%m-%d')
    submit   = SubmitField('Procurar')
