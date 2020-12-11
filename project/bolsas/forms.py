"""

.. topic:: Bolsas (formulários)

   O formulário do módulo *Bolsas* recebe dados informados pelo usuário para o registro de
   uma modalide/nível de bolsa. O formulário é o mesmo usado quando da atualização de dados de uma bolsa.

   * BolsaForm: utilizado registrar ou atualizar dados de uma bolsa.

**Campos definidos no formulário (todos são obrigatórios):**

"""

# forms.py dentro de bolsas

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, SubmitField
from wtforms.validators import DataRequired, Regexp

class BolsaForm(FlaskForm):
    mod         = StringField('Modalidade:',validators=[DataRequired(message="Informe a modalidade!")])
    niv         = StringField('Nível:',validators=[DataRequired(message="Informe o nível! Se não houver, coloque *.")])
    mensalidade = StringField('Valor da Mensalidade:',validators=[DataRequired(message="Informe o valor!")])
    auxilio     = StringField('Valor dos auxílios:',validators=[DataRequired(message="Informe o valor!")])
    submit      = SubmitField('Registrar')
