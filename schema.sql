-- ============================================================
--  Svetka MVP — начальная схема БД
--  Вставьте в Neon SQL Editor и нажмите Run
--  Порядок важен — FK constraints соблюдены
-- ============================================================

-- users
CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    telegram_user_id    BIGINT NOT NULL,
    username            VARCHAR(255),
    first_name          VARCHAR(255),
    last_name           VARCHAR(255),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at        TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_telegram_user_id ON users (telegram_user_id);

-- chats
CREATE TABLE IF NOT EXISTS chats (
    id                      SERIAL PRIMARY KEY,
    telegram_chat_id        BIGINT NOT NULL,
    title                   VARCHAR(255) NOT NULL,
    username                VARCHAR(255),
    owner_user_id           INTEGER REFERENCES users(id),
    bot_added_by_user_id    INTEGER REFERENCES users(id),
    connected_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity_at        TIMESTAMPTZ,
    member_count            INTEGER DEFAULT 0,
    tariff                  VARCHAR(20) DEFAULT 'free',
    status                  VARCHAR(20) DEFAULT 'active'
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_chats_telegram_chat_id ON chats (telegram_chat_id);

-- chat_members
CREATE TABLE IF NOT EXISTS chat_members (
    id                  SERIAL PRIMARY KEY,
    chat_id             INTEGER NOT NULL REFERENCES chats(id),
    user_id             INTEGER NOT NULL REFERENCES users(id),
    role                VARCHAR(20) DEFAULT 'member',
    granted_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by_user_id  INTEGER REFERENCES users(id),
    can_ban             BOOLEAN DEFAULT FALSE,
    can_mute            BOOLEAN DEFAULT FALSE,
    can_warn            BOOLEAN DEFAULT FALSE,
    can_edit_welcome    BOOLEAN DEFAULT FALSE,
    can_edit_rules      BOOLEAN DEFAULT FALSE,
    can_manage_protection BOOLEAN DEFAULT FALSE,
    can_manage_triggers BOOLEAN DEFAULT FALSE,
    can_view_logs       BOOLEAN DEFAULT FALSE,
    can_view_stats      BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_chat_members_chat_id ON chat_members (chat_id);

-- chat_settings
CREATE TABLE IF NOT EXISTS chat_settings (
    chat_id                     INTEGER PRIMARY KEY REFERENCES chats(id),
    welcome_enabled             BOOLEAN DEFAULT FALSE,
    welcome_text                TEXT,
    welcome_buttons             JSONB,
    welcome_delete_after        INTEGER,
    rules_enabled               BOOLEAN DEFAULT FALSE,
    rules_text                  TEXT,
    anti_flood_enabled          BOOLEAN DEFAULT FALSE,
    anti_flood_limit            INTEGER DEFAULT 5,
    anti_flood_interval         INTEGER DEFAULT 5,
    anti_flood_action           VARCHAR(20) DEFAULT 'mute',
    anti_links_enabled          BOOLEAN DEFAULT FALSE,
    anti_links_action           VARCHAR(20) DEFAULT 'delete',
    stop_words_enabled          BOOLEAN DEFAULT FALSE,
    stop_words_list             JSONB,
    stop_words_action           VARCHAR(20) DEFAULT 'delete',
    repeat_filter_enabled       BOOLEAN DEFAULT FALSE,
    repeat_filter_sensitivity   FLOAT DEFAULT 0.8,
    caps_filter_enabled         BOOLEAN DEFAULT FALSE,
    caps_filter_threshold       FLOAT DEFAULT 0.7,
    caps_filter_min_length      INTEGER DEFAULT 10,
    triggers_enabled            BOOLEAN DEFAULT TRUE,
    logs_enabled                BOOLEAN DEFAULT TRUE,
    default_warn_limit          INTEGER DEFAULT 3,
    warn_limit_action           VARCHAR(20) DEFAULT 'mute',
    default_mute_duration       INTEGER DEFAULT 3600
);

-- punishments
CREATE TABLE IF NOT EXISTS punishments (
    id                  SERIAL PRIMARY KEY,
    chat_id             INTEGER NOT NULL REFERENCES chats(id),
    user_id             INTEGER NOT NULL REFERENCES users(id),
    issued_by_user_id   INTEGER REFERENCES users(id),
    type                VARCHAR(20) NOT NULL,
    reason              TEXT,
    starts_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ,
    status              VARCHAR(20) DEFAULT 'active'
);
CREATE INDEX IF NOT EXISTS ix_punishments_chat_id ON punishments (chat_id);
CREATE INDEX IF NOT EXISTS ix_punishments_user_id ON punishments (user_id);

-- warnings
CREATE TABLE IF NOT EXISTS warnings (
    id                  SERIAL PRIMARY KEY,
    chat_id             INTEGER NOT NULL REFERENCES chats(id),
    user_id             INTEGER NOT NULL REFERENCES users(id),
    issued_by_user_id   INTEGER REFERENCES users(id),
    reason              TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status              VARCHAR(20) DEFAULT 'active'
);
CREATE INDEX IF NOT EXISTS ix_warnings_chat_id ON warnings (chat_id);
CREATE INDEX IF NOT EXISTS ix_warnings_user_id ON warnings (user_id);

-- triggers
CREATE TABLE IF NOT EXISTS triggers (
    id              SERIAL PRIMARY KEY,
    chat_id         INTEGER NOT NULL REFERENCES chats(id),
    trigger_text    VARCHAR(500) NOT NULL,
    response_text   TEXT NOT NULL,
    is_enabled      BOOLEAN DEFAULT TRUE,
    match_type      VARCHAR(20) DEFAULT 'contains',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_triggers_chat_id ON triggers (chat_id);

-- logs
CREATE TABLE IF NOT EXISTS logs (
    id              SERIAL PRIMARY KEY,
    chat_id         INTEGER NOT NULL REFERENCES chats(id),
    actor_user_id   INTEGER REFERENCES users(id),
    target_user_id  INTEGER REFERENCES users(id),
    action_type     VARCHAR(100) NOT NULL,
    payload_json    JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_logs_chat_id    ON logs (chat_id);
CREATE INDEX IF NOT EXISTS ix_logs_action_type ON logs (action_type);
CREATE INDEX IF NOT EXISTS ix_logs_created_at  ON logs (created_at);

-- system_logs
CREATE TABLE IF NOT EXISTS system_logs (
    id          SERIAL PRIMARY KEY,
    level       VARCHAR(20) NOT NULL,
    service     VARCHAR(50) NOT NULL,
    event_type  VARCHAR(100) NOT NULL,
    payload_json JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_system_logs_level      ON system_logs (level);
CREATE INDEX IF NOT EXISTS ix_system_logs_created_at ON system_logs (created_at);

-- command_usage
CREATE TABLE IF NOT EXISTS command_usage (
    id          SERIAL PRIMARY KEY,
    chat_id     INTEGER NOT NULL REFERENCES chats(id),
    user_id     INTEGER REFERENCES users(id),
    command     VARCHAR(100) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_command_usage_chat_id ON command_usage (chat_id);

-- daily_metrics
CREATE TABLE IF NOT EXISTS daily_metrics (
    id                          SERIAL PRIMARY KEY,
    chat_id                     INTEGER NOT NULL REFERENCES chats(id),
    date                        DATE NOT NULL,
    messages_count              INTEGER DEFAULT 0,
    commands_count              INTEGER DEFAULT 0,
    moderation_actions_count    INTEGER DEFAULT 0,
    warnings_count              INTEGER DEFAULT 0,
    mutes_count                 INTEGER DEFAULT 0,
    bans_count                  INTEGER DEFAULT 0,
    deleted_messages_count      INTEGER DEFAULT 0,
    mini_app_opens_count        INTEGER DEFAULT 0,
    active_users_count          INTEGER DEFAULT 0,
    protection_triggers_count   INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_daily_metrics_chat_id ON daily_metrics (chat_id);
CREATE INDEX IF NOT EXISTS ix_daily_metrics_date    ON daily_metrics (date);

-- subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id          SERIAL PRIMARY KEY,
    chat_id     INTEGER NOT NULL UNIQUE REFERENCES chats(id),
    plan        VARCHAR(20) DEFAULT 'free',
    status      VARCHAR(20) DEFAULT 'active',
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ,
    is_trial    BOOLEAN DEFAULT FALSE,
    granted_by  VARCHAR(255)
);

-- internal_notes (заметки команды в Super Admin)
CREATE TABLE IF NOT EXISTS internal_notes (
    id          SERIAL PRIMARY KEY,
    chat_id     INTEGER NOT NULL REFERENCES chats(id),
    created_by  VARCHAR(255) NOT NULL,
    text        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_internal_notes_chat_id ON internal_notes (chat_id);

-- alembic version (чтобы backend не пытался re-мигрировать, если запустите alembic позже)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO alembic_version (version_num) VALUES ('0001')
ON CONFLICT DO NOTHING;
