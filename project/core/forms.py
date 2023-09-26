"""

.. topic:: Core (formulários)

   * ArquivoForm: permite escolher o arquivo para carga de dados.

**Campos definidos no formulário (todos são obrigatórios):**

"""

# forms.py dentro de core

from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.fields.html5 import DateField


class ArquivoForm(FlaskForm):

    arquivo = FileField('Arquivo:', validators=[FileRequired(message="Selecione um arquivo!"),FileAllowed(['csv'], 'Somente .csv!')])

    submit  = SubmitField('Importar')
    

class RefEnvioForm(FlaskForm):

    data_ref = DateField('Data de Referência: ', format='%Y-%m-%d')

    submit  = SubmitField('Registrar')    


