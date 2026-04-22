/* ═══════════════════════════════════════════════
   hc-core.js — shared state & API helpers
   for all Health Console pages
═══════════════════════════════════════════════ */

const state = {
  access: localStorage.getItem('evarya_access') || '',
  refresh: localStorage.getItem('evarya_refresh') || '',
  user: (() => { try { return JSON.parse(localStorage.getItem('evarya_user') || 'null'); } catch { return null; } })(),
  categories: [],
  members: [],
  flows: [],
  questions: [],
  options: [],
  transitions: [],
  activeSession: null
};

async function bootstrapSessionToken() {
  if (state.access) return true;
  try {
    const response = await fetch('/api/auth/session/', { credentials: 'same-origin' });
    if (!response.ok) return false;
    const data = await response.json();
    state.user = data.user;
    setTokens(data.tokens);
    showApi(data || {});
    return Boolean(state.access);
  } catch {
    return false;
  }
}

/* ── Status bar ── */
function setStatus(message, isError = false) {
  const box = document.getElementById('status');
  if (!box) return;
  box.textContent = message;
  box.style.borderColor = isError ? '#efbac2' : '#d7dedb';
  box.style.background  = isError ? '#fff1f3' : '#ffffff';
}

/* ── API output (hc-api page) ── */
function showApi(data) {
  const el = document.getElementById('apiOutput');
  if (el) el.textContent = JSON.stringify(data, null, 2);
  localStorage.setItem('evarya_last_api', JSON.stringify(data, null, 2));
}

/* ── Tokens ── */
function setTokens(tokens) {
  if (!tokens) return;
  state.access  = tokens.access  || state.access;
  state.refresh = tokens.refresh || state.refresh;
  localStorage.setItem('evarya_access',  state.access);
  localStorage.setItem('evarya_refresh', state.refresh);
  if (state.user) localStorage.setItem('evarya_user', JSON.stringify(state.user));
  if (window.sbRefreshToken) window.sbRefreshToken();
}

/* ── Core request ── */
async function request(path, options = {}) {
  await bootstrapSessionToken();
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (state.access) headers.set('Authorization', `Bearer ${state.access}`);

  const response = await fetch(path, { ...options, headers, credentials: 'same-origin' });
  let data = null;
  const text = await response.text();
  if (text) { try { data = JSON.parse(text); } catch { data = { raw: text }; } }

  if (response.status === 401 && state.refresh && !options._retried) {
    const refreshed = await fetch('/api/auth/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ refresh: state.refresh })
    });
    const refreshData = await refreshed.json().catch(() => ({}));
    if (refreshed.ok && refreshData.access) {
      setTokens({ access: refreshData.access, refresh: state.refresh });
      return request(path, { ...options, _retried: true });
    }

    ['evarya_access','evarya_refresh','evarya_user'].forEach(k => localStorage.removeItem(k));
    state.access = '';
    state.refresh = '';
    state.user = null;
    if (await bootstrapSessionToken()) return request(path, { ...options, _retried: true });
  }

  showApi(data || {});
  if (!response.ok) {
    let message = data?.detail || data?.non_field_errors || data?.message || data?.raw || '';
    if (!message && data && typeof data === 'object') {
      message = Object.entries(data)
        .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
        .join(' | ');
    }
    throw new Error(Array.isArray(message) ? message.join(', ') : String(message || `Request failed with ${response.status}`));
  }
  return data;
}

/* ── Form helpers ── */
function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function compactPayload(data) {
  const payload = {};
  Object.entries(data).forEach(([key, value]) => {
    if (key === 'id') return;
    if (value === '') return;
    if (['age','version','display_order','option_order','flow','question','option','next_question','category_id','flow_id','family_member_id'].includes(key)) {
      payload[key] = Number(value);
    } else if (['is_active','is_start_question'].includes(key)) {
      payload[key] = value === 'true';
    } else {
      payload[key] = value;
    }
  });
  return payload;
}

function fillSelect(selector, items, labelFn, includeBlank = false) {
  document.querySelectorAll(selector).forEach(select => {
    const current = select.value;
    select.innerHTML = includeBlank ? '<option value="">None</option>' : '';
    items.forEach(item => {
      const option = document.createElement('option');
      option.value = item.id;
      option.textContent = labelFn(item);
      select.appendChild(option);
    });
    if ([...select.options].some(o => o.value === current)) select.value = current;
  });
}

