/* =========================================================

   ========================================================= */

const ROLES = {
  customer: {
    label:        'Customer Portal',
    accountLabel: 'Customer Account',
    signinSub:    'Sign in to your customer account',
    signupSub:    'Join FuelGo as a customer',
    icon:         'fa-user',
    canRegister:  true,
    loginUrl:     '/accounts/login/',
    registerUrl:  '/accounts/register/',
    slideFeatures: ['Instant Delivery', 'Live Tracking', 'Secure & Verified'],
    slideIcons:    ['fa-bolt', 'fa-map-location-dot', 'fa-shield-check'],
  },
  provider: {
    label:        'Station Owner Portal',
    accountLabel: 'Station Owner Account',
    signinSub:    'Sign in to manage your fuel station',
    signupSub:    'Register your fuel station on FuelGo',
    icon:         'fa-gas-pump',
    canRegister:  true,
    loginUrl:     '/accounts/login/',
    registerUrl:  '/accounts/register/',
    slideFeatures: ['Manage Orders', 'Track Stock', 'AI Demand Forecast'],
    slideIcons:    ['fa-receipt', 'fa-boxes-stacked', 'fa-brain'],
  },
  driver: {
    label:        'Driver Portal',
    accountLabel: 'Driver Account',
    signinSub:    'Sign in to view your deliveries',
    signupSub:    'Register as a FuelGo delivery driver',
    icon:         'fa-id-badge',
    canRegister:  true,
    loginUrl:     '/accounts/login/',
    registerUrl:  '/accounts/register/',
    slideFeatures: ['View Assignments', 'Track Earnings', 'Live Navigation'],
    slideIcons:    ['fa-clipboard-list', 'fa-coins', 'fa-map-location-dot'],
  },
  admin: {
    label:        'Admin Portal',
    accountLabel: 'Administrator Account',
    signinSub:    'Sign in to the system admin panel',
    signupSub:    '',
    icon:         'fa-shield-halved',
    canRegister:  false,
    loginUrl:     '/accounts/login/',
    registerUrl:  null,
    slideFeatures: [],
    slideIcons:    [],
  },
};

let currentRole = 'customer';
let isSignupMode = false;

/* ---- Switch active role ---- */
function switchRole(role) {
  currentRole = role;
  const cfg = ROLES[role];

  // Update tab active state
  document.querySelectorAll('.role-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.role === role);
  });

  // Update form actions to role-specific URLs
  const signinForm = document.getElementById('signinForm');
  const signupForm = document.getElementById('signupForm');
  if (signinForm) signinForm.action = cfg.loginUrl;
  if (signupForm && cfg.registerUrl) signupForm.action = cfg.registerUrl;

  // Update hidden role inputs
  document.getElementById('signinRoleInput').value = role;
  document.getElementById('signupRoleInput').value = role;

  // Update subtitles
  document.getElementById('signinSubtitle').textContent = cfg.signinSub;
  if (cfg.signupSub) document.getElementById('signupSubtitle').textContent = cfg.signupSub;

  // Update role badges
  const badgeHtml = `<i class="fas ${cfg.icon}"></i>`;
  document.getElementById('signinRoleBadge').innerHTML  = `${badgeHtml}<span>${cfg.label}</span>`;
  document.getElementById('signupRoleBadge').innerHTML  = `${badgeHtml}<span>${cfg.accountLabel}</span>`;

  // Provider extra fields (station map picker)
  const providerFields = document.getElementById('providerFields');
  if (providerFields) {
    providerFields.style.display = role === 'provider' ? 'block' : 'none';
  }

  // No-signup note for admin
  const noSignupNote = document.getElementById('noSignupNote');
  if (noSignupNote) {
    noSignupNote.style.display = cfg.canRegister ? 'none' : 'flex';
    if (!cfg.canRegister) {
      noSignupNote.innerHTML = `<i class="fas fa-info-circle text-orange"></i>
        Admin accounts are created by the system administrator only.`;
    }
  }

  // If role can't register and we're on signup, flip back
  if (!cfg.canRegister && isSignupMode) switchToSignin();

  // Update sliding panel features list
  updateSlideFeatures(cfg);
  animateBadges();
}

