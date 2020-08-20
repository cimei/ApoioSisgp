"""novas tabelas siconv

Revision ID: 5699b907ea59
Revises: 
Create Date: 2019-07-04 13:33:50.211950

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5699b907ea59'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('desembolso',
    sa.Column('ID_DESEMBOLSO', sa.String(), nullable=False),
    sa.Column('NR_CONVENIO', sa.String(), nullable=True),
    sa.Column('DT_ULT_DESEMBOLSO', sa.String(), nullable=True),
    sa.Column('QTD_DIAS_SEM_DESEMBOLSO', sa.String(), nullable=True),
    sa.Column('DATA_DESEMBOLSO', sa.String(), nullable=True),
    sa.Column('ANO_DESEMBOLSO', sa.String(), nullable=True),
    sa.Column('MES_DESEMBOLSO', sa.String(), nullable=True),
    sa.Column('NR_SIAFI', sa.String(), nullable=True),
    sa.Column('VL_DESEMBOLSADO', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('ID_DESEMBOLSO')
    )
    op.create_table('empenho',
    sa.Column('ID_EMPENHO', sa.String(), nullable=False),
    sa.Column('NR_CONVENIO', sa.String(), nullable=True),
    sa.Column('NR_EMPENHO', sa.String(), nullable=True),
    sa.Column('TIPO_NOTA', sa.String(), nullable=True),
    sa.Column('DESC_TIPO_NOTA', sa.String(), nullable=True),
    sa.Column('DATA_EMISSAO', sa.String(), nullable=True),
    sa.Column('COD_SITUACAO_EMPENHO', sa.String(), nullable=True),
    sa.Column('DESC_SITUACAO_EMPENHO', sa.String(), nullable=True),
    sa.Column('VALOR_EMPENHO', sa.String(), nullable=True),
    sa.Column('ID_DESEMBOLSO', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('ID_EMPENHO')
    )
    op.create_table('pagamento',
    sa.Column('id_pagamento', sa.Integer(), nullable=False),
    sa.Column('NR_CONVENIO', sa.String(), nullable=True),
    sa.Column('IDENTIF_FORNECEDOR', sa.String(), nullable=True),
    sa.Column('NOME_FORNECEDOR', sa.String(), nullable=True),
    sa.Column('VL_PAGO', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id_pagamento')
    )
    op.create_table('programa_interesse',
    sa.Column('COD_PROGRAMA', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('COD_PROGRAMA')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('profile_image', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=64), nullable=True),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('despacha', sa.Boolean(), nullable=True),
    sa.Column('email_confirmation_sent_on', sa.DateTime(), nullable=True),
    sa.Column('email_confirmed', sa.Boolean(), nullable=True),
    sa.Column('email_confirmed_on', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('demandas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('programa', sa.String(), nullable=False),
    sa.Column('sei', sa.String(), nullable=False),
    sa.Column('convênio', sa.String(length=6), nullable=True),
    sa.Column('ano_convênio', sa.String(length=4), nullable=True),
    sa.Column('tipo', sa.String(), nullable=False),
    sa.Column('data', sa.DateTime(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('titulo', sa.String(length=140), nullable=False),
    sa.Column('desc', sa.Text(), nullable=False),
    sa.Column('necessita_despacho', sa.Boolean(), nullable=True),
    sa.Column('conclu', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('despachos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('data', sa.DateTime(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('demanda_id', sa.Integer(), nullable=False),
    sa.Column('texto', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['demanda_id'], ['demandas.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('providencias',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('data', sa.DateTime(), nullable=False),
    sa.Column('demanda_id', sa.Integer(), nullable=False),
    sa.Column('texto', sa.Text(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['demanda_id'], ['demandas.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('sqlite_sequence')
    op.drop_table('conv_programas_a_pegar')
    op.alter_column('acordos', 'sei',
               existing_type=sa.NUMERIC(),
               nullable=True)
    op.drop_index('processo_pagamento', table_name='pagamentospdctr')
    op.alter_column('processos_mae', 'acordo_nome',
               existing_type=sa.NUMERIC(),
               nullable=True)
    op.alter_column('processos_mae', 'epe',
               existing_type=sa.NUMERIC(),
               nullable=True)
    op.alter_column('processos_mae', 'uf',
               existing_type=sa.NUMERIC(precision=2),
               nullable=False)
    op.alter_column('processos_mae', 'valor',
               existing_type=sa.REAL(),
               nullable=True)
    op.alter_column('ref_pag_pdctr', 'data_ref',
               existing_type=sa.DATE(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('ref_pag_pdctr', 'data_ref',
               existing_type=sa.DATE(),
               nullable=False)
    op.alter_column('processos_mae', 'valor',
               existing_type=sa.REAL(),
               nullable=False)
    op.alter_column('processos_mae', 'uf',
               existing_type=sa.NUMERIC(precision=2),
               nullable=True)
    op.alter_column('processos_mae', 'epe',
               existing_type=sa.NUMERIC(),
               nullable=False)
    op.alter_column('processos_mae', 'acordo_nome',
               existing_type=sa.NUMERIC(),
               nullable=False)
    op.create_index('processo_pagamento', 'pagamentospdctr', ['processo', 'data_pagamento', 'tipo_pagamento'], unique=False)
    op.alter_column('acordos', 'sei',
               existing_type=sa.NUMERIC(),
               nullable=False)
    op.create_table('conv_programas_a_pegar',
    sa.Column('cod_programa', sa.INTEGER(), nullable=True)
    )
    op.create_table('sqlite_sequence',
    sa.Column('name', sa.NullType(), nullable=True),
    sa.Column('seq', sa.NullType(), nullable=True)
    )
    op.drop_table('providencias')
    op.drop_table('despachos')
    op.drop_table('demandas')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('programa_interesse')
    op.drop_table('pagamento')
    op.drop_table('empenho')
    op.drop_table('desembolso')
    # ### end Alembic commands ###