function itemCard(title, detail, actions = '') {
  return `<div class="hc-item"><div class="hc-item-head"><strong>${title}</strong>${actions}</div><div class="hc-meta">${detail}</div></div>`;
}

function flagPill(flag) {
  if (!flag) return '<span class="pill">OPEN</span>';
  const cls = String(flag).toLowerCase();
  return `<span class="pill ${cls}">${flag}</span>`;
}

/* ── Data loaders ── */
async function loadProfile() {
  const profile = await request('/api/auth/basic-information/');
  state.user = profile;
  localStorage.setItem('evarya_user', JSON.stringify(profile));
  if (typeof window.renderProfileSummary === 'function') {
    window.renderProfileSummary(profile);
  } else {
    const el = document.getElementById('profileJson');
    if (el) el.textContent = JSON.stringify(profile, null, 2);
  }
  const form = document.getElementById('profileForm');
  if (form) Object.entries(profile).forEach(([key, value]) => {
    const input = form.querySelector(`[name="${key}"]`);
    if (input) input.value = value ?? '';
  });
  if (window.sbRefreshToken) window.sbRefreshToken();
  return profile;
}

async function loadCategories() {
  state.categories = await request('/api/auth/family-categories/');
  renderCategories();
  return state.categories;
}

async function loadMembers() {
  state.members = await request('/api/auth/family-members/');
  renderMembers();
  return state.members;
}

async function loadFlows() {
  state.flows = await request('/api/triage/flows/');
  renderBuilderSelects();
  renderBuilderList('flows', state.flows);
  return state.flows;
}

async function loadQuestions() {
  state.questions = await request('/api/triage/questions/');
  renderBuilderSelects();
  renderBuilderList('questions', state.questions);
  return state.questions;
}

async function loadOptions() {
  state.options = await request('/api/triage/options/');
  renderBuilderSelects();
  renderBuilderList('options', state.options);
  return state.options;
}

async function loadTransitions() {
  state.transitions = await request('/api/triage/transitions/');
  renderBuilderList('transitions', state.transitions);
  return state.transitions;
}

async function loadEverything() {
  if (!state.access && !(await bootstrapSessionToken())) { setStatus('Login first, then refresh dashboard data.', true); return; }
  setStatus('Loading dashboard data...');
  await Promise.allSettled([loadProfile(), loadCategories(), loadMembers(), loadFlows(), loadQuestions(), loadOptions(), loadTransitions()]);
  setStatus('Dashboard data loaded.');
}

async function loadSessions() {
  const sel = document.getElementById('sessionStatus');
  const status = sel ? sel.value : '';
  const path = status ? `/api/triage/sessions/?status=${encodeURIComponent(status)}` : '/api/triage/sessions/';
  const sessions = await request(path);
  renderSessions(sessions);
  return sessions;
}

/* ── Render helpers (only run if relevant element exists) ── */
function renderCategories() {
  const el = document.getElementById('categoryList');
  if (el) el.innerHTML = state.categories.map(c =>
    itemCard(`#${c.id} ${c.name}`, 'Use this ID when creating family members.')
  ).join('') || '<p class="hc-hint">No categories yet.</p>';
  fillSelect('select[name="category_id"]', state.categories, i => `#${i.id} ${i.name}`);
}

function renderMembers() {
  const el = document.getElementById('memberList');
  if (el) el.innerHTML = state.members.map(m =>
    itemCard(`#${m.id} ${m.name}`, `${m.category?.name||'No category'} · ${m.age} · ${m.gender} · ${m.phone_number||'No phone'}`,
      `<button class="btn-hc secondary" style="padding:5px 10px;min-height:unset;font-size:.75rem;" data-fill-member="${m.id}">Edit</button>`)
  ).join('') || '<p class="hc-hint">No members yet.</p>';
  fillSelect('select[name="family_member_id"]', state.members, i => `#${i.id} ${i.name}`, true);
}

