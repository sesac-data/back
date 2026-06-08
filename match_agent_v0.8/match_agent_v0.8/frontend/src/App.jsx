import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  AlertCircle,
  Bell,
  Building2,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  FileCheck2,
  FileText,
  LayoutDashboard,
  Mail,
  Search,
  Settings,
  ShieldCheck,
  Upload,
  UsersRound,
  Wand2,
} from 'lucide-react';
import './styles.css';
import { fetchGeneralCompanyRecommendationDemo } from './services/recommendationService.js';

const roleMeta = {
  company: {
    label: '일반기업',
    tone: 'blue',
    accent: '#0b63ce',
    tagline: '직원 현황과 신청 가능 지원금을 한 곳에서 관리',
    onboarding: ['기업정보 등록', '직원 명단 업로드', '완료'],
  },
  firm: {
    label: '노무법인',
    tone: 'purple',
    accent: '#6d3df2',
    tagline: '고객사별 지원금 검토와 서류 진행률을 관리',
    onboarding: ['첫 고객사 등록', '직원 명단 등록', '완료'],
  },
};

const companyMetrics = [
  { label: '예상 수급액', value: '2,250만원', hint: '개인별 중복 제거 후', tone: 'teal' },
  { label: '신청 가능 지원금', value: '2건', hint: '육아휴직, 대체인력', tone: 'blue' },
  { label: '마감 알림', value: '3건', hint: '30일 내 제출 필요', tone: 'orange' },
  { label: '직원 현황', value: '2명', hint: '휴직/단축 대상자', tone: 'slate' },
];

const firmMetrics = [
  { label: '관리 고객사', value: '12개사', hint: '이번 달 2개 추가', tone: 'purple' },
  { label: '이달 뉴스레터', value: '8건', hint: '발송 대기 3건', tone: 'blue' },
  { label: '서류 완료율', value: '76%', hint: '검수 요청 5건', tone: 'teal' },
  { label: '마감 알림', value: '9건', hint: '고객사별 집계', tone: 'orange' },
];

const employees = [
  {
    name: '김민지',
    status: '육아휴직 예정',
    childAge: '5세',
    weeklyHours: 40,
    amount: 22500000,
    supports: ['대체인력 인건비 지원', '육아휴직 지원금'],
  },
  {
    name: '이서준',
    status: '육아휴직 예정',
    childAge: '8세',
    weeklyHours: 35,
    amount: 22500000,
    supports: ['대체인력 인건비 지원', '육아휴직 지원금'],
  },
];

const documents = [
  { title: '출산육아기 고용안정장려금 지급신청서', status: '작성중', due: 'D-12' },
  { title: '육아휴직 실시 증명 서류', status: '검토완료', due: 'D-18' },
  { title: '사업주 가족관계 확인 서류', status: '요청필요', due: 'D-21' },
];

const clients = [
  { name: '루디컴퍼니', employees: 4, status: '서류 검수', amount: '4,500만원' },
  { name: '세움테크', employees: 2, status: '직원 등록', amount: '1,170만원' },
  { name: '온유푸드', employees: 6, status: '뉴스레터 수신', amount: '검토중' },
];

function money(value) {
  return `${Math.round(value / 10000).toLocaleString()}만원`;
}

function formatDemoMoney(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '계산 불가';
  }

  return `${Number(value).toLocaleString('ko-KR')}원`;
}

function formatJson(value) {
  if (value === null || value === undefined) {
    return '계산 불가';
  }

  if (typeof value === 'string') {
    return value;
  }

  return JSON.stringify(value, null, 2);
}

