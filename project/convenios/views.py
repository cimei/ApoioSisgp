"""
.. topic:: Convênios (views)

    Os Convênios são instrumentos de parceria entre o CNPq e Entidades Parceiras Estaduais - EPEs onde
    há repasse direto de recursos das partes para a conta do convênio.

    Os convênios são gerenciados por meio do SICONV, contudo o trâmite administrativo no CNPq demanda os registros em processo
    SEI.

    Um convênio tem atributos relativos ao SEI registrados manualmente. Demais dados podem ser importados do SICONV.

    Os campos relativos ao SEI são:

    * Número do convênio no SICONV
    * Ano do convênio no SICONV
    * Número do processo SEI
    * Sigla da EPE
    * Unidade da Federação da EPE
    * Sigla do programa

    Dados relativos ao importado do SICONV estão em implementação...

.. topic:: Ações relacionadas aos convênios

    * Lista programas da coordenação: lista_programas_pref
    * Atualiza lista de programas da coordenação: prog_pref_update
    * Insere um novo programa na lista de programas da coordenação: cria_Prog_Pref
    * Atualizar dados SEI de um convenio: update_SEI
    * Registrar um dados SEI de um convê no sistema: cria_SEI
    * Listar convênios SICONV: lista_convenios_SICONV
    * Mostra detalhes de um determinado convênio: convenio_detalhe
    * Listar demandas de um determinado Convênio: SEI_demandas
    * Listar demandas relacinadas aos processos de uma UF: demandas_UF
    * Listar mensagens SICONV previamente carregadas: msg_siconv
    * Mostra quadro de convênios por UF: quadro_convenios
    * Lista os convênios conforme selecionado no quado de convênios: lista_convenios_quadro
    * Lista todos os convênios de uma UF selecionada no quado de convênios: lista_convenios_uf
    * Mostra dados gerais dos programas e seus convênios: resumo_convenios

"""

# views.py na pasta convenios

from flask import render_template,url_for,flash, redirect,request,Blueprint
from flask_login import current_user,login_required
from sqlalchemy import func, distinct
from sqlalchemy.sql import label
from project import db
from project.models import DadosSEI, Convenio, Demanda, User, Programa_Interesse, RefSICONV, Empenho,\
                           Desembolso, Pagamento, Chamadas, MSG_Siconv, Proposta, Programa, Coords, Emp_Cap_Cus
from project.convenios.forms import SEIForm, ProgPrefForm, ListaForm, NDForm
from project.demandas.views import registra_log_auto

import locale
import datetime
from datetime import date


convenios = Blueprint('convenios',__name__,
                            template_folder='templates/convenios')

#

def none_0(a):
    '''
    DOCSTRING: Transforma None em 0.
    INPUT: campo a ser trandormado.
    OUTPUT: 0, se a entrada for None, caso contrário, a entrada.
    '''
    if a == None:
        a = 0
    return a

## lista programas da coordenação

@convenios.route('/lista_programas_pref')
def lista_programas_pref():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos programas sob a responsabilidade da coordenação.               |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    ## lê tabela programas_a_pegar
    progs = db.session.query(Programa_Interesse.cod_programa,
                             Programa_Interesse.desc,
                             Programa_Interesse.sigla,
                             Programa_Interesse.coord)\
                      .order_by(Programa_Interesse.sigla).all()

    quantidade = len(progs)

    inst = db.session.query(RefSICONV.cod_inst).first()

    return render_template('lista_programas_pref.html', progs = progs, quantidade=quantidade, cod_inst = inst.cod_inst)

#
### ATUALIZAR LISTA DE PROGRAMAS PREFERENCIAIS (PROGRAMAS DA COORDENAÇÃO)

@convenios.route("/<int:cod_prog>/update", methods=['GET', 'POST'])
@login_required
def prog_pref_update(cod_prog):
    """
    +----------------------------------------------------------------------------------------------+
    |Permite atualizar os dados de um programa preferencial (programa da coordenação).             |
    |                                                                                              |
    |Recebe o código do progrma como parâmetro.                                                    |
    +----------------------------------------------------------------------------------------------+
    """

    programa = Programa_Interesse.query.get_or_404(cod_prog)

    form = ProgPrefForm()

    if form.validate_on_submit():

        programa.cod_programa = form.cod_programa.data
        programa.desc         = form.desc.data
        programa.sigla        = form.sigla.data
        programa.coord        = form.coord.data

        db.session.commit()

        registra_log_auto(current_user.id,None,'pre')

        flash('Programa preferencial atualizado!','sucesso')
        return redirect(url_for('convenios.lista_programas_pref'))
    # traz a informação atual do programa
    elif request.method == 'GET':
        form.cod_programa.data = programa.cod_programa
        form.desc.data         = programa.desc
        form.sigla.data        = programa.sigla
        form.coord.data        = programa.coord

    return render_template('add_prog_pref.html',
                           form=form)

#
### INSERIR PROGRAMA PREFERENCIAL (PROGRAMAS DA COORDENAÇÃO)