function renderBuilderList(kind, items) {
  const el = document.getElementById('builderList');
  if (!el) return;
  const html = items.map(item => {
    if (kind==='flows')       return itemCard(`#${item.id} ${item.name}`,`${item.code} · v${item.version} · ${item.is_active?'active':'inactive'}`,`<button class="btn-sm" data-detail-flow="${item.id}">Get</button>`);
    if (kind==='questions')   return itemCard(`#${item.id} ${item.code}`,`Flow ${item.flow} · ${item.text}`,`<button class="btn-sm" data-detail-question="${item.id}">Get</button>`);
    if (kind==='options')     return itemCard(`#${item.id} ${item.label}`,`Question ${item.question} · ${item.code} · ${item.flag_effect}`,`<button class="btn-sm" data-detail-option="${item.id}">Get</button>`);
    return itemCard(`#${item.id} option ${item.option}`,`Next ${item.next_question||'none'} · End ${item.end_flag||'none'}`,`<button class="btn-sm" data-detail-transition="${item.id}">Get</button>`);
  }).join('');
  el.innerHTML = html || `<p class="hc-hint">No ${kind} yet.</p>`;
}

function renderBuilderSelects() {
  fillSelect('select[name="flow"], select[name="flow_id"]', state.flows, i => `#${i.id} ${i.name}`);
  fillSelect('select[name="question"]', state.questions, i => `#${i.id} ${i.code}`);
  fillSelect('select[name="next_question"]', state.questions, i => `#${i.id} ${i.code}`, true);
  fillSelect('select[name="option"]', state.options, i => `#${i.id} ${i.label}`);
}

function renderSessions(sessions) {
  const el = document.getElementById('sessionList');
  if (!el) return;
  el.innerHTML = sessions.map(session =>
    itemCard(`#${session.id} ${session.flow_name}`,
      `${session.patient_name} · ${session.status} · ${session.answers.length} answers`,
      `${flagPill(session.final_flag)} <button class="btn-sm" data-session="${session.id}">Open</button>`)
  ).join('') || '<p class="hc-hint">No sessions yet.</p>';
}

function renderCurrentQuestion(session) {
  state.activeSession = session;
  const jsonEl = document.getElementById('sessionJson');
  if (jsonEl) jsonEl.textContent = JSON.stringify(session || {}, null, 2);
  const el = document.getElementById('currentQuestion');
  if (!el) return;
  if (!session) { el.innerHTML='<p class="hc-hint">Start or open a session.</p>'; return; }
  if (session.status === 'COMPLETED') {
    el.innerHTML = itemCard(`Completed ${session.final_flag||''}`, session.final_message||'No final message.');
    return;
  }
  const question = session.current_question;
  const options = (question?.options||[]).map(o =>
    `<button class="btn-hc" style="min-height:56px;background:#edf6f3;color:var(--ink);border:1px solid var(--line);text-align:left;font-size:.82rem;" data-answer="${o.id}">${o.label}<br><span class="hc-meta">${o.flag_effect}</span></button>`
  ).join('');
  el.innerHTML=`<div class="hc-item"><strong>${question?.text||'No current question'}</strong><p class="hc-meta">${question?.help_text||''}</p><div class="option-grid">${options}</div></div>`;
}

/* ── Global click delegation (answers, fill-member, sessions, detail buttons) ── */
document.addEventListener('click', async event => {
  const answerButton = event.target.closest('[data-answer]');
  if (answerButton && state.activeSession) {
    try {
      const data = await request(`/api/triage/sessions/${state.activeSession.id}/answer/`, {
        method:'POST', body: JSON.stringify({ option_id: Number(answerButton.dataset.answer) })
      });
      renderCurrentQuestion(data.session);
      await loadSessions();
      setStatus('Answer saved.');
    } catch(error) { setStatus(error.message, true); }
  }

  const memberButton = event.target.closest('[data-fill-member]');
  if (memberButton) {
    const member = state.members.find(i => i.id === Number(memberButton.dataset.fillMember));
    if (member) {
      const form = document.getElementById('memberForm');
      if (form) {
        form.elements.id.value          = member.id;
        form.elements.category_id.value = member.category_id || member.category?.id || '';
        form.elements.name.value        = member.name;
        form.elements.age.value         = member.age;
        form.elements.gender.value      = member.gender;
        form.elements.phone_number.value = member.phone_number || '';
      }
    }
  }

  const sessionButton = event.target.closest('[data-session]');
  if (sessionButton) {
    try {
      const session = await request(`/api/triage/sessions/${sessionButton.dataset.session}/`);
      renderCurrentQuestion(session);
      setStatus(`Opened session #${session.id}.`);
    } catch(error) { setStatus(error.message, true); }
  }

  /* Detail buttons */
  const detailMap = [
    ['detailFlow','/api/triage/flows/'],
    ['detailQuestion','/api/triage/questions/'],
    ['detailOption','/api/triage/options/'],
    ['detailTransition','/api/triage/transitions/']
  ];
  for (const [key, path] of detailMap) {
    const btn = event.target.closest(`[data-${key.replace(/[A-Z]/g,m=>'-'+m.toLowerCase())}]`);
    if (btn) {
      const id = btn.dataset[key];
      try {
        const data = await request(`${path}${id}/`);
        setStatus(`Loaded ${key.replace('detail','').toLowerCase()} #${id}.`);
        showApi(data);
      } catch(error) { setStatus(error.message, true); }
    }
  }
});

