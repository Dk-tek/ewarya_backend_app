/**
 * Evarya.health — app.js
 * Full patient triage flow per spec document:
 * Landing → P1 (symptom) → P2 (confirm+age) → P3 (associated)
 * → RED FLAG check → P4 (cluster) → P5 (details) → P6 (vitals)
 * → P7 (summary+waiting+zoom) → P8 (payment) → P9 (sub nudge)
 */

'use strict';

/* ══════════════════════════════════════
   SYMPTOM DATA
══════════════════════════════════════ */
const TRIGGER_KEYWORDS = [
  'chest pain','breathlessness','fever','vomiting','headache',
  'abdominal pain','dizziness','weakness','fainting','collapse','trauma',
  'cough','palpitations','bleeding','confusion',
];

const ASSOC_MAP = {
  'chest pain':     ['Sweating','Radiation to arm or jaw','Shortness of breath','Nausea','Dizziness','Palpitations'],
  'breathlessness': ['Chest tightness','Wheezing','Coughing','Dizziness','Fatigue','Bluish lips or fingers'],
  'fever':          ['Chills','Body aches','Sore throat','Headache','Rash','Vomiting'],
  'vomiting':       ['Nausea','Abdominal pain','Diarrhoea','Dizziness','Blood in vomit','Dehydration'],
  'headache':       ['Nausea','Light sensitivity','Neck stiffness','Visual changes','Dizziness','Vomiting'],
  'abdominal pain': ['Nausea','Vomiting','Fever','Bloating','Blood in stool','Rigidity'],
  'dizziness':      ['Nausea','Vomiting','Hearing loss','Double vision','Fainting','Headache'],
  'weakness':       ['Facial drooping','Speech difficulty','Vision change','Headache','Numbness','Loss of balance'],
  default:          ['Nausea','Dizziness','Fatigue','Headache','Fever','Weakness'],
};

/* ── Red flag combinations ── */
const RED_FLAG_RULES = [
  { sym:'chest pain',     assoc:['Sweating','Radiation to arm or jaw'], label:'Possible cardiac event — ACS pattern' },
  { sym:'chest pain',     assoc:['Shortness of breath','Dizziness'],   label:'Possible cardiac event' },
  { sym:'chest pain',     assoc:['Sweating'],                          label:'Chest pain with sweating', single:true },
  { sym:'breathlessness', assoc:['Bluish lips or fingers'],            label:'Possible hypoxia — cyanosis', single:true },
  { sym:'breathlessness', assoc:['Chest tightness','Dizziness'],       label:'Severe respiratory distress' },
  { sym:'headache',       assoc:['Neck stiffness','Vomiting'],         label:'Possible meningitis' },
  { sym:'headache',       assoc:['Visual changes'],                    label:'Neurological emergency', single:true },
  { sym:'weakness',       assoc:['Facial drooping'],                   label:'Possible stroke — FAST', single:true },
  { sym:'weakness',       assoc:['Speech difficulty'],                 label:'Possible stroke — FAST', single:true },
  { sym:'vomiting',       assoc:['Blood in vomit'],                    label:'GI bleeding emergency', single:true },
  { sym:'abdominal pain', assoc:['Rigidity','Fever'],                  label:'Surgical abdomen' },
];

/* ── Cluster definitions ── */
const CLUSTERS = {
  'chest pain':     { name:'Cardiac', icon:'❤️', desc:'Heart and circulation related', color:'var(--red)' },
  'breathlessness': { name:'Respiratory', icon:'🫁', desc:'Breathing and lungs related', color:'#2980b9' },
  'fever':          { name:'Infectious', icon:'🦠', desc:'Infection or inflammatory process', color:'var(--yellow)' },
  'vomiting':       { name:'Gastrointestinal', icon:'🤢', desc:'Digestive system related', color:'#8e44ad' },
  'headache':       { name:'Neurological', icon:'🧠', desc:'Brain and nervous system related', color:'#2c3e50' },
  'abdominal pain': { name:'Gastrointestinal', icon:'🤢', desc:'Digestive system related', color:'#8e44ad' },
  'dizziness':      { name:'Vestibular / Neurological', icon:'😵', desc:'Balance and nervous system', color:'#2c3e50' },
  'weakness':       { name:'Neurological', icon:'🧠', desc:'Possible stroke or neurological event', color:'var(--red)' },
  default:          { name:'General', icon:'🩺', desc:'General physician assessment', color:'var(--forest)' },
};