@convenios.route("/cria_Prog_Pref", methods=['GET', 'POST'])
@login_required
def cria_Prog_Pref():
    """
    +---------------------------------------------------------------------------------------+
    |Permite inseir um programa na lista de programas preferenciais.                        |
    +---------------------------------------------------------------------------------------+
    """

    form = ProgPrefForm()

    if form.validate_on_submit():
        programa = Programa_Interesse(cod_programa = form.cod_programa.data,
                                      desc         = form.desc.data,
                                      sigla        = form.sigla.data,
                                      coord        = form.coord.data)
        db.session.add(programa)
        db.session.commit()

        registra_log_auto(current_user.id,None,'pre')

        flash('Programa preferencial inserido!','sucesso')
        return redirect(url_for('convenios.lista_programas_pref'))

    return render_template('add_prog_pref.html', form=form)




### ATUALIZAR SEI

@convenios.route("/<int:SEI_id>/update_SEI", methods=['GET', 'POST'])
@login_required
def update_SEI(SEI_id):
    """
    +----------------------------------------------------------------------------------------------+
    |Permite atualizar os dados de um registro SEI de um convênio selecionado na tela de consulta. |
    |                                                                                              |
    |Recebe o ID do registro SEI como parâmetro.                                                   |
    +----------------------------------------------------------------------------------------------+
    """

    dadosSEI = DadosSEI.query.get_or_404(SEI_id)

    form = SEIForm()

    if form.validate_on_submit():

        dadosSEI.nr_convenio = form.nr_convenio.data
        dadosSEI.ano         = form.ano.data
        dadosSEI.sei         = form.sei.data
        dadosSEI.epe         = form.epe.data
        dadosSEI.uf          = form.uf.data
        dadosSEI.programa    = form.programa.data

        db.session.commit()

        registra_log_auto(current_user.id,None,'sei')

        flash('Registro SEI do convênio atualizado!','sucesso')
        return redirect(url_for('convenios.lista_convenios_SICONV',lista='todos',coord='*'))
    # traz a informação atual do registro SEI
    elif request.method == 'GET':
        form.nr_convenio.data = dadosSEI.nr_convenio
        form.ano.data         = dadosSEI.ano
        form.sei.data         = dadosSEI.sei
        form.epe.data         = dadosSEI.epe
        form.uf.data          = dadosSEI.uf
        form.programa.data    = dadosSEI.programa

    return render_template('add_SEI.html', title='Update',
                           form=form)

### CRIAR SEI

@convenios.route("/<conv>/criar_dadosSEI", methods=['GET', 'POST'])
@login_required
def cria_SEI(conv):
    """
    +---------------------------------------------------------------------------------------+
    |Permite registrar os dados de um processo SEI referente a um convênio.                 |
    +---------------------------------------------------------------------------------------+
    """

    form = SEIForm()

    if form.validate_on_submit():

        verifica = db.session.query(DadosSEI).filter(DadosSEI.nr_convenio == form.nr_convenio.data).first()

        if verifica == None:

            dadosSEI = DadosSEI(nr_convenio = form.nr_convenio.data,
                                ano         = form.ano.data,
                                sei         = form.sei.data,
                                epe         = form.epe.data,
                                uf          = form.uf.data,
                                programa    = form.programa.data,
                               )
            db.session.add(dadosSEI)
            db.session.commit()

            registra_log_auto(current_user.id,None,'sei')

            flash('Registro SEI para convênio criado!','sucesso')
        else:
            flash ('Já existe registro de processo SEI para o convênio '+str(form.nr_convenio.data)+'! Favor verificar.', 'erro')

        return redirect(url_for('convenios.lista_convenios_SICONV',lista='todos',coord='*'))

    else:

        if conv != '*':
            form.nr_convenio.data = conv

        return render_template('add_SEI.html', form=form)

## lista convênios

