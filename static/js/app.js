/**
 * Blog Platform — Shared Utilities v2
 * Toast notifications, skeleton screens, reading time,
 * auto-resize textarea, back-to-top, scroll tracking.
 */

// ── API helper ─────────────────────────────────────────────────────────────────
const api = {
  async request(method, url, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({ error: 'Invalid server response' }));
    return { ok: res.ok, status: res.status, data };
  },
  get:    (url)       => api.request('GET',    url),
  post:   (url, body) => api.request('POST',   url, body),
  put:    (url, body) => api.request('PUT',    url, body),
  delete: (url)       => api.request('DELETE', url),
};

// ── Global state ───────────────────────────────────────────────────────────────
const state = { user: null, loaded: false };

async function loadCurrentUser() {
  if (state.loaded) return state.user;
  const { ok, data } = await api.get('/api/me');
  if (ok) {
    state.user   = data.authenticated ? data.user : null;
    state.loaded = true;
  }
  return state.user;
}

// ── Toast notification system ──────────────────────────────────────────────────
function ensureToastContainer() {
  let el = document.getElementById('toast-container');
  if (!el) {
    el = document.createElement('div');
    el.id = 'toast-container';
    el.setAttribute('aria-live', 'polite');
    el.setAttribute('role', 'status');
    document.body.appendChild(el);
  }
  return el;
}

function showAlert(message, type = 'error') {
  const icons = { error: '⚠️', success: '✅', info: 'ℹ️' };
  const container = ensureToastContainer();

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || '📢'}</span>
    <span class="toast-msg">${message}</span>
    <button class="toast-close" aria-label="Dismiss">✕</button>
  `;

  const close = () => {
    toast.classList.add('removing');
    setTimeout(() => toast.remove(), 220);
  };
  toast.querySelector('.toast-close').addEventListener('click', close);
  container.appendChild(toast);
  setTimeout(close, type === 'error' ? 6000 : 4000);
}

// ── Date formatting ────────────────────────────────────────────────────────────
function formatDate(iso) {
  const d    = new Date(iso);
  const now  = new Date();
  const diff = (now - d) / 1000;
  if (diff < 60)     return 'just now';
  if (diff < 3600)   return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400)  return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// ── Reading time ───────────────────────────────────────────────────────────────
function readingTime(text) {
  const words = text.trim().split(/\s+/).length;
  const mins  = Math.max(1, Math.ceil(words / 200));
  return `${mins} min read`;
}

// ── Word count ─────────────────────────────────────────────────────────────────
function wordCount(text) {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}

// ── Escape HTML ────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ── Avatar HTML ────────────────────────────────────────────────────────────────
function avatarHtml(username, cls = '') {
  const letter = (username || '?')[0].toUpperCase();
  return `<span class="avatar ${cls}" data-letter="${letter}" aria-hidden="true">${letter}</span>`;
}

// ── Skeleton card HTML ─────────────────────────────────────────────────────────
function skeletonCards(n = 3) {
  return Array.from({ length: n }, () => `
    <div class="skeleton-card">
      <div class="skeleton sk-line sk-title mb-2"></div>
      <div class="skeleton sk-line sk-sm mb-2"></div>
      <div class="skeleton sk-block mb-2"></div>
      <div class="skeleton sk-line sk-xs"></div>
    </div>`
  ).join('');
}

// ── Confirm modal ──────────────────────────────────────────────────────────────
function confirmModal(title, message, dangerLabel = 'Delete') {
  return new Promise((resolve) => {
    const backdrop = document.getElementById('confirm-modal');
    if (!backdrop) { resolve(window.confirm(message)); return; }

    document.getElementById('confirm-title').textContent = title;
    document.getElementById('confirm-msg').textContent   = message;
    const okBtn = document.getElementById('confirm-ok');
    okBtn.textContent = dangerLabel;
    backdrop.classList.add('open');

    const onConfirm = () => { cleanup(); resolve(true); };
    const onCancel  = () => { cleanup(); resolve(false); };

    okBtn.addEventListener('click', onConfirm, { once: true });
    document.getElementById('confirm-cancel').addEventListener('click', onCancel, { once: true });
    backdrop.addEventListener('click', (e) => { if (e.target === backdrop) onCancel(); }, { once: true });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') onCancel(); }, { once: true });

    function cleanup() { backdrop.classList.remove('open'); }
  });
}

// ── Navbar rendering ───────────────────────────────────────────────────────────
function renderNavbar(user) {
  const navLinks = document.getElementById('nav-links');
  if (!navLinks) return;
  if (user) {
    navLinks.innerHTML = `
      <span class="nav-user">
        ${avatarHtml(user.username)}
        <strong>${escapeHtml(user.username)}</strong>
      </span>
      <a href="/create" class="btn btn-primary btn-sm">✏️ Write</a>
      <a href="/logout" class="btn btn-ghost btn-sm">Logout</a>
    `;
  } else {
    navLinks.innerHTML = `
      <a href="/login"    class="btn btn-ghost   btn-sm">Login</a>
      <a href="/register" class="btn btn-primary btn-sm">Sign Up →</a>
    `;
  }
}

// ── Button loading state ───────────────────────────────────────────────────────
function setButtonLoading(btn, loading) {
  if (loading) {
    btn.dataset.originalHtml = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> Loading…`;
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.originalHtml || 'Submit';
    btn.disabled  = false;
  }
}