/* ── Doctors ── */
const DOCTORS = {
  'Cardiac':            { name:'Dr. Kumar Anand',   spec:'Cardiologist',           icon:'❤️' },
  'Respiratory':        { name:'Dr. Meena Rao',     spec:'Pulmonologist',           icon:'🫁' },
  'Neurological':       { name:'Dr. Vikram Nair',   spec:'Neurologist',             icon:'🧠' },
  'Gastrointestinal':   { name:'Dr. Suresh Pillai', spec:'Gastroenterologist',      icon:'🤢' },
  'Infectious':         { name:'Dr. Priya Sharma',  spec:'General Physician',       icon:'🩺' },
  'Emergency':          { name:'Dr. Arjun Menon',   spec:'Emergency Specialist',    icon:'🚨' },
  'General':            { name:'Dr. Priya Sharma',  spec:'General Physician',       icon:'🩺' },
  default:              { name:'Dr. Priya Sharma',  spec:'General Physician',       icon:'🩺' },
};

/* ── Waiting guidance per symptom ── */
const GUIDANCE = {
  'chest pain':     ['Sit or lie in a comfortable position','Do not exert yourself','Avoid eating or drinking until seen','If pain worsens, call 112 immediately'],
  'breathlessness': ['Sit upright — do not lie flat','Try to stay calm and breathe slowly','Avoid triggers such as dust or smoke','If lips turn blue, call 112 immediately'],
  'fever':          ['Stay hydrated — drink water or oral rehydration salts','Rest in a cool environment','Take paracetamol if temperature exceeds 38.5°C','Monitor for neck stiffness or rash'],
  'vomiting':       ['Take small sips of water to stay hydrated','Avoid solid food until vomiting subsides','Lie on your side to avoid choking','Seek help immediately if blood is present'],
  'headache':       ['Rest in a quiet, dark room','Apply a cool compress to your forehead','Avoid bright screens','Seek help immediately if headache is sudden and severe'],
  default:          ['Rest and stay hydrated','Monitor your symptoms','Do not drive or operate machinery','Contact emergency services if symptoms worsen suddenly'],
};

/* ══════════════════════════════════════
   STATE
══════════════════════════════════════ */
let S = {
  symptomRaw: '', keyword: '',
  age: 0, gender: '', lmp: '',
  assocSelected: [],
  riskLevel: 'green',
  redFlag: false, redFlagLabel: '',
  cluster: null,
  name: '', phone: '',
  conditions: [], uploadFile: null,
  vitals: { bp:'', spo2:'', temp:'' },
  doctor: null,
  currentPage: 1,
};

/* ══════════════════════════════════════
   HELPERS
══════════════════════════════════════ */
function show(id){ document.getElementById(id)?.classList.remove('hidden') }
function hide(id){ document.getElementById(id)?.classList.add('hidden') }

function showPage(n) {
  document.querySelectorAll('.triage-page').forEach(p => p.classList.remove('active'));
  const pg = document.getElementById('page-' + n);
  if (pg) pg.classList.add('active');
  S.currentPage = n;

  // Progress bar
  const total = 7;
  const labels = ['','Symptom Input','Confirm & Age','Associated Symptoms','Symptom Cluster','Patient Details','Vital Signs','Summary'];
  const pct = Math.round((Math.min(n,7) / total) * 100);
  const fill = document.getElementById('prog-fill');
  if (fill) fill.style.width = pct + '%';
  const cur = document.getElementById('prog-cur');
  if (cur) cur.textContent = Math.min(n, 7);
  const lbl = document.getElementById('prog-label');
  if (lbl) lbl.textContent = labels[Math.min(n,7)] || '';

  // Hide progress on payment/sub
  const pw = document.getElementById('triage-progress-wrap');
  if (pw) pw.style.display = (n >= 8) ? 'none' : '';

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function detectKeyword(text) {
  const lower = text.toLowerCase();
  return TRIGGER_KEYWORDS.find(kw => lower.includes(kw)) || '';
}

function showToast(msg) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 3000);
}

