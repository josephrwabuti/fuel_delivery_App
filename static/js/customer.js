/* =========================================================
   FuelGo – Customer Dashboard JavaScript
   Handles: sidebar toggle, station modals, search/filter,
            order detail modals, notifications, scroll effects
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

  /* ========== SIDEBAR TOGGLE ========== */
  const sidebar        = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');
  const sidebarToggle  = document.getElementById('sidebarToggle');
  const sidebarClose   = document.getElementById('sidebarClose');

  function openSidebar() {
    sidebar?.classList.add('open');
    sidebarOverlay?.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar?.classList.remove('open');
    sidebarOverlay?.classList.remove('open');
    document.body.style.overflow = '';
  }

  sidebarToggle?.addEventListener('click', openSidebar);
  sidebarClose?.addEventListener('click', closeSidebar);
  sidebarOverlay?.addEventListener('click', closeSidebar);

  /* ========== STATION MODAL ========== */
  const DEMO_STATIONS = {
    1: {
      name:    'Total Energies – Kariakoo',
      address: 'Kariakoo St, Dar es Salaam',
      status:  'open',
      rating:  '4.9',
      reviews: '238',
      hours:   'Mon–Sun: 6:00 AM – 10:00 PM',
      phone:   '+255 712 000 001',
      eta:     '~8 minutes',
      fuels: [
        { type: 'Petrol (RON 91)', price: '2,850', available: true },
        { type: 'Diesel',          price: '2,700', available: true },
      ],
    },
    2: {
      name:    'Puma Energy – Msimbazi',
      address: 'Msimbazi Centre, Dar es Salaam',
      status:  'open',
      rating:  '4.7',
      reviews: '184',
      hours:   'Mon–Sun: 5:30 AM – 11:00 PM',
      phone:   '+255 712 000 002',
      eta:     '~14 minutes',
      fuels: [
        { type: 'Petrol (RON 91)', price: '2,830', available: true },
        { type: 'Diesel',          price: '2,680', available: true },
      ],
    },
    3: {
      name:    'Oryx Petrol – Kinondoni',
      address: 'Kinondoni Rd, Dar es Salaam',
      status:  'open',
      rating:  '4.6',
      reviews: '97',
      hours:   'Mon–Sat: 7:00 AM – 9:00 PM',
      phone:   '+255 712 000 003',
      eta:     '~18 minutes',
      fuels: [
        { type: 'Petrol (RON 91)', price: '2,860', available: true },
        { type: 'Diesel',          price: '2,720', available: false },
      ],
    },
    4: {
      name:    'Engen – Ilala',
      address: 'Lumumba St, Ilala, Dar es Salaam',
      status:  'open',
      rating:  '4.5',
      reviews: '63',
      hours:   'Mon–Sun: 6:00 AM – 10:00 PM',
      phone:   '+255 712 000 004',
      eta:     '~22 minutes',
      fuels: [
        { type: 'Petrol (RON 91)', price: '2,840', available: true },
        { type: 'Diesel',          price: '2,690', available: true },
      ],
    },
    5: {
      name:    'Shell – Temeke',
      address: 'Chang\'ombe Rd, Temeke',
      status:  'closed',
      rating:  '4.8',
      reviews: '201',
      hours:   'Mon–Sun: 6:00 AM – 10:00 PM',
      phone:   '+255 712 000 005',
      eta:     '~28 minutes',
      fuels: [
        { type: 'Petrol (RON 91)', price: '2,870', available: true },
        { type: 'Diesel',          price: '2,710', available: true },
      ],
    },
    6: {
      name:    'GAPCO – Ubungo',
      address: 'Morogoro Rd, Ubungo',
      status:  'open',
      rating:  '4.4',
      reviews: '52',
      hours:   'Mon–Fri: 7:00 AM – 8:00 PM',
      phone:   '+255 712 000 006',
      eta:     '~32 minutes',
      fuels: [
        { type: 'Diesel', price: '2,660', available: true },
      ],
    },
  };

  window.openStationModal = function (id) {
    const modal = document.getElementById('stationModal');
    if (!modal) return;
    const s = DEMO_STATIONS[id];
    if (!s) return;

    document.getElementById('modalInitial').textContent = s.name.charAt(0);
    document.getElementById('modalName').textContent    = s.name;
    document.getElementById('modalAddr').innerHTML      = `<i class="fas fa-location-dot"></i> ${s.address}`;

    const statusEl = document.getElementById('modalStatus');
    if (statusEl) {
      statusEl.className = `sc-status-badge ${s.status} d-inline-flex mt-1`;
      statusEl.innerHTML = `<span class="sdot"></span> ${s.status === 'open' ? 'Open' : 'Closed'}`;
    }

    // Fuel table
    const fuelTable = document.getElementById('modalFuelTable');
    if (fuelTable) {
      fuelTable.innerHTML = `<div class="mft-row header"><span>Fuel Type</span><span>Price/L</span><span>Stock</span></div>` +
        s.fuels.map(f => `
          <div class="mft-row">
            <span>${f.type}</span>
            <span>TZS ${f.price}</span>
            <span class="sc-fuel-stock ${f.available ? 'in' : 'out'}">${f.available ? 'Available' : 'Out of Stock'}</span>
          </div>`).join('');
    }

    // Info grid
    const infoGrid = document.getElementById('modalInfoGrid');
    if (infoGrid) {
      infoGrid.innerHTML = `
        <div class="mig-item"><i class="fas fa-clock text-orange"></i><div><strong>Operating Hours</strong><span>${s.hours}</span></div></div>
        <div class="mig-item"><i class="fas fa-phone text-orange"></i><div><strong>Phone</strong><span>${s.phone}</span></div></div>
        <div class="mig-item"><i class="fas fa-star text-orange"></i><div><strong>Rating</strong><span>${s.rating} / 5 (${s.reviews} reviews)</span></div></div>
        <div class="mig-item"><i class="fas fa-truck-fast text-orange"></i><div><strong>Avg. Delivery</strong><span>${s.eta}</span></div></div>
      `;
    }

    // Order button
    const orderBtn = document.getElementById('modalOrderBtn');
    if (orderBtn) {
      orderBtn.href = `/customer/order/?station=${id}`;
      if (s.status === 'closed') {
        orderBtn.classList.add('disabled');
        orderBtn.innerHTML = '<i class="fas fa-moon"></i> Currently Closed';
        orderBtn.style.pointerEvents = 'none';
        orderBtn.style.opacity = '0.5';
      } else {
        orderBtn.classList.remove('disabled');
        orderBtn.innerHTML = '<i class="fas fa-bolt"></i> Order from This Station';
        orderBtn.style.pointerEvents = '';
        orderBtn.style.opacity = '';
      }
    }

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  };

  window.closeStationModal = function () {
    const modal = document.getElementById('stationModal');
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = '';
  };

  // Close modals on overlay click
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function (e) {
      if (e.target === this) {
        this.style.display = 'none';
        document.body.style.overflow = '';
      }
    });
  });

  // Close on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay').forEach(m => {
        m.style.display = 'none';
      });
      document.body.style.overflow = '';
      closeSidebar();
    }
  });

  /* ========== STATION SEARCH & FILTER (stations page) ========== */
  const stationSearch = document.getElementById('stationSearch');
  const searchClear   = document.getElementById('searchClear');
  const stationsGrid  = document.getElementById('stationsGrid');

  if (stationSearch) {
    stationSearch.addEventListener('input', function () {
      const q = this.value.toLowerCase().trim();
      searchClear.style.display = q ? 'block' : 'none';
      filterStations();
    });
    searchClear?.addEventListener('click', function () {
      stationSearch.value = '';
      this.style.display = 'none';
      filterStations();
    });
  }

  // Filter chips
  let activeFilter = 'all';
  document.querySelectorAll('.fchip').forEach(chip => {
    chip.addEventListener('click', function () {
      document.querySelectorAll('.fchip').forEach(c => c.classList.remove('active'));
      this.classList.add('active');
      activeFilter = this.dataset.filter;
      filterStations();
    });
  });

  function filterStations() {
    const q = stationSearch ? stationSearch.value.toLowerCase().trim() : '';
    const cards = document.querySelectorAll('.station-card');
    let visible = 0;

    cards.forEach(card => {
      const name     = (card.dataset.name || '').toLowerCase();
      const status   = (card.dataset.status || '').toLowerCase();
      const fuels    = (card.dataset.fuels || '').toLowerCase();

      let show = true;
      if (q && !name.includes(q)) show = false;
      if (activeFilter === 'open'    && status !== 'open')  show = false;
      if (activeFilter === 'petrol'  && !fuels.includes('petrol')) show = false;
      if (activeFilter === 'diesel'  && !fuels.includes('diesel')) show = false;

      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    // Sort
    sortStations();

    const countEl = document.getElementById('resultsCount');
    if (countEl) {
      countEl.innerHTML = `<i class="fas fa-location-dot text-orange"></i> Showing <strong>${visible}</strong> station${visible !== 1 ? 's' : ''} near you`;
    }
  }

  // Sort
  const sortSelect = document.getElementById('stationSort');
  sortSelect?.addEventListener('change', sortStations);

  function sortStations() {
    if (!stationsGrid) return;
    const cards = [...stationsGrid.querySelectorAll('.station-card')];
    const by = sortSelect?.value || 'distance';

    cards.sort((a, b) => {
      if (by === 'distance') {
        return parseFloat(a.dataset.distance || 99) - parseFloat(b.dataset.distance || 99);
      }
      if (by === 'rating') {
        const ra = parseFloat(a.querySelector('.sc-rating')?.textContent || '0');
        const rb = parseFloat(b.querySelector('.sc-rating')?.textContent || '0');
        return rb - ra;
      }
      if (by === 'price') {
        const getPx = el => {
          const txt = el.querySelector('.sc-fuel-price')?.textContent || '9999';
          return parseFloat(txt.replace(/[^0-9]/g, ''));
        };
        return getPx(a) - getPx(b);
      }
      return 0;
    });

    cards.forEach(c => stationsGrid.appendChild(c));
  }

  /* ========== GRID / LIST VIEW TOGGLE ========== */
  const gridViewBtn = document.getElementById('gridView');
  const listViewBtn = document.getElementById('listView');

  gridViewBtn?.addEventListener('click', function () {
    gridViewBtn.classList.add('active');
    listViewBtn.classList.remove('active');
    if (stationsGrid) {
      stationsGrid.classList.remove('list-view');
    }
  });
  listViewBtn?.addEventListener('click', function () {
    listViewBtn.classList.add('active');
    gridViewBtn.classList.remove('active');
    if (stationsGrid) {
      stationsGrid.classList.add('list-view');
    }
  });

  /* ========== NOTIFICATIONS BELL DROPDOWN ========== */
  const bellBtn = document.querySelector('.topbar-icon-btn');
  if (bellBtn) {
    bellBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      let dropdown = document.getElementById('notifDropdown');
      if (dropdown) {
        dropdown.remove();
        return;
      }
      dropdown = document.createElement('div');
      dropdown.id = 'notifDropdown';
      dropdown.className = 'notif-dropdown';
      dropdown.innerHTML = `
        <div class="nd-header">
          <span>Notifications</span>
          <button class="nd-mark-all">Mark all read</button>
        </div>
        <div class="nd-item unread">
          <div class="nd-icon orange"><i class="fas fa-truck-fast"></i></div>
          <div class="nd-body">
            <div class="nd-title">Driver assigned for Order #FG-2047</div>
            <div class="nd-time">2 minutes ago</div>
          </div>
        </div>
        <div class="nd-item unread">
          <div class="nd-icon blue"><i class="fas fa-circle-check"></i></div>
          <div class="nd-body">
            <div class="nd-title">Your order #FG-2041 was delivered</div>
            <div class="nd-time">Yesterday at 14:52</div>
          </div>
        </div>
        <div class="nd-item unread">
          <div class="nd-icon purple"><i class="fas fa-gas-pump"></i></div>
          <div class="nd-body">
            <div class="nd-title">New station opened near you: Oryx Ubungo</div>
            <div class="nd-time">2 days ago</div>
          </div>
        </div>
        <div class="nd-item">
          <div class="nd-icon orange"><i class="fas fa-tag"></i></div>
          <div class="nd-body">
            <div class="nd-title">Fuel price update: Petrol now TZS 2,850/L</div>
            <div class="nd-time">3 days ago</div>
          </div>
        </div>
        <div class="nd-footer"><a href="/customer/notifications/">View all notifications</a></div>
      `;

      bellBtn.parentElement.style.position = 'relative';
      bellBtn.parentElement.appendChild(dropdown);

      dropdown.querySelector('.nd-mark-all')?.addEventListener('click', () => {
        dropdown.querySelectorAll('.nd-item.unread').forEach(i => i.classList.remove('unread'));
        const badge = bellBtn.querySelector('.icon-badge');
        if (badge) badge.style.display = 'none';
      });

      setTimeout(() => {
        document.addEventListener('click', function handler(e) {
          if (!dropdown.contains(e.target) && e.target !== bellBtn) {
            dropdown.remove();
            document.removeEventListener('click', handler);
          }
        });
      }, 0);
    });
  }

  /* ========== SCROLL-IN REVEAL ========== */
  const revealEls = document.querySelectorAll(
    '.stat-card, .qa-card, .station-mini-card, .station-card, .step-card, .ht-row'
  );

  if ('IntersectionObserver' in window) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            entry.target.style.opacity  = '1';
            entry.target.style.transform = 'translateY(0)';
          }, (i % 6) * 60);
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });

    revealEls.forEach(el => {
      el.style.opacity   = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      obs.observe(el);
    });
  }

  /* ========== ORDER HISTORY FILTER ========== */
  const orderSearch = document.getElementById('orderSearch');
  if (orderSearch) {
    orderSearch.addEventListener('input', function () {
      const q = this.value.toLowerCase();
      document.querySelectorAll('.ht-row').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }

  /* ========== PROFILE FORM ========== */
  const profileForm = document.getElementById('profileForm');
  if (profileForm) {
    profileForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const btn  = document.getElementById('saveProfileBtn');
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Saving…';
      btn.disabled  = true;
      setTimeout(() => {
        btn.innerHTML = '<i class="fas fa-circle-check"></i> Saved!';
        btn.style.background = '#22c55e';
        setTimeout(() => {
          btn.innerHTML = orig;
          btn.disabled  = false;
          btn.style.background = '';
        }, 2000);
      }, 1200);
    });
  }

  /* ========== PASSWORD CHANGE FORM ========== */
  const pwForm = document.getElementById('changePasswordForm');
  if (pwForm) {
    pwForm.addEventListener('submit', function (e) {
      const np = document.getElementById('newPassword')?.value;
      const cp = document.getElementById('confirmNewPassword')?.value;
      if (np !== cp) {
        e.preventDefault();
        const msg = document.getElementById('pwMatchMsg');
        if (msg) { msg.textContent = 'Passwords do not match'; msg.style.display = 'flex'; }
      }
    });
    document.getElementById('newPassword')?.addEventListener('input', function () {
      checkPwStrength(this.value);
    });
  }

  function checkPwStrength(value) {
    const fill  = document.getElementById('pwStrengthFill');
    const label = document.getElementById('pwStrengthLabel');
    if (!fill || !label) return;
    let score = 0;
    if (value.length >= 8) score++;
    if (/[A-Z]/.test(value)) score++;
    if (/[0-9]/.test(value)) score++;
    if (/[^A-Za-z0-9]/.test(value)) score++;
    const levels = [
      { pct:'0%', color:'transparent', text:'' },
      { pct:'25%', color:'#ef4444', text:'Weak' },
      { pct:'50%', color:'#f97316', text:'Fair' },
      { pct:'75%', color:'#eab308', text:'Good' },
      { pct:'100%', color:'#22c55e', text:'Strong' },
    ];
    const lvl = levels[Math.min(score, 4)];
    fill.style.width = lvl.pct;
    fill.style.background = lvl.color;
    label.textContent = lvl.text ? `Strength: ${lvl.text}` : '';
    label.style.color = lvl.color;
  }

  /* ========== TOGGLE PASSWORD VISIBILITY ========== */
  window.toggleVisibility = function (inputId, iconId) {
    const inp  = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    if (!inp || !icon) return;
    inp.type = inp.type === 'password' ? 'text' : 'password';
    icon.classList.toggle('fa-eye');
    icon.classList.toggle('fa-eye-slash');
  };

  /* ========== SMOOTH ACTIVE NAV HIGHLIGHT ========== */
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

});

