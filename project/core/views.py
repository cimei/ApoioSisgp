"""
.. topic:: Core (views)

    Este é o módulo inicial do sistema.

    Apresenta as telas de início, informação e procedimentos de carda de dados em lote.

.. topic:: Ações relacionadas aos bolsistas

    * Tela inicial: index
    * Tela de informações: info
    * Carrega dados de unidade em lote: CarregaUnidades
    * Carrega dados de pessoa em lote: CarregaPessoas

"""

# core/views.py

from flask import render_template,url_for,flash, redirect,request,Blueprint

import os
from datetime import datetime as dt
import tempfile
from flask_login import current_user
from werkzeug.utils import secure_filename
import csv

from project.core.forms import ArquivoForm
from project import db
from project.models import Unidades, Pessoas


core = Blueprint("core",__name__)


## função para abrir arquivo csv

def PegaArquivo(form):

    '''
        DOCSTRING: solicita arquivo do usuário e salva em diretório temporário para ser utilizado
        INPUT: formulário de entrada
        OUTPUT: arquivo de trabalho
    '''

    tempdirectory = tempfile.gettempdir()

    print ('### tempdir: ',tempdirectory )

    f = form.arquivo.data
    fname = secure_filename(f.filename)
    arquivo = os.path.join(tempdirectory, fname)
    f.save(arquivo)

    print ('***  ARQUIVO ***',arquivo)

    pasta = os.path.normpath(tempdirectory)

    if not os.path.exists(pasta):
        os.makedirs(os.path.normpath(pasta))

    arq = fname
    arq = os.path.normpath(pasta+'/'+arq)

    return arq

@core.route('/')
def index():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta a tela inicial do aplicativo.                                                |
    +---------------------------------------------------------------------------------------+
    """

    return render_template ('index.html',sistema='Apoio SISGP')

@core.route('/info')
def info():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta a tela de informações do aplicativo.                                         |
    +---------------------------------------------------------------------------------------+
    """

    return render_template('info.html')

