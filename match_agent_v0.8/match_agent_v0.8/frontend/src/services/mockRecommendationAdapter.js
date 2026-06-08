const mockResult = {
  source: 'mock',
  isMock: true,
  calculatedAt: '2026-06-07',
  inputSnapshot: {
    companyName: '루디커머스',
    employeeName: '김민지',
    leaveType: '육아휴직',
    leaveStartDate: '2026-07-01',
    leaveEndDate: '2026-12-31',
    hasReplacementWorker: true,
  },
  summarized_combinations: [
    {
      policy_ids: ['POLICY-PARENTAL-LEAVE'],
      policy_results: [
        {
          policy_id: 'POLICY-PARENTAL-LEAVE',
          policy_name: '육아휴직 지원금',
          status: 'calculated',
          base_amount: 300000,
          bonus_amount: 0,
          estimated_total_amount: 300000,
          calculation_steps: [
            {
              step: 'monthly_fixed_calculation',
              input: { monthly_amount: 100000, eligible_months: 3 },
              result: 300000,
            },
          ],
          passed_conditions: [
            {
              condition_id: 'COND-001',
              field: 'leave_type',
              operator: 'eq',
              expected: '육아휴직',
              actual: '육아휴직',
              reason: 'condition_passed',
              evidence_snippets: ['육아휴직을 허용한 사업주에게 월 정액 지원금을 지급합니다.'],
            },
          ],
          failed_conditions: [],
          applied_bonuses: [],
          skipped_bonuses: [],
          evidence_snippets: ['육아휴직을 허용한 사업주에게 월 정액 지원금을 지급합니다.'],
        },
      ],
      total_base_amount: 300000,
      total_bonus_amount: 0,
      total_subsidy_amount: 300000,
      calculation_steps: [
        {
          policy_id: 'POLICY-PARENTAL-LEAVE',
          calculation_steps: [
            {
              step: 'monthly_fixed_calculation',
              input: { monthly_amount: 100000, eligible_months: 3 },
              result: 300000,
            },
          ],
        },
      ],
      evidence_snippets: ['육아휴직을 허용한 사업주에게 월 정액 지원금을 지급합니다.'],
    },
    {
      policy_ids: ['POLICY-PARENTAL-LEAVE', 'POLICY-REPLACEMENT-WORKER'],
      policy_results: [
        {
          policy_id: 'POLICY-PARENTAL-LEAVE',
          policy_name: '육아휴직 지원금',
          status: 'calculated',
          base_amount: 300000,
          bonus_amount: 0,
          estimated_total_amount: 300000,
          calculation_steps: [
            {
              step: 'monthly_fixed_calculation',
              input: { monthly_amount: 100000, eligible_months: 3 },
              result: 300000,
            },
          ],
          passed_conditions: [
            {
              condition_id: 'COND-001',
              field: 'leave_type',
              operator: 'eq',
              expected: '육아휴직',
              actual: '육아휴직',
              reason: 'condition_passed',
              evidence_snippets: ['육아휴직을 허용한 사업주에게 월 정액 지원금을 지급합니다.'],
            },
          ],
          failed_conditions: [],
          applied_bonuses: [],
          skipped_bonuses: [],
          evidence_snippets: ['육아휴직을 허용한 사업주에게 월 정액 지원금을 지급합니다.'],
        },
        {
          policy_id: 'POLICY-REPLACEMENT-WORKER',
          policy_name: '대체인력 지원금',
          status: 'calculated',
          base_amount: 1800000,
          bonus_amount: 300000,
          estimated_total_amount: 2100000,
          calculation_steps: [
            {
              step: 'base_support_calculation',
              calculation_type: 'period_tiered',
              status: 'calculated',
              result: 1800000,
            },
            {
              step: 'conditional_bonus',
              benefit_id: 'BONUS-REPLACEMENT',
              result: 300000,
            },
          ],
          passed_conditions: [
            {
              condition_id: 'COND-002',
              field: 'has_replacement_worker',
              operator: 'eq',
              expected: true,
              actual: true,
              reason: 'condition_passed',
              evidence_snippets: ['대체인력을 채용한 경우 추가 지원금을 지급합니다.'],
            },
          ],
          failed_conditions: [],
          applied_bonuses: [
            {
              benefit_id: 'BONUS-REPLACEMENT',
              calculation_type: 'monthly_fixed',
              bonus_type: 'replacement_worker',
              requested_months: 6,
              eligible_months: 3,
              monthly_amount: 100000,
              result: 300000,
              evidence_snippets: ['대체인력을 채용한 경우 추가 지원금을 지급합니다.'],
            },
          ],
          skipped_bonuses: [],
          evidence_snippets: [
            '대체인력을 채용한 경우 추가 지원금을 지급합니다.',
            '첫 3개월은 월 600000원을 지급합니다.',
          ],
        },
      ],
      total_base_amount: 2100000,
      total_bonus_amount: 300000,
      total_subsidy_amount: 2400000,
      calculation_steps: [
        {
          policy_id: 'POLICY-PARENTAL-LEAVE',
          calculation_steps: [
            {
              step: 'monthly_fixed_calculation',
              input: { monthly_amount: 100000, eligible_months: 3 },
              result: 300000,
            },
          ],
        },
        {
          policy_id: 'POLICY-REPLACEMENT-WORKER',
          calculation_steps: [
            {
              step: 'base_support_calculation',
              calculation_type: 'period_tiered',
              status: 'calculated',
              result: 1800000,
            },
            {
              step: 'conditional_bonus',
              benefit_id: 'BONUS-REPLACEMENT',
              result: 300000,
            },
          ],
        },
      ],
      evidence_snippets: [
        '육아휴직을 허용한 사업주에게 월 정액 지원금을 지급합니다.',
        '대체인력을 채용한 경우 추가 지원금을 지급합니다.',
        '첫 3개월은 월 600000원을 지급합니다.',
      ],
    },
    {
      policy_ids: ['POLICY-NULL-AMOUNT-DEMO'],
      policy_results: [
        {
          policy_id: 'POLICY-NULL-AMOUNT-DEMO',
          policy_name: '금액 검토 필요 정책',
          status: 'calculated',
          base_amount: null,
          bonus_amount: 0,
          estimated_total_amount: null,
          calculation_steps: [
            {
              step: 'amount_validation',
              result: 'needs_review',
            },
          ],
          passed_conditions: [],
          failed_conditions: [],
          applied_bonuses: [],
          skipped_bonuses: [],
          evidence_snippets: ['정책 원문에 금액이 명시되지 않아 검토가 필요합니다.'],
        },
      ],
      total_base_amount: null,
      total_bonus_amount: 0,
      total_subsidy_amount: null,
      calculation_steps: [
        {
          policy_id: 'POLICY-NULL-AMOUNT-DEMO',
          calculation_steps: [
            {
              step: 'amount_validation',
              result: 'needs_review',
            },
          ],
        },
      ],
      evidence_snippets: ['정책 원문에 금액이 명시되지 않아 검토가 필요합니다.'],
    },
  ],
  rejected_combinations: [
    {
      policy_ids: ['POLICY-PARENTAL-LEAVE', 'POLICY-OVERLAP-BLOCKED'],
      reasons: [
        {
          type: 'mutually_exclusive',
          details: {
            rule_id: 'CR-001',
            rule_type: 'mutually_exclusive',
            source_policy_id: 'POLICY-OVERLAP-BLOCKED',
            target_policy_id: 'POLICY-PARENTAL-LEAVE',
            reason: '동일 기간 중복 수급 불가',
            evidence_snippets: ['동일한 휴직 기간에는 두 지원금을 함께 받을 수 없습니다.'],
          },
        },
      ],
    },
    {
      policy_ids: ['POLICY-REPLACEMENT-WORKER'],
      reasons: [
        {
          type: 'requires',
          details: {
            rule_id: 'CR-REQ-001',
            rule_type: 'requires',
            source_policy_id: 'POLICY-REPLACEMENT-WORKER',
            required_policy_ids: ['POLICY-PARENTAL-LEAVE'],
            missing_policy_ids: ['POLICY-PARENTAL-LEAVE'],
            reason: '육아휴직 지원 대상인 경우에만 대체인력 지원 검토',
            evidence_snippets: ['대체인력 지원은 육아휴직 허용 사업주를 대상으로 합니다.'],
          },
        },
      ],
    },
  ],
  errors: [],
};

export async function fetchRecommendationDemo(input) {
  return {
    ...mockResult,
    inputSnapshot: {
      ...mockResult.inputSnapshot,
      ...input,
    },
  };
}