@convenios.route('/<lista>/<coord>/lista_convenios_SICONV', methods=['GET', 'POST'])
def lista_convenios_SICONV(lista,coord):
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos convênios de responsabilidade da COPES no SICONV.              |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """

    form = ListaForm()

    if form.validate_on_submit():

        coord = form.coord.data

        if coord == '' or coord == None:
            coord = '*'

        return redirect(url_for('convenios.lista_convenios_SICONV',lista=lista,coord=coord))

    else:

        #
        if coord == '*':

            form.coord.data = ''

            programa = db.session.query(Proposta.ID_PROPOSTA,
                                        Proposta.ID_PROGRAMA,
                                        Proposta.UF_PROPONENTE,
                                        Programa.COD_PROGRAMA,
                                        Programa_Interesse.sigla)\
                                        .join(Programa,Programa.ID_PROGRAMA == Proposta.ID_PROGRAMA)\
                                        .join(Programa_Interesse,Programa_Interesse.cod_programa == Programa.COD_PROGRAMA)\
                                        .subquery()
        else:

            form.coord.data = coord

            if coord == 'inst':
                programa = db.session.query(Proposta.ID_PROPOSTA,
                                            Proposta.ID_PROGRAMA,
                                            Proposta.UF_PROPONENTE,
                                            Programa.COD_PROGRAMA,
                                            Programa_Interesse.sigla)\
                                            .join(Programa,Programa.ID_PROGRAMA == Proposta.ID_PROGRAMA)\
                                            .outerjoin(Programa_Interesse,Programa_Interesse.cod_programa == Programa.COD_PROGRAMA)\
                                            .subquery()
            else:
                programa = db.session.query(Proposta.ID_PROPOSTA,
                                            Proposta.ID_PROGRAMA,
                                            Proposta.UF_PROPONENTE,
                                            Programa.COD_PROGRAMA,
                                            Programa_Interesse.sigla)\
                                            .join(Programa,Programa.ID_PROGRAMA == Proposta.ID_PROGRAMA)\
                                            .join(Programa_Interesse,Programa_Interesse.cod_programa == Programa.COD_PROGRAMA)\
                                            .filter(Programa_Interesse.coord.like('%'+coord+'%'))\
                                            .subquery()

        if lista == 'todos':

            convenio = db.session.query(Convenio.NR_CONVENIO,
                                        DadosSEI.nr_convenio,
                                        DadosSEI.ano,
                                        DadosSEI.sei,
                                        DadosSEI.epe,
                                        programa.c.UF_PROPONENTE,
                                        programa.c.sigla,
                                        Convenio.SIT_CONVENIO,
                                        Convenio.SUBSITUACAO_CONV,
                                        Convenio.DIA_FIM_VIGENC_CONV,
                                        Convenio.VL_REPASSE_CONV,
                                        Convenio.VL_CONTRAPARTIDA_CONV,
                                        DadosSEI.id,
                                        Convenio.VL_DESEMBOLSADO_CONV)\
                                        .join(programa, programa.c.ID_PROPOSTA == Convenio.ID_PROPOSTA)\
                                        .outerjoin(DadosSEI, Convenio.NR_CONVENIO == DadosSEI.nr_convenio)\
                                        .order_by(DadosSEI.programa.desc(),Convenio.SIT_CONVENIO,
                                                  DadosSEI.uf,DadosSEI.ano.desc())\
                                        .all()
    #
        elif lista == 'em execução':

            convenio = db.session.query(Convenio.NR_CONVENIO,
                                        DadosSEI.nr_convenio,
                                        DadosSEI.ano,
                                        DadosSEI.sei,
                                        DadosSEI.epe,
                                        programa.c.UF_PROPONENTE,
                                        programa.c.sigla,
                                        Convenio.SIT_CONVENIO,
                                        Convenio.SUBSITUACAO_CONV,
                                        Convenio.DIA_FIM_VIGENC_CONV,
                                        Convenio.VL_REPASSE_CONV,
                                        Convenio.VL_CONTRAPARTIDA_CONV,
                                        DadosSEI.id,
                                        Convenio.VL_DESEMBOLSADO_CONV)\
                                        .join(programa, programa.c.ID_PROPOSTA == Convenio.ID_PROPOSTA)\
                                        .outerjoin(DadosSEI, Convenio.NR_CONVENIO == DadosSEI.nr_convenio)\
                                        .filter(Convenio.SIT_CONVENIO == 'Em execução')\
                                        .order_by(Convenio.SUBSITUACAO_CONV.desc(),Convenio.DIA_FIM_VIGENC_CONV,
                                                  DadosSEI.programa.desc(), DadosSEI.uf,DadosSEI.ano.desc())\
                                        .all()

        #
        elif lista[:8] == 'programa':

            convenio = db.session.query(Convenio.NR_CONVENIO,
                                        DadosSEI.nr_convenio,
                                        DadosSEI.ano,
                                        DadosSEI.sei,
                                        DadosSEI.epe,
                                        programa.c.UF_PROPONENTE,
                                        programa.c.sigla,
                                        Convenio.SIT_CONVENIO,
                                        Convenio.SUBSITUACAO_CONV,
                                        Convenio.DIA_FIM_VIGENC_CONV,
                                        Convenio.VL_REPASSE_CONV,
                                        Convenio.VL_CONTRAPARTIDA_CONV,
                                        DadosSEI.id,
                                        Convenio.VL_DESEMBOLSADO_CONV)\
                                        .join(programa, programa.c.ID_PROPOSTA == Convenio.ID_PROPOSTA)\
                                        .outerjoin(DadosSEI, Convenio.NR_CONVENIO == DadosSEI.nr_convenio)\
                                        .filter(programa.c.sigla == lista[8:])\
                                        .order_by(Convenio.SIT_CONVENIO,Convenio.DIA_FIM_VIGENC_CONV,
                                                  DadosSEI.programa.desc(), DadosSEI.uf,DadosSEI.ano.desc())\
                                        .all()

        ## lê data de carga dos dados dos convênios
        data_carga = db.session.query(RefSICONV.data_ref).first()

        convenio_s = []
        for conv in convenio:

            conv_s = list(conv)
            if conv_s[11] is not None:
                conv_s[11] = locale.currency(conv_s[11], symbol=False, grouping = True)
            if conv_s[10] is not None:
                vl_a_desembolsar = locale.currency(conv.VL_REPASSE_CONV - conv.VL_DESEMBOLSADO_CONV, symbol=False, grouping = True)
                conv_s[10] = locale.currency(conv_s[10], symbol=False, grouping = True)
            if conv_s[9] is not None:
                conv_s[9] = conv_s[9].strftime('%x')

            conv_s.append((conv.DIA_FIM_VIGENC_CONV - datetime.date.today()).days)

            conv_s.append(vl_a_desembolsar)

            convenio_s.append(conv_s)

        quantidade = len(convenio)

        return render_template('list_convenios.html', convenio = convenio_s, quantidade=quantidade, lista=lista,
                                form = form, data_carga = str(data_carga[0]))


#
    ## Detalhes de um convênio específico
@convenios.route('/<conv>/convenio_detalhe')
def convenio_detalhe(conv):
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta os dados de um convênio específico.                                          |
    |Recebe o número do convênio como parâmetro.                                            |
    +---------------------------------------------------------------------------------------+
    """

    convenio = db.session.query(Convenio).get(conv)

    ## lê data de carga dos dados dos convênios
    data_carga = db.session.query(RefSICONV.data_ref).first()


    empenho_desembolso = db.session.query(Empenho.NR_EMPENHO,
                                          Empenho.DESC_TIPO_NOTA,
                                          Empenho.DATA_EMISSAO,
                                          Empenho.DESC_SITUACAO_EMPENHO,
                                          Empenho.VALOR_EMPENHO,
                                          Desembolso.DATA_DESEMBOLSO,
                                          Desembolso.NR_SIAFI,
                                          Desembolso.VL_DESEMBOLSADO,
                                          Emp_Cap_Cus.nd,
                                          Empenho.ID_EMPENHO)\
                                         .outerjoin(Desembolso, Desembolso.ID_EMPENHO == Empenho.ID_EMPENHO)\
                                         .outerjoin(Emp_Cap_Cus, Emp_Cap_Cus.id_empenho == Empenho.ID_EMPENHO)\
                                         .filter(Empenho.NR_CONVENIO == conv)\
                                         .order_by(Empenho.DATA_EMISSAO.desc()).all()


    empenho = db.session.query(label('emp_tot',func.sum(Empenho.VALOR_EMPENHO)))\
                               .filter(Empenho.NR_CONVENIO == conv)

    pagamento = db.session.query(Pagamento.IDENTIF_FORNECEDOR,
                                 Pagamento.NOME_FORNECEDOR,
                                 label("pago",func.sum(Pagamento.VL_PAGO)),
                                 label("qtd",func.count(Pagamento.VL_PAGO)))\
                                 .filter(Pagamento.NR_CONVENIO == conv)\
                                 .group_by(Pagamento.NOME_FORNECEDOR)\
                                 .order_by(Pagamento.NOME_FORNECEDOR).all()

    dadosSEI = db.session.query(DadosSEI).filter(DadosSEI.nr_convenio == conv).first()

    if dadosSEI != None:
        sei_conv = dadosSEI.sei
    else:
        sei_conv = '*'

    chamadas = db.session.query(Chamadas.id,
                                    Chamadas.chamada,
                                    Chamadas.qtd_projetos,
                                    Chamadas.vl_total_chamada,
                                    Chamadas.doc_sei,
                                    Chamadas.obs).filter(Chamadas.sei == sei_conv).all()

    proposta = db.session.query(Proposta).filter(Proposta.ID_PROPOSTA == convenio.ID_PROPOSTA).first()

    programa = db.session.query(Programa).filter(Programa.ID_PROGRAMA == proposta.ID_PROGRAMA).first()