function esc(s) {
  return s ? String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') : '';
}

/* ══════════════════════════════════════
   LAUNCH TRIAGE
══════════════════════════════════════ */
function startTriage() {
  const landing = document.getElementById('landing');
  const app     = document.getElementById('triage-app');
  if (landing) landing.style.display = 'none';
  if (app) { app.classList.add('active'); }
  showPage(1);
  document.getElementById('symptom-input')?.focus();
}

/* ══════════════════════════════════════
   PAGE 1 — Symptom Input
══════════════════════════════════════ */
function initP1() {
  const nextBtn = document.getElementById('p1-next');
  nextBtn?.addEventListener('click', () => {
    const val = document.getElementById('symptom-input')?.value.trim() || '';
    if (!val) { show('p1-err'); return; }
    hide('p1-err');
    S.symptomRaw = val;
    S.keyword    = detectKeyword(val);
    goToP2();
  });
  document.getElementById('symptom-input')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') nextBtn?.click();
  });

  // Voice input
  initVoice();
}

function goToP2() {
  const kwEl = document.getElementById('kw-text');
  if (kwEl) kwEl.textContent = S.keyword || S.symptomRaw;
  const conf = document.getElementById('symptom-confirm');
  if (conf) conf.value = S.symptomRaw;
  showPage(2);
}

/* ── Voice ── */
function initVoice() {
  const btn = document.getElementById('voice-btn');
  const status = document.getElementById('voice-status');
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    if (status) status.textContent = 'Voice input not supported in this browser';
    btn?.setAttribute('disabled', '');
    return;
  }
  const rec = new SpeechRecognition();
  rec.continuous = false;
  rec.interimResults = false;
  let listening = false;

  btn?.addEventListener('click', () => {
    if (listening) { rec.stop(); return; }
    const lang = document.getElementById('triage-lang')?.value || 'en';
    const langMap = { en:'en-IN', ta:'ta-IN', hi:'hi-IN' };
    rec.lang = langMap[lang] || 'en-IN';
    rec.start();
  });

  rec.onstart = () => {
    listening = true;
    btn?.classList.add('listening');
    if (status) status.textContent = '🔴 Listening… speak now';
  };
  rec.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    const inp = document.getElementById('symptom-input');
    if (inp) inp.value = transcript;
    if (status) status.textContent = '✓ Captured: ' + transcript;
  };
  rec.onerror = () => {
    if (status) status.textContent = 'Mic error — please type instead';
  };
  rec.onend = () => {
    listening = false;
    btn?.classList.remove('listening');
  };
}

/* ══════════════════════════════════════
   PAGE 2 — Confirm + Age + Gender + LMP
══════════════════════════════════════ */
function initP2() {
  // Gender pills
  document.querySelectorAll('#gender-row .radio-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#gender-row .radio-pill').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      S.gender = btn.dataset.g;
      checkLmpVisibility();
    });
  });

  document.getElementById('age-in')?.addEventListener('input', checkLmpVisibility);

  document.getElementById('p2-back')?.addEventListener('click', () => showPage(1));
  document.getElementById('p2-next')?.addEventListener('click', () => {
    const sym  = document.getElementById('symptom-confirm')?.value.trim() || '';
    const age  = parseInt(document.getElementById('age-in')?.value) || 0;
    const err  = document.getElementById('p2-err');
    const errMsg = document.getElementById('p2-err-msg');

    if (!sym) {
      if (errMsg) errMsg.textContent = 'Please confirm your symptom.';
      show('p2-err'); return;
    }
    if (!age || age <= 0) {
      if (errMsg) errMsg.textContent = 'Please enter a valid age.';
      show('p2-err'); return;
    }
    if (!S.gender) {
      if (errMsg) errMsg.textContent = 'Please select your gender.';
      show('p2-err'); return;
    }
    // LMP check
    if (S.gender === 'female' && age >= 15 && age <= 45) {
      const lmp = document.getElementById('lmp-in')?.value;
      if (!lmp) {
        if (errMsg) errMsg.textContent = 'Last menstrual period is required.';
        show('p2-err'); return;
      }
      S.lmp = lmp;
    }

    hide('p2-err');
    S.symptomRaw = sym;
    S.keyword    = detectKeyword(sym);
    S.age        = age;

    buildAssocPage();
    showPage(3);
  });
}

