# Mock Company Recommendation Test Plan

## Case 04 - Hana Machine

Source folder:

`C:\Users\laiep\project_sesac\data\가상기업데이터_20개\04_주식회사_하나기계`

Source files:

- `기업특징.txt`
- `사업자등록증.pdf`
- `직원명단.xlsx`

Generated expected fixture:

`tests/fixtures/mock_company_cases/04_hana_machine_expected.json`

## Extractable Fields

Company:

- Company name: `(주)하나기계`
- Business registration number: `659-88-57040`
- Representative: `손예준`
- Industry: `제조업 / 의료용 기기 제조업`
- Industry code: `27199`
- Address: `부산광역시 해운대구 센텀중앙로 79, 센텀사이언스파크 11층 (우동)`
- Insured employee count: `26`
- Priority support / SME: `true`

Target employee:

- Name: `오유진`
- Department / role: `고객지원팀/CS`
- Employment type: `정규직`
- Hire date: `2021-10-28`
- Leave type: `육아휴직`
- Leave start: `2025-06-16`
- Leave end: `2026-03-15`
- Leave duration: `273 days`
- Monthly salary: `5,660,000`

Replacement worker:

- Name: `김태경`
- Department / role: `고객지원팀/CS(대체)`
- Employment type: `기간제`
- Hire / work start date: `2025-01-05`
- Work end date: `2026-03-15`
- Employment duration: `435 days`
- New hire flag: `Y`

Business registration PDF:

- Registration number: `659-88-57040`
- Company name: `(주)하나기계`
- Representative: `손예준`
- Opening date: `2019-09-23`
- Industry: `제조업 / 의료용 기기 제조업`

## Current Recommendation Input Mapping

Mapped to the current demo API / rule adapter:

- `company.size`
- `company.has_replacement_worker`
- `employee.leave_type`
- `leave_event.leave_type`
- `leave_event.start_date`
- `leave_event.end_date`
- `leave_event.requested_months`
- `leave_event.has_replacement_worker`
- `employer_cost_items`

Available for future rule input expansion:

- `company.insured_employee_count`
- `company.is_priority_support_enterprise`
- `employee.hire_date`
- `leave_event.duration_days`
- `replacement_worker.hire_date`
- `replacement_worker.employment_duration_days`
- `replacement_worker.is_new_hire`

Missing from upload:

- Child age / grade / child age months
- Employee gender
- Working-hour reduction before/after hours
- Flexible work type and reduced hours
- Attendance management, work-rule, contract-change fields
- Work-life balance system approval, install date, and usage obligation fields

## Seven-Policy Verification Mapping

| Policy ID | Status for This Case | Reason |
|---|---|---|
| `parental_leave_reduction_support` | Partially evaluable | Parental leave period exists, but child age/months and detailed tier qualifiers are missing. |
| `replacement_workshare_support` | Evaluable, expected ineligible | Replacement worker was hired on `2025-01-05`, earlier than the allowed earliest date `2025-04-16`. |
| `worklife_balance_45_support` | Not evaluable | Company-wide worktime reduction project fields are missing. |
| `childcare_flexible_start_support` | Not applicable | Case is parental leave, not childcare 10 a.m. start support. |
| `working_hours_reduction_support` | Not applicable | Case is parental leave, not prescribed working-hour reduction. |
| `flexible_work_incent` | Not applicable | No flexible-work event is provided. |
| `flexible_work_system_support` | Not applicable | No system support purchase / approval / install data is provided. |

## Expected Result

Primary assertion:

- `replacement_workshare_support` must be rejected or absent from eligible recommendations.
- Reason code: `replacement_worker_hired_before_allowed_window`
- Expected support amount for that policy: `0`

Manual check:

- Leave start date: `2025-06-16`
- Two-month-before threshold: `2025-04-16`
- Replacement worker hire date: `2025-01-05`
- Result: hire date is earlier than threshold, so the new replacement worker hire condition is not met.

## Current Backend Gap

The general-company demo adapter now preserves `replacement_worker.hire_date`, `replacement_worker.employment_duration_days`, `company.insured_employee_count`, and leave-event dates in `rule_input`.

This fixture now has a test-only actual-vs-expected runner. The runner injects an approved in-memory fixture containing `replacement_workshare_support` and uses the shared condition evaluator to check the replacement hire-window condition.

## Input Schema Readiness Check

Readiness script:

`python scripts\check_mock_company_case_readiness.py`

Audit output:

`output/mock_company_case_checks/04_hana_machine_input_schema_audit.json`

Current actual-result generation path:

`services.demo_recommendation_orchestrator.run_demo_recommendation_pipeline(payload)`

The current payload can be passed to the pipeline, and the resulting `rule_input` now preserves the fields needed for the replacement worker hire-window check.

Current adapter output shape:

```json
{
  "company": {
    "size": "small",
    "has_replacement_worker": true,
    "insured_employee_count": 26
  },
  "employee": {
    "leave_type": "parental_leave"
  },
  "leave_event": {
    "type": "parental_leave",
    "leave_type": "parental_leave",
    "start_date": "2025-06-16",
    "end_date": "2026-03-15"
  },
  "replacement_worker": {
    "hire_date": "2025-01-05",
    "employment_duration_days": 435
  }
}
```