#

    VL_GLOBAL_CONV              = locale.currency(convenio.VL_GLOBAL_CONV, symbol=False, grouping = True)

    if convenio.VL_REPASSE_CONV == 0 or convenio.VL_REPASSE_CONV == None:
        percent_desemb_repass   = 0
    else:
        percent_desemb_repass   = round(100*convenio.VL_DESEMBOLSADO_CONV / convenio.VL_REPASSE_CONV)

    if convenio.VL_CONTRAPARTIDA_CONV == 0 or convenio.VL_CONTRAPARTIDA_CONV == None:
        percent_ingre_contrap   = 0
    else:
        percent_ingre_contrap   = round(100*convenio.VL_INGRESSO_CONTRAPARTIDA / convenio.VL_CONTRAPARTIDA_CONV)

    if convenio.VL_REPASSE_CONV == 0 or convenio.VL_REPASSE_CONV == None:
        percent_empen_repass    = 0
    else:
        percent_empen_repass    = round(100*convenio.VL_EMPENHADO_CONV / convenio.VL_REPASSE_CONV)

    VL_REPASSE_CONV             = locale.currency(convenio.VL_REPASSE_CONV, symbol=False, grouping = True)
    VL_DESEMBOLSADO_CONV        = locale.currency(convenio.VL_DESEMBOLSADO_CONV, symbol=False, grouping = True)
    VL_EMPENHADO_CONV           = locale.currency(convenio.VL_EMPENHADO_CONV, symbol=False, grouping = True)
    VL_CONTRAPARTIDA_CONV       = locale.currency(convenio.VL_CONTRAPARTIDA_CONV, symbol=False, grouping = True)
    VL_INGRESSO_CONTRAPARTIDA   = locale.currency(convenio.VL_INGRESSO_CONTRAPARTIDA, symbol=False, grouping = True)
    VL_RENDIMENTO_APLICACAO     = locale.currency(convenio.VL_RENDIMENTO_APLICACAO, symbol=False, grouping = True)

    vl_a_empenhar    = locale.currency(convenio.VL_REPASSE_CONV - convenio.VL_EMPENHADO_CONV, symbol=False, grouping = True)
    vl_a_desembolsar = locale.currency(convenio.VL_REPASSE_CONV - convenio.VL_DESEMBOLSADO_CONV, symbol=False, grouping = True)

    pagamento_s = []
    pag_tot = 0
    for pag in pagamento:
        pag_s = list(pag)
        pag_tot += pag[2]
        if pag_s[2] is not None:
            pag_s[2] = locale.currency(pag_s[2], symbol=False, grouping = True)

        pagamento_s.append(pag_s)

    qtd_pag = len(pagamento)

    emp_tot = 0
    desemb_tot = 0
    empenho_desembolso_s = []

    for e_d in empenho_desembolso:
        e_d_s = list (e_d)
        if e_d_s[4] == None:
            p_emp = ''
        else:
            p_emp = locale.currency(e_d_s[4], symbol=False, grouping = True)
        if e_d_s[7] == None:
            p_des = ''
        else:
            p_des = locale.currency(e_d_s[7], symbol=False, grouping = True)
        if e_d_s[6] == None:
            siafi = ''
        else:
            siafi = e_d_s[6]
        if e_d_s[8] == None:
            nd = '?'
        else:
            nd = e_d_s[8]

        empenho_desembolso_s.append([e_d_s[0],e_d_s[1],e_d_s[2],e_d_s[3],p_emp,e_d_s[5],siafi,p_des,nd,e_d_s[9]])

        if e_d.VL_DESEMBOLSADO == None:
            desemb_tot += 0
        else:
            desemb_tot += e_d.VL_DESEMBOLSADO

    chamadas_s = []
    chamadas_tot = 0
    qtd_proj = 0
    for chamada in chamadas:
        chamadas_s.append([chamada.id,chamada.chamada,chamada.qtd_projetos,
                          locale.currency(chamada.vl_total_chamada, symbol=False, grouping = True),
                          chamada.doc_sei,chamada.obs])
        chamadas_tot += chamada.vl_total_chamada
        qtd_proj += chamada.qtd_projetos
    qtd_chamadas = len(chamadas)

    if sei_conv != '*':
        sei = str(dadosSEI.sei).split('/')[0]+'_'+str(dadosSEI.sei).split('/')[1]
    else:
        sei = 'Nº SEI não informado'

    return render_template('convenio_detalhe.html',convenio=convenio,
                                                   dadosSEI = dadosSEI,
                                                   VL_GLOBAL_CONV = VL_GLOBAL_CONV,
                                                   VL_REPASSE_CONV = VL_REPASSE_CONV,
                                                   VL_DESEMBOLSADO_CONV = VL_DESEMBOLSADO_CONV,
                                                   VL_EMPENHADO_CONV = VL_EMPENHADO_CONV,
                                                   VL_CONTRAPARTIDA_CONV = VL_CONTRAPARTIDA_CONV,
                                                   VL_INGRESSO_CONTRAPARTIDA = VL_INGRESSO_CONTRAPARTIDA,
                                                   VL_RENDIMENTO_APLICACAO = VL_RENDIMENTO_APLICACAO,
                                                   vl_a_empenhar = vl_a_empenhar,
                                                   vl_a_desembolsar = vl_a_desembolsar,
                                                   empenho_desembolso=empenho_desembolso_s,
                                                   pagamento=pagamento_s,
                                                   qtd_pag=qtd_pag,
                                                   pag_tot=locale.currency(pag_tot, symbol=False, grouping = True),
                                                   emp_tot=locale.currency(empenho[0][0], symbol=False, grouping = True),
                                                   desemb_tot=locale.currency(desemb_tot, symbol=False, grouping = True),
                                                   chamadas=chamadas_s,
                                                   qtd_chamadas=qtd_chamadas,
                                                   qtd_proj=qtd_proj,
                                                   chamadas_tot=locale.currency(chamadas_tot, symbol=False, grouping = True),
                                                   sei = sei,
                                                   data_carga = data_carga[0],
                                                   proposta=proposta,
                                                   percent_desemb_repass=percent_desemb_repass,
                                                   percent_ingre_contrap=percent_ingre_contrap,
                                                   percent_empen_repass=percent_empen_repass,
                                                   programa=programa)