function checkLmpVisibility() {
  const age = parseInt(document.getElementById('age-in')?.value) || 0;
  const lmpWrap = document.getElementById('lmp-wrap');
  if (!lmpWrap) return;
  if (S.gender === 'female' && age >= 15 && age <= 45) lmpWrap.classList.remove('hidden');
  else lmpWrap.classList.add('hidden');
}

/* ══════════════════════════════════════
   PAGE 3 — Associated Symptoms
══════════════════════════════════════ */
function buildAssocPage() {
  const group = document.getElementById('assoc-group');
  if (!group) return;
  const options = ASSOC_MAP[S.keyword] || ASSOC_MAP.default;
  group.innerHTML = options.map(sym => `
    <label class="check-item">
      <input type="checkbox" value="${esc(sym)}" />
      ${esc(sym)}
    </label>`).join('');

  group.querySelectorAll('.check-item').forEach(item => {
    item.addEventListener('click', () => item.classList.toggle('checked'));
  });
}

function initP3() {
  document.getElementById('p3-back')?.addEventListener('click', () => showPage(2));
  document.getElementById('p3-next')?.addEventListener('click', () => {
    // Collect selected
    S.assocSelected = [...document.querySelectorAll('#assoc-group input:checked')].map(c => c.value);

    // Check red flags
    if (checkRedFlags()) {
      showRedFlagScreen();
    } else {
      buildClusterPage();
      showPage(4);
    }
  });
}

/* ══════════════════════════════════════
   RED FLAG ENGINE
══════════════════════════════════════ */
function checkRedFlags() {
  const sym   = S.keyword.toLowerCase();
  const assoc = S.assocSelected;

  // Age flags
  if (S.age < 5 || S.age > 60) {
    // Don't auto-red just for age, but flag it
  }

  for (const rule of RED_FLAG_RULES) {
    if (sym.includes(rule.sym) || S.symptomRaw.toLowerCase().includes(rule.sym)) {
      const matched = rule.assoc.filter(a => assoc.includes(a));
      const threshold = rule.single ? 1 : 2;
      if (matched.length >= threshold) {
        S.redFlag = true;
        S.redFlagLabel = rule.label;
        S.riskLevel = 'red';
        return true;
      }
    }
  }

  // Severity escalation by age
  if (S.age < 5 || S.age > 60) {
    if (assoc.length >= 2) { S.riskLevel = 'yellow'; }
    else { S.riskLevel = 'yellow'; }
  } else if (assoc.length >= 3) {
    S.riskLevel = 'yellow';
  }

  return false;
}

function showRedFlagScreen() {
  const overlay = document.getElementById('redflag-overlay');
  const flagText = document.getElementById('rf-flag-text');
  if (flagText) flagText.textContent = 'Detected: ' + S.redFlagLabel;
  overlay?.classList.remove('hidden');
}