Required fields for this case:

| Field | Present in payload | Present in current rule_input | Notes |
|---|---:|---:|---|
| `replacement_worker.hire_date` | yes | yes | Required for two-month hire-window check. |
| `replacement_worker.employment_duration_days` | yes | yes | Required for 30-day replacement employment check. |
| `company.insured_employee_count` | yes | yes | Required for amount tier / company size policy conditions. |
| `leave_event.start_date` | yes | yes | Used to derive requested months and now preserved in rule_input. |
| `leave_event.end_date` | yes | yes | Used to derive requested months and now preserved in rule_input. |
| `leave_event.type` | no | yes | Derived from `leave_event.leave_type`. |

Conclusion:

- Pipeline execution with the draft payload is possible.
- Replacement worker input fields are preserved in `rule_input`.
- Actual comparison against this expected result is valid through the test-only fixture `hana_machine_replacement_workshare`.
- The next implementation step should be to connect equivalent approved human-reviewed policy JSON through the normal policy source once policy review is ready.

## Actual vs Expected Runner

Runner:

`python scripts\run_mock_company_expected_check.py`

Output:

`output/mock_company_case_checks/04_hana_machine_actual_vs_expected.json`

Current result:

- `comparison_passed`: `true`
- `actual_result_is_comparable`: `true`
- Target policy `replacement_workshare_support` is rejected as ineligible.
- Expected reason code `replacement_worker_hired_before_allowed_window` is present.
- No recommended or alternative combination includes the target policy.

## 20-Case Expected Draft Inventory

Generated by:

`python scripts\build_mock_company_expected_cases.py`

Inventory output:

`C:\Users\laiep\project_sesac\output\mock_company_case_checks\mock_company_expected_case_inventory.json`

Scope:

- Scanned 20 mock company folders.
- Checked `기업특징.txt`, `사업자등록증.pdf`, and `직원명단.xlsx` presence.
- Generated expected-result drafts only; no actual recommendation comparison was run for the new cases.
- Existing `04_hana_machine_expected.json` was preserved.

Summary:

- Total folders: 20
- Expected drafts generated or preserved: 20
- Holds: 0
- Policy counts: `{"parental_leave_reduction_support": 10, "replacement_workshare_support": 10}`
- Status counts: `{"eligible": 10, "ineligible": 10}`

Actual-vs-expected readiness:

- High-comparability cases: `mock_company_06, mock_company_07, mock_company_08, mock_company_09, mock_company_10, mock_company_17, mock_company_18, mock_company_19, 04_hana_machine`
- Rule-input expansion is still needed for parental leave / working-hour reduction duration checks before full comparison.

## Batch Actual-vs-Expected Runner

Runner:

`python scripts\run_batch_actual_vs_expected.py`

Single-case runner (now with CLI args):

`python scripts\run_mock_company_expected_check.py --case <path> --output <path>`

### Batch Scope

- 9 high-comparability cases targeting `replacement_workshare_support` only.
- All cases use the test fixture `hana_machine_replacement_workshare` injected via `load_approved_policies` monkey-patch.
- No DB write, no approved auto-processing, no policy JSON mutation, no frontend change.
- 고령자/청년/고용촉진/정규직전환 policies are excluded.

### Batch Results (2026-06-14)

| Case ID | Passed | Expected | Actual | Reason Code Match |
|---|:---:|---|---|:---:|
| `mock_company_06` | ✅ | eligible | eligible | ✅ |
| `mock_company_07` | ❌ | eligible | ineligible | ❌ |
| `mock_company_08` | ✅ | eligible | eligible | ✅ |
| `mock_company_09` | ❌ | eligible | ineligible | ❌ |
| `mock_company_10` | ✅ | eligible | eligible | ✅ |
| `mock_company_17` | ❌ | ineligible | ineligible | ❌ |
| `mock_company_18` | ❌ | ineligible | ineligible | ❌ |
| `mock_company_19` | ✅ | ineligible | ineligible | ✅ |
| `04_hana_machine` | ✅ | ineligible | ineligible | ✅ |

Summary: **5/9 passed**, 0 errors, all 9 comparable.

### Failure Analysis

- `mock_company_07`, `mock_company_09`: Expected eligible but pipeline rejected. Both expected `replacement_worker_requirements_met`. The test fixture's condition evaluator rejected them, suggesting their replacement worker data may hit a condition boundary (hire window or employment duration) that the expected-result draft didn't anticipate.
- `mock_company_17`, `mock_company_18`: Expected ineligible with reason code `replacement_worker_employment_duration_under_30_days`, but the pipeline rejected with a different reason code (likely `replacement_worker_hired_before_allowed_window`). The pipeline correctly identified ineligibility, but through a different condition than expected. This is a reason-code mismatch, not an eligibility mismatch.

### Outputs

- Batch JSON: `output/mock_company_case_checks/mock_company_batch_actual_vs_expected.json`
- Batch summary: `output/mock_company_case_checks/mock_company_batch_summary.md`