#

#
### altera dados de chamada homologada

@convenios.route("/<id>/<conv>/update_nd", methods=['GET', 'POST'])
@login_required
def update_nd(id,conv):
    """
    +---------------------------------------------------------------------------------------+
    |Permite alterar os dados de natureza de despesa de um empenho.                         |
    |                                                                                       |
    |Recebe o id do empenho como parâmetro.                                                 |
    +---------------------------------------------------------------------------------------+
    """

    nd = Emp_Cap_Cus.query.get(id)

    form = NDForm()

    if form.validate_on_submit():

        if nd != None:
            nd.nd = form.nd.data
        else:
            nd = Emp_Cap_Cus(id_empenho = id,
                             nd         = form.nd.data)
            db.session.add(nd)

        db.session.commit()

        registra_log_auto(current_user.id,None,'and')

        flash('ND atualizada!','sucesso')

        return redirect(url_for('convenios.convenio_detalhe', conv=conv))
    #
    # traz a informação atual
    elif request.method == 'GET':

        if nd != None:
            form.nd.data = nd.nd

    emp = db.session.query(Empenho.NR_EMPENHO).filter(Empenho.ID_EMPENHO == id).first()

    return render_template('add_nd.html', form=form, emp=emp)

# lista das demandas relacionadas a um convênio