/* ========== NOTIFICATION DROPDOWN CSS (injected) ========== */
(function injectNotifStyles() {
  const style = document.createElement('style');
  style.textContent = `
    .notif-dropdown {
      position: absolute; top: calc(100% + 8px); right: 0;
      width: 320px; background: var(--navy-800);
      border: 1px solid var(--border-m); border-radius: 14px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.5); z-index: 600;
      overflow: hidden; animation: modalIn 0.25s ease;
    }
    .nd-header {
      display: flex; justify-content: space-between; align-items: center;
      padding: 14px 16px; border-bottom: 1px solid var(--border-s);
      font-size: 0.88rem; font-weight: 700; color: var(--text-p);
    }
    .nd-mark-all {
      font-size: 0.75rem; color: var(--orange); background: none; border: none;
      cursor: pointer; font-family: 'Outfit', sans-serif; font-weight: 600;
    }
    .nd-item {
      display: flex; align-items: flex-start; gap: 12px;
      padding: 12px 16px; border-bottom: 1px solid var(--border-s);
      transition: background 0.2s;
    }
    .nd-item:hover { background: var(--glass-l); }
    .nd-item.unread { background: rgba(232,93,4,0.04); }
    .nd-icon {
      width: 34px; height: 34px; border-radius: 9px; flex-shrink: 0;
      display: flex; align-items: center; justify-content: center; font-size: 0.85rem;
    }
    .nd-icon.orange { background: var(--orange-dim); color: var(--orange); }
    .nd-icon.blue   { background: var(--blue-dim);   color: var(--blue);   }
    .nd-icon.purple { background: var(--purple-dim); color: var(--purple); }
    .nd-title { font-size: 0.82rem; color: var(--text-p); font-weight: 500; line-height: 1.4; }
    .nd-time  { font-size: 0.72rem; color: var(--text-m); margin-top: 3px; }
    .nd-footer { padding: 12px 16px; text-align: center; }
    .nd-footer a { font-size: 0.8rem; color: var(--orange); font-weight: 600; }

    /* List view for stations grid */
    .stations-grid.list-view {
      grid-template-columns: 1fr !important;
    }
    .stations-grid.list-view .station-card {
      flex-direction: row; align-items: center; gap: 16px; flex-wrap: wrap;
    }
    .stations-grid.list-view .sc-top-bar { order: 0; }
    .stations-grid.list-view .sc-body-main { flex: 1; order: 1; }
    .stations-grid.list-view .sc-divider { display: none; }
    .stations-grid.list-view .sc-fuels-row { order: 2; }
    .stations-grid.list-view .sc-actions { order: 3; }
  `;
  document.head.appendChild(style);
})();