/* ---- Update slide panel features ---- */
function updateSlideFeatures(cfg) {
  ['slideStateA', 'slideStateB'].forEach(stateId => {
    const el = document.getElementById(stateId);
    if (!el) return;
    const featuresEl = el.querySelector('.slide-features');
    if (!featuresEl || !cfg.slideFeatures.length) return;
    featuresEl.innerHTML = cfg.slideFeatures.map((f, i) =>
      `<div class="sf-item"><i class="fas ${cfg.slideIcons[i] || 'fa-check'}"></i> ${f}</div>`
    ).join('');
  });
}

/* ---- Animate role badges ---- */
function animateBadges() {
  ['signinRoleBadge','signupRoleBadge'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.transform = 'scale(0.9)'; el.style.opacity = '0.5';
    setTimeout(() => { el.style.transition = 'all 0.3s ease'; el.style.transform = 'scale(1)'; el.style.opacity = '1'; }, 100);
  });
}

/* ---- Flip to signup ---- */
function switchToSignup() {
  const cfg = ROLES[currentRole];
  if (!cfg.canRegister) return;
  isSignupMode = true;
  document.getElementById('authContainer').classList.add('flipped');
  document.getElementById('slideStateA').style.display = 'none';
  document.getElementById('slideStateB').style.display = 'flex';
}

/* ---- Flip to signin ---- */
function switchToSignin() {
  isSignupMode = false;
  document.getElementById('authContainer').classList.remove('flipped');
  document.getElementById('slideStateA').style.display = 'flex';
  document.getElementById('slideStateB').style.display = 'none';
}

/* ---- Toggle password visibility ---- */
function togglePass(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon  = document.getElementById(iconId);
  if (!input || !icon) return;
  if (input.type === 'password') { input.type = 'text'; icon.classList.replace('fa-eye','fa-eye-slash'); }
  else                           { input.type = 'password'; icon.classList.replace('fa-eye-slash','fa-eye'); }
}

/* ---- Password strength ---- */
function checkStrength(value) {
  const fill  = document.getElementById('strengthFill');
  const label = document.getElementById('strengthLabel');
  if (!fill || !label) return;
  let score = 0;
  if (value.length >= 8) score++;
  if (/[A-Z]/.test(value)) score++;
  if (/[0-9]/.test(value)) score++;
  if (/[^A-Za-z0-9]/.test(value)) score++;
  if (value.length >= 12) score++;
  const levels = [
    { pct:'0%',   color:'transparent', text:'' },
    { pct:'25%',  color:'#ef4444',     text:'Weak' },
    { pct:'50%',  color:'#f97316',     text:'Fair' },
    { pct:'75%',  color:'#eab308',     text:'Good' },
    { pct:'90%',  color:'#22c55e',     text:'Strong' },
    { pct:'100%', color:'#16a34a',     text:'Very Strong' },
  ];
  const lvl = levels[Math.min(score,5)];
  fill.style.width = lvl.pct; fill.style.background = lvl.color;
  label.textContent = lvl.text ? `Password strength: ${lvl.text}` : '';
  label.setAttribute('style', lvl.color ? `color:${lvl.color}` : '');
}

/* ---- Password match ---- */
function checkMatch() {
  const pass    = document.getElementById('signupPass');
  const confirm = document.getElementById('confirmPass');
  const msg     = document.getElementById('matchMsg');
  if (!pass || !confirm || !msg) return;
  if (!confirm.value) { msg.textContent = ''; return; }
  if (pass.value === confirm.value) {
    msg.textContent = '✓ Passwords match'; msg.style.color = '#22c55e'; confirm.style.borderColor = '#22c55e';
  } else {
    msg.textContent = '✗ Passwords do not match'; msg.style.color = '#ef4444'; confirm.style.borderColor = '#ef4444';
  }
}