@convenios.route('/<conv>')
def SEI_demandas (conv):
    """+--------------------------------------------------------------------------------------+
       |Mostra as demandas relacionadas a um processo SEI quando seu NUP é selecionado em uma |
       |lista de convênios.                                                                   |
       |Recebe o número do convênio como parâmetro.                                           |
       +--------------------------------------------------------------------------------------+
    """

    conv_SEI = db.session.query(DadosSEI.sei,DadosSEI.programa,DadosSEI.nr_convenio,DadosSEI.ano)\
                         .filter_by(nr_convenio=conv).first()

    SEI = conv_SEI.sei
    SEI_s = str(SEI).split('/')[0]+'_'+str(SEI).split('/')[1]

    #demandas_count = Demanda.query.filter(Demanda.sei.like('%'+SEI+'%')).count()
    demandas_count = Demanda.query.filter(Demanda.convênio == conv).count()

    #demandas = Demanda.query.filter(Demanda.sei.like('%'+SEI+'%'))\
    #                        .order_by(Demanda.data.desc()).all()
    demandas = Demanda.query.filter(Demanda.convênio == conv)\
                            .order_by(Demanda.data.desc()).all()


    autores=[]
    for demanda in demandas:
        autores.append(str(User.query.filter_by(id=demanda.user_id).first()).split(';')[0])

    dados = [conv_SEI.programa,SEI_s,conv_SEI.nr_convenio,conv_SEI.ano]

    return render_template('Conv_demandas.html',demandas_count=demandas_count,demandas=demandas,sei=SEI, autores=autores,dados=dados)

#
#
#vendo demandas relacionadas aos processos de uma UF

@convenios.route('/<programa>/<filtro>/<uf>/demandas_UF')
def demandas_UF(programa,filtro,uf):
    """
        +----------------------------------------------------------------------+
        |Lista as demandas, de uma determinada UF.                             |
        +----------------------------------------------------------------------+
    """

    processos = db.session.query(DadosSEI.sei)\
                                .filter(DadosSEI.uf == uf)\
                                .all()

    demandas_s = []
    qtd = 0

    if programa == 'todos':
        programa = ''

    for processo in processos:

        if filtro == 'nc':
            demandas = Demanda.query.filter(Demanda.sei==processo.sei,Demanda.programa.like('%'+programa+'%'), Demanda.conclu==False)\
                                    .order_by(Demanda.data.desc()).all()
        else:
            demandas = Demanda.query.filter(Demanda.sei==processo.sei,Demanda.programa.like('%'+programa+'%'))\
                                    .order_by(Demanda.data.desc()).all()
        qtd += len(demandas)

        demandas_s.append(demandas)

    if programa == '':
        programa = 'todos'

    return render_template('UF_demandas.html',demandas=demandas_s,filtro=filtro,uf=uf,qtd=qtd,programa=programa)


# lista das demandas relacionadas a um convênio

@convenios.route('/msg_siconv')
def msg_siconv ():
    """+--------------------------------------------------------------------------------------+
       |Lista as mensagens da tela inicial do SICONV que foram previamente carregadas em      |
       |procedimento próprio.                                                                 |
       +--------------------------------------------------------------------------------------+
    """
    msgs = db.session.query(MSG_Siconv.data_ref,
                            MSG_Siconv.nr_convenio,
                            MSG_Siconv.desc,
                            DadosSEI.programa,
                            DadosSEI.epe,
                            DadosSEI.uf,
                            DadosSEI.sei,
                            Convenio.SIT_CONVENIO,
                            MSG_Siconv.sit)\
                            .join(DadosSEI,MSG_Siconv.nr_convenio == DadosSEI.nr_convenio)\
                            .join(Convenio,MSG_Siconv.nr_convenio == Convenio.NR_CONVENIO)\
                            .order_by(DadosSEI.programa,MSG_Siconv.desc).all()

    data_ref = msgs[0].data_ref

    return render_template('MSG_Siconv.html',msgs=msgs,data_ref=data_ref)

