import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PolicyExtractionRequest:
    case_id: str
    source_text: str
    prompt: str
    model: str
    prompt_version: str


@dataclass
class PolicyExtractionResult:
    case_id: str
    model: str
    prompt_version: str
    raw_response: Optional[str]
    parsed_candidate: Optional[Dict[str, Any]]
    parse_error: Optional[str]
    elapsed_ms: int
    token_usage: Optional[Dict[str, Any]]

    def to_dict(
        self
    ) -> Dict[str, Any]:

        return {
            "case_id":
                self.case_id,
            "model":
                self.model,
            "prompt_version":
                self.prompt_version,
            "raw_response":
                self.raw_response,
            "parsed_candidate":
                self.parsed_candidate,
            "parse_error":
                self.parse_error,
            "elapsed_ms":
                self.elapsed_ms,
            "token_usage":
                self.token_usage,
        }


class PolicyExtractionAdapter:

    def extract(
        self,
        request: PolicyExtractionRequest,
    ) -> PolicyExtractionResult:

        raise NotImplementedError


def parse_candidate_json(
    raw_response: Optional[str]
) -> tuple[Optional[Dict[str, Any]], Optional[str]]:

    if raw_response is None:

        return None, "empty_response"

    try:

        parsed = json.loads(
            raw_response
        )

    except json.JSONDecodeError as exc:

        return None, str(
            exc
        )

    if not isinstance(
        parsed,
        dict
    ):

        return None, "parsed_json_must_be_object"

    return parsed, None


def measure_ms(
    started_at: float
) -> int:

    return int(
        (
            time.perf_counter()
            - started_at
        )
        * 1000
    )
