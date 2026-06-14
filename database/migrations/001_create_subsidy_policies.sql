CREATE TABLE IF NOT EXISTS subsidy_policies (
    id BIGSERIAL PRIMARY KEY,
    policy_id VARCHAR(100) NOT NULL,
    policy_name VARCHAR(255) NOT NULL,
    policy_version VARCHAR(50) NOT NULL,
    review_status VARCHAR(30) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    policy_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (policy_id, policy_version)
);

CREATE INDEX IF NOT EXISTS idx_subsidy_policies_approved_active
    ON subsidy_policies (review_status, is_active);
