/* =========================================================
   FuelGo – Auth Page JavaScript
   Handles: role switching, panel flip, password strength,
            match check, password toggle, form loading states
   ========================================================= */

/* ---- Role configuration ---- */
const ROLES = {
  customer: {
    label:       'Customer Portal',
    accountLabel:'Customer Account',
    signinSub:   'Sign in to your customer account',
    signupSub:   'Join FuelGo as a customer',
    icon:        'fa-user',
    canRegister: true,
  },
  provider: {
    label:       'Station Owner Portal',
    accountLabel:'Station Owner Account',
    signinSub:   'Sign in to manage your fuel station',
    signupSub:   'Register your fuel station',
    icon:        'fa-gas-pump',
    canRegister: true,
  },
  driver: {
    label:'Driver Portal',
    accountLabel:'Driver Account',
    signinSub:'Sign in to view your deliveries',
    signupSub:'Register as a FuelGo Driver',
    icon:'fa-id-badge',
    canRegister:true,
  },
  admin: {
    label:       'Admin Portal',
    accountLabel:'Administrator Account',
    signinSub:   'Sign in to the system admin panel',
    signupSub:   '',
    icon:        'fa-shield-halved',
    canRegister: false,
  },
};

let currentRole = 'customer';
let isSignupMode = false;

/* ---- Switch active role ---- */
function switchRole(role) {
  currentRole = role;
  const cfg = ROLES[role];

  /* Update tab active state */
  document.querySelectorAll('.role-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.role === role);
  });

  /* Update hidden inputs */
  document.getElementById('signinRoleInput').value = role;
  document.getElementById('signupRoleInput').value = role;

  /* Update subtitles */
  document.getElementById('signinSubtitle').textContent = cfg.signinSub;
  if (cfg.signupSub) document.getElementById('signupSubtitle').textContent = cfg.signupSub;

  /* Update role badges */
  const badgeIcon = `<i class="fas ${cfg.icon}"></i>`;
  document.getElementById('signinRoleBadge').innerHTML  = `${badgeIcon}<span>${cfg.label}</span>`;
  document.getElementById('signupRoleBadge').innerHTML  = `${badgeIcon}<span>${cfg.accountLabel}</span>`;

  /* Show / hide provider extra fields */
 const providerFields = document.getElementById('providerFields');
  const driverFields = document.getElementById('driverFields');

  if (providerFields) {
      providerFields.style.display =
          role === 'provider' ? 'block' : 'none';
  }

  if (driverFields) {
      driverFields.style.display =
          role === 'driver' ? 'block' : 'none';
  }

  /* Show / hide "no signup" note on sign-in panel */
  const noSignupNote = document.getElementById('noSignupNote');
  if (noSignupNote) {
    noSignupNote.style.display = cfg.canRegister ? 'none' : 'flex';
  }

  /* If current role can't register, hide the Create Account button
     in the sliding panel and switch back to signin if on signup */
  const slideStateA = document.getElementById('slideStateA');
  const slideStateB = document.getElementById('slideStateB');
  if (!cfg.canRegister && isSignupMode) {
    switchToSignin();
  }

  /* Animate badge */
  animateBadges();
}

/* ---- Animate role badges ---- */
function animateBadges() {
  ['signinRoleBadge','signupRoleBadge'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.transform = 'scale(0.92)';
    el.style.opacity   = '0.5';
    setTimeout(() => {
      el.style.transition = 'all 0.3s ease';
      el.style.transform  = 'scale(1)';
      el.style.opacity    = '1';
    }, 120);
  });
}

/* ---- Flip to signup ---- */
function switchToSignup() {
  const cfg = ROLES[currentRole];
  if (!cfg.canRegister) return; // guard

  isSignupMode = true;
  const container = document.getElementById('authContainer');
  container.classList.add('flipped');

  /* Swap slide panel content */
  document.getElementById('slideStateA').style.display = 'none';
  document.getElementById('slideStateB').style.display = 'flex';
}

/* ---- Flip to signin ---- */
function switchToSignin() {
  isSignupMode = false;
  const container = document.getElementById('authContainer');
  container.classList.remove('flipped');

  /* Swap slide panel content */
  document.getElementById('slideStateA').style.display = 'flex';
  document.getElementById('slideStateB').style.display = 'none';
}

/* ---- Toggle password visibility ---- */
function togglePass(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon  = document.getElementById(iconId);
  if (!input || !icon) return;

  if (input.type === 'password') {
    input.type = 'text';
    icon.classList.replace('fa-eye', 'fa-eye-slash');
  } else {
    input.type = 'password';
    icon.classList.replace('fa-eye-slash', 'fa-eye');
  }
}

