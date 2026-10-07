-- Local application accounts; no seeded credentials and no academic data changes.
CREATE TABLE IF NOT EXISTS user_accounts (
    user_id UUID PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    full_name VARCHAR(160) NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin','dean','teacher','registrar')),
    teacher_id VARCHAR(50) REFERENCES teachers(teacher_id),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK ((role = 'teacher' AND teacher_id IS NOT NULL) OR (role <> 'teacher' AND teacher_id IS NULL))
);
CREATE TABLE IF NOT EXISTS account_sessions (
    token_hash VARCHAR(64) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_accounts(user_id),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS security_events (
    event_id BIGSERIAL PRIMARY KEY,
    actor_id UUID REFERENCES user_accounts(user_id),
    action VARCHAR(80) NOT NULL,
    target TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
