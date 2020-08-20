"""

.. topic:: Acordos (formulários)

   O formulário do módulo *Acordos* recebe dados informados pelo usuário para o registro
   de um novo acordo e é o mesmo utilizado quando da atualização de dados de um acordo já existente.

   * AcordoForm: registrar ou atualizar dados de um acordo.
   * Programa_CNPqForm: registrar ou atualizar dados de um programa do CNPq.
   * ArquivoForm: permite escolher o arquivo excel para carga de dados de acordo.

**Campos definidos no formulário (todos são obrigatórios):**

"""

# forms.py dentro de acordos

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, DateField, SubmitField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Regexp
from flask_wtf.file import FileField, FileAllowed, FileRequired
from project import db
from project.models import Programa_CNPq, Processo_Mae, Coords

class AcordoForm(FlaskForm):

    programas_cnpq = db.session.query(Programa_CNPq.COD_PROGRAMA,Programa_CNPq.SIGLA_PROGRAMA)\
                               .order_by(Programa_CNPq.NOME_PROGRAMA).all()
    lista_progs = [(prog[0],prog[1]) for prog in programas_cnpq]
    lista_progs.insert(0,('',''))

    programa_cnpq    = SelectField('Programa CNPq:',choices= lista_progs)
    nome             = StringField('Edição:',validators=[DataRequired(message="Informe um nome ou edição!")])
    sei              = StringField('Número SEI:',validators=[DataRequired(message="Informe o Programa!")]) # incluir regex para sei
    epe              = StringField('Sigla da EPE:',validators=[DataRequired(message="Informe a Instituição!")])
    uf               = StringField('UF (sigla):',validators=[DataRequired(message="Informe a sigla da UF!")])
    data_inicio      = DateField('Data de início do Acordo:',format='%d/%m/%Y',validators=[DataRequired(message="Informe data do início!")])
    data_fim         = DateField('Data de término do Acordo:',format='%d/%m/%Y',validators=[DataRequired(message="Informe data do término!")])
    valor_cnpq       = StringField('Valor alocado pelo CNPq:',validators=[DataRequired(message="Informe o valor!")])
    valor_epe        = StringField('Valor alocado pela EPE:',validators=[DataRequired(message="Informe o valor!")])

    submit           = SubmitField('Registrar')

#
class Programa_CNPqForm(FlaskForm):

    coords = db.session.query(Coords.sigla)\
                      .order_by(Coords.sigla).all()
    lista_coords = [(c[0],c[0]) for c in coords]
    lista_coords.insert(0,('',''))

    cod_programa   = StringField('Código:',validators=[DataRequired(message="Informe o código do programa!")])
    nome_programa  = StringField('Nome:',validators=[DataRequired(message="Informe o nome do Programa!")])
    sigla_programa = StringField('Sigla:',validators=[DataRequired(message="Informe a sigla do Programa!")])
    coord          = SelectField('Coordenação:',choices= lista_coords, validators=[DataRequired(message="Escolha uma Coordenção!")])

    submit      = SubmitField('Registrar')

class ArquivoForm(FlaskForm):

    arquivo = FileField('Arquivo:', validators=[FileRequired(message="Selecione um arquivo!"),FileAllowed(['xls'], 'Somente .xls!')])

    submit  = SubmitField('Importar')
#
def func_ProcMae_Acordo(programa):

    class ProcMae_Acordo(FlaskForm):
        pass

    procs_mae = db.session.query(Processo_Mae.id,Processo_Mae.proc_mae)\
                          .filter(Processo_Mae.cod_programa == programa)\
                          .all()

    lista_procs = [(str(proc[0]),proc[1]) for proc in procs_mae]

    proc_mae  = SelectMultipleField('Processos Mãe:',choices= lista_procs)

    submit      = SubmitField('Registrar')
    setattr(ProcMae_Acordo, "proc_mae", proc_mae)
    setattr(ProcMae_Acordo, "submit", submit)

    return ProcMae_Acordo()

#
# form para escolher a coordenação na lista de convênios
class ListaForm(FlaskForm):

    coords = db.session.query(Coords.sigla)\
                      .order_by(Coords.sigla).all()
    lista_coords = [(c[0],c[0]) for c in coords]
    lista_coords.insert(0,('',''))

    coord        = SelectField('Coordenação:',choices= lista_coords)
    submit       = SubmitField('Filtrar')
