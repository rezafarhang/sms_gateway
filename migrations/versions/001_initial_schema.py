"""initial schema with accounts and sms tables

Revision ID: b15c4b8243d8
Revises:
Create Date: 2025-12-22 10:03:39.667422

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b15c4b8243d8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('accounts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('api_key', sa.String(length=100), nullable=False),
    sa.Column('balance', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('api_key')
    )
    op.create_index('idx_accounts_api_key', 'accounts', ['api_key'], unique=False)
    op.create_table('sms',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('account_id', sa.UUID(), nullable=False),
    sa.Column('phone_number', sa.String(length=20), nullable=False),
    sa.Column('message', sa.String(length=70), nullable=False),
    sa.Column('sms_type', sa.SmallInteger(), nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('sent_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
    sa.PrimaryKeyConstraint('id', 'created_at'),
    postgresql_partition_by='RANGE (created_at)'
    )

    op.execute("""
        CREATE TABLE sms_2025_12 PARTITION OF sms
        FOR VALUES FROM ('2025-12-01') TO ('2026-01-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_01 PARTITION OF sms
        FOR VALUES FROM ('2026-01-01') TO ('2026-02-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_02 PARTITION OF sms
        FOR VALUES FROM ('2026-02-01') TO ('2026-03-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_03 PARTITION OF sms
        FOR VALUES FROM ('2026-03-01') TO ('2026-04-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_04 PARTITION OF sms
        FOR VALUES FROM ('2026-04-01') TO ('2026-05-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_05 PARTITION OF sms
        FOR VALUES FROM ('2026-05-01') TO ('2026-06-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_06 PARTITION OF sms
        FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_07 PARTITION OF sms
        FOR VALUES FROM ('2026-07-01') TO ('2026-08-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_08 PARTITION OF sms
        FOR VALUES FROM ('2026-08-01') TO ('2026-09-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_09 PARTITION OF sms
        FOR VALUES FROM ('2026-09-01') TO ('2026-10-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_10 PARTITION OF sms
        FOR VALUES FROM ('2026-10-01') TO ('2026-11-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_11 PARTITION OF sms
        FOR VALUES FROM ('2026-11-01') TO ('2026-12-01')
    """)

    op.execute("""
        CREATE TABLE sms_2026_12 PARTITION OF sms
        FOR VALUES FROM ('2026-12-01') TO ('2027-01-01')
    """)
    op.create_index('idx_sms_created', 'sms', ['created_at'], unique=False)
    op.create_index('idx_sms_status', 'sms', ['status'], unique=False)
    op.create_index('idx_sms_account_created', 'sms', ['account_id', 'created_at'], unique=False)
    op.create_index('idx_sms_account_status', 'sms', ['account_id', 'status', 'created_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_index('idx_sms_account_status', table_name='sms')
    op.drop_index('idx_sms_account_created', table_name='sms')
    op.drop_index('idx_sms_status', table_name='sms')
    op.drop_index('idx_sms_created', table_name='sms')
    op.drop_table('sms')
    op.drop_index('idx_accounts_api_key', table_name='accounts')
    op.drop_table('accounts')