function App() {
  const isRecommendationDemoPath = (
    typeof window !== 'undefined'
    && window.location.pathname === '/company/recommendation-demo'
  );
  const [role, setRole] = useState('company');
  const [screen, setScreen] = useState(isRecommendationDemoPath ? 'app' : 'landing');
  const [view, setView] = useState(isRecommendationDemoPath ? 'recommendationDemo' : 'hub');
  const meta = roleMeta[role];

  const enterApp = (nextRole = role) => {
    setRole(nextRole);
    setView('hub');
    setScreen('app');
  };

  if (screen === 'landing') {
    return <Landing role={role} setRole={setRole} enterApp={enterApp} />;
  }

  if (screen === 'onboarding') {
    return <Onboarding role={role} enterApp={enterApp} />;
  }

  return (
    <div className={`app-shell ${meta.tone}`}>
      <Sidebar role={role} view={view} setView={setView} onLogout={() => setScreen('landing')} />
      <main className="main-panel">
        <Topbar role={role} view={view} setScreen={setScreen} />
        <section className="content-area">
          {view === 'hub' && <Hub role={role} setView={setView} />}
          {view === 'recommendationDemo' && <RecommendationDemo />}
          {view === 'employees' && <EmployeeManagement role={role} />}
          {view === 'documents' && <DocumentManagement />}
          {view === 'replacement' && <ReplacementManagement />}
          {view === 'settings' && <SettingsView role={role} />}
          {view === 'clients' && <ClientManagement />}
          {view === 'newsletter' && <NewsletterView />}
        </section>
      </main>
    </div>
  );
}