#
## quadro dos convênios

@convenios.route('/quadro_convenios')
def quadro_convenios():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta um quadro de convênios selecionáveis por UF e Programa que estejam           |
    |com os dados SEI preenchidos.                                                          |
    +---------------------------------------------------------------------------------------+
    """
    programas = db.session.query(DadosSEI.programa).filter(DadosSEI.nr_convenio != '')\
                                                   .order_by(DadosSEI.programa).group_by(DadosSEI.programa)

    convenios = db.session.query(func.count(Convenio.NR_CONVENIO),
                                DadosSEI.programa,
                                func.sum(Convenio.VL_GLOBAL_CONV),
                                DadosSEI.uf)\
                                .outerjoin(DadosSEI, Convenio.NR_CONVENIO == DadosSEI.nr_convenio)\
                                .order_by(DadosSEI.uf,DadosSEI.programa)\
                                .group_by(DadosSEI.uf)\
                                .group_by(DadosSEI.programa)\
                                .all()

    ufs = db.session.query(DadosSEI.uf).filter(DadosSEI.nr_convenio != '')\
                                       .group_by(DadosSEI.uf).order_by(DadosSEI.uf)

    ## lê data de carga dos dados dos convênios
    data_carga = db.session.query(RefSICONV.data_ref).first()

    convenios_s = []
    for conv in convenios:

        conv_s = list(conv)
        if conv_s[2] is not None:
            conv_s[2] = locale.currency(conv_s[2], symbol=False, grouping = True)

        convenios_s.append(conv_s)

    quantidade = len(list(ufs))

    linha = []
    linhas = []
    item = []

    for uf in ufs:
        for prog in programas:
            flag = False
            for conv in convenios_s:

                if conv[3] == uf.uf:
                    if conv[1] == prog.programa:
                        linha.append(conv)
                        flag = True
                    else:
                        item = [0,prog.programa,'',uf.uf]

            if not flag:
                linha.append(item)
                flag = False


        linhas.append(linha)
        linha=[]


    return render_template('quadro_convenios.html', quantidade=quantidade,
                            programas=programas,linhas=linhas,data_carga = str(data_carga[0]))

#
## lista convênios do quadro por UF e por programa

@convenios.route('/<uf>/<programa>/lista_convenios_mapa')
def lista_convenios_quadro(uf,programa):
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos convênios de uma determinada UF em um programa específico      |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    convenio = db.session.query(Convenio.NR_CONVENIO,
                                DadosSEI.nr_convenio,
                                DadosSEI.ano,
                                DadosSEI.sei,
                                DadosSEI.epe,
                                DadosSEI.uf,
                                DadosSEI.programa,
                                Convenio.SIT_CONVENIO,
                                Convenio.SUBSITUACAO_CONV,
                                Convenio.DIA_FIM_VIGENC_CONV,
                                Convenio.VL_GLOBAL_CONV,
                                DadosSEI.id)\
                                .outerjoin(DadosSEI, Convenio.NR_CONVENIO == DadosSEI.nr_convenio)\
                                .order_by(Convenio.SIT_CONVENIO,Convenio.DIA_FIM_VIGENC_CONV,DadosSEI.ano.desc())\
                                .filter(DadosSEI.uf == uf, DadosSEI.programa == programa)\
                                .all()

    ## lê data de carga dos dados dos convênios
    data_carga = db.session.query(RefSICONV.data_ref).first()

    convenio_s = []

    for conv in convenio:

        conv_s = list(conv)
        if conv_s[10] is not None:
            conv_s[10] = locale.currency(conv_s[10], symbol=False, grouping = True)
        if conv_s[9] is not None:
            conv_s[9] = conv_s[9].strftime('%x')

        conv_s.append((conv.DIA_FIM_VIGENC_CONV - datetime.date.today()).days)

        convenio_s.append(conv_s)

    quantidade = len(convenio)


    return render_template('list_convenios_quadro.html', convenio = convenio_s, quantidade=quantidade,
                            uf=uf,programa=programa,data_carga = str(data_carga[0]))

#
## lista convênios do quadro por UF (todos os programas)

@convenios.route('/<uf>/lista_convenios_mapa')
def lista_convenios_uf(uf):
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta uma lista dos convênios de uma determinada UF (todos os programas)           |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    convenio = db.session.query(Convenio.NR_CONVENIO,
                                DadosSEI.nr_convenio,
                                DadosSEI.ano,
                                DadosSEI.sei,
                                DadosSEI.epe,
                                DadosSEI.uf,
                                DadosSEI.programa,
                                Convenio.SIT_CONVENIO,
                                Convenio.SUBSITUACAO_CONV,
                                Convenio.DIA_FIM_VIGENC_CONV,
                                Convenio.VL_GLOBAL_CONV,
                                DadosSEI.id)\
                                .outerjoin(DadosSEI, Convenio.NR_CONVENIO == DadosSEI.nr_convenio)\
                                .order_by(DadosSEI.programa,Convenio.SIT_CONVENIO,Convenio.DIA_FIM_VIGENC_CONV,DadosSEI.ano.desc())\
                                .filter(DadosSEI.uf == uf)\
                                .all()

    ## lê data de carga dos dados dos convênios
    data_carga = db.session.query(RefSICONV.data_ref).first()

    convenio_s = []

    for conv in convenio:

        conv_s = list(conv)
        if conv_s[10] is not None:
            conv_s[10] = locale.currency(conv_s[10], symbol=False, grouping = True)
        if conv_s[9] is not None:
            conv_s[9] = conv_s[9].strftime('%x')

        conv_s.append((conv.DIA_FIM_VIGENC_CONV - datetime.date.today()).days)

        convenio_s.append(conv_s)

    quantidade = len(convenio)


    return render_template('list_convenios_quadro.html', convenio = convenio_s, quantidade=quantidade,
                            uf=uf,programa='todos', data_carga = str(data_carga[0]))

#
## RESUMO convênios

@convenios.route('/resumo_convenios')
def resumo_convenios():
    """
    +---------------------------------------------------------------------------------------+
    |Apresenta um resumo dos convênios por programa da coordenação.                         |
    |                                                                                       |
    +---------------------------------------------------------------------------------------+
    """
    convenios_exec = db.session.query(Convenio.ID_PROPOSTA,
                                      label('conv_exec',Convenio.NR_CONVENIO))\
                                      .filter(Convenio.SIT_CONVENIO=='Em execução')\
                                      .subquery()


    programas = db.session.query(Programa_Interesse.cod_programa,
                                 Programa_Interesse.sigla,
                                 label('qtd',func.count(Convenio.NR_CONVENIO)),
                                 label('vl_global',func.sum(Convenio.VL_GLOBAL_CONV)),
                                 label('vl_repasse',func.sum(Convenio.VL_REPASSE_CONV)),
                                 label('vl_empenhado',func.sum(Convenio.VL_EMPENHADO_CONV)),
                                 label('vl_desembolsado',func.sum(Convenio.VL_DESEMBOLSADO_CONV)),
                                 label('vl_contrapartida',func.sum(Convenio.VL_CONTRAPARTIDA_CONV)),
                                 label('vl_ingresso_contra',func.sum(Convenio.VL_INGRESSO_CONTRAPARTIDA)),
                                 label('qtd_exec',func.count(convenios_exec.c.conv_exec)))\
                                .join(Programa,Programa.COD_PROGRAMA==Programa_Interesse.cod_programa)\
                                .join(Proposta,Proposta.ID_PROGRAMA==Programa.ID_PROGRAMA)\
                                .join(Convenio,Convenio.ID_PROPOSTA==Proposta.ID_PROPOSTA)\
                                .outerjoin(convenios_exec,convenios_exec.c.ID_PROPOSTA==Proposta.ID_PROPOSTA)\
                                .group_by(Programa_Interesse.sigla)\
                                .order_by(Programa_Interesse.sigla.desc())\
                                .all()

    ## lê data de carga dos dados dos convênios
    data_carga = db.session.query(RefSICONV.data_ref).first()

    programas_s = []
    for prog in programas:

        prog_s = list(prog)

        prog_s[3] = locale.currency(none_0(prog_s[3]), symbol=False, grouping = True)
        prog_s[4] = locale.currency(none_0(prog_s[4]), symbol=False, grouping = True)
        prog_s[5] = locale.currency(none_0(prog_s[5]), symbol=False, grouping = True)
        prog_s[6] = locale.currency(none_0(prog_s[6]), symbol=False, grouping = True)
        prog_s[7] = locale.currency(none_0(prog_s[7]), symbol=False, grouping = True)
        prog_s[8] = locale.currency(none_0(prog_s[8]), symbol=False, grouping = True)

        if none_0(prog.vl_repasse) != 0:

            empenhado_repasse = round(100*float(none_0(prog.vl_empenhado))/float(none_0(prog.vl_repasse)))
            prog_s.append(empenhado_repasse)

            desembolsado_repasse = round(100*float(none_0(prog.vl_desembolsado))/float(none_0(prog.vl_repasse)))
            prog_s.append(desembolsado_repasse)

        if none_0(prog.vl_contrapartida) != 0:

            ingressado_contrapartida = round(100*float(none_0(prog.vl_ingresso_contra))/float(none_0(prog.vl_contrapartida)))
            prog_s.append(ingressado_contrapartida)

        programas_s.append(prog_s)


    return render_template('resumo_convenios.html',programas=programas_s,data_carga=str(data_carga[0]))
