"""Initial migration: all tables

Revision ID: 0001
Revises: 
Create Date: 2026-03-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(255), nullable=True),
        sa.Column('last_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_telegram_user_id', 'users', ['telegram_user_id'], unique=True)

    # chats
    op.create_table(
        'chats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_chat_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('owner_user_id', sa.Integer(), nullable=True),
        sa.Column('bot_added_by_user_id', sa.Integer(), nullable=True),
        sa.Column('connected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('member_count', sa.Integer(), default=0),
        sa.Column('tariff', sa.String(20), default='free'),
        sa.Column('status', sa.String(20), default='active'),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['bot_added_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chats_telegram_chat_id', 'chats', ['telegram_chat_id'], unique=True)

    # chat_members
    op.create_table(
        'chat_members',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), default='member'),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('granted_by_user_id', sa.Integer(), nullable=True),
        sa.Column('can_ban', sa.Boolean(), default=False),
        sa.Column('can_mute', sa.Boolean(), default=False),
        sa.Column('can_warn', sa.Boolean(), default=False),
        sa.Column('can_edit_welcome', sa.Boolean(), default=False),
        sa.Column('can_edit_rules', sa.Boolean(), default=False),
        sa.Column('can_manage_protection', sa.Boolean(), default=False),
        sa.Column('can_manage_triggers', sa.Boolean(), default=False),
        sa.Column('can_view_logs', sa.Boolean(), default=False),
        sa.Column('can_view_stats', sa.Boolean(), default=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['granted_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_members_chat_id', 'chat_members', ['chat_id'])

    # chat_settings
    op.create_table(
        'chat_settings',
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('welcome_enabled', sa.Boolean(), default=False),
        sa.Column('welcome_text', sa.Text(), nullable=True),
        sa.Column('welcome_buttons', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('welcome_delete_after', sa.Integer(), nullable=True),
        sa.Column('rules_enabled', sa.Boolean(), default=False),
        sa.Column('rules_text', sa.Text(), nullable=True),
        sa.Column('anti_flood_enabled', sa.Boolean(), default=False),
        sa.Column('anti_flood_limit', sa.Integer(), default=5),
        sa.Column('anti_flood_interval', sa.Integer(), default=5),
        sa.Column('anti_flood_action', sa.String(20), default='mute'),
        sa.Column('anti_links_enabled', sa.Boolean(), default=False),
        sa.Column('anti_links_action', sa.String(20), default='delete'),
        sa.Column('stop_words_enabled', sa.Boolean(), default=False),
        sa.Column('stop_words_list', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('stop_words_action', sa.String(20), default='delete'),
        sa.Column('repeat_filter_enabled', sa.Boolean(), default=False),
        sa.Column('repeat_filter_sensitivity', sa.Float(), default=0.8),
        sa.Column('caps_filter_enabled', sa.Boolean(), default=False),
        sa.Column('caps_filter_threshold', sa.Float(), default=0.7),
        sa.Column('caps_filter_min_length', sa.Integer(), default=10),
        sa.Column('triggers_enabled', sa.Boolean(), default=True),
        sa.Column('logs_enabled', sa.Boolean(), default=True),
        sa.Column('default_warn_limit', sa.Integer(), default=3),
        sa.Column('warn_limit_action', sa.String(20), default='mute'),
        sa.Column('default_mute_duration', sa.Integer(), default=3600),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.PrimaryKeyConstraint('chat_id'),
    )

    # punishments
    op.create_table(
        'punishments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('issued_by_user_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), default='active'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['issued_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_punishments_chat_id', 'punishments', ['chat_id'])
    op.create_index('ix_punishments_user_id', 'punishments', ['user_id'])

    # warnings
    op.create_table(
        'warnings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('issued_by_user_id', sa.Integer(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(20), default='active'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['issued_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_warnings_chat_id', 'warnings', ['chat_id'])
    op.create_index('ix_warnings_user_id', 'warnings', ['user_id'])

    # triggers
    op.create_table(
        'triggers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('trigger_text', sa.String(500), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.Column('match_type', sa.String(20), default='contains'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_triggers_chat_id', 'triggers', ['chat_id'])

    # logs
    op.create_table(
        'logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_logs_chat_id', 'logs', ['chat_id'])
    op.create_index('ix_logs_action_type', 'logs', ['action_type'])
    op.create_index('ix_logs_created_at', 'logs', ['created_at'])

    # system_logs
    op.create_table(
        'system_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('service', sa.String(50), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_system_logs_level', 'system_logs', ['level'])
    op.create_index('ix_system_logs_created_at', 'system_logs', ['created_at'])

    # command_usage
    op.create_table(
        'command_usage',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('command', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_command_usage_chat_id', 'command_usage', ['chat_id'])

    # daily_metrics
    op.create_table(
        'daily_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('messages_count', sa.Integer(), default=0),
        sa.Column('commands_count', sa.Integer(), default=0),
        sa.Column('moderation_actions_count', sa.Integer(), default=0),
        sa.Column('warnings_count', sa.Integer(), default=0),
        sa.Column('mutes_count', sa.Integer(), default=0),
        sa.Column('bans_count', sa.Integer(), default=0),
        sa.Column('deleted_messages_count', sa.Integer(), default=0),
        sa.Column('mini_app_opens_count', sa.Integer(), default=0),
        sa.Column('active_users_count', sa.Integer(), default=0),
        sa.Column('protection_triggers_count', sa.Integer(), default=0),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_daily_metrics_chat_id', 'daily_metrics', ['chat_id'])
    op.create_index('ix_daily_metrics_date', 'daily_metrics', ['date'])

    # subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('plan', sa.String(20), default='free'),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_trial', sa.Boolean(), default=False),
        sa.Column('granted_by', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chat_id'),
    )

    # internal_notes
    op.create_table(
        'internal_notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_internal_notes_chat_id', 'internal_notes', ['chat_id'])


def downgrade() -> None:
    op.drop_table('internal_notes')
    op.drop_table('subscriptions')
    op.drop_table('daily_metrics')
    op.drop_table('command_usage')
    op.drop_table('system_logs')
    op.drop_table('logs')
    op.drop_table('triggers')
    op.drop_table('warnings')
    op.drop_table('punishments')
    op.drop_table('chat_settings')
    op.drop_table('chat_members')
    op.drop_table('chats')
    op.drop_table('users')