function Landing({ role, setRole, enterApp }) {
  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="brand">인센트닥<span> v2</span></div>
        <nav>
          <button>지원금 진단</button>
          <button>서류 관리</button>
          <button>고객사 관리</button>
        </nav>
      </header>
      <section className="landing-hero">
        <div className="hero-copy">
          <span className="eyebrow">육아지원금 추천 · 신청관리 플랫폼</span>
          <h1>정책 추천부터 서류 마감까지<br />한 화면에서 운영합니다</h1>
          <p>일반기업과 노무법인을 분리된 플로우로 운영하고, 온보딩 이후에는 각 허브에서 동일 정보를 계속 수정·관리합니다.</p>
          <div className="role-switch">
            {Object.entries(roleMeta).map(([key, item]) => (
              <button
                key={key}
                className={role === key ? 'active' : ''}
                onClick={() => setRole(key)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="hero-actions">
            <button className="primary" onClick={() => enterApp(role)}>기존 로그인</button>
            <button className="secondary" onClick={() => setRole(role) || enterApp(role)}>데모 바로가기</button>
          </div>
        </div>
        <div className="login-card">
          <div className={`role-badge ${role}`}>{roleMeta[role].label}</div>
          <h2>신규 가입</h2>
          <p>{roleMeta[role].tagline}</p>
          <label>이메일</label>
          <input defaultValue={role === 'company' ? 'admin@ludi.com' : 'manager@laborfirm.kr'} />
          <label>사업자번호</label>
          <input defaultValue="123-45-67890" />
          <button className="primary full" onClick={() => setRole(role) || enterApp(role)}>
            신규 1회 온보딩 시작
          </button>
        </div>
      </section>
      <section className="landing-features">
        <Feature icon={<LayoutDashboard />} title="기업관리 허브" text="예상 수급액, 신청 가능 지원금, 마감 알림을 첫 화면에서 확인" />
        <Feature icon={<UsersRound />} title="직원 관리" text="직원/휴직 정보는 기업 관리 또는 고객사 관리 하위에서 수정" />
        <Feature icon={<FileCheck2 />} title="서류·일정 관리" text="제출서류, 승인 접수, 마감일을 운영 플로우에 맞게 추적" />
      </section>
    </div>
  );
}

function Feature({ icon, title, text }) {
  return (
    <div className="feature">
      {icon}
      <strong>{title}</strong>
      <span>{text}</span>
    </div>
  );
}

function Onboarding({ role, enterApp }) {
  const meta = roleMeta[role];
  return (
    <div className="onboarding">
      <div className="wizard-card">
        <span className={`role-badge ${role}`}>{meta.label}</span>
        <h1>신규 1회 온보딩 Wizard</h1>
        <p>{role === 'company' ? '기업정보와 직원 명단을 처음 한 번만 입력합니다.' : '첫 고객사와 직원 명단을 등록해 운영을 시작합니다.'}</p>
        <div className="wizard-steps">
          {meta.onboarding.map((step, index) => (
            <div className="wizard-step" key={step}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <strong>{step}</strong>
            </div>
          ))}
        </div>
        <div className="upload-box">
          <Upload />
          <strong>{role === 'company' ? '직원 명단 업로드' : '고객사 직원 명단 등록'}</strong>
          <span>xlsx, csv 또는 수기 입력을 지원합니다.</span>
        </div>
        <button className="primary full" onClick={() => enterApp(role)}>온보딩 완료 후 허브로 이동</button>
      </div>
    </div>
  );
}

function Sidebar({ role, view, setView, onLogout }) {
  const isCompany = role === 'company';
  const items = isCompany
    ? [
        ['hub', LayoutDashboard, '기업관리 허브'],
        ['recommendationDemo', CheckCircle2, '지원금 조합 비교'],
        ['employees', UsersRound, '기업 관리'],
        ['documents', CalendarDays, '서류·일정 관리'],
        ['replacement', Wand2, '대체인력 관리'],
        ['settings', Settings, '기업 설정'],
      ]
    : [
        ['hub', LayoutDashboard, '기업관리 허브'],
        ['clients', Building2, '고객사 관리'],
        ['documents', ClipboardCheck, '서류 검수 관리'],
        ['newsletter', Mail, '뉴스레터 발송'],
        ['settings', Settings, '파트너 설정'],
      ];
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">인센트닥<span>{isCompany ? ' 기업' : ' 파트너'}</span></div>
      <div className="sidebar-section">메인</div>
      {items.map(([key, Icon, label]) => (
        <button
          key={key}
          className={view === key ? 'active' : ''}
          onClick={() => setView(key)}
        >
          <Icon size={18} />
          {label}
        </button>
      ))}
      <div className="sidebar-spacer" />
      <button onClick={onLogout} className="ghost">로그아웃</button>
    </aside>
  );
}

function Topbar({ role, view, setScreen }) {
  const labels = {
    hub: '기업관리 허브',
    recommendationDemo: '지원금 조합 비교',
    employees: role === 'company' ? '기업 관리 · 직원 관리' : '직원 관리',
    documents: role === 'company' ? '서류·일정 관리' : '서류 검수 관리',
    replacement: '대체인력 관리',
    settings: role === 'company' ? '기업 설정' : '파트너 설정',
    clients: '고객사 관리',
    newsletter: '뉴스레터 발송',
  };
  return (
    <header className="topbar">
      <div>
        <h1>{labels[view]}</h1>
        <span>2026년 6월 5일 기준 데모</span>
      </div>
      <div className="topbar-actions">
        <button className="icon-btn"><Search size={18} /></button>
        <button className="icon-btn"><Bell size={18} /></button>
        <button className="outline" onClick={() => setScreen('onboarding')}>온보딩 다시보기</button>
      </div>
    </header>
  );
}

function Hub({ role, setView }) {
  const isCompany = role === 'company';
  const metrics = isCompany ? companyMetrics : firmMetrics;
  return (
    <div className="screen">
      <div className="metric-grid">
        {metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}
      </div>
      <div className="hub-grid">
        <section className="panel wide">
          <div className="panel-head">
            <div>
              <h2>{isCompany ? '신청 가능 지원금' : '고객사 진행 현황'}</h2>
              <p>{isCompany ? '정책 충돌과 회사 단위 지원금을 제외한 추천 결과입니다.' : '고객사별 직원·서류 진행상태를 확인합니다.'}</p>
            </div>
            <button className="outline" onClick={() => setView(isCompany ? 'employees' : 'clients')}>자세히 보기</button>
          </div>
          {isCompany ? <RecommendationList /> : <ClientList compact />}
        </section>
        <section className="panel">
          <h2>마감 알림</h2>
          <Deadline label="육아휴직 지원금 서류 제출" day="D-12" />
          <Deadline label="대체인력 채용 증빙 확인" day="D-18" />
          <Deadline label="출퇴근관리시스템 견적 검토" day="D-25" />
        </section>
      </div>
      <InfoStrip />
    </div>
  );
}

function MetricCard({ label, value, hint, tone }) {
  return (
    <div className={`metric-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{hint}</small>
    </div>
  );
}

function RecommendationList() {
  return (
    <div className="recommendation-list">
      {employees.map((employee) => (
        <article className="recommendation-row" key={employee.name}>
          <div>
            <strong>{employee.name}</strong>
            <span>{employee.status} · 자녀 {employee.childAge} · 주 {employee.weeklyHours}시간</span>
          </div>
          <div className="support-tags">
            {employee.supports.map((support) => <em key={support}>{support}</em>)}
          </div>
          <b>{money(employee.amount)}</b>
        </article>
      ))}
    </div>
  );
}

function RecommendationDemo() {
  const [input, setInput] = useState({
    companyName: '루디커머스',
    employeeName: '김민지',
    leaveType: '육아휴직',
    leaveStartDate: '2026-07-01',
    leaveEndDate: '2026-12-31',
    hasReplacementWorker: true,
  });
  const [result, setResult] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const validCombinations = result?.summarized_combinations || [];
  const rejectedCombinations = result?.rejected_combinations || [];
  const highestTotal = validCombinations.reduce((highest, combination) => {
    const amount = combination.total_subsidy_amount;
    if (amount === null || amount === undefined) {
      return highest;
    }
    return highest === null || amount > highest ? amount : highest;
  }, null);

  useEffect(() => {
    runDemo();
  }, []);

  const updateInput = (field, value) => {
    setInput((current) => ({
      ...current,
      [field]: value,
    }));
  };

  async function runDemo() {
    setLoading(true);
    setError('');

    try {
      const nextResult = await fetchGeneralCompanyRecommendationDemo(input);
      setResult(nextResult);
      setSelected(nextResult.summarized_combinations?.[0] || nextResult.rejected_combinations?.[0] || null);
    } catch (demoError) {
      setError(demoError.message || '계산 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="screen recommendation-demo">
      <section className="panel demo-hero-panel">
        <div>
          <span className="eyebrow">팀 공유용 데모</span>
          <h2>육아휴직 지원금 조합 비교</h2>
          <p>현재 구현된 계산 엔진 결과를 일반기업 테스트 입력값으로 확인하는 데모 화면입니다.</p>
        </div>
        <div className="demo-status">
          <span>{result?.isMock ? 'mock adapter 사용 중' : 'API adapter 사용 중'}</span>
          <strong>경로: /company/recommendation-demo</strong>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>테스트 입력</h2>
            <p>입력값은 데모 어댑터로 전달되며, 프론트에서 지원금 계산을 다시 수행하지 않습니다.</p>
          </div>
          <button className="primary small" onClick={runDemo} disabled={loading}>
            {loading ? '확인 중' : '지원금 확인'}
          </button>
        </div>
        <div className="demo-input-grid">
          <label>
            기업명
            <input value={input.companyName} onChange={(event) => updateInput('companyName', event.target.value)} />
          </label>
          <label>
            직원명
            <input value={input.employeeName} onChange={(event) => updateInput('employeeName', event.target.value)} />
          </label>
          <label>
            휴직 유형
            <select value={input.leaveType} onChange={(event) => updateInput('leaveType', event.target.value)}>
              <option>육아휴직</option>
              <option>근로시간 단축</option>
            </select>
          </label>
          <label>
            휴직 시작일
            <input type="date" value={input.leaveStartDate} onChange={(event) => updateInput('leaveStartDate', event.target.value)} />
          </label>
          <label>
            휴직 종료일
            <input type="date" value={input.leaveEndDate} onChange={(event) => updateInput('leaveEndDate', event.target.value)} />
          </label>
          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={input.hasReplacementWorker}
              onChange={(event) => updateInput('hasReplacementWorker', event.target.checked)}
            />
            대체인력 채용 여부
          </label>
        </div>
      </section>

      {error && (
        <section className="panel warning-panel">
          <AlertCircle />
          <strong>계산 오류</strong>
          <span>{error}</span>
        </section>
      )}

      {!loading && result && (
        <>
          <div className="metric-grid">
            <MetricCard label="적용 가능한 조합 수" value={`${validCombinations.length}개`} hint="충돌과 requires 위반이 없는 조합" tone="teal" />
            <MetricCard label="제외된 조합 수" value={`${rejectedCombinations.length}개`} hint="충돌 또는 선행 정책 누락" tone="orange" />
            <MetricCard label="가장 높은 총지원금" value={formatDemoMoney(highestTotal)} hint="총지원금 기준 단순 비교" tone="blue" />
            <MetricCard label="계산 기준일" value={result.calculatedAt || '-'} hint={result.isMock ? 'mock 데이터' : 'API 데이터'} tone="slate" />
          </div>

          <div className="demo-result-grid">
            <section className="panel">
              <h2>유효 조합 목록</h2>
              {validCombinations.length === 0 && <p className="empty-state">결과 없음</p>}
              <div className="combination-list">
                {validCombinations.map((combination) => (
                  <CombinationCard
                    key={combination.policy_ids.join('|')}
                    combination={combination}
                    selected={selected === combination}
                    onSelect={() => setSelected(combination)}
                  />
                ))}
              </div>
            </section>

            <section className="panel">
              <h2>제외 조합 목록</h2>
              {rejectedCombinations.length === 0 && <p className="empty-state">결과 없음</p>}
              <div className="combination-list">
                {rejectedCombinations.map((combination) => (
                  <RejectedCombinationCard
                    key={combination.policy_ids.join('|')}
                    combination={combination}
                    selected={selected === combination}
                    onSelect={() => setSelected(combination)}
                  />
                ))}
              </div>
            </section>
          </div>

          <RecommendationDetail selected={selected} />
        </>
      )}
    </div>
  );
}

function CombinationCard({ combination, selected, onSelect }) {
  return (
    <article className={`demo-card ${selected ? 'active' : ''}`}>
      <div>
        <strong>{combination.policy_ids.join(' + ')}</strong>
        <span>포함 정책 수 {combination.policy_ids.length}개</span>
      </div>
      <dl>
        <dt>기본 지원금</dt>
        <dd>{formatDemoMoney(combination.total_base_amount)}</dd>
        <dt>추가 지원금</dt>
        <dd>{formatDemoMoney(combination.total_bonus_amount)}</dd>
        <dt>총지원금</dt>
        <dd>{formatDemoMoney(combination.total_subsidy_amount)}</dd>
      </dl>
      <button className="outline small" onClick={onSelect}>상세 보기</button>
    </article>
  );
}

function RejectedCombinationCard({ combination, selected, onSelect }) {
  const reasonTypes = combination.reasons.map((reason) => reason.type).join(', ');
  const reasonText = combination.reasons.map((reason) => reason.details?.reason).filter(Boolean).join(' / ');
  const evidence = combination.reasons.flatMap((reason) => reason.details?.evidence_snippets || []);

  return (
    <article className={`demo-card rejected ${selected ? 'active' : ''}`}>
      <div>
        <strong>{combination.policy_ids.join(' + ')}</strong>
        <span>{reasonTypes}</span>
      </div>
      <p>{reasonText || '제외 사유가 구조화되어 있습니다.'}</p>
      <ul>
        {evidence.map((snippet) => <li key={snippet}>{snippet}</li>)}
      </ul>
      <button className="outline small" onClick={onSelect}>상세 보기</button>
    </article>
  );
}

function RecommendationDetail({ selected }) {
  if (!selected) {
    return (
      <section className="panel">
        <h2>상세 영역</h2>
        <p className="empty-state">결과 없음</p>
      </section>
    );
  }

  const isRejected = Boolean(selected.reasons);

  return (
    <section className="panel detail-panel">
      <div className="panel-head">
        <div>
          <h2>상세 영역</h2>
          <p>{selected.policy_ids.join(' + ')}</p>
        </div>
        <span className={`detail-badge ${isRejected ? 'rejected' : 'valid'}`}>
          {isRejected ? '제외 조합' : '유효 조합'}
        </span>
      </div>

      {isRejected ? (
        <div className="detail-grid">
          {selected.reasons.map((reason) => (
            <article className="detail-block" key={`${reason.type}-${reason.details?.rule_id || reason.details?.source_policy_id}`}>
              <h3>{reason.type}</h3>
              <dl>
                <dt>제외 사유</dt>
                <dd>{reason.details?.reason || '계산 불가'}</dd>
                <dt>근거</dt>
                <dd>{(reason.details?.evidence_snippets || []).join(' / ') || '계산 불가'}</dd>
              </dl>
              <pre>{formatJson(reason.details)}</pre>
            </article>
          ))}
        </div>
      ) : (
        <div className="detail-grid">
          {selected.policy_results.map((policyResult) => (
            <article className="detail-block" key={policyResult.policy_id}>
              <h3>{policyResult.policy_name || policyResult.policy_id}</h3>
              <dl>
                <dt>base_amount</dt>
                <dd>{formatDemoMoney(policyResult.base_amount)}</dd>
                <dt>bonus_amount</dt>
                <dd>{formatDemoMoney(policyResult.bonus_amount)}</dd>
                <dt>estimated_total_amount</dt>
                <dd>{formatDemoMoney(policyResult.estimated_total_amount)}</dd>
              </dl>
              <h4>calculation_steps</h4>
              <pre>{formatJson(policyResult.calculation_steps)}</pre>
              <h4>passed_conditions</h4>
              <pre>{formatJson(policyResult.passed_conditions)}</pre>
              <h4>failed_conditions</h4>
              <pre>{formatJson(policyResult.failed_conditions)}</pre>
              <h4>applied_bonuses</h4>
              <pre>{formatJson(policyResult.applied_bonuses)}</pre>
              <h4>skipped_bonuses</h4>
              <pre>{formatJson(policyResult.skipped_bonuses)}</pre>
              <h4>evidence_snippets</h4>
              <pre>{formatJson(policyResult.evidence_snippets)}</pre>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function EmployeeManagement({ role }) {
  return (
    <div className="screen two-col">
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>직원 관리</h2>
            <p>{role === 'company' ? '기업 관리 하위화면에서 직원·휴직 정보를 상시 수정합니다.' : '선택 고객사 기준으로 직원 정보를 관리합니다.'}</p>
          </div>
          <button className="primary small">직원 추가</button>
        </div>
        <div className="employee-table">
          {employees.map((employee) => (
            <div className="employee-card" key={employee.name}>
              <div>
                <strong>{employee.name}</strong>
                <span>{employee.status}</span>
              </div>
              <dl>
                <dt>자녀 나이</dt><dd>{employee.childAge}</dd>
                <dt>근로시간</dt><dd>주 {employee.weeklyHours}시간</dd>
                <dt>예상 수급액</dt><dd>{money(employee.amount)}</dd>
              </dl>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <h2>빠른 작업</h2>
        <ActionItem icon={<Upload />} title="엑셀 업로드" text="직원 명단과 휴직 예정일을 일괄 등록" />
        <ActionItem icon={<UsersRound />} title="휴직 유형 선택" text="육아휴직, 근로시간 단축, 대체인력 연결" />
        <ActionItem icon={<CheckCircle2 />} title="시작일/종료일 설정" text="지원금 기간과 마감 알림 자동 계산" />
      </section>
    </div>
  );
}

function DocumentManagement() {
  return (
    <div className="screen">
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>서류·일정 관리</h2>
            <p>직원별 제출서류와 검수 상태, 신청 마감일을 함께 관리합니다.</p>
          </div>
          <button className="primary small">일정 추가</button>
        </div>
        <div className="doc-list">
          {documents.map((doc) => (
            <article className="doc-row" key={doc.title}>
              <FileText />
              <div>
                <strong>{doc.title}</strong>
                <span>{doc.status}</span>
              </div>
              <b>{doc.due}</b>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function ReplacementManagement() {
  return (
    <div className="screen two-col">
      <section className="panel">
        <h2>대체인력 관리</h2>
        <p className="panel-desc">AI 구인공고 초안, 워크넷 게시, 추가 수급액 확인을 한 플로우에서 처리합니다.</p>
        <div className="timeline">
          <Step title="구인공고 초안 생성" state="완료" />
          <Step title="워크넷 게시" state="대기" />
          <Step title="채용 증빙 연결" state="필요" />
        </div>
      </section>
      <section className="panel warning-panel">
        <AlertCircle />
        <strong>대체인력 지원금은 직원 개인 지원금과 중복 여부를 반드시 확인해야 합니다.</strong>
        <span>현재 추천 엔진은 같은 정책 묶음에서 최고액 1개만 개인 총액에 반영합니다.</span>
      </section>
    </div>
  );
}

function ClientManagement() {
  return (
    <div className="screen">
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>고객사 관리</h2>
            <p>노무법인은 고객사별 직원 관리와 서류 검수 상태를 분리해서 운영합니다.</p>
          </div>
          <button className="primary small">고객사 추가</button>
        </div>
        <ClientList />
      </section>
    </div>
  );
}

function ClientList({ compact = false }) {
  return (
    <div className={compact ? 'client-list compact' : 'client-list'}>
      {clients.map((client) => (
        <article className="client-row" key={client.name}>
          <Building2 />
          <div>
            <strong>{client.name}</strong>
            <span>직원 {client.employees}명 · {client.status}</span>
          </div>
          <b>{client.amount}</b>
        </article>
      ))}
    </div>
  );
}

function NewsletterView() {
  return (
    <div className="screen two-col">
      <section className="panel">
        <h2>뉴스레터 발송</h2>
        <p className="panel-desc">AI 주제 추천, 초안 생성, 수신 기업 선택, 일괄 발송을 지원합니다.</p>
        <ActionItem icon={<Wand2 />} title="AI 주제 추천" text="이번 달 육아지원 정책 변경사항 요약" />
        <ActionItem icon={<Mail />} title="수신 기업 선택" text="고객사 조건에 맞는 대상 자동 필터" />
      </section>
      <section className="panel">
        <h2>발송 대기</h2>
        <Deadline label="6월 육아휴직 지원금 변경 안내" day="3개사" />
        <Deadline label="대체인력 지원 증빙 체크리스트" day="5개사" />
      </section>
    </div>
  );
}

function SettingsView({ role }) {
  return (
    <div className="screen two-col">
      <section className="panel">
        <h2>{role === 'company' ? '기업 설정' : '파트너 설정'}</h2>
        <p className="panel-desc">{role === 'company' ? '사업자 정보, 담당자 정보, 계정 권한을 수정합니다.' : '법인 정보, 수수료·계좌, 플랜과 알림을 관리합니다.'}</p>
        <ActionItem icon={<ShieldCheck />} title="계정·권한 관리" text="담당자별 접근 권한 설정" />
        <ActionItem icon={<Settings />} title="알림 설정" text="마감일, 서류 반려, 신규 정책 알림" />
      </section>
      <section className="panel">
        <h2>운영 메모</h2>
        <InfoStrip compact />
      </section>
    </div>
  );
}

function ActionItem({ icon, title, text }) {
  return (
    <div className="action-item">
      {icon}
      <div>
        <strong>{title}</strong>
        <span>{text}</span>
      </div>
      <ChevronRight />
    </div>
  );
}

function Deadline({ label, day }) {
  return (
    <div className="deadline">
      <span>{label}</span>
      <strong>{day}</strong>
    </div>
  );
}

function Step({ title, state }) {
  return (
    <div className="step">
      <span>{state}</span>
      <strong>{title}</strong>
    </div>
  );
}

function InfoStrip({ compact = false }) {
  return (
    <div className={`info-strip ${compact ? 'compact' : ''}`}>
      <AlertCircle />
      <span>
        직원 관리는 독립 메뉴처럼 보일 수 있지만, 일반기업의 기업 관리와 노무법인의 고객사 관리 아래에서 운영되는 하위화면입니다.
      </span>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