@core.route('/carregaUnidades', methods=['GET', 'POST'])
def CarregaUnidades():
    """
    +---------------------------------------------------------------------------------------+
    |Executa o procedimento de carga dos dados de Unidades                                  |
    +---------------------------------------------------------------------------------------+

    """

    tipo = "unid"

    form = ArquivoForm()

    if form.validate_on_submit():

        if current_user.userAtivo:

            arq = PegaArquivo(form)

            print ('*****************************************************************')
            print ('<<',dt.now().strftime("%x %X"),'>> ','Carregando dados de Unidades...')
            print ('*****************************************************************')

            qtd = 0
            qtd_exist = 0
            qtdLinhas = 0

            siglaExistente = db.session.query(Unidades.undSigla).all()

            l_siglaExistente = [s[0] for s in siglaExistente]

            # abre csv e gera a lista data_lines
            with open(arq, newline='',encoding = 'utf-8-sig') as data:
                data_lines = csv.DictReader(data,delimiter=';')

                for linha in data_lines:

                    qtdLinhas += 1

                    if linha['undSigla'] in l_siglaExistente:

                        qtd_exist += 1
            
                    if linha['undSigla'] != '' and linha['undSigla'] != None and linha['undSigla'] not in l_siglaExistente:

                        if linha['unidadeIdPai'] == '' or linha['unidadeIdPai'] == 0:
                            pai = None
                        else:
                            pai = linha['unidadeIdPai']

                        if linha['pessoaIdChefe'] == '' or linha['pessoaIdChefe'] == 0:
                            chefe = None
                        else:
                            chefe = linha['pessoaIdChefe']

                        if linha['pessoaIdChefeSubstituto'] == '' or linha['pessoaIdChefeSubstituto'] == 0:
                            subs = None
                        else:
                            subs = linha['pessoaIdChefeSubstituto']    

                        unidade_gravar = Unidades(undSigla                = linha['undSigla'],
                                                undDescricao            = linha['undDescricao'],
                                                unidadeIdPai            = pai,
                                                tipoUnidadeId           = linha['tipoUnidadeId'],
                                                situacaoUnidadeId       = linha['situacaoUnidadeId'],
                                                ufId                    = linha['ufId'],
                                                undNivel                = linha['undNivel'],
                                                tipoFuncaoUnidadeId     = linha['tipoFuncaoUnidadeId'],
                                                Email                   = linha['Email'],
                                                undCodigoSIORG          = linha['undCodigoSIORG'],
                                                pessoaIdChefe           = chefe,
                                                pessoaIdChefeSubstituto = subs)

                        db.session.add(unidade_gravar)

                        qtd += 1

                db.session.commit()

                print ('*** ',qtdLinhas,'linhas no arquivo de entrada.')
                print ('*** ',qtd,'linhas inseridas na tabela unidade.')
                print ('*** ',qtd_exist,'linhas com siglas já existentes foram ignoradas.')
                print ('*****************************************************************')

                if qtd_exist == 0:

                    flash('Executada carga de unidades no DBSISGP. ' +\
                        str(qtdLinhas) +' linhas no arquivo de entrada, ' +\
                        str(qtd) + ' linhas efetivamente inseridas e ' +\
                        ' nenhuma linha foi ignorada por conter sigla de unidade já existente.','sucesso')

                else:

                    flash('Executada carga de unidades no DBSISGP. ' +\
                        str(qtdLinhas) +' linhas no arquivo de entrada, ' +\
                        str(qtd) + ' linhas efetivamente inseridas e ' +\
                        str(qtd_exist) + ' linhas ignoradas por conter siglas de unidades já existentes.','perigo')


            if os.path.exists(arq):
                os.remove(arq)

            return redirect(url_for('unidades.lista_unidades'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('unidades.lista_unidades'))

    return render_template('grab_file.html',form=form, tipo = tipo)


@core.route('/carregaPessoas', methods=['GET', 'POST'])
def CarregaPessoas():
    """
    +---------------------------------------------------------------------------------------+
    |Executa o procedimento de carga dos dados de Pessoas                                  |
    +---------------------------------------------------------------------------------------+

    """

    tipo = "pes"

    form = ArquivoForm()

    if form.validate_on_submit():

        if current_user.userAtivo:

            arq = PegaArquivo(form)

            print ('*****************************************************************')
            print ('<<',dt.now().strftime("%x %X"),'>> ','Carregando dados de Pessoas...')
            print ('*****************************************************************')

            qtd = 0
            qtd_exist = 0
            qtdLinhas = 0

            cpfExistente = db.session.query(Pessoas.pesCPF).all()

            l_cpfExistente = [c[0] for c in cpfExistente]

            # abre csv e gera a lista data_lines
            with open(arq, newline='',encoding = 'utf-8-sig') as data:
                data_lines = csv.DictReader(data,delimiter=';')

                for linha in data_lines:

                    qtdLinhas += 1

                    if linha['pesCPF'] in l_cpfExistente:

                        qtd_exist += 1
            
                    if linha['pesCPF'] != '' and linha['pesCPF'] != None and linha['pesCPF'] not in l_cpfExistente:

                        if linha['tipoFuncaoId'] == '' or linha['tipoFuncaoId'] == 0:
                            func = None
                        else:
                            func = linha['tipoFuncaoId']

                        if linha['situacaoPessoaId'] == '' or linha['situacaoPessoaId'] == 0:
                            sit = None
                        else:
                            sit = linha['situacaoPessoaId']

                        if linha['tipoVinculoId'] == '' or linha['tipoVinculoId'] == 0:
                            vinc = None
                        else:
                            vinc = linha['tipoVinculoId']   

                        pessoa_gravar = Pessoas(pesNome           = linha['pesNome'],
                                                pesCPF            = linha['pesCPF'],
                                                pesDataNascimento = linha['pesDataNascimento'],
                                                pesMatriculaSiape = linha['pesMatriculaSiape'],
                                                pesEmail          = linha['pesEmail'],
                                                unidadeId         = linha['unidadeId'],
                                                tipoFuncaoId      = func,
                                                cargaHoraria      = linha['cargaHoraria'],
                                                situacaoPessoaId  = sit,
                                                tipoVinculoId     = vinc)

                        db.session.add(pessoa_gravar)

                        qtd += 1

                db.session.commit()

                print ('*** ',qtdLinhas,'linhas no arquivo de entrada.')
                print ('*** ',qtd,'linhas inseridas na tabela pessoa.')
                print ('*** ',qtd_exist,'linhas com cpfs já existentes foram ignoradas.')
                print ('*****************************************************************')

                if qtd_exist == 0:

                    flash('Executada carga de Pessoas no DBSISGP. ' +\
                        str(qtdLinhas) +' linhas no arquivo de entrada, ' +\
                        str(qtd) + ' linhas efetivamente inseridas e ' +\
                        ' nenhuma linha foi ignorada por conter cpf de Pessoa já existente no banco.','sucesso')

                else:

                    flash('Executada carga de Pessoas no DBSISGP. ' +\
                        str(qtdLinhas) +' linhas no arquivo de entrada, ' +\
                        str(qtd) + ' linhas efetivamente inseridas e ' +\
                        str(qtd_exist) + ' linhas ignoradas por conter cpfs de Pessoas já existentes.','perigo')
            

            if os.path.exists(arq):
                os.remove(arq)        

            return redirect(url_for('pessoas.lista_pessoas'))

        else:

            flash('O seu usuário precisa ser ativado para esta operação!','erro')

            return redirect(url_for('pessoas.lista_pessoas'))

    return render_template('grab_file.html',form=form, tipo = tipo)