/* ══════════════════════════════════════
   PAGE 4 — Cluster
══════════════════════════════════════ */
function buildClusterPage() {
  const cluster = CLUSTERS[S.keyword] || CLUSTERS.default;
  S.cluster = cluster;

  // Second-pass risk: if cluster is Cardiac/Neurological + age flag
  if ((cluster.name === 'Cardiac' || cluster.name === 'Neurological') && (S.age > 60 || S.age < 5)) {
    S.riskLevel = 'red';
  }

  const disp = document.getElementById('cluster-display');
  if (disp) {
    disp.innerHTML = `
      <div style="display:flex;align-items:center;gap:1rem;background:var(--forest-xlt);border:1px solid rgba(23,79,64,.15);border-radius:var(--r-lg);padding:1.25rem 1.4rem">
        <div style="font-size:2.5rem">${cluster.icon}</div>
        <div>
          <div style="font-family:var(--f-display);font-size:1.15rem;font-weight:600;color:var(--ink)">${cluster.name} Pattern</div>
          <div style="font-size:.82rem;color:var(--ink-lt);margin-top:.15rem">${cluster.desc}</div>
        </div>
      </div>`;
  }

  const note = document.getElementById('cluster-risk-note');
  if (note) {
    if (S.riskLevel === 'yellow') {
      note.innerHTML = `<div class="risk-alert yellow"><span class="ri">⚠️</span><div><strong>Elevated Risk</strong> — Your combination of symptoms suggests a need for priority review.</div></div>`;
    } else if (S.riskLevel === 'green') {
      note.innerHTML = `<div class="risk-alert green"><span class="ri">✅</span><div>Your symptoms appear non-urgent. A doctor will review your case in the normal queue.</div></div>`;
    }
  }
}

function initP4() {
  document.getElementById('p4-back')?.addEventListener('click', () => showPage(3));
  document.getElementById('p4-next')?.addEventListener('click', () => showPage(5));
}

/* ══════════════════════════════════════
   PAGE 5 — Patient Details
══════════════════════════════════════ */
function initP5() {
  // Condition cards
  document.querySelectorAll('#cond-grid .cond-card').forEach(card => {
    card.addEventListener('click', () => card.classList.toggle('selected'));
  });

  // File upload
  document.getElementById('records-file')?.addEventListener('change', function() {
    const preview = document.getElementById('upload-preview');
    if (this.files[0]) {
      S.uploadFile = this.files[0];
      if (preview) preview.textContent = '✓ ' + this.files[0].name;
    }
  });

  document.getElementById('p5-back')?.addEventListener('click', () => showPage(4));
  document.getElementById('p5-next')?.addEventListener('click', () => {
    S.name  = document.getElementById('pt-name')?.value.trim() || '';
    S.phone = document.getElementById('pt-phone')?.value.trim() || '';
    S.conditions = [...document.querySelectorAll('#cond-grid input:checked')].map(c => c.value);

    // Red → skip vitals
    if (S.riskLevel === 'red') {
      buildSummaryPage();
      showPage(7);
    } else {
      showPage(6);
    }
  });
}

/* ══════════════════════════════════════
   PAGE 6 — Vitals
══════════════════════════════════════ */
function initP6() {
  document.getElementById('p6-back')?.addEventListener('click', () => showPage(5));
  document.getElementById('p6-next')?.addEventListener('click', () => {
    S.vitals.bp   = document.getElementById('v-bp')?.value.trim() || '';
    S.vitals.spo2 = document.getElementById('v-spo2')?.value.trim() || '';
    S.vitals.temp = document.getElementById('v-temp')?.value.trim() || '';
    buildSummaryPage();
    showPage(7);
  });
}

