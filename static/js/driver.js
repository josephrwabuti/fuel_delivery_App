/* =========================================================
   FuelGo – Driver Dashboard JavaScript
   Handles: sidebar, duty toggle, modals, toasts, notifications,
            reveal animations, search/filter
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

  /* ===== SIDEBAR TOGGLE ===== */
  const sidebar        = document.getElementById('sidebar');
  const overlay        = document.getElementById('sidebarOverlay');
  const toggleBtn      = document.getElementById('sidebarToggle');
  const closeBtn       = document.getElementById('sidebarClose');

  function openSidebar()  { sidebar?.classList.add('open'); overlay?.classList.add('open'); document.body.style.overflow = 'hidden'; }
  function closeSidebar() { sidebar?.classList.remove('open'); overlay?.classList.remove('open'); document.body.style.overflow = ''; }

  toggleBtn?.addEventListener('click', openSidebar);
  closeBtn?.addEventListener('click', closeSidebar);
  overlay?.addEventListener('click', closeSidebar);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeSidebar();
      document.querySelectorAll('.modal-overlay').forEach(m => {
        m.style.display = 'none';
      });
      document.body.style.overflow = '';
    }
  });

  /* ===== DUTY STATUS TOGGLE ===== */
  window.toggleDuty = function (checkbox) {
    const label = document.getElementById('dutyLabel');
    if (checkbox.checked) {
      if (label) { label.textContent = 'On Duty'; label.style.color = 'var(--green)'; }
      showToast('You are now On Duty. You will receive delivery assignments.', 'success');
    } else {
      if (label) { label.textContent = 'Off Duty'; label.style.color = 'var(--red)'; }
      showToast('You are now Off Duty. No new orders will be assigned.', 'error');
    }
    // POST to Django: fetch('/driver/toggle-duty/', { method:'POST', headers:{...}, body:... })
  };

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
    setTimeout(() => {
      t.style.opacity = '0';
      t.style.transition = 'opacity 0.3s';
      setTimeout(() => t.remove(), 300);
    }, 3500);
  };

  /* ===== NOTIFICATIONS BELL ===== */
  const bell = document.getElementById('notifBell');
  if (bell) {
    bell.addEventListener('click', function (e) {
      e.stopPropagation();
      let dd = document.getElementById('driverNotifDD');
      if (dd) { dd.remove(); return; }
      dd = document.createElement('div');
      dd.id = 'driverNotifDD';
      dd.className = 'notif-dropdown';

      let notifs;
      try { notifs = JSON.parse(this.dataset.notifs || '[]'); } catch { notifs = []; }
      const itemsHtml = notifs.length
        ? notifs.map(n => `
            <div class="nd-item${n.is_read ? '' : ' unread'}">
              <div class="nd-icon ${n.is_read ? 'blue' : 'orange'}"><i class="fas fa-bell"></i></div>
              <div class="nd-body"><div class="nd-title">${n.title}</div><div class="nd-time">${n.time}</div></div>
            </div>`).join('')
        : '<div class="nd-item" style="justify-content:center;color:var(--text-m);font-size:.8rem;padding:20px">No notifications</div>';

      const csrf = document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
      dd.innerHTML = `
        <div class="nd-header"><span>Notifications</span>
          <button class="nd-mark-all">Mark all read</button>
        </div>
        ${itemsHtml}
        <div class="nd-footer"><a href="/delivery/notifications/">View all</a></div>`;

      bell.parentElement.style.position = 'relative';
      bell.parentElement.appendChild(dd);

      dd.querySelector('.nd-mark-all')?.addEventListener('click', () => {
        fetch('/notifications/mark-all-read/', { method: 'POST', headers: {'X-CSRFToken': csrf} });
        dd.querySelectorAll('.nd-item.unread').forEach(i => i.classList.remove('unread'));
      });

      setTimeout(() => {
        document.addEventListener('click', function h(e) {
          if (!dd.contains(e.target) && e.target !== bell) { dd.remove(); document.removeEventListener('click', h); }
        });
      }, 0);
    });
  }

  /* ===== SCROLL-IN REVEAL ===== */
  const revealEls = document.querySelectorAll(
    '.kpi-card, .home-card, .order-card, .driver-card-full, .earn-card, .txn-item, .rdt-row, .dt-row, .ao-item, .notif-item'
  );
  if ('IntersectionObserver' in window && revealEls.length) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            entry.target.style.opacity  = '1';
            entry.target.style.transform = 'translateY(0)';
          }, (i % 6) * 55);
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.07 });
    revealEls.forEach(el => {
      el.style.opacity   = '0';
      el.style.transform = 'translateY(18px)';
      el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      obs.observe(el);
    });
  }

  /* ===== HISTORY TABLE FILTER ===== */
  document.querySelectorAll('.fchip').forEach(chip => {
    chip.addEventListener('click', function () {
      document.querySelectorAll('.fchip').forEach(c => c.classList.remove('active'));
      this.classList.add('active');
      const f = this.dataset.filter;
      document.querySelectorAll('.dt-row.hist, .order-card').forEach(row => {
        row.style.display = (f === 'all' || row.dataset.status === f) ? '' : 'none';
      });
    });
  });

  /* ===== SEARCH ===== */
  const histSearch  = document.getElementById('histSearch');
  const orderSearch = document.getElementById('orderSearch');

  histSearch?.addEventListener('input', function () {
    const q = this.value.toLowerCase();
    document.querySelectorAll('.dt-row.hist').forEach(row => {
      row.style.display = (row.dataset.search || row.textContent.toLowerCase()).includes(q) ? '' : 'none';
    });
  });

  orderSearch?.addEventListener('input', function () {
    const q = this.value.toLowerCase();
    document.querySelectorAll('.order-card').forEach(card => {
      card.style.display = (card.dataset.search || '').includes(q) ? '' : 'none';
    });
  });

  /* ===== INJECT NOTIFICATION DROPDOWN STYLES ===== */
  const style = document.createElement('style');
  style.textContent = `
    .notif-dropdown{position:absolute;top:calc(100% + 8px);right:0;width:300px;
      background:var(--navy-800);border:1px solid var(--border-m);border-radius:14px;
      box-shadow:0 20px 50px rgba(0,0,0,0.5);z-index:600;overflow:hidden;
      animation:modalIn 0.25s ease}
    .nd-header{display:flex;justify-content:space-between;align-items:center;
      padding:12px 14px;border-bottom:1px solid var(--border-s);
      font-size:0.86rem;font-weight:700;color:var(--text-p)}
    .nd-mark{font-size:0.73rem;color:var(--orange);background:none;border:none;
      cursor:pointer;font-family:'Outfit',sans-serif;font-weight:600}
    .nd-item{display:flex;align-items:flex-start;gap:10px;padding:11px 14px;
      border-bottom:1px solid var(--border-s);transition:background 0.2s}
    .nd-item:hover{background:var(--glass-l)}.nd-item.unread{background:rgba(232,93,4,0.04)}
    .nd-icon{width:32px;height:32px;border-radius:8px;flex-shrink:0;
      display:flex;align-items:center;justify-content:center;font-size:0.8rem}
    .nd-icon.orange{background:var(--orange-dim);color:var(--orange)}
    .nd-icon.green{background:rgba(34,197,94,0.12);color:var(--green)}
    .nd-icon.blue{background:var(--blue-dim);color:var(--blue)}
    .nd-title{font-size:0.8rem;color:var(--text-p);line-height:1.4}
    .nd-time{font-size:0.7rem;color:var(--text-m);margin-top:2px}
    .nd-footer{padding:10px 14px;text-align:center}
    .nd-footer a{font-size:0.78rem;color:var(--orange);font-weight:600}
  `;
  document.head.appendChild(style);

});
