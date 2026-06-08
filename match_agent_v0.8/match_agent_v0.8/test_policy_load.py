from services.policy_loader_service import (
    load_latest_policy_json
)

policy = load_latest_policy_json(
    "flexible_work_incent"
)

print(policy)