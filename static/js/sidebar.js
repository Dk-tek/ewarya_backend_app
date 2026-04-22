/* ═══════════════════════════════════════════════
   sidebar.js — injects the shared sidebar into
   every page and handles active-link highlighting
═══════════════════════════════════════════════ */

(function () {

  /* ── Sidebar HTML ── */
  const html = `
  <aside class="sidebar" id="sidebar">
    <div class="sidebar-logo">
      <div class="sidebar-logo-icon">🏥</div>
      <div>
        <h2>Evaryahealth</h2>
        <p>Unified Admin Panel</p>
      </div>
    </div>

    <div class="nav-label">Admin</div>
    <a class="nav-item" href="/dashboard/" data-page="dashboard">
      <span class="nav-icon">📊</span> Dashboard
    </a>
    <a class="nav-item" href="/consultations/" data-page="consultations">
      <span class="nav-icon">📋</span> Consultations
    </a>
    <a class="nav-item" href="/doctors/" data-page="doctors">
      <span class="nav-icon">👨‍⚕️</span> Doctors
    </a>
    <a class="nav-item" href="/patients/" data-page="patients">
      <span class="nav-icon">👤</span> Patients
    </a>
    <a class="nav-item" href="/analytics/" data-page="analytics">
      <span class="nav-icon">📈</span> Analytics
    </a>
    <a class="nav-item" href="/settings/" data-page="settings">
      <span class="nav-icon">⚙️</span> Settings
    </a>

    <div class="sidebar-divider"></div>
    <div class="nav-label">Health Console</div>

    <a class="nav-item" href="/hc-profile/" data-page="hc-profile">
      <span class="nav-icon">🪪</span> Profile
    </a>
    <a class="nav-item" href="/hc-family/" data-page="hc-family">
      <span class="nav-icon">👨‍👩‍👧</span> Family Data
    </a>
    <a class="nav-item" href="/hc-builder/" data-page="hc-builder">
      <span class="nav-icon">🛠️</span> Triage Builder
    </a>
    <a class="nav-item" href="/hc-triage/" data-page="hc-triage">
      <span class="nav-icon">🩺</span> Triage Test
    </a>

    <div class="sidebar-divider"></div>

    <!-- Session pill (HC token display) -->
    <div class="session-pill" id="sb-session-pill">
      <strong>HC Session</strong>
      <span id="sb-session-state">No token saved.</span>
      <button class="clear-token-btn" onclick="sbClearToken()">Clear token</button>
    </div>

    <div class="sidebar-footer">
      <button class="logout-btn" onclick="sbLogout()">
        <span>🚪</span> Admin Logout
      </button>
    </div>
  </aside>`;

  /* ── Inject ── */
  document.body.insertAdjacentHTML('afterbegin', html);

  /* ── Mark active link ── */
  const page = document.documentElement.dataset.page || document.body.dataset.page || '';
  const protectedPages = ['hc-profile', 'hc-family', 'hc-builder', 'hc-triage'];
  if (protectedPages.includes(page) && !localStorage.getItem('evarya_access')) {
    fetch('/api/auth/session/', { credentials: 'same-origin' })
      .then(response => response.ok ? response.json() : Promise.reject())
      .then(data => {
        if (data?.tokens?.access) {
          localStorage.setItem('evarya_access', data.tokens.access);
          localStorage.setItem('evarya_refresh', data.tokens.refresh || '');
          if (data.user) localStorage.setItem('evarya_user', JSON.stringify(data.user));
          sbRefreshToken();
        } else {
          window.location.href = '/login/';
        }
      })
      .catch(() => { window.location.href = '/login/'; });
  }

  document.querySelectorAll('.nav-item[data-page]').forEach(el => {
    if (el.dataset.page === page) el.classList.add('active');
  });

  /* ── HC token display ── */
  function sbRefreshToken() {
    const access = localStorage.getItem('evarya_access') || '';
    const user   = (() => { try { return JSON.parse(localStorage.getItem('evarya_user') || 'null'); } catch { return null; } })();
    const el     = document.getElementById('sb-session-state');
    if (el) el.textContent = access
      ? `Token saved.${user ? ' ' + user.username : ''}`
      : 'No token saved.';
  }
  sbRefreshToken();

  window.sbClearToken = function () {
    ['evarya_access','evarya_refresh','evarya_user'].forEach(k => localStorage.removeItem(k));
    sbRefreshToken();
  };

  /* ── Admin logout ── */
  window.sbLogout = function () {
    if (confirm('Log out of admin?')) {
      window.location.href = '/login/';
    }
  };

  /* expose refresh for HC pages */
  window.sbRefreshToken = sbRefreshToken;

})();