/* ---- Password strength ---- */
function checkStrength(value) {
  const fill  = document.getElementById('strengthFill');
  const label = document.getElementById('strengthLabel');
  if (!fill || !label) return;

  let score = 0;
  if (value.length >= 8)            score++;
  if (/[A-Z]/.test(value))          score++;
  if (/[0-9]/.test(value))          score++;
  if (/[^A-Za-z0-9]/.test(value))   score++;
  if (value.length >= 12)           score++;

  const levels = [
    { pct: '0%',   color: 'transparent',  text: '',            css: '' },
    { pct: '25%',  color: '#ef4444',      text: 'Weak',        css: 'color:#ef4444' },
    { pct: '50%',  color: '#f97316',      text: 'Fair',        css: 'color:#f97316' },
    { pct: '75%',  color: '#eab308',      text: 'Good',        css: 'color:#eab308' },
    { pct: '90%',  color: '#22c55e',      text: 'Strong',      css: 'color:#22c55e' },
    { pct: '100%', color: '#16a34a',      text: 'Very Strong', css: 'color:#16a34a' },
  ];

  const lvl = levels[Math.min(score, 5)];
  fill.style.width      = lvl.pct;
  fill.style.background = lvl.color;
  label.textContent     = lvl.text ? `Password strength: ${lvl.text}` : '';
  label.setAttribute('style', lvl.css);
}

/* ---- Password match check ---- */
function checkMatch() {
  const pass    = document.getElementById('signupPass');
  const confirm = document.getElementById('confirmPass');
  const msg     = document.getElementById('matchMsg');
  if (!pass || !confirm || !msg) return;

  if (confirm.value.length === 0) {
    msg.textContent = '';
    return;
  }

  if (pass.value === confirm.value) {
    msg.textContent = '✓ Passwords match';
    msg.style.color = '#22c55e';
    confirm.style.borderColor = '#22c55e';
  } else {
    msg.textContent = '✗ Passwords do not match';
    msg.style.color = '#ef4444';
    confirm.style.borderColor = '#ef4444';
  }
}

/* ---- Form loading state ---- */
function setLoading(formId, btnId, loading) {
  const btn    = document.getElementById(btnId);
  const text   = btn?.querySelector('.btn-text');
  const loader = btn?.querySelector('.btn-loader');
  if (!btn) return;
  btn.disabled        = loading;
  text.style.display  = loading ? 'none'   : 'flex';
  loader.style.display= loading ? 'flex'   : 'none';
}

/* ---- Form submit handlers ---- */
document.addEventListener('DOMContentLoaded', function () {

  /* Signin form */
  const signinForm = document.getElementById('signinForm');
  if (signinForm) {
    signinForm.addEventListener('submit', function (e) {
      setLoading('signinForm', 'signinBtn', true);
      // allow natural form POST; Django will handle it.
      // Remove the line below when Django backend is ready;
      // it's only here to prevent reload during UI-only testing.
      // e.preventDefault();
    });
  }

  /* Signup form */
  const signupForm = document.getElementById('signupForm');
  if (signupForm) {
    signupForm.addEventListener('submit', function (e) {
      /* Client-side password match guard */
      const pass    = document.getElementById('signupPass');
      const confirm = document.getElementById('confirmPass');
      if (pass && confirm && pass.value !== confirm.value) {
        e.preventDefault();
        const msg = document.getElementById('matchMsg');
        if (msg) {
          msg.textContent  = '✗ Passwords do not match';
          msg.style.color  = '#ef4444';
        }
        confirm.focus();
        return;
      }
      setLoading('signupForm', 'signupBtn', true);
    });
  }

  /* Input focus: subtle icon colour fix for Firefox */
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

  /* Initialise role (in case page is loaded with a URL param) */
  const params = new URLSearchParams(window.location.search);
  const roleParam = params.get('role');
  if (roleParam && ROLES[roleParam]) {
    switchRole(roleParam);
  }

  /* Auto-flip to signup if ?mode=signup */
  if (params.get('mode') === 'signup') {
    switchToSignup();
  }

});



function formatPhone(input) {
  let v = input.value.replace(/\D/g, "").slice(0, 9);

  let out = v.replace(/(\d{3})(\d{3})(\d{0,3})/, (_, a, b, c) => {
    return c ? `${a} ${b} ${c}` : b ? `${a} ${b}` : a;
  });

  input.value = out;
}

document.getElementById("phoneInput")?.addEventListener("input", function () {
  formatPhone(this);
});

const driverLic = document.querySelector("input[name='license_number']");

if (driverLic) {
  driverLic.addEventListener("input", function (e) {
    let v = e.target.value.replace(/\D/g, "").slice(0, 11);
    e.target.value = v; // NO formatting
  });
}

const businessLic = document.querySelector("input[name='license_no']");

if (businessLic) {
  businessLic.addEventListener("input", function (e) {
    let v = e.target.value.replace(/\D/g, "").slice(0, 12);
    e.target.value = v; // NO formatting
  });
}