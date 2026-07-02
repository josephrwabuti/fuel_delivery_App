/* =========================================================
   FuelGo – Admin Panel JavaScript
   Handles: sidebar, modals, toasts, confirm dialogs,
            notifications bell, search/filter, reveal animations
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

  /* ===== SIDEBAR TOGGLE ===== */
  const sidebar   = document.getElementById('sidebar');
  const overlay   = document.getElementById('sidebarOverlay');
  const toggleBtn = document.getElementById('sidebarToggle');
  const closeBtn  = document.getElementById('sidebarClose');

  function openSidebar()  { sidebar?.classList.add('open'); overlay?.classList.add('open'); document.body.style.overflow = 'hidden'; }
  function closeSidebar() { sidebar?.classList.remove('open'); overlay?.classList.remove('open'); document.body.style.overflow = ''; }

  toggleBtn?.addEventListener('click', openSidebar);
  closeBtn?.addEventListener('click', closeSidebar);
  overlay?.addEventListener('click', closeSidebar);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeSidebar();
      document.querySelectorAll('.modal-overlay').forEach(m => { m.style.display = 'none'; });
      document.body.style.overflow = '';
    }
  });

  /* ===== MODAL HELPERS ===== */
  window.openModal = function (id) {
    const m = document.getElementById(id);
    if (m) { m.style.display = 'flex'; document.body.style.overflow = 'hidden'; }
  };
  window.closeModal = function (id) {
    const m = document.getElementById(id);
    if (m) { m.style.display = 'none'; document.body.style.overflow = ''; }
  };

  document.querySelectorAll('.modal-overlay').forEach(mo => {
    mo.addEventListener('click', function (e) {
      if (e.target === this) { this.style.display = 'none'; document.body.style.overflow = ''; }
    });
  });

  /* ===== TOAST SYSTEM ===== */
  window.showToast = function (msg, type = 'info') {
    let wrap = document.getElementById('toastWrap');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.id = 'toastWrap';
      wrap.className = 'toast-wrap';
      document.body.appendChild(wrap);
    }
    const icons = { success: 'fa-circle-check', error: 'fa-circle-xmark', info: 'fa-circle-info' };
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> ${msg}`;
    wrap.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity 0.3s'; setTimeout(() => t.remove(), 300); }, 3800);
  };

  /* ===== CONFIRM DIALOG ===== */
  window.showConfirm = function (title, body, color, onConfirm) {
    const modal    = document.getElementById('confirmModal');
    const iconEl   = document.getElementById('confirmIcon');
    const titleEl  = document.getElementById('confirmTitle');
    const subEl    = document.getElementById('confirmSub');
    const actionBtn = document.getElementById('confirmActionBtn');

    if (!modal) return;

    titleEl.textContent = title;
    subEl.innerHTML     = body;

    // Style icon by colour
    iconEl.className = 'mhs-icon';
    const iconMap = {
      green:  { cls: 'mhs-icon',     style: 'background:rgba(34,197,94,0.12);color:var(--green)',   icon: 'fa-circle-check' },
      red:    { cls: 'mhs-icon',     style: 'background:rgba(239,68,68,0.1);color:var(--red)',       icon: 'fa-triangle-exclamation' },
      orange: { cls: 'mhs-icon',     style: 'background:var(--orange-dim);color:var(--orange)',      icon: 'fa-question-circle' },
    };
    const cfg = iconMap[color] || iconMap.orange;
    iconEl.setAttribute('style', cfg.style);
    iconEl.innerHTML = `<i class="fas ${cfg.icon}"></i>`;

    // Style confirm button
    actionBtn.className = `btn-modal-${color === 'red' ? 'danger' : 'confirm'}`;
    actionBtn.textContent = 'Confirm';

    // Attach callback
    const newBtn = actionBtn.cloneNode(true);
    newBtn.textContent = 'Confirm';
    newBtn.className   = actionBtn.className;
    newBtn.addEventListener('click', () => {
      closeModal('confirmModal');
      if (typeof onConfirm === 'function') onConfirm();
    });
    actionBtn.parentNode.replaceChild(newBtn, actionBtn);

    openModal('confirmModal');
  };

  /* ===== NOTIFICATIONS BELL ===== */
  const bell = document.getElementById('notifBell');
  if (bell) {
    bell.addEventListener('click', function (e) {
      e.stopPropagation();
      let dd = document.getElementById('adminNotifDD');
      if (dd) { dd.remove(); return; }

      let notifs = [];
      try { notifs = JSON.parse(bell.dataset.notifs || '[]'); } catch(e) {}

      dd = document.createElement('div');
      dd.id = 'adminNotifDD';
      dd.className = 'notif-dropdown';

      let itemsHtml = '';
      if (notifs.length === 0) {
        itemsHtml = '<div class="nd-item"><div class="nd-body"><div class="nd-title">No notifications</div></div></div>';
      } else {
        notifs.forEach(function(n) {
          const unreadClass = n.is_read ? '' : ' unread';
          itemsHtml += '<div class="nd-item' + unreadClass + '">' +
            '<div class="nd-icon orange"><i class="fas fa-bell"></i></div>' +
            '<div class="nd-body"><div class="nd-title">' + escapeHtml(n.message) + '</div><div class="nd-time">' + escapeHtml(n.time) + '</div></div>' +
            '</div>';
        });
      }

      dd.innerHTML = `
        <div class="nd-header">
          <span>Notifications</span>
        </div>
        ${itemsHtml}
        <div class="nd-footer"><a href="/activity/">View all activity</a></div>
      `;

      bell.parentElement.style.position = 'relative';
      bell.parentElement.appendChild(dd);

      setTimeout(() => {
        document.addEventListener('click', function h(e) {
          if (!dd.contains(e.target) && e.target !== bell) { dd.remove(); document.removeEventListener('click', h); }
        });
      }, 0);
    });
  }

  function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
  }

  /* ===== SCROLL-IN REVEAL ===== */
  const revealEls = document.querySelectorAll(
    '.kpi-card, .dash-card, .report-card, .msr-item, .pa-item, .af-item, .al-item, .tl-item, .health-card, .settings-card, .dt-row'
  );
  if ('IntersectionObserver' in window && revealEls.length) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            entry.target.style.opacity  = '1';
            entry.target.style.transform = 'translateY(0)';
          }, (i % 8) * 45);
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.06 });

    revealEls.forEach(el => {
      el.style.opacity   = '0';
      el.style.transform = 'translateY(16px)';
      el.style.transition = 'opacity 0.38s ease, transform 0.38s ease';
      obs.observe(el);
    });
  }

  /* ===== GENERIC TABLE SEARCH ===== */
  function bindSearch(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.addEventListener('input', function () {
      const q = this.value.toLowerCase();
      document.querySelectorAll('.dt-row').forEach(r => {
        r.style.display = (r.dataset.search || r.textContent.toLowerCase()).includes(q) ? '' : 'none';
      });
    });
  }
  bindSearch('stationSearch');
  bindSearch('driverSearch');
  bindSearch('custSearch');
  bindSearch('orderSearch');

  /* ===== GENERIC FILTER CHIPS ===== */
  document.querySelectorAll('.fchip').forEach(chip => {
    chip.addEventListener('click', function () {
      const parent = this.closest('.filter-chips');
      parent?.querySelectorAll('.fchip').forEach(c => c.classList.remove('active'));
      this.classList.add('active');
      const f = this.dataset.filter;
      document.querySelectorAll('.dt-row').forEach(r => {
        r.style.display = (f === 'all' || r.dataset.status === f) ? '' : 'none';
      });
    });
  });

  /* ===== PERIOD BUTTONS (reports) ===== */
  document.querySelectorAll('.period-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const cw = document.getElementById('customRangeWrap');
      if (cw) cw.style.display = this.dataset.period === 'custom' ? 'flex' : 'none';
    });
  });

  /* ===== LIVE ACTIVITY FEED (simulate new entries) ===== */
  const feed = document.getElementById('activityFeed');
  if (feed) {
    const demoEvents = [
      { icon: 'orange', fa: 'fa-receipt',    msg: 'New order <strong>#FG-2048</strong> placed by Baraka Juma' },
      { icon: 'green',  fa: 'fa-circle-check', msg: 'Order <strong>#FG-2046</strong> delivered by John Mwalimu' },
      { icon: 'blue',   fa: 'fa-user-plus',  msg: 'New customer <strong>Fatuma Ally</strong> registered' },
      { icon: 'orange', fa: 'fa-truck-fast', msg: 'Driver assigned to <strong>#FG-2048</strong>' },
    ];
    let eventIndex = 0;
    setInterval(() => {
      const ev   = demoEvents[eventIndex % demoEvents.length];
      const item = document.createElement('div');
      item.className = 'af-item';
      item.style.opacity = '0';
      item.style.transition = 'opacity 0.5s';
      item.innerHTML = `
        <div class="af-icon ${ev.icon}"><i class="fas ${ev.fa}"></i></div>
        <div class="af-body">
          <div class="af-msg">${ev.msg}</div>
          <div class="af-time">Just now</div>
        </div>`;
      feed.prepend(item);
      setTimeout(() => { item.style.opacity = '1'; }, 50);
      // Remove oldest if too many
      const items = feed.querySelectorAll('.af-item');
      if (items.length > 10) items[items.length - 1].remove();
      eventIndex++;
    }, 12000);
  }

  /* ===== INJECT NOTIFICATION DROPDOWN STYLES ===== */
  const style = document.createElement('style');
  style.textContent = `
    .notif-dropdown {
      position:absolute;top:calc(100% + 8px);right:0;width:310px;
      background:var(--navy-800);border:1px solid var(--border-m);
      border-radius:14px;box-shadow:0 20px 50px rgba(0,0,0,0.5);
      z-index:600;overflow:hidden;animation:modalIn 0.25s ease;
    }
    .nd-header {
      display:flex;justify-content:space-between;align-items:center;
      padding:12px 16px;border-bottom:1px solid var(--border-s);
      font-size:0.86rem;font-weight:700;color:var(--text-p);
    }
    .nd-mark {
      font-size:0.73rem;color:var(--orange);background:none;
      border:none;cursor:pointer;font-family:'Outfit',sans-serif;font-weight:600;
    }
    .nd-item {
      display:flex;align-items:flex-start;gap:11px;padding:11px 16px;
      border-bottom:1px solid var(--border-s);transition:background 0.2s;
    }
    .nd-item:hover{background:var(--glass-l);}
    .nd-item.unread{background:rgba(232,93,4,0.04);}
    .nd-icon {
      width:32px;height:32px;border-radius:8px;flex-shrink:0;
      display:flex;align-items:center;justify-content:center;font-size:0.82rem;
    }
    .nd-icon.orange{background:var(--orange-dim);color:var(--orange);}
    .nd-icon.blue{background:var(--blue-dim);color:var(--blue);}
    .nd-icon.green{background:rgba(34,197,94,0.12);color:var(--green);}
    .nd-icon.yellow{background:rgba(234,179,8,0.12);color:var(--yellow);}
    .nd-body{flex:1;}
    .nd-title{font-size:0.8rem;color:var(--text-p);line-height:1.4;}
    .nd-time{font-size:0.7rem;color:var(--text-m);margin-top:2px;}
    .nd-footer{padding:11px 16px;text-align:center;}
    .nd-footer a{font-size:0.78rem;color:var(--orange);font-weight:600;}
  `;
  document.head.appendChild(style);

});