/* ══════════════════════════════════════
   PAGE 7 — Summary + Doctor Waiting
══════════════════════════════════════ */
function buildSummaryPage() {
  // Triage badge
  const badgeWrap = document.getElementById('triage-badge-wrap');
  const badgeMap = {
    red:    { emoji:'🔴', label:'Red — Immediate Review',       cls:'red'    },
    yellow: { emoji:'🟡', label:'Yellow — Priority Review (~5 min)', cls:'yellow' },
    green:  { emoji:'🟢', label:'Green — Normal Queue',         cls:'green'  },
  };
  const bd = badgeMap[S.riskLevel];
  if (badgeWrap && bd) {
    badgeWrap.innerHTML = `<div class="triage-badge ${bd.cls}">${bd.emoji} ${bd.label}</div>`;
  }

  // Summary table
  const condText = S.conditions.length ? S.conditions.join(', ') : 'None reported';
  const vitalsText = [
    S.vitals.bp   && `BP: ${S.vitals.bp}`,
    S.vitals.spo2 && `SpO₂: ${S.vitals.spo2}%`,
    S.vitals.temp && `Temp: ${S.vitals.temp}°C`,
  ].filter(Boolean).join(' · ') || 'Not recorded';

  const ageFlags = [];
  if (S.age < 5)  ageFlags.push('Age < 5 (high risk)');
  if (S.age > 60) ageFlags.push('Age > 60 (high risk)');

  const rows = [
    ['Primary Symptom', S.symptomRaw],
    ['Associated Symptoms', S.assocSelected.length ? S.assocSelected.join(', ') : 'None'],
    ['Age / Gender', `${S.age} yrs / ${S.gender}`],
    S.lmp ? ['Last Menstrual Period', S.lmp] : null,
    ['Medical History', condText],
    ['Vital Signs', vitalsText],
    ageFlags.length ? ['Risk Flags', ageFlags.join(', ')] : null,
  ].filter(Boolean);

  const table = document.getElementById('sum-table');
  if (table) {
    table.innerHTML = rows.map(([k,v]) => `
      <div class="sum-row">
        <div class="sum-key">${k}</div>
        <div class="sum-val">${esc(v)}</div>
      </div>`).join('');
  }

  // Guidance
  const guidance = GUIDANCE[S.keyword] || GUIDANCE.default;
  const gList = document.getElementById('guidance-list');
  if (gList) {
    gList.innerHTML = guidance.map(g => `<li>${esc(g)}</li>`).join('');
  }

  // Doctor assignment
  const cluster = S.cluster || CLUSTERS.default;
  const docKey  = S.riskLevel === 'red' ? 'Emergency' : (cluster.name || 'General');
  S.doctor = DOCTORS[docKey] || DOCTORS.default;

  document.getElementById('doc-avatar').textContent   = S.doctor.icon;
  document.getElementById('doc-name-display').textContent = S.doctor.name;
  document.getElementById('doc-spec-display').textContent = S.doctor.spec;

  // ETA chip
  const etaWrap = document.getElementById('eta-chip-wrap');
  const etaMap = { red:'Immediate','yellow':'~5 minutes','green':'~10–15 minutes' };
  if (etaWrap) {
    etaWrap.innerHTML = `<div class="eta-chip">⏱ Estimated wait: <strong>${etaMap[S.riskLevel]}</strong></div>`;
  }

  // Queue status for non-red
  if (S.riskLevel !== 'red') {
    const qs = document.getElementById('queue-status');
    if (qs) qs.style.display = 'flex';
  }

  // Show Zoom button after delay
  setTimeout(() => {
    const zBtn = document.getElementById('zoom-btn');
    if (zBtn) {
      zBtn.classList.remove('hidden');
      zBtn.addEventListener('click', () => {
        window.open('https://zoom.us/join', '_blank');
        showToast('Opening Zoom — please join the call.');
      });
    }
    // Update status
    const cl = document.getElementById('connect-label');
    if (cl) cl.textContent = 'Doctor is ready — join the call';
    const cd = document.querySelector('.connecting-dot');
    if (cd) cd.style.background = 'var(--green)';
  }, S.riskLevel === 'red' ? 3000 : 8000);
}

function initP7() {
  document.getElementById('p7-back')?.addEventListener('click', () => {
    if (S.riskLevel === 'red') showPage(5);
    else showPage(6);
  });

  document.getElementById('p7-submit')?.addEventListener('click', () => {
    saveCase();
    showToast('Case submitted successfully ✓');
    // Show payment after submit
    setTimeout(() => showPage(8), 800);
    // Hide step-nav on P7 after submission
    const nav = document.querySelector('#page-7 .step-nav');
    if (nav) nav.style.display = 'none';
  });
}

