import runpy
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
TEST_PATH = APP_DIR / "test_db_builder_policy_scope_filter.py"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


if __name__ == "__main__":

    runpy.run_path(
        str(TEST_PATH),
        run_name="__main__",
    )
