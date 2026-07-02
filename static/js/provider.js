/* =========================================================
   FuelGo – Provider Dashboard JavaScript
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

  /* ===== SIDEBAR TOGGLE ===== */
  const sidebar        = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');
  const sidebarToggle  = document.getElementById('sidebarToggle');
  const sidebarClose   = document.getElementById('sidebarClose');

  function openSidebar()  { sidebar?.classList.add('open'); sidebarOverlay?.classList.add('open'); document.body.style.overflow = 'hidden'; }
  function closeSidebar() { sidebar?.classList.remove('open'); sidebarOverlay?.classList.remove('open'); document.body.style.overflow = ''; }

  sidebarToggle?.addEventListener('click', openSidebar);
  sidebarClose?.addEventListener('click', closeSidebar);
  sidebarOverlay?.addEventListener('click', closeSidebar);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeSidebar();
      document.querySelectorAll('.modal-overlay').forEach(m => { m.style.display = 'none'; });
      document.body.style.overflow = '';
    }
  });

  /* ===== STATION OPEN/CLOSE TOGGLE ===== */
  window.toggleStationOpen = function (checkbox) {
    const label = document.getElementById('openLabel');
    const csrf = document.querySelector('[name=csrfmiddlewaretoken]');
    fetch('/provider/station/toggle-open/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrf ? csrf.value : '',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    }).then(r => r.json()).then(data => {
      if (data.is_open) {
        if (label) { label.textContent = 'Open'; label.style.color = 'var(--green)'; }
        showToast('Station is now Open for orders.', 'success');
      } else {
        if (label) { label.textContent = 'Closed'; label.style.color = 'var(--red)'; }
        showToast('Station marked Closed. No new orders will be received.', 'error');
      }
    }).catch(() => {
      checkbox.checked = !checkbox.checked;
      showToast('Failed to update status.', 'error');
    });
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

  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function (e) {
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
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> ${msg}`;
    wrap.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  };

  /* ===== ORDER SEARCH & FILTER ===== */
  const orderSearch = document.getElementById('orderSearch');
  if (orderSearch) {
    orderSearch.addEventListener('input', function () {
      const q = this.value.toLowerCase();
      document.querySelectorAll('.dt-row').forEach(row => {
        const searchVal = row.dataset.search || row.textContent.toLowerCase();
        row.style.display = searchVal.includes(q) ? '' : 'none';
      });
    });
  }

  let activeStatusFilter = 'all';
  document.querySelectorAll('.fchip').forEach(chip => {
    chip.addEventListener('click', function () {
      document.querySelectorAll('.fchip').forEach(c => c.classList.remove('active'));
      this.classList.add('active');
      activeStatusFilter = this.dataset.filter;
      applyOrderFilter();
    });
  });

  function applyOrderFilter() {
    const q = orderSearch ? orderSearch.value.toLowerCase() : '';
    document.querySelectorAll('.dt-row').forEach(row => {
      const statusMatch = activeStatusFilter === 'all' || row.dataset.status === activeStatusFilter;
      const searchMatch = !q || (row.dataset.search || row.textContent.toLowerCase()).includes(q);
      row.style.display = (statusMatch && searchMatch) ? '' : 'none';
    });
  }

  /* ===== DRIVER FILTER ===== */
  const driverSearch = document.getElementById('driverSearch');
  if (driverSearch) {
    driverSearch.addEventListener('input', function () {
      const q = this.value.toLowerCase();
      document.querySelectorAll('.driver-card-full').forEach(card => {
        card.style.display = (card.dataset.name || '').includes(q) ? '' : 'none';
      });
    });
  }

  /* ===== NOTIFICATIONS BELL ===== */
  const bellBtn = document.getElementById('notifBell');
  if (bellBtn) {
    bellBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      let dropdown = document.getElementById('notifDropdown');
      if (dropdown) { dropdown.remove(); return; }
      dropdown = document.createElement('div');
      dropdown.id = 'notifDropdown';
      dropdown.className = 'notif-dropdown';

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
      dropdown.innerHTML = `
        <div class="nd-header"><span>Notifications</span><button class="nd-mark-all">Mark all read</button></div>
        ${itemsHtml}
        <div class="nd-footer"><a href="#">View all notifications</a></div>`;

      bellBtn.parentElement.style.position = 'relative';
      bellBtn.parentElement.appendChild(dropdown);

      dropdown.querySelector('.nd-mark-all')?.addEventListener('click', () => {
        fetch('/notifications/mark-all-read/', { method: 'POST', headers: {'X-CSRFToken': csrf} });
        dropdown.querySelectorAll('.nd-item.unread').forEach(i => i.classList.remove('unread'));
      });

      setTimeout(() => {
        document.addEventListener('click', function h(e) {
          if (!dropdown.contains(e.target) && e.target !== bellBtn) { dropdown.remove(); document.removeEventListener('click', h); }
        });
      }, 0);
    });
  }

  /* ===== SCROLL-IN REVEAL ===== */
  const revealEls = document.querySelectorAll('.kpi-card, .dash-card, .driver-card-full, .report-card, .insight-card, .dt-row, .stock-kpi-card');
  if ('IntersectionObserver' in window) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => { entry.target.style.opacity = '1'; entry.target.style.transform = 'translateY(0)'; }, (i % 6) * 55);
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.06 });
    revealEls.forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(18px)';
      el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      obs.observe(el);
    });
  }

  /* ===== INJECT NOTIFICATION STYLES ===== */
  const style = document.createElement('style');
  style.textContent = `
    .notif-dropdown{position:absolute;top:calc(100% + 8px);right:0;width:300px;background:var(--navy-800);border:1px solid var(--border-m);border-radius:14px;box-shadow:0 20px 50px rgba(0,0,0,0.5);z-index:600;overflow:hidden;animation:modalIn 0.25s ease}
    .nd-header{display:flex;justify-content:space-between;align-items:center;padding:12px 14px;border-bottom:1px solid var(--border-s);font-size:0.86rem;font-weight:700;color:var(--text-p)}
    .nd-mark-all{font-size:0.73rem;color:var(--orange);background:none;border:none;cursor:pointer;font-family:'Outfit',sans-serif;font-weight:600}
    .nd-item{display:flex;align-items:flex-start;gap:10px;padding:11px 14px;border-bottom:1px solid var(--border-s);transition:background 0.2s}
    .nd-item:hover{background:var(--glass-l)}.nd-item.unread{background:rgba(232,93,4,0.04)}
    .nd-icon{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:0.82rem;flex-shrink:0}
    .nd-icon.orange{background:var(--orange-dim);color:var(--orange)}.nd-icon.green{background:rgba(34,197,94,0.12);color:var(--green)}.nd-icon.red{background:rgba(239,68,68,0.1);color:var(--red)}
    .nd-title{font-size:0.8rem;color:var(--text-p);line-height:1.4}.nd-time{font-size:0.7rem;color:var(--text-m);margin-top:2px}
    .nd-footer{padding:10px 14px;text-align:center}.nd-footer a{font-size:0.78rem;color:var(--orange);font-weight:600}
  `;
  document.head.appendChild(style);

});