/* ══════════════════════════════════════
   PAGE 8 — Payment
══════════════════════════════════════ */
window.selectPlan = function(card) {
  document.querySelectorAll('.pay-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
};

function initP8() {
  document.getElementById('pay-btn')?.addEventListener('click', () => {
    showToast('Redirecting to payment gateway…');
    setTimeout(() => showPage(9), 1200);
  });
}

/* ══════════════════════════════════════
   SAVE TO LOCALSTORAGE
══════════════════════════════════════ */
function saveCase() {
  const rec = {
    id:         Date.now().toString(),
    name:       S.name,
    age:        S.age,
    gender:     S.gender,
    phone:      S.phone,
    lmp:        S.lmp,
    symptom:    S.symptomRaw,
    keyword:    S.keyword,
    assocSymptoms: S.assocSelected,
    riskLevel:  S.riskLevel,
    redFlag:    S.redFlag,
    redFlagLabel: S.redFlagLabel,
    cluster:    S.cluster?.name || '',
    conditions: S.conditions,
    vitals:     S.vitals,
    doctor:     S.doctor,
    createdAt:  new Date().toISOString(),
  };
  const all = JSON.parse(localStorage.getItem('evarya_cases') || '[]');
  all.push(rec);
  localStorage.setItem('evarya_cases', JSON.stringify(all));
}

/* ══════════════════════════════════════
   RED FLAG OVERLAY BUTTON
══════════════════════════════════════ */
function initRedFlagOverlay() {
  document.getElementById('rf-continue')?.addEventListener('click', () => {
    hide('redflag-overlay');
    // Skip P4, P5 → show summary with RED
    buildSummaryPage();
    showPage(7);
  });
}

/* ══════════════════════════════════════
   HEADER SCROLL + MOBILE NAV
══════════════════════════════════════ */
function initHeader() {
  const hdr = document.getElementById('site-header');
  window.addEventListener('scroll', () => {
    hdr?.classList.toggle('scrolled', window.scrollY > 20);
  }, { passive: true });

  const ham = document.getElementById('nav-hamburger');
  const nav = document.getElementById('main-nav');
  ham?.addEventListener('click', () => {
    ham.classList.toggle('open');
    nav?.classList.toggle('open');
  });
}

/* ══════════════════════════════════════
   CONTACT FORM
══════════════════════════════════════ */
function initContact() {
  const ta = document.getElementById('contact-msg');
  ta?.addEventListener('focus', () => { ta.style.borderColor='var(--forest)'; ta.style.boxShadow='0 0 0 3px rgba(23,79,64,.1)'; });
  ta?.addEventListener('blur',  () => { ta.style.borderColor='var(--border)'; ta.style.boxShadow='none'; });

  document.getElementById('contact-submit')?.addEventListener('click', function() {
    this.textContent = 'Message Sent ✓';
    this.disabled = true;
    this.style.background = 'var(--green)';
    this.style.borderColor = 'var(--green)';
  });
}

/* ══════════════════════════════════════
   INIT
══════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initContact();
  initP1();
  initP2();
  initP3();
  initP4();
  initP5();
  initP6();
  initP7();
  initP8();
  initRedFlagOverlay();

  // CTA buttons
  const launch = () => startTriage();
  document.getElementById('cta-main')?.addEventListener('click', launch);
  document.getElementById('header-cta')?.addEventListener('click', launch);

  // Condition card toggle
  document.querySelectorAll('#cond-grid .cond-card').forEach(c => {
    c.addEventListener('click', () => c.classList.toggle('selected'));
  });

  // Mobile nav close on link click
  document.querySelectorAll('.main-nav a').forEach(a => {
    a.addEventListener('click', () => {
      document.getElementById('main-nav')?.classList.remove('open');
      document.getElementById('nav-hamburger')?.classList.remove('open');
    });
  });
});
