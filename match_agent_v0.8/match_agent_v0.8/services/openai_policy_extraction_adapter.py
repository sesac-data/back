import os
import time
from typing import Any, Dict, Optional

from openai import OpenAI

from services.policy_extraction_adapter import (
    PolicyExtractionAdapter,
    PolicyExtractionRequest,
    PolicyExtractionResult,
    measure_ms,
    parse_candidate_json,
)


class OpenAIPolicyExtractionAdapter(
    PolicyExtractionAdapter
):

    def __init__(
        self,
        api_key: Optional[str] = None,
        client=None,
    ):

        resolved_api_key = api_key or os.environ.get(
            "OPENAI_API_KEY"
        )

        if client is None and not resolved_api_key:

            raise ValueError(
                "OPENAI_API_KEY is required to run policy extraction LLM evaluation."
            )

        self.client = client or OpenAI(
            api_key=resolved_api_key
        )

    def extract(
        self,
        request: PolicyExtractionRequest,
    ) -> PolicyExtractionResult:

        started_at = time.perf_counter()
        raw_response = None
        token_usage = None
        parse_error = None
        parsed_candidate = None

        response = self.client.chat.completions.create(
            model=request.model,
            response_format={
                "type":
                    "json_object",
            },
            temperature=0,
            messages=[
                {
                    "role":
                        "system",
                    "content":
                        (
                            "You extract policy source text into a candidate JSON object. "
                            "Return JSON only."
                        ),
                },
                {
                    "role":
                        "user",
                    "content":
                        request.prompt,
                },
            ],
        )

        raw_response = (
            response
            .choices[0]
            .message
            .content
        )
        parsed_candidate, parse_error = parse_candidate_json(
            raw_response
        )
        token_usage = _usage_to_dict(
            getattr(
                response,
                "usage",
                None,
            )
        )

        return PolicyExtractionResult(
            case_id=request.case_id,
            model=request.model,
            prompt_version=request.prompt_version,
            raw_response=raw_response,
            parsed_candidate=parsed_candidate,
            parse_error=parse_error,
            elapsed_ms=measure_ms(
                started_at
            ),
            token_usage=token_usage,
        )


def _usage_to_dict(
    usage
) -> Optional[Dict[str, Any]]:

    if usage is None:

        return None

    if hasattr(
        usage,
        "model_dump"
    ):

        return usage.model_dump()

    return {
        "prompt_tokens":
            getattr(
                usage,
                "prompt_tokens",
                None,
            ),
        "completion_tokens":
            getattr(
                usage,
                "completion_tokens",
                None,
            ),
        "total_tokens":
            getattr(
                usage,
                "total_tokens",
                None,
            ),
    }
