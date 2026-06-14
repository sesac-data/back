# Real Policy Extraction Evaluation Dataset

This directory is reserved for real policy-source evaluation cases.

Do not store generated candidates here. Do not store approved policy DB rows here.

Each case must use the same `case_id` stem across the three subdirectories:

```text
raw_text/{case_id}.txt
gold/{case_id}.json
metadata/{case_id}.json
```

Example:

```text
raw_text/parental_leave_replacement_support.txt
gold/parental_leave_replacement_support.json
metadata/parental_leave_replacement_support.json
```

## raw_text

`raw_text/{case_id}.txt` contains the original policy source text copied from the collected source.

## gold

`gold/{case_id}.json` contains the human-written expected policy JSON used by the evaluator.

The gold JSON is for evaluation only. It must not be auto-promoted to `approved`.

## metadata

`metadata/{case_id}.json` must contain:

```json
{
  "case_id": "case_id_matching_file_stem",
  "policy_name": "Human-readable policy name",
  "source_url": "https://example.gov/policy",
  "source_type": "official_page",
  "collected_at": "2026-06-14",
  "notes": "Collection or review notes"
}
```

## Runner

Run live extraction evaluation with:

```powershell
python scripts\run_policy_extraction_llm_eval.py --dataset data\policy_extraction_real_eval --prompt-version policy_extraction_v2 --runs 5
```

Reports are written separately from mock fixtures under:

```text
output/policy_extraction_real_eval/
```
