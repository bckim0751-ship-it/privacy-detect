const API = '';

// ── 유틸 ─────────────────────────────────────────────────────────────────────

async function api(method, path, body) {
  const res = await fetch(API + path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '오류가 발생했습니다.' }));
    throw new Error(err.detail || '오류가 발생했습니다.');
  }
  if (res.status === 204) return null;
  return res.json();
}

function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type}`;
  el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 3000);
}

function fmtDate(s) {
  if (!s) return '-';
  return s.slice(0, 10);
}

function fmtDateTime(s) {
  if (!s) return '-';
  return s.replace('T', ' ').slice(0, 16);
}

function typeBadge(t) {
  return t === 'collection_use'
    ? '<span class="badge badge-blue">수집·이용</span>'
    : '<span class="badge badge-purple">제3자 제공</span>';
}

function statusBadge(s) {
  const map = {
    active: ['badge-green', '시행중'],
    draft:  ['badge-yellow', '초안'],
    inactive: ['badge-gray', '미사용'],
  };
  const [cls, label] = map[s] || ['badge-gray', s];
  return `<span class="badge ${cls}">${label}</span>`;
}

function requiredBadge(r) {
  return r
    ? '<span class="badge badge-red">필수</span>'
    : '<span class="badge badge-orange">선택</span>';
}

// ── 네비게이션 ────────────────────────────────────────────────────────────────

let currentPage = 'dashboard';

function showPage(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`page-${page}`).classList.add('active');
  document.querySelector(`.nav-btn[data-page="${page}"]`).classList.add('active');
  currentPage = page;
  if (page === 'dashboard') loadDashboard();
  if (page === 'services') loadServices();
  if (page === 'consent-forms') loadConsentForms();
}

document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => showPage(btn.dataset.page));
});

// ── 모달 ─────────────────────────────────────────────────────────────────────

function openModal(id) { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

document.querySelectorAll('.modal-close, [data-modal]').forEach(el => {
  el.addEventListener('click', () => closeModal(el.dataset.modal || el.closest('.modal-backdrop').id));
});

document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
  backdrop.addEventListener('click', e => {
    if (e.target === backdrop) closeModal(backdrop.id);
  });
});

// ── 대시보드 ──────────────────────────────────────────────────────────────────

async function loadDashboard() {
  const [stats, forms] = await Promise.all([
    api('GET', '/api/dashboard'),
    api('GET', '/api/consent-forms'),
  ]);

  document.getElementById('stat-services').textContent = stats.total_services;
  document.getElementById('stat-forms').textContent = stats.total_consent_forms;
  document.getElementById('stat-collection').textContent = stats.collection_use_count;
  document.getElementById('stat-third').textContent = stats.third_party_count;
  document.getElementById('stat-active').textContent = stats.active_count;
  document.getElementById('stat-draft').textContent = stats.draft_count;
  document.getElementById('stat-required').textContent = stats.required_count;
  document.getElementById('stat-optional').textContent = stats.optional_count;

  const tbody = document.getElementById('dashboard-tbody');
  if (!forms.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">등록된 동의서가 없습니다.</td></tr>';
    return;
  }
  tbody.innerHTML = forms.slice(0, 10).map(f => `
    <tr>
      <td>${f.service.name}</td>
      <td>${typeBadge(f.consent_type)}</td>
      <td>${requiredBadge(f.is_required)}</td>
      <td>${f.version}</td>
      <td>${statusBadge(f.status)}</td>
      <td>${fmtDate(f.effective_date)}</td>
      <td>${fmtDateTime(f.updated_at)}</td>
    </tr>
  `).join('');
}

// ── 서비스 관리 ───────────────────────────────────────────────────────────────

let allServices = [];

async function loadServices() {
  const q = document.getElementById('service-search').value.trim();
  const url = q ? `/api/services?q=${encodeURIComponent(q)}` : '/api/services';
  allServices = await api('GET', url);
  renderServicesTable();
}

function renderServicesTable() {
  // 서비스별 동의서 수를 계산하기 위해 별도 조회 필요할 수 있으나, 간단히 서비스 목록만 표시
  const tbody = document.getElementById('services-tbody');
  if (!allServices.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">등록된 서비스가 없습니다.</td></tr>';
    return;
  }
  tbody.innerHTML = allServices.map(s => `
    <tr>
      <td><code>${s.code}</code></td>
      <td><strong>${s.name}</strong></td>
      <td>${s.department || '-'}</td>
      <td>${fmtDate(s.created_at)}</td>
      <td>
        <button class="btn btn-sm btn-ghost" onclick="showServiceForms(${s.id}, '${s.name.replace(/'/g, "\\'")}')">동의서 보기</button>
      </td>
      <td style="display:flex;gap:4px">
        <button class="btn btn-sm btn-secondary" onclick="editService(${s.id})">수정</button>
        <button class="btn btn-sm btn-danger" onclick="deleteService(${s.id})">삭제</button>
      </td>
    </tr>
  `).join('');
}

function showServiceForms(serviceId, serviceName) {
  showPage('consent-forms');
  document.getElementById('filter-service').value = serviceId;
  loadConsentForms();
}

document.getElementById('service-search').addEventListener('keydown', e => {
  if (e.key === 'Enter') loadServices();
});

// 서비스 등록
document.getElementById('btn-new-service').addEventListener('click', () => {
  document.getElementById('modal-service-title').textContent = '서비스 등록';
  document.getElementById('form-service').reset();
  document.getElementById('svc-id').value = '';
  document.getElementById('svc-code').disabled = false;
  openModal('modal-service');
});

document.getElementById('form-service').addEventListener('submit', async e => {
  e.preventDefault();
  const id = document.getElementById('svc-id').value;
  const body = {
    code: document.getElementById('svc-code').value.trim(),
    name: document.getElementById('svc-name').value.trim(),
    department: document.getElementById('svc-dept').value.trim() || null,
    description: document.getElementById('svc-desc').value.trim() || null,
  };
  try {
    if (id) {
      await api('PUT', `/api/services/${id}`, body);
      toast('서비스가 수정되었습니다.');
    } else {
      await api('POST', '/api/services', body);
      toast('서비스가 등록되었습니다.');
    }
    closeModal('modal-service');
    loadServices();
    refreshServiceSelects();
  } catch (err) {
    toast(err.message, 'error');
  }
});

async function editService(id) {
  const svc = await api('GET', `/api/services/${id}`);
  document.getElementById('modal-service-title').textContent = '서비스 수정';
  document.getElementById('svc-id').value = svc.id;
  document.getElementById('svc-code').value = svc.code;
  document.getElementById('svc-code').disabled = true;
  document.getElementById('svc-name').value = svc.name;
  document.getElementById('svc-dept').value = svc.department || '';
  document.getElementById('svc-desc').value = svc.description || '';
  openModal('modal-service');
}

async function deleteService(id) {
  if (!confirm('서비스를 삭제하면 관련 동의서도 모두 삭제됩니다. 계속하시겠습니까?')) return;
  try {
    await api('DELETE', `/api/services/${id}`);
    toast('서비스가 삭제되었습니다.');
    loadServices();
    refreshServiceSelects();
  } catch (err) {
    toast(err.message, 'error');
  }
}

// ── 동의서 관리 ───────────────────────────────────────────────────────────────

async function loadConsentForms() {
  await refreshServiceSelects();
  const params = new URLSearchParams();
  const sv = document.getElementById('filter-service').value;
  const tv = document.getElementById('filter-type').value;
  const stv = document.getElementById('filter-status').value;
  const qv = document.getElementById('filter-q').value.trim();
  if (sv) params.set('service_id', sv);
  if (tv) params.set('consent_type', tv);
  if (stv) params.set('status', stv);
  if (qv) params.set('q', qv);

  const forms = await api('GET', `/api/consent-forms?${params}`);
  renderFormsTable(forms);
}

function renderFormsTable(forms) {
  const tbody = document.getElementById('forms-tbody');
  if (!forms.length) {
    tbody.innerHTML = '<tr><td colspan="9" class="empty-state">등록된 동의서가 없습니다.</td></tr>';
    return;
  }
  tbody.innerHTML = forms.map(f => `
    <tr>
      <td><span title="${f.service.code}">${f.service.name}</span></td>
      <td>${typeBadge(f.consent_type)}</td>
      <td>${requiredBadge(f.is_required)}</td>
      <td><span class="truncate" title="${f.purpose}">${f.purpose}</span></td>
      <td><span class="truncate" title="${f.retention_period}">${f.retention_period}</span></td>
      <td>${f.version}</td>
      <td>${statusBadge(f.status)}</td>
      <td>${fmtDate(f.effective_date)}</td>
      <td style="display:flex;gap:4px;flex-wrap:wrap">
        <button class="btn btn-sm btn-ghost" onclick="viewForm(${f.id})">상세</button>
        <button class="btn btn-sm btn-secondary" onclick="editForm(${f.id})">수정</button>
        <button class="btn btn-sm btn-danger" onclick="deleteForm(${f.id})">삭제</button>
      </td>
    </tr>
  `).join('');
}

document.getElementById('btn-search-forms').addEventListener('click', loadConsentForms);
document.getElementById('filter-q').addEventListener('keydown', e => {
  if (e.key === 'Enter') loadConsentForms();
});

// 서비스 셀렉트 새로고침
async function refreshServiceSelects() {
  const services = await api('GET', '/api/services');
  allServices = services;
  const filterSel = document.getElementById('filter-service');
  const currentFilterVal = filterSel.value;
  filterSel.innerHTML = '<option value="">전체 서비스</option>' +
    services.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  filterSel.value = currentFilterVal;

  const formSel = document.getElementById('cf-service');
  const currentFormVal = formSel.value;
  formSel.innerHTML = services.map(s => `<option value="${s.id}">${s.name} (${s.code})</option>`).join('');
  if (currentFormVal) formSel.value = currentFormVal;
}

// 제3자 제공 섹션 토글
document.getElementById('cf-type').addEventListener('change', function () {
  const isThird = this.value === 'third_party';
  document.getElementById('third-party-section').style.display = isThird ? 'block' : 'none';
  const purposeLabel = document.querySelector('label[for="cf-purpose"]') || document.querySelector('#cf-purpose').previousElementSibling;
  const itemsLabel = document.querySelector('#cf-items').previousElementSibling;
  if (isThird) {
    document.getElementById('cf-purpose').placeholder = '예: 제휴 서비스 제공 및 혜택 안내';
    document.getElementById('cf-items').placeholder = '예: 이름, 휴대폰번호, 이메일주소';
  } else {
    document.getElementById('cf-purpose').placeholder = '예: 서비스 회원가입 및 관리, 고객 상담 처리';
    document.getElementById('cf-items').placeholder = '예: 이름, 휴대폰번호, 이메일주소, 생년월일';
  }
});

// 동의서 등록
document.getElementById('btn-new-form').addEventListener('click', async () => {
  await refreshServiceSelects();
  document.getElementById('modal-form-title').textContent = '동의서 등록';
  document.getElementById('form-consent').reset();
  document.getElementById('cf-id').value = '';
  document.getElementById('cf-version').value = '1.0';
  document.getElementById('third-party-section').style.display = 'none';
  document.getElementById('change-note-section').style.display = 'none';
  openModal('modal-form');
});

document.getElementById('form-consent').addEventListener('submit', async e => {
  e.preventDefault();
  const id = document.getElementById('cf-id').value;
  const isThird = document.getElementById('cf-type').value === 'third_party';

  const body = {
    service_id: parseInt(document.getElementById('cf-service').value),
    consent_type: document.getElementById('cf-type').value,
    is_required: document.getElementById('cf-required').value === 'true',
    status: document.getElementById('cf-status').value,
    version: document.getElementById('cf-version').value.trim(),
    effective_date: document.getElementById('cf-effective').value || null,
    purpose: document.getElementById('cf-purpose').value.trim(),
    items: document.getElementById('cf-items').value.trim(),
    retention_period: document.getElementById('cf-retention').value.trim(),
    refusal_consequence: document.getElementById('cf-refusal').value.trim() || null,
    memo: document.getElementById('cf-memo').value.trim() || null,
    recipient: isThird ? (document.getElementById('cf-recipient').value.trim() || null) : null,
    recipient_purpose: isThird ? (document.getElementById('cf-recipient-purpose').value.trim() || null) : null,
    recipient_retention_period: isThird ? (document.getElementById('cf-recipient-retention').value.trim() || null) : null,
  };

  if (id) {
    body.change_note = document.getElementById('cf-change-note').value.trim() || null;
    body.changed_by = document.getElementById('cf-changed-by').value.trim() || null;
  }

  try {
    if (id) {
      await api('PUT', `/api/consent-forms/${id}`, body);
      toast('동의서가 수정되었습니다.');
    } else {
      await api('POST', '/api/consent-forms', body);
      toast('동의서가 등록되었습니다.');
    }
    closeModal('modal-form');
    loadConsentForms();
    if (currentPage === 'dashboard') loadDashboard();
  } catch (err) {
    toast(err.message, 'error');
  }
});

async function editForm(id) {
  await refreshServiceSelects();
  const f = await api('GET', `/api/consent-forms/${id}`);
  document.getElementById('modal-form-title').textContent = '동의서 수정';
  document.getElementById('cf-id').value = f.id;
  document.getElementById('cf-service').value = f.service_id;
  document.getElementById('cf-type').value = f.consent_type;
  document.getElementById('cf-required').value = String(f.is_required);
  document.getElementById('cf-status').value = f.status;
  document.getElementById('cf-version').value = f.version;
  document.getElementById('cf-effective').value = f.effective_date || '';
  document.getElementById('cf-purpose').value = f.purpose;
  document.getElementById('cf-items').value = f.items;
  document.getElementById('cf-retention').value = f.retention_period;
  document.getElementById('cf-refusal').value = f.refusal_consequence || '';
  document.getElementById('cf-memo').value = f.memo || '';
  document.getElementById('cf-recipient').value = f.recipient || '';
  document.getElementById('cf-recipient-purpose').value = f.recipient_purpose || '';
  document.getElementById('cf-recipient-retention').value = f.recipient_retention_period || '';
  document.getElementById('cf-change-note').value = '';
  document.getElementById('cf-changed-by').value = '';
  document.getElementById('third-party-section').style.display = f.consent_type === 'third_party' ? 'block' : 'none';
  document.getElementById('change-note-section').style.display = 'block';
  openModal('modal-form');
}

async function deleteForm(id) {
  if (!confirm('동의서를 삭제하시겠습니까? 개정 이력도 함께 삭제됩니다.')) return;
  try {
    await api('DELETE', `/api/consent-forms/${id}`);
    toast('동의서가 삭제되었습니다.');
    loadConsentForms();
    if (currentPage === 'dashboard') loadDashboard();
  } catch (err) {
    toast(err.message, 'error');
  }
}

// ── 동의서 상세 보기 ──────────────────────────────────────────────────────────

async function viewForm(id) {
  const [f, history] = await Promise.all([
    api('GET', `/api/consent-forms/${id}`),
    api('GET', `/api/consent-forms/${id}/history`),
  ]);

  const typeLabel = f.consent_type === 'collection_use' ? '수집·이용 동의서' : '제3자 제공 동의서';
  const statusLabel = { active: '시행중', draft: '초안', inactive: '미사용' }[f.status] || f.status;

  let thirdPartyHtml = '';
  if (f.consent_type === 'third_party') {
    thirdPartyHtml = `
      <div class="detail-item full"><div class="detail-label">제공받는 자</div><div class="detail-value">${f.recipient || '-'}</div></div>
      <div class="detail-item full"><div class="detail-label">제공받는 자의 이용 목적</div><div class="detail-value">${f.recipient_purpose || '-'}</div></div>
      <div class="detail-item full"><div class="detail-label">제공받는 자의 보유·이용 기간</div><div class="detail-value">${f.recipient_retention_period || '-'}</div></div>
    `;
  }

  const historyHtml = history.length
    ? history.map(h => {
        const snap = JSON.parse(h.snapshot);
        return `
          <div class="history-item">
            <div class="history-meta">
              v${h.version} · ${fmtDateTime(h.created_at)}
              ${h.changed_by ? `· <strong>${h.changed_by}</strong>` : ''}
            </div>
            ${h.change_note ? `<div class="history-note">📝 ${h.change_note}</div>` : ''}
            <div style="margin-top:8px;font-size:12px;color:var(--text-muted)">
              상태: ${snap.status} | 목적: ${snap.purpose?.slice(0, 60)}...
            </div>
          </div>`;
      }).join('')
    : '<div style="color:var(--text-muted);font-size:13px">개정 이력이 없습니다.</div>';

  document.getElementById('modal-detail-body').innerHTML = `
    <div class="detail-grid">
      <div class="detail-item"><div class="detail-label">서비스</div><div class="detail-value">${f.service.name} (${f.service.code})</div></div>
      <div class="detail-item"><div class="detail-label">동의서 유형</div><div class="detail-value">${typeBadge(f.consent_type)}</div></div>
      <div class="detail-item"><div class="detail-label">필수/선택</div><div class="detail-value">${requiredBadge(f.is_required)}</div></div>
      <div class="detail-item"><div class="detail-label">상태</div><div class="detail-value">${statusBadge(f.status)}</div></div>
      <div class="detail-item"><div class="detail-label">버전</div><div class="detail-value">${f.version}</div></div>
      <div class="detail-item"><div class="detail-label">시행일</div><div class="detail-value">${fmtDate(f.effective_date)}</div></div>
      <div class="detail-item full"><div class="detail-label">수집·이용 목적</div><div class="detail-value">${f.purpose}</div></div>
      <div class="detail-item full"><div class="detail-label">수집 항목</div><div class="detail-value">${f.items}</div></div>
      <div class="detail-item full"><div class="detail-label">보유·이용 기간</div><div class="detail-value">${f.retention_period}</div></div>
      <div class="detail-item full"><div class="detail-label">동의 거부 시 불이익</div><div class="detail-value">${f.refusal_consequence || '-'}</div></div>
      ${thirdPartyHtml}
      <div class="detail-item full"><div class="detail-label">담당자 메모</div><div class="detail-value">${f.memo || '-'}</div></div>
      <div class="detail-item"><div class="detail-label">최초 등록</div><div class="detail-value">${fmtDateTime(f.created_at)}</div></div>
      <div class="detail-item"><div class="detail-label">최종 수정</div><div class="detail-value">${fmtDateTime(f.updated_at)}</div></div>
    </div>
    <div class="section-divider" style="margin-top:24px">개정 이력 (${history.length}건)</div>
    ${historyHtml}
  `;
  openModal('modal-detail');
}

// ── 초기 로드 ─────────────────────────────────────────────────────────────────

loadDashboard();