// ── Char counter (inline) ──────────────────────────────────────────────────────
function addCharCounter(textarea, counterEl, max) {
  const update = () => {
    const len = textarea.value.length;
    counterEl.textContent = `${len} / ${max}`;
    counterEl.className = 'char-count' + (len > max ? ' over' : len > max * .85 ? ' warn' : '');
  };
  textarea.addEventListener('input', update);
  update();
}

// ── Auto-resize textarea ───────────────────────────────────────────────────────
function autoResize(textarea) {
  const resize = () => {
    textarea.style.height = 'auto';
    textarea.style.height = Math.max(textarea.scrollHeight, 120) + 'px';
  };
  textarea.addEventListener('input', resize);
  resize();
}

// ── Navbar scroll shadow ───────────────────────────────────────────────────────
function initNavbarScroll() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;
  const onScroll = () => navbar.classList.toggle('scrolled', window.scrollY > 10);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

// ── Back-to-top button ─────────────────────────────────────────────────────────
function initBackToTop() {
  const btn = document.getElementById('back-to-top');
  if (!btn) return;
  window.addEventListener('scroll', () => btn.classList.toggle('visible', window.scrollY > 400), { passive: true });
  btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

// ── Reading progress bar ───────────────────────────────────────────────────────
function initReadingProgress() {
  const bar = document.getElementById('reading-progress');
  if (!bar) return;
  window.addEventListener('scroll', () => {
    const docH = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    bar.style.width = docH > 0 ? `${(window.scrollY / docH) * 100}%` : '0%';
  }, { passive: true });
}

// ── LocalStorage autosave ──────────────────────────────────────────────────────
function initAutosave(key, titleEl, bodyEl, indicatorEl) {
  const SAVE_KEY = `blog_draft_${key}`;
  const saved = localStorage.getItem(SAVE_KEY);
  if (saved) {
    try {
      const { title, body } = JSON.parse(saved);
      if (title && !titleEl.value) titleEl.value = title;
      if (body  && !bodyEl.value)  bodyEl.value  = body;
      titleEl.dispatchEvent(new Event('input'));
      bodyEl.dispatchEvent(new Event('input'));
    } catch {}
  }

  let saveTimer;
  const save = () => {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      localStorage.setItem(SAVE_KEY, JSON.stringify({ title: titleEl.value, body: bodyEl.value }));
      if (indicatorEl) {
        indicatorEl.classList.add('visible');
        setTimeout(() => indicatorEl.classList.remove('visible'), 2000);
      }
    }, 800);
  };

  titleEl.addEventListener('input', save);
  bodyEl.addEventListener('input', save);

  return () => localStorage.removeItem(SAVE_KEY);
}

// ── DOMContentLoaded init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  initNavbarScroll();
  initBackToTop();
  initReadingProgress();
  const user = await loadCurrentUser();
  renderNavbar(user);
});
