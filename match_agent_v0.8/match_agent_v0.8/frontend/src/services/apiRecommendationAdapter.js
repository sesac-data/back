const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000';
const DEFAULT_POLICY_SOURCE = 'demo_fixture';

export function toApiRequest(input = {}) {
  return {
    policy_source: normalizePolicySource(
      input.policy_source
      || input.policySource
      || import.meta.env?.VITE_RECOMMENDATION_POLICY_SOURCE
      || DEFAULT_POLICY_SOURCE,
    ),
    company: {
      company_name: input.companyName,
      size: input.companySize || 'small',
      has_replacement_worker: Boolean(input.hasReplacementWorker),
    },
    employee: {
      employee_name: input.employeeName,
      leave_type: normalizeLeaveType(input.leaveType),
    },
    leave_event: {
      leave_type: normalizeLeaveType(input.leaveType),
      start_date: input.leaveStartDate,
      end_date: input.leaveEndDate,
      has_replacement_worker: Boolean(input.hasReplacementWorker),
    },
    employer_cost_items: input.employer_cost_items || defaultEmployerCostItems(),
  };
}

function normalizePolicySource(policySource) {
  if (policySource === 'policy_db') {
    return 'policy_db';
  }

  return DEFAULT_POLICY_SOURCE;
}

function normalizeLeaveType(leaveType) {
  if (leaveType === 'parental_leave') {
    return 'parental_leave';
  }

  return 'parental_leave';
}

function defaultEmployerCostItems() {
  return [
    {
      cost_id: 'COST-GLOBAL-001',
      cost_type: 'administrative_cost',
      description: 'TEST FIXTURE explicit administrative cost',
      amount: 1000,
      applies_to_policy_ids: [],
    },
    {
      cost_id: 'COST-POLICY-B-001',
      cost_type: 'replacement_worker_salary',
      description: 'TEST FIXTURE explicit replacement worker salary',
      amount: 700,
      applies_to_policy_ids: ['smoke-optimal-b'],
    },
    {
      cost_id: 'COST-AND-001',
      cost_type: 'combined_operation_cost',
      description: 'TEST FIXTURE explicit cost only when A and B are both present',
      amount: 500,
      applies_to_policy_ids: ['smoke-optimal-a', 'smoke-optimal-b'],
    },
  ];
}

export function normalizeApiRecommendationResponse(apiResult, input = {}) {
  const recommended = apiResult.recommended_combination
    ? [apiResult.recommended_combination]
    : [];
  const alternatives = apiResult.alternative_combinations || [];

  return {
    source: 'api',
    isMock: false,
    calculatedAt: new Date().toISOString().slice(0, 10),
    inputSnapshot: {
      ...input,
    },
    recommended_combination: apiResult.recommended_combination || null,
    alternative_combinations: alternatives,
    summarized_combinations: [
      ...recommended,
      ...alternatives,
    ],
    rejected_combinations: apiResult.rejected_combinations || [],
    errors: apiResult.errors || [],
    meta: apiResult.meta || {},
  };
}

export async function fetchRecommendationDemo(input) {
  const baseUrl = import.meta.env?.VITE_RECOMMENDATION_API_BASE_URL || DEFAULT_API_BASE_URL;
  const response = await fetch(`${baseUrl}/api/demo/recommendations/calculate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(toApiRequest(input)),
  });
  const payload = await response.json();

  if (!response.ok) {
    const message = payload.errors?.[0]?.reason || 'API recommendation request failed';
    throw new Error(message);
  }

  return normalizeApiRecommendationResponse(payload, input);
}