/* ---- Loading state ---- */
function setLoading(formId, btnId, loading) {
  const btn    = document.getElementById(btnId);
  const text   = btn?.querySelector('.btn-text');
  const loader = btn?.querySelector('.btn-loader');
  if (!btn) return;
  btn.disabled = loading;
  if (text)   text.style.display   = loading ? 'none' : 'flex';
  if (loader) loader.style.display = loading ? 'flex' : 'none';
}

/* ---- Provider registration validation ---- */
function validateProviderFields() {
  if (currentRole !== 'provider') return true;
  const stationName    = document.querySelector('[name="station_name"]')?.value?.trim();
  const stationAddress = document.getElementById('stationAddressInput')?.value?.trim();
  const stationLat     = document.getElementById('stationLat')?.value;
  const licenceNo      = document.querySelector('[name="license_no"]')?.value?.trim();

  if (!stationName) { showFormError('Please enter your station name.'); return false; }
  if (!stationAddress || !stationLat) { showFormError('Please pin your station location on the map.'); return false; }
  if (!licenceNo) { showFormError('Please enter your business licence number.'); return false; }
  return true;
}

function showFormError(msg) {
  let err = document.querySelector('.signup-form-error');
  if (!err) {
    err = document.createElement('div');
    err.className = 'signup-form-error';
    err.style.cssText = 'display:flex;align-items:center;gap:8px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#ef4444;padding:9px 14px;border-radius:8px;font-size:.83rem;margin-bottom:12px';
    document.getElementById('signupForm')?.prepend(err);
  }
  err.innerHTML = '<i class="fas fa-circle-xmark"></i> ' + msg;
  setTimeout(() => { err.style.display = 'none'; }, 4000);
}

/* ---- DOMContentLoaded ---- */
document.addEventListener('DOMContentLoaded', function () {

  // Set initial form actions
  const cfg = ROLES['customer'];
  const signinForm = document.getElementById('signinForm');
  const signupForm = document.getElementById('signupForm');
  if (signinForm) signinForm.action = cfg.loginUrl;
  if (signupForm) signupForm.action = cfg.registerUrl;

  // Signin submit
  if (signinForm) {
    signinForm.addEventListener('submit', function () {
      setLoading('signinForm', 'signinBtn', true);
    });
  }

  // Signup submit — validate first
  if (signupForm) {
    signupForm.addEventListener('submit', function (e) {
      // Password match guard
      const pass    = document.getElementById('signupPass');
      const confirm = document.getElementById('confirmPass');
      if (pass && confirm && pass.value !== confirm.value) {
        e.preventDefault();
        const msg = document.getElementById('matchMsg');
        if (msg) { msg.textContent = '✗ Passwords do not match'; msg.style.color = '#ef4444'; }
        confirm.focus();
        return;
      }
      // Provider fields guard
      if (!validateProviderFields()) { e.preventDefault(); return; }
      setLoading('signupForm', 'signupBtn', true);
    });
  }

  // Input focus colour fix
  document.querySelectorAll('.fg-field').forEach(field => {
    field.addEventListener('focus', () => {
      const icon = field.closest('.input-group-fg')?.querySelector('.ig-icon');
      if (icon) icon.style.color = 'var(--orange)';
    });
    field.addEventListener('blur', () => {
      const icon = field.closest('.input-group-fg')?.querySelector('.ig-icon');
      if (icon) icon.style.color = '';
    });
  });

  // Read URL params — ?role=driver&mode=signup
  const params = new URLSearchParams(window.location.search);
  const roleParam = params.get('role');
  const modeParam = params.get('mode');
  if (roleParam && ROLES[roleParam]) switchRole(roleParam);
  if (modeParam === 'signup') switchToSignup();
});