/* ── Sample triage flow ── */
async function createSampleFlow() {
  setStatus('Creating sample flow...');
  const suffix = Date.now().toString().slice(-5);
  const flowResp = await request('/api/triage/flows/', { method:'POST', body: JSON.stringify({ name:`Fever quick check ${suffix}`, code:`fever-quick-check-${suffix}`, description:'Quick patient triage flow for fever symptoms.', version:1, is_active:true }) });
  const flowId = flowResp.flow.id;
  const q1 = await request('/api/triage/questions/', { method:'POST', body: JSON.stringify({ flow:flowId, code:'temperature', text:'What is the highest temperature recorded today?', category:'fever', help_text:'Use the most recent reliable reading.', display_order:1, is_start_question:true, is_active:true }) });
  const q2 = await request('/api/triage/questions/', { method:'POST', body: JSON.stringify({ flow:flowId, code:'warning-signs', text:'Are there breathing issues, confusion, chest pain, or severe weakness?', category:'risk', help_text:'Choose yes if any warning sign is present.', display_order:2, is_start_question:false, is_active:true }) });
  const mild      = await request('/api/triage/options/', { method:'POST', body: JSON.stringify({ question:q1.question.id, code:'mild', label:'Below 100.4 F', option_order:1, flag_effect:'GREEN', is_active:true }) });
  const high      = await request('/api/triage/options/', { method:'POST', body: JSON.stringify({ question:q1.question.id, code:'high', label:'100.4 F or higher', option_order:2, flag_effect:'NONE', is_active:true }) });
  const warningNo = await request('/api/triage/options/', { method:'POST', body: JSON.stringify({ question:q2.question.id, code:'no', label:'No warning signs', option_order:1, flag_effect:'YELLOW', is_active:true }) });
  const warningYes= await request('/api/triage/options/', { method:'POST', body: JSON.stringify({ question:q2.question.id, code:'yes', label:'Yes, warning signs are present', option_order:2, flag_effect:'RED', is_active:true }) });
  await request('/api/triage/transitions/', { method:'POST', body: JSON.stringify({ option:mild.option.id, end_flag:'GREEN', end_message:'Home care and hydration are reasonable. Monitor symptoms.' }) });
  await request('/api/triage/transitions/', { method:'POST', body: JSON.stringify({ option:high.option.id, next_question:q2.question.id }) });
  await request('/api/triage/transitions/', { method:'POST', body: JSON.stringify({ option:warningNo.option.id, end_flag:'YELLOW', end_message:'Book a clinician review if fever persists or worsens.' }) });
  await request('/api/triage/transitions/', { method:'POST', body: JSON.stringify({ option:warningYes.option.id, end_flag:'RED', end_message:'Seek urgent medical care now.' }) });
  await Promise.all([loadFlows(), loadQuestions(), loadOptions(), loadTransitions()]);
  setStatus('Sample triage flow created. Open Triage test to run it.');
}

/* ── createOrUpdate helper for builder forms ── */
async function createOrUpdate(formSelector, basePath, update = false, label = 'item') {
  const form = document.querySelector(formSelector);
  const id = form.elements.id.value;
  if (update && !id) return setStatus(`Enter a ${label} ID to update.`, true);
  const path = update ? `${basePath}${id}/` : basePath;
  const method = update ? 'PATCH' : 'POST';
  try {
    await request(path, { method, body: JSON.stringify(compactPayload(formData(form))) });
    await Promise.all([loadFlows(), loadQuestions(), loadOptions(), loadTransitions()]);
    setStatus(`${label} ${update ? 'updated' : 'created'}.`);
  } catch(error) { setStatus(error.message, true); }
}

/* Auto-init: refresh sidebar token state */
if (window.sbRefreshToken) window.sbRefreshToken();
