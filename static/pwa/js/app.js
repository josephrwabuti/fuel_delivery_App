let App = {
  user: null,
  role: null,
  currentPage: null,
  navItems: [],
  geolocationWatchId: null,
  selectedStation: null,
  driverLocationInterval: null,
  customerTrackInterval: null,
};

function $id(id) { return document.getElementById(id); }
function qs(sel, ctx) { return (ctx || document).querySelector(sel); }
function qsa(sel, ctx) { return (ctx || document).querySelectorAll(sel); }

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function statusBadge(status) {
  const cls = "badge-" + status.toLowerCase().replace(/\s+/g, "_");
  const labels = {
    pending: "Pending", confirmed: "Confirmed", assigned: "Assigned",
    picked_up: "Picked Up", delivering: "Delivering", delivered: "Delivered",
    cancelled: "Cancelled", out: "Out for Delivery",
  };
  return `<span class="badge ${cls}">${labels[status] || status}</span>`;
}

function showToast(msg, type) {
  const t = $id("toast");
  t.textContent = msg;
  t.className = "toast show" + (type ? " " + type : "");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 3000);
}

function showLoading(show) {
  $id("loading-overlay").style.display = show ? "flex" : "none";
}

// ─── Map helpers ──────────────────────────────────────
function osmLayer() {
  return L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>',
    maxZoom: 19,
  });
}

function userIcon() {
  return L.divIcon({ className: "", html: '<div class="pwa-marker-user"></div>', iconSize: [18, 18], iconAnchor: [9, 9] });
}

function stationIcon(open) {
  return L.divIcon({ className: "", html: `<div class="pwa-marker-station${open ? "" : " closed"}"></div>`, iconSize: [14, 14], iconAnchor: [7, 7] });
}

function deliveryIcon() {
  return L.divIcon({ className: "", html: '<div class="pwa-marker-delivery"></div>', iconSize: [22, 22], iconAnchor: [11, 11] });
}

function routeStartIcon() {
  return L.divIcon({ className: "", html: '<div class="pwa-marker-route-start"></div>', iconSize: [14, 14], iconAnchor: [7, 7] });
}

function routeEndIcon() {
  return L.divIcon({ className: "", html: '<div class="pwa-marker-route-end"></div>', iconSize: [16, 16], iconAnchor: [8, 8] });
}

function driverIcon() {
  return L.divIcon({ className: "", html: '<div class="pwa-marker-driver"></div>', iconSize: [20, 20], iconAnchor: [10, 10] });
}

function haversine(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function requestLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation not supported"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      (err) => {
        const msgs = { 1: "Location access denied", 2: "Location unavailable", 3: "Timed out" };
        reject(new Error(msgs[err.code] || "Could not detect location"));
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
    );
  });
}

function reverseGeocode(lat, lng) {
  return fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`)
    .then((r) => r.json())
    .then((d) => {
      const a = d.address;
      return [a?.road, a?.suburb || a?.neighbourhood, a?.city || a?.town].filter(Boolean).join(", ") || d.display_name || `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    })
    .catch(() => `${lat.toFixed(5)}, ${lng.toFixed(5)}`);
}

function getMapCenter(stations) {
  const defaultCenter = [-6.8235, 39.2695];
  if (!stations || !stations.length) return defaultCenter;
  const lats = stations.map((s) => s.lat).filter((v) => v);
  const lngs = stations.map((s) => s.lng).filter((v) => v);
  if (!lats.length || !lngs.length) return defaultCenter;
  return [lats.reduce((a, b) => a + b, 0) / lats.length, lngs.reduce((a, b) => a + b, 0) / lngs.length];
}

function cleanupMap(mapVar) {
  if (window[mapVar]) {
    window[mapVar].remove();
    window[mapVar] = null;
  }
}

// ─── Router ───────────────────────────────────────────
function navigate(hash) {
  if (!hash || hash === "#") hash = App.role === "customer" ? "#/customer/dashboard" : "#/driver/dashboard";
  location.hash = hash;
}

window.addEventListener("hashchange", () => renderPage());
window.addEventListener("load", () => init());

async function init() {
  await registerSW();
  renderAuth();
  try {
    const res = await API.getUser();
    if (res.status === "success" && res.user) {
      App.user = res.user;
      App.role = res.user.role;
      showApp();
      if (!location.hash || location.hash === "#") navigate();
      renderPage();
    } else {
      showAuth();
    }
  } catch {
    showAuth();
  }
}

async function registerSW() {
  if ("serviceWorker" in navigator) {
    try {
      await navigator.serviceWorker.register("/static/pwa/sw.js");
    } catch {}
  }
}

function showApp() {
  $id("auth-screen").classList.remove("show");
  $id("app").style.display = "flex";
  $id("bottom-nav").classList.add("show");
  updateHeader();
  requestLocation().catch(() => {});
}

function showAuth() {
  $id("auth-screen").classList.add("show");
  $id("app").style.display = "none";
  $id("bottom-nav").classList.remove("show");
}

// ─── Header & Nav ─────────────────────────────────────
function updateHeader(title, showBack, action) {
  const h = $id("app-header");
  const back = qs(".back-btn", h);
  const h1 = qs("h1", h);
  const act = qs(".header-action", h);
  back.style.display = showBack ? "block" : "none";
  h1.textContent = title || "FuelGo";
  if (action) {
    act.style.display = "block";
    act.textContent = action.label;
    act.onclick = action.onclick;
  } else {
    act.style.display = "none";
  }
}

function setupNav(items) {
  const nav = $id("bottom-nav");
  nav.innerHTML = items.map((item, i) => `
    <button class="nav-item" data-index="${i}" onclick="navigate('${item.hash}')">
      <span class="nav-icon-wrap">
        <span class="nav-icon">${item.icon}</span>
        ${item.badge ? `<span class="badge">${item.badge}</span>` : ""}
      </span>
      <span>${item.label}</span>
    </button>
  `).join("");
  App.navItems = items;
}

function updateNavActive(hash) {
  qsa(".nav-item").forEach((el, i) => {
    el.classList.toggle("active", App.navItems[i] && App.navItems[i].hash === hash);
  });
}

function updateNavBadge(index, count) {
  const items = qsa(".nav-item");
  if (items[index]) {
    const wrap = qs(".nav-icon-wrap", items[index]);
    let badge = qs(".badge", wrap);
    if (count > 0) {
      if (!badge) {
        badge = document.createElement("span");
        badge.className = "badge";
        wrap.appendChild(badge);
      }
      badge.textContent = count;
    } else if (badge) {
      badge.remove();
    }
  }
}

// ─── Page Renderer ────────────────────────────────────
async function renderPage() {
  if (App.driverLocationInterval) { clearInterval(App.driverLocationInterval); App.driverLocationInterval = null; }
  if (App.customerTrackInterval) { clearInterval(App.customerTrackInterval); App.customerTrackInterval = null; }
  const hash = location.hash || "#/customer/dashboard";
  updateNavActive(hash);

  const content = $id("app-content");
  const pages = qsa(".page", content);

  let match;
  if ((match = hash.match(/^#\/customer\/(\w+)(?:\?(.+))?$/))) {
    App.role = "customer";
    const page = match[1];
    const params = new URLSearchParams(match[2] || "");
    setupCustomerNav();
    await renderCustomerPage(page, params);
  } else if ((match = hash.match(/^#\/driver\/(\w+)$/))) {
    App.role = "driver";
    const page = match[1];
    setupDriverNav();
    await renderDriverPage(page);
  } else {
    navigate();
  }
}

// ─── CUSTOMER PAGES ───────────────────────────────────
const CUSTOMER_NAV = [
  { hash: "#/customer/dashboard", icon: "🏠", label: "Home" },
  { hash: "#/customer/stations", icon: "⛽", label: "Stations" },
  { hash: "#/customer/order", icon: "📋", label: "Order" },
  { hash: "#/customer/tracking", icon: "📍", label: "Track" },
  { hash: "#/customer/history", icon: "📜", label: "History" },
  { hash: "#/customer/profile", icon: "👤", label: "Profile" },
  { hash: "#/customer/notifications", icon: "🔔", label: "Alerts" },
];

function setupCustomerNav() {
  setupNav(CUSTOMER_NAV);
}

async function renderCustomerPage(page, params) {
  const content = $id("app-content");
  content.scrollTop = 0;
  try {
    switch (page) {
      case "dashboard": await renderCustomerDashboard(content); break;
      case "stations": await renderCustomerStations(content); break;
      case "order": await renderCustomerOrder(content, params); break;
      case "tracking": await renderCustomerTracking(content); break;
      case "history": await renderCustomerHistory(content); break;
      case "profile": await renderCustomerProfile(content); break;
      case "notifications": await renderCustomerNotifications(content); break;
      default: navigate("#/customer/dashboard");
    }
  } catch (e) {
    content.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><div class="empty-title">Error loading page</div><div class="empty-sub">${escapeHtml(e.message)}</div></div>`;
  }
}

async function renderCustomerDashboard(content) {
  updateHeader("FuelGo");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  const data = await API.customerDashboard();
  if (data.status !== "success") return;
  const d = data;
  const active = d.active_order;

  let html = `
    <div style="margin-bottom:16px">
      <div style="font-size:14px;color:var(--text2)">Good ${d.time_of_day},</div>
      <div style="font-size:22px;font-weight:700">${escapeHtml(App.user.first_name || "Customer")}</div>
    </div>
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-icon">📦</div><div class="stat-value">${d.total_orders}</div><div class="stat-label">Total Orders</div></div>
      <div class="stat-card"><div class="stat-icon">✅</div><div class="stat-value">${d.delivered_orders}</div><div class="stat-label">Delivered</div></div>
      <div class="stat-card"><div class="stat-icon">⛽</div><div class="stat-value">${d.total_litres}</div><div class="stat-label">Litres</div></div>
      <div class="stat-card"><div class="stat-icon">⏱️</div><div class="stat-value">${d.avg_delivery_time || "--"}</div><div class="stat-label">Avg Min</div></div>
    </div>`;

  if (active) {
    html += `
      <div class="card" style="border-left:3px solid var(--primary);cursor:pointer" onclick="navigate('#/customer/tracking')">
        <div class="card-header"><span class="card-title">🚚 Active Order #${active.display_id}</span>${statusBadge(active.status)}</div>
        <div style="font-size:13px;color:var(--text2)">${escapeHtml(active.fuel_type)} · ${active.quantity}L · TZS ${Number(active.total_amount).toLocaleString()}</div>
        <div style="font-size:13px;color:var(--text2)">${escapeHtml(active.station_name)}</div>
      </div>`;
  }

  html += `<div class="card"><div class="card-header"><span class="card-title">⛽ Nearby Stations</span></div>`;
  if (d.nearby_stations && d.nearby_stations.length) {
    html += `<div class="h-scroll">`;
    for (const s of d.nearby_stations) {
      html += `
        <div class="card station-card" style="min-width:180px;cursor:pointer" onclick="navigate('#/customer/order?station=${s.id}')">
          <div class="sc-name">${escapeHtml(s.name)}</div>
          <div class="sc-addr">${escapeHtml(s.address)}</div>
          <div class="sc-meta">⭐ ${s.rating} · ${s.review_count} reviews</div>
        </div>`;
    }
    html += `</div>`;
  } else {
    html += `<div class="empty-state"><div class="empty-icon">📍</div><div class="empty-title">No stations nearby</div></div>`;
  }
  html += `</div>`;

  html += `<div class="card"><div class="card-header"><span class="card-title">📜 Recent Orders</span></div>`;
  if (d.recent_orders && d.recent_orders.length) {
    for (const o of d.recent_orders) {
      html += `
        <div class="list-item">
          <div class="li-icon">⛽</div>
          <div class="li-content">
            <div class="li-title">${escapeHtml(o.station_name)}</div>
            <div class="li-sub">${o.fuel_type} · ${o.quantity}L · ${o.created_at}</div>
          </div>
          <div class="li-right">${statusBadge(o.status)}<br><span style="font-size:12px;color:var(--text2)">TZS ${Number(o.total_amount).toLocaleString()}</span></div>
        </div>`;
    }
  } else {
    html += `<div class="empty-state"><div class="empty-icon">📦</div><div class="empty-title">No orders yet</div></div>`;
  }
  html += `</div>`;

  content.innerHTML = html;
}

async function renderCustomerStations(content) {
  updateHeader("Find Stations");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  const data = await API.customerStations();
  if (data.status !== "success") return;
  const stations = data.stations;

  cleanupMap("stationMapInstance");
  let userPos = null;

  let html = `
    <div class="tabs" style="margin-bottom:8px">
      <button class="tab active" onclick="toggleStationView('list', this)">📋 List</button>
      <button class="tab" onclick="toggleStationView('map', this)">🗺️ Map</button>
    </div>
    <div id="station-list-view">
      <div class="search-bar">
        <input type="text" id="station-search" placeholder="Search stations..." oninput="filterStationList()">
        <select id="fuel-filter" onchange="filterStationList()">
          <option value="">All Fuels</option>
          <option value="Petrol">Petrol</option>
          <option value="Diesel">Diesel</option>
          <option value="Kerosene">Kerosene</option>
        </select>
      </div>
      <div id="stations-list">`;

  for (const s of stations) {
    const dist = userPos ? haversine(userPos.lat, userPos.lng, s.lat, s.lng).toFixed(1) : null;
    html += `
      <div class="card station-card" data-sid="${s.id}" data-name="${escapeHtml(s.name).toLowerCase()}" data-fuels="${s.fuels.map(f => f.type).join(",")}" data-lat="${s.lat}" data-lng="${s.lng}">
        <div class="sc-name">${escapeHtml(s.name)}</div>
        <div class="sc-addr">${escapeHtml(s.address)}</div>
        <div class="sc-fuels">${s.fuels.map(f => `<span class="fuel-tag"><span class="ft-dot ${f.available ? 'available' : 'unavailable'}"></span>${f.type} · TZS ${Number(f.price).toLocaleString()}</span>`).join("")}</div>
        <div class="sc-meta">⭐ ${s.rating} · ${s.review_count} reviews · ${s.hours}${dist ? ` · 📍 ${dist} km` : ""}</div>
        <div style="margin-top:10px"><button class="btn btn-primary btn-sm" onclick="navigate('#/customer/order?station=${s.id}')">Order Here</button></div>
      </div>`;
  }
  html += `</div></div>
    <div id="station-map-view" style="display:none">
      <div id="station-map" style="height:400px;border-radius:var(--radius);overflow:hidden;margin-bottom:10px"></div>
      <div style="display:flex;gap:12px;font-size:12px;color:var(--text2);margin-bottom:10px;flex-wrap:wrap">
        <span><span style="display:inline-block;width:12px;height:12px;background:#3b82f6;border-radius:50%;vertical-align:middle;margin-right:4px"></span> You</span>
        <span><span style="display:inline-block;width:12px;height:12px;background:#f97316;border-radius:50%;vertical-align:middle;margin-right:4px"></span> Open</span>
        <span><span style="display:inline-block;width:12px;height:12px;background:#64748b;border-radius:50%;vertical-align:middle;margin-right:4px"></span> Closed</span>
      </div>
      <div id="station-map-list"></div>
    </div>`;

  content.innerHTML = html;

  window.filterStationList = function () {
    const q = $id("station-search").value.toLowerCase();
    const fuel = $id("fuel-filter").value;
    qsa(".station-card").forEach(el => {
      const name = el.dataset.name;
      const fuels = el.dataset.fuels;
      el.style.display = (!q || name.includes(q)) && (!fuel || fuels.includes(fuel)) ? "block" : "none";
    });
  };

  window.toggleStationView = function (view, btn) {
    qsa("#station-list-view, #station-map-view").forEach(v => v.style.display = "none");
    qsa(".tabs .tab").forEach(t => t.classList.remove("active"));
    btn.classList.add("active");
    if (view === "map") {
      $id("station-map-view").style.display = "block";
      initStationMap(stations);
    } else {
      $id("station-list-view").style.display = "block";
    }
  };

  async function initStationMap(stations) {
    if (window.stationMapInstance) return;
    try {
      userPos = await requestLocation();
    } catch {}
    const center = userPos ? [userPos.lat, userPos.lng] : getMapCenter(stations);
    const map = L.map("station-map", { zoomControl: true, scrollWheelZoom: true }).setView(center, 13);
    osmLayer().addTo(map);
    window.stationMapInstance = map;

    if (userPos) {
      L.marker([userPos.lat, userPos.lng], { icon: userIcon() }).addTo(map).bindPopup("<strong>📍 You are here</strong>");
    }
    for (const s of stations) {
      const dist = userPos ? haversine(userPos.lat, userPos.lng, s.lat, s.lng).toFixed(1) : "—";
      const fuelsHtml = s.fuels.map(f => `${f.type}: TZS ${Number(f.price).toLocaleString()}/L${f.available ? "" : " (Out)"}`).join("<br>");
      const popup = `
        <div style="min-width:180px">
          <div style="font-weight:700;font-size:15px;margin-bottom:4px">${escapeHtml(s.name)}</div>
          <div style="color:${s.is_open ? "#22c55e" : "#ef4444"};font-size:12px;font-weight:600">● ${s.is_open ? "Open" : "Closed"}</div>
          <div style="font-size:12px;color:#94a3b8">📍 ${dist} km away</div>
          <div style="font-size:12px;color:#94a3b8">🕐 ${s.hours}</div>
          <div style="font-size:12px;margin:4px 0">${fuelsHtml}</div>
          ${s.is_open ? `<a href="#/customer/order?station=${s.id}" style="display:block;text-align:center;background:#f97316;color:#fff;border-radius:8px;padding:8px;font-size:13px;font-weight:700;margin-top:8px;text-decoration:none">⚡ Order Here</a>` : ""}
        </div>`;
      L.marker([s.lat, s.lng], { icon: stationIcon(s.is_open) }).addTo(map).bindPopup(popup, { maxWidth: 240 });
    }
    setTimeout(() => map.invalidateSize(), 200);
  }
}

async function renderCustomerOrder(content, params) {
  updateHeader("Place Order", true, { label: "Stations", onclick: () => navigate("#/customer/stations") });
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;

  cleanupMap("orderMapInstance");

  const stationsRes = await API.customerStations();
  const stations = stationsRes.stations;
  let deliveryLat = null, deliveryLng = null;
  window._orderDelivery = { lat: null, lng: null, address: "" };

  let html = `
    <div class="form-group">
      <label>⛽ Station</label>
      <select id="order-station" onchange="updateOrderFuels()">
        <option value="">Select station</option>`;
  for (const s of stations) {
    html += `<option value="${s.id}" ${params.get("station") == s.id ? "selected" : ""}>${escapeHtml(s.name)}</option>`;
  }
  html += `</select></div>
    <div class="form-group"><label>Fuel Type</label><select id="order-fuel" onchange="updateOrderTotal()"><option value="">Select station first</option></select></div>
    <div class="form-group"><label>Quantity (Litres)</label>
      <div style="display:flex;gap:8px;align-items:center">
        <button class="btn btn-outline btn-sm" onclick="adjustQty(-5)">−5</button>
        <input type="number" id="order-qty" min="1" value="5" oninput="updateOrderTotal()" style="text-align:center;flex:1">
        <button class="btn btn-outline btn-sm" onclick="adjustQty(5)">+5</button>
      </div>
    </div>

    <div class="card" style="border:2px solid var(--primary);margin-bottom:12px">
      <div class="card-title" style="margin-bottom:8px">📍 Delivery Location</div>
      <div style="margin-bottom:8px;display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn btn-primary btn-sm" id="btn-detect-loc" onclick="detectOrderLocation()">📡 Use My Location</button>
        <button class="btn btn-outline btn-sm" id="btn-pin-map" onclick="toggleOrderMap()">🗺️ Pin on Map</button>
      </div>
      <div id="order-loc-status" style="font-size:13px;color:var(--text2);margin-bottom:8px">📍 Tap "Use My Location" or pin on the map</div>
      <input type="text" id="order-address" placeholder="Delivery address (auto-filled)" style="margin-bottom:8px">
      <input type="hidden" id="order-lat">
      <input type="hidden" id="order-lng">
      <div id="order-map-container" style="display:none;height:260px;border-radius:var(--radius-sm);overflow:hidden;margin-top:8px"></div>
    </div>

    <div class="form-group"><label>📞 Phone</label><input type="tel" id="order-phone" placeholder="Phone number" value="${escapeHtml(App.user.phone || "")}"></div>
    <div class="form-group"><label>💳 Payment Method</label>
      <select id="order-payment">
        <option value="Cash">Cash on Delivery</option>
        <option value="M-Pesa">M-Pesa</option>
        <option value="Tigo Pesa">Tigo Pesa</option>
      </select>
    </div>
    <div class="form-group"><label>📝 Notes (optional)</label><textarea id="order-notes" rows="2" placeholder="Any special instructions"></textarea></div>

    <div class="card" style="background:var(--bg2)">
      <div style="display:flex;justify-content:space-between;font-size:14px"><span>Delivery Fee</span><span>TZS 2,000</span></div>
      <div style="display:flex;justify-content:space-between;font-size:14px;margin-top:4px"><span>Fuel Cost</span><span id="order-fuel-cost">TZS 0</span></div>
      <hr style="border-color:var(--bg3);margin:8px 0">
      <div style="display:flex;justify-content:space-between;font-size:20px;font-weight:700"><span>Total</span><span id="order-total">TZS 2,000</span></div>
    </div>
    <button class="btn btn-primary btn-block" style="margin-top:8px" onclick="submitOrder()">⚡ Place Order</button>`;

  content.innerHTML = html;
  window._stations = stations;

  requestLocation().then(pos => {
    qsa(".station-card").forEach(el => {
      const lat = parseFloat(el.dataset.lat);
      const lng = parseFloat(el.dataset.lng);
      if (lat && lng) {
        const dist = haversine(pos.lat, pos.lng, lat, lng).toFixed(1);
        const meta = el.querySelector(".sc-meta");
        if (meta && !meta.textContent.includes("km")) meta.textContent += ` · 📍 ${dist} km`;
      }
    });
  }).catch(() => {});

  if (params.get("station")) {
    $id("order-station").value = params.get("station");
    updateOrderFuels();
  }

  window._orderMapInstance = null;
  window._orderMarker = null;

  window.detectOrderLocation = async function () {
    const status = $id("order-loc-status");
    const btn = $id("btn-detect-loc");
    btn.disabled = true;
    btn.innerHTML = '⏳ Detecting...';
    status.innerHTML = '<span style="color:var(--primary)">📍 Getting your location...</span>';
    try {
      const pos = await requestLocation();
      deliveryLat = pos.lat;
      deliveryLng = pos.lng;
      $id("order-lat").value = pos.lat;
      $id("order-lng").value = pos.lng;
      const addr = await reverseGeocode(pos.lat, pos.lng);
      _orderDelivery.address = addr;
      $id("order-address").value = addr;
      status.innerHTML = `<span style="color:var(--success)">✅ Location captured: ${escapeHtml(addr)}</span>`;
      btn.innerHTML = '📡 Update Location';
      btn.disabled = false;
      if (window._orderMapInstance && window._orderMarker) {
        window._orderMarker.setLatLng([pos.lat, pos.lng]);
        window._orderMapInstance.setView([pos.lat, pos.lng], 16);
      }
    } catch (e) {
      status.innerHTML = `<span style="color:var(--danger)">⚠️ ${e.message}. Please pin on the map.</span>`;
      btn.innerHTML = '📡 Try Again';
      btn.disabled = false;
      toggleOrderMap();
    }
  };

  window.toggleOrderMap = function () {
    const container = $id("order-map-container");
    const btn = $id("btn-pin-map");
    const isVisible = container.style.display === "block";
    container.style.display = isVisible ? "none" : "block";
    btn.classList.toggle("active", !isVisible);

    if (!isVisible && !window._orderMapInstance) {
      const cLat = deliveryLat || -6.8235;
      const cLng = deliveryLng || 39.2695;
      const map = L.map("order-map-container", { zoomControl: true, scrollWheelZoom: true }).setView([cLat, cLng], 15);
      osmLayer().addTo(map);
      window._orderMapInstance = map;

      if (deliveryLat) {
        window._orderMarker = L.marker([deliveryLat, deliveryLng], { icon: deliveryIcon(), draggable: true })
          .addTo(map)
          .on("dragend", async (e) => {
            const p = e.target.getLatLng();
            await onOrderMapClick(p.lat, p.lng);
          });
      }

      map.on("click", async (e) => {
        await onOrderMapClick(e.latlng.lat, e.latlng.lng);
      });

      setTimeout(() => map.invalidateSize(), 200);
    } else if (!isVisible && window._orderMapInstance) {
      setTimeout(() => window._orderMapInstance.invalidateSize(), 200);
    }
  };

  async function onOrderMapClick(lat, lng) {
    deliveryLat = lat;
    deliveryLng = lng;
    $id("order-lat").value = lat;
    $id("order-lng").value = lng;
    const status = $id("order-loc-status");
    status.innerHTML = '<span style="color:var(--primary)">📍 Getting address...</span>';

    if (window._orderMarker) {
      window._orderMarker.setLatLng([lat, lng]);
    } else if (window._orderMapInstance) {
      window._orderMarker = L.marker([lat, lng], { icon: deliveryIcon(), draggable: true })
        .addTo(window._orderMapInstance)
        .on("dragend", async (e) => {
          const p = e.target.getLatLng();
          await onOrderMapClick(p.lat, p.lng);
        });
    }
    window._orderMapInstance.setView([lat, lng], 16);

    const addr = await reverseGeocode(lat, lng);
    _orderDelivery.address = addr;
    $id("order-address").value = addr;
    status.innerHTML = `<span style="color:var(--success)">✅ Pinned: ${escapeHtml(addr)}</span>`;
  }

  window.adjustQty = function (delta) {
    const inp = $id("order-qty");
    inp.value = Math.max(1, Math.min(200, (parseInt(inp.value) || 5) + delta));
    updateOrderTotal();
  };
}

window.updateOrderFuels = function () {
  const sel = $id("order-station");
  const fuelSel = $id("order-fuel");
  const sid = parseInt(sel.value);
  fuelSel.innerHTML = '<option value="">Select fuel</option>';
  if (!sid) return;
  const s = window._stations.find(st => st.id === sid);
  if (s && s.fuels) {
    for (const f of s.fuels) {
      if (f.available) fuelSel.innerHTML += `<option value="${f.type}" data-price="${f.price}">${f.type} · TZS ${Number(f.price).toLocaleString()}/L</option>`;
    }
  }
  updateOrderTotal();
};

window.updateOrderTotal = function () {
  const fuelSel = $id("order-fuel");
  const qty = parseFloat($id("order-qty").value) || 0;
  const opt = fuelSel.options[fuelSel.selectedIndex];
  const price = opt ? parseFloat(opt.dataset.price || "0") : 0;
  const fuelCost = price * qty;
  const total = fuelCost + 2000;
  $id("order-fuel-cost").textContent = `TZS ${fuelCost.toLocaleString()}`;
  $id("order-total").textContent = `TZS ${total.toLocaleString()}`;
};

window.submitOrder = async function () {
  const stationId = parseInt($id("order-station").value);
  const fuelType = $id("order-fuel").value;
  const qty = parseFloat($id("order-qty").value);
  const address = $id("order-address").value;
  const phone = $id("order-phone").value;
  const payment = $id("order-payment").value;
  const notes = $id("order-notes").value;
  const lat = $id("order-lat").value;
  const lng = $id("order-lng").value;

  if (!stationId || !fuelType || !qty) {
    showToast("Please select station, fuel and quantity", "error");
    return;
  }
  if (!address || !lat || !lng) {
    showToast("Please set your delivery location (use GPS or pin on map)", "error");
    return;
  }

  try {
    showLoading(true);
    const res = await API.createOrder({
      station_id: stationId, fuel_type: fuelType, quantity: qty,
      delivery_address: address, phone, payment_method: payment,
      notes, lat: parseFloat(lat), lng: parseFloat(lng),
    });
    showLoading(false);
    if (res.status === "success") {
      showToast("Order placed successfully! 🎉", "success");
      navigate("#/customer/tracking");
    }
  } catch (e) {
    showLoading(false);
    showToast(e.message, "error");
  }
};

async function renderCustomerTracking(content) {
  updateHeader("Track Delivery");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  cleanupMap("trackMapInstance");
  const data = await API.customerTracking();
  if (data.status !== "success") return;
  const o = data.active_order;
  if (!o) {
    content.innerHTML = `<div class="empty-state"><div class="empty-icon">✅</div><div class="empty-title">No Active Order</div><div class="empty-sub">Place an order to track it here</div><button class="btn btn-primary" style="margin-top:16px" onclick="navigate('#/customer/order')">Order Now</button></div>`;
    return;
  }

  const steps = [
    { label: "Order Placed", time: o.created_at, done: true },
    { label: "Confirmed", time: o.confirmed_at, done: !!o.confirmed_at },
    { label: "Picked Up", time: o.picked_up_at, done: !!o.picked_up_at },
    { label: "Delivered", time: null, done: o.status === "delivered" },
  ];
  const currentIdx = steps.findLastIndex(s => s.done);

  let html = `
    <div class="card">
      <div class="card-header"><span class="card-title">Order #${o.display_id}</span>${statusBadge(o.status)}</div>
      <div style="font-size:14px"><strong>${escapeHtml(o.station_name)}</strong></div>
      <div style="font-size:13px;color:var(--text2)">${escapeHtml(o.fuel_type)} · ${o.quantity}L · TZS ${Number(o.total_amount).toLocaleString()}</div>
      <div style="font-size:13px;color:var(--text2)">📍 ${escapeHtml(o.delivery_address)}</div>
    </div>`;

  if (o.driver) {
    html += `
      <div class="card">
        <div class="card-title" style="margin-bottom:8px">🚚 Driver</div>
        <div style="display:flex;gap:12px;align-items:center">
          <div class="avatar" style="width:48px;height:48px;font-size:20px;margin:0">👤</div>
          <div>
            <div style="font-weight:600">${escapeHtml(o.driver.name)}</div>
            <div style="font-size:13px;color:var(--text2)">📞 ${escapeHtml(o.driver.phone)}</div>
            <div style="font-size:13px;color:var(--text2)">🚗 ${escapeHtml(o.driver.plate)} · ⭐ ${o.driver.rating}</div>
          </div>
        </div>
      </div>`;
  }

  html += `<div class="card"><div class="card-title" style="margin-bottom:12px">Progress</div><ul class="stepper">`;
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i];
    const cls = s.done ? "completed" : (i === currentIdx + 1 ? "active" : "");
    html += `<li class="step ${cls}"><div class="step-dot">${s.done ? "✓" : (i === currentIdx + 1 ? "●" : "")}</div><div class="step-content"><div class="step-label">${s.label}</div>${s.time ? `<div class="step-time">${s.time}</div>` : ""}</div></li>`;
  }
  html += `</ul></div>`;

  if (o.status === "delivering") {
    html += `<button class="btn btn-success btn-block" onclick="confirmDelivery(${o.id})">✓ Confirm Delivery</button>`;
  }
  if (["pending", "confirmed", "assigned"].includes(o.status)) {
    html += `<button class="btn btn-danger btn-block" style="margin-top:8px" onclick="cancelOrder(${o.id})">✕ Cancel Order</button>`;
  }

  content.innerHTML = html;

  if (o.delivery_address) {
    const mapDiv = document.createElement("div");
    mapDiv.id = "track-map";
    mapDiv.style.cssText = "height:220px;border-radius:var(--radius);overflow:hidden;margin-top:12px";
    const firstCard = qs(".card", content);
    if (firstCard) firstCard.after(mapDiv);

    let map, userMarker, driverMarker;
    try {
      const pos = await requestLocation();
      map = L.map("track-map", { zoomControl: false, scrollWheelZoom: true }).setView([pos.lat, pos.lng], 14);
      osmLayer().addTo(map);
      userMarker = L.marker([pos.lat, pos.lng], { icon: userIcon() }).addTo(map).bindPopup("<strong>📍 Your Location</strong>");
    } catch {
      map = L.map("track-map", { zoomControl: false, scrollWheelZoom: true }).setView([-6.8235, 39.2695], 10);
      osmLayer().addTo(map);
    }
    window.trackMapInstance = map;
    setTimeout(() => map.invalidateSize(), 200);

    if (o.driver && o.driver.current_lat && o.driver.current_lng) {
      driverMarker = L.marker([o.driver.current_lat, o.driver.current_lng], { icon: driverIcon() }).addTo(map).bindPopup(`<strong>🚚 ${escapeHtml(o.driver.name)}</strong><br>${o.driver.location_updated_at ? "Updated: " + o.driver.location_updated_at : ""}`);
    }

    if (o.status === "delivering") {
      App.customerTrackInterval = setInterval(async () => {
        try {
          const res = await API.customerTracking();
          if (res.status !== "success" || !res.active_order) return;
          const d = res.active_order.driver;
          if (d && d.current_lat && d.current_lng && map) {
            if (driverMarker) {
              driverMarker.setLatLng([d.current_lat, d.current_lng]);
              driverMarker.setPopupContent(`<strong>🚚 ${escapeHtml(d.name)}</strong><br>Updated: ${d.location_updated_at || "recently"}`);
            } else {
              driverMarker = L.marker([d.current_lat, d.current_lng], { icon: driverIcon() }).addTo(map).bindPopup(`<strong>🚚 ${escapeHtml(d.name)}</strong>`);
            }
          }
        } catch {}
      }, 10000);
    }
  }
}

window.confirmDelivery = async function (id) {
  try {
    showLoading(true);
    const res = await API.confirmDelivery(id);
    showLoading(false);
    if (res.status === "success") { showToast("Delivery confirmed!", "success"); navigate("#/customer/tracking"); }
  } catch (e) { showLoading(false); showToast(e.message, "error"); }
};

window.cancelOrder = async function (id) {
  if (!confirm("Cancel this order?")) return;
  try {
    showLoading(true);
    const res = await API.cancelOrder(id);
    showLoading(false);
    if (res.status === "success") { showToast("Order cancelled", "success"); navigate("#/customer/tracking"); }
  } catch (e) { showLoading(false); showToast(e.message, "error"); }
};

async function renderCustomerHistory(content) {
  updateHeader("Order History");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  const data = await API.customerHistory();
  if (data.status !== "success") return;

  if (!data.orders || !data.orders.length) {
    content.innerHTML = `<div class="empty-state"><div class="empty-icon">📜</div><div class="empty-title">No orders yet</div><div class="empty-sub">Your order history will appear here</div></div>`;
    return;
  }

  const statuses = ["All", "Pending", "Confirmed", "Delivered", "Cancelled"];
  let html = `<div class="tabs" id="history-tabs">`;
  for (const s of statuses) {
    html += `<button class="tab ${s === 'All' ? 'active' : ''}" onclick="filterHistory('${s}')">${s}</button>`;
  }
  html += `</div><div id="history-list">`;
  for (const o of data.orders) {
    html += `
      <div class="order-card card" data-status="${o.status}">
        <div class="oc-row"><span class="oc-title">#${o.id} · ${escapeHtml(o.station_name)}</span>${statusBadge(o.status)}</div>
        <div class="oc-sub">${escapeHtml(o.fuel_type)} · ${o.quantity}L · TZS ${Number(o.total_amount).toLocaleString()}</div>
        <div class="oc-sub">${o.created_at} · ${escapeHtml(o.payment_method)}</div>
      </div>`;
  }
  html += `</div>`;
  content.innerHTML = html;

  window.filterHistory = function (status) {
    qsa("#history-tabs .tab").forEach(t => t.classList.toggle("active", t.textContent === status));
    qsa(".order-card").forEach(el => {
      el.style.display = status === "All" || el.dataset.status === status.toLowerCase() ? "block" : "none";
    });
  };
}

async function renderCustomerProfile(content) {
  updateHeader("My Profile");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  const data = await API.customerProfile();
  if (data.status !== "success") return;
  const p = data.profile;
  const s = data.stats;

  let html = `
    <div style="text-align:center;margin-bottom:16px">
      <div class="avatar">${(App.user.first_name || "C")[0].toUpperCase()}</div>
      <div style="font-size:18px;font-weight:600">${escapeHtml(p.first_name)} ${escapeHtml(p.last_name)}</div>
      <div style="font-size:13px;color:var(--text2)">${escapeHtml(p.email)}</div>
    </div>
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">${s.total_orders}</div><div class="stat-label">Orders</div></div>
      <div class="stat-card"><div class="stat-value">${s.delivered_orders}</div><div class="stat-label">Delivered</div></div>
      <div class="stat-card"><div class="stat-value">${s.total_litres}</div><div class="stat-label">Litres</div></div>
      <div class="stat-card"><div class="stat-value">${escapeHtml(p.date_joined)}</div><div class="stat-label">Member</div></div>
    </div>
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">Edit Profile</div>
      <div class="form-group"><label>First Name</label><input type="text" id="pf-fname" value="${escapeHtml(p.first_name)}"></div>
      <div class="form-group"><label>Last Name</label><input type="text" id="pf-lname" value="${escapeHtml(p.last_name)}"></div>
      <div class="form-group"><label>Phone</label><input type="tel" id="pf-phone" value="${escapeHtml(p.phone || "")}"></div>
      <button class="btn btn-primary btn-block" onclick="updateCustomerProfile()">Save Changes</button>
    </div>
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">Change Password</div>
      <div class="form-group"><label>Current Password</label><input type="password" id="cp-old"></div>
      <div class="form-group"><label>New Password</label><input type="password" id="cp-new1"></div>
      <div class="form-group"><label>Confirm Password</label><input type="password" id="cp-new2"></div>
      <button class="btn btn-outline btn-block" onclick="changePassword()">Change Password</button>
    </div>
    <button class="btn btn-danger btn-block" style="margin-top:8px" onclick="logoutUser()">Logout</button>`;

  content.innerHTML = html;
}

window.updateCustomerProfile = async function () {
  try {
    showLoading(true);
    const res = await API.updateCustomerProfile({
      first_name: $id("pf-fname").value,
      last_name: $id("pf-lname").value,
      phone: $id("pf-phone").value,
    });
    showLoading(false);
    if (res.status === "success") showToast("Profile updated!", "success");
  } catch (e) { showLoading(false); showToast(e.message, "error"); }
};

window.changePassword = async function () {
  const old = $id("cp-old").value;
  const p1 = $id("cp-new1").value;
  const p2 = $id("cp-new2").value;
  if (!old || !p1 || !p2) { showToast("Fill all fields", "error"); return; }
  if (p1 !== p2) { showToast("Passwords don't match", "error"); return; }
  try {
    showLoading(true);
    const res = await API.changePassword({ old_password: old, password1: p1, password2: p2 });
    showLoading(false);
    if (res.status === "success") { showToast("Password changed!", "success"); $id("cp-old").value = $id("cp-new1").value = $id("cp-new2").value = ""; }
  } catch (e) { showLoading(false); showToast(e.message, "error"); }
};

async function renderCustomerNotifications(content) {
  updateHeader("Notifications");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  const data = await API.customerNotifications();
  if (data.status !== "success") return;

  let html = `<div style="text-align:right;margin-bottom:8px">`;
  if (data.unread_count > 0) html += `<button class="btn btn-sm btn-outline" onclick="markAllRead()">Mark All Read</button>`;
  html += `</div><div id="notif-list">`;

  if (!data.notifications || !data.notifications.length) {
    html += `<div class="empty-state"><div class="empty-icon">🔔</div><div class="empty-title">No notifications</div></div>`;
  } else {
    for (const n of data.notifications) {
      html += `
        <div class="notif-item ${n.is_read ? "" : "unread"}">
          <div class="notif-title">${escapeHtml(n.title)}</div>
          <div class="notif-message">${escapeHtml(n.message)}</div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px">
            <span class="notif-time">${n.time}</span>
            ${n.is_read ? "" : `<button class="btn btn-sm btn-outline" onclick="dismissNotif(${n.id})">Dismiss</button>`}
          </div>
        </div>`;
    }
  }
  html += `</div>`;
  content.innerHTML = html;
}

window.dismissNotif = async function (id) {
  try {
    await API.dismissNotification(id);
    renderPage();
  } catch {}
};

window.markAllRead = async function () {
  try {
    await API.markNotificationsRead();
    renderPage();
  } catch {}
};

// ─── DRIVER PAGES ─────────────────────────────────────
const DRIVER_NAV = [
  { hash: "#/driver/dashboard", icon: "🏠", label: "Home" },
  { hash: "#/driver/orders", icon: "📋", label: "Orders" },
  { hash: "#/driver/active", icon: "📍", label: "Active" },
  { hash: "#/driver/earnings", icon: "💰", label: "Earnings" },
  { hash: "#/driver/history", icon: "📜", label: "History" },
  { hash: "#/driver/profile", icon: "👤", label: "Profile" },
  { hash: "#/driver/notifications", icon: "🔔", label: "Alerts" },
];

function setupDriverNav() {
  setupNav(DRIVER_NAV);
}

async function renderDriverPage(page) {
  const content = $id("app-content");
  content.scrollTop = 0;
  try {
    switch (page) {
      case "dashboard": await renderDriverDashboard(content); break;
      case "orders": await renderDriverOrders(content); break;
      case "active": await renderDriverActive(content); break;
      case "earnings": await renderDriverEarnings(content); break;
      case "history": await renderDriverHistory(content); break;
      case "profile": await renderDriverProfile(content); break;
      case "notifications": await renderDriverNotifications(content); break;
      default: navigate("#/driver/dashboard");
    }
  } catch (e) {
    content.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><div class="empty-title">Error</div><div class="empty-sub">${escapeHtml(e.message)}</div></div>`;
  }
}

async function renderDriverDashboard(content) {
  updateHeader("Driver Dashboard", false, {
    label: "Duty",
    onclick: toggleDuty,
  });
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  const data = await API.driverDashboard();
  if (data.status !== "success") return;
  const d = data;

  let html = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <div>
        <div style="font-size:14px;color:var(--text2)">Good ${d.time_of_day},</div>
        <div style="font-size:22px;font-weight:700">${escapeHtml(App.user.driver?.name || "Driver")}</div>
      </div>
      <div class="duty-indicator ${d.on_duty ? 'duty-on' : 'duty-off'}">
        <span class="duty-dot"></span> ${d.on_duty ? "On Duty" : "Off Duty"}
      </div>
    </div>
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-icon">📦</div><div class="stat-value">${d.today_deliveries}</div><div class="stat-label">Today</div></div>
      <div class="stat-card"><div class="stat-icon">🏆</div><div class="stat-value">${d.total_deliveries}</div><div class="stat-label">Total</div></div>
      <div class="stat-card"><div class="stat-icon">⭐</div><div class="stat-value">${d.rating}</div><div class="stat-label">Rating</div></div>
      <div class="stat-card"><div class="stat-icon">⏱️</div><div class="stat-value">${d.on_time_pct}%</div><div class="stat-label">On Time</div></div>
    </div>
    <div class="card"><div class="card-title" style="margin-bottom:8px">💰 Earnings</div>
      <div class="stats-grid" style="grid-template-columns:repeat(2,1fr)">
        <div class="stat-card"><div class="stat-value">TZS ${Number(d.today_earnings).toLocaleString()}</div><div class="stat-label">Today</div></div>
        <div class="stat-card"><div class="stat-value">TZS ${Number(d.weekly_earnings).toLocaleString()}</div><div class="stat-label">This Week</div></div>
      </div>
      <div class="bar-chart">`;
  for (const ed of d.earnings_data) {
    html += `<div class="bar-item"><div class="bar" style="height:${ed.pct}%"></div><div class="bar-label">${ed.day}</div></div>`;
  }
  html += `</div></div>`;

  if (d.assigned_orders && d.assigned_orders.length) {
    html += `<div class="card"><div class="card-title" style="margin-bottom:8px">📋 New Orders</div>`;
    for (const o of d.assigned_orders) {
      html += `
        <div class="list-item" onclick="navigate('#/driver/active')">
          <div class="li-icon">⛽</div>
          <div class="li-content">
            <div class="li-title">${escapeHtml(o.station_name)} → ${escapeHtml(o.customer_name)}</div>
            <div class="li-sub">${o.fuel_type} · ${o.quantity}L · ${escapeHtml(o.delivery_address)}</div>
          </div>
          <div class="li-right"><span style="color:var(--primary);font-weight:600">TZS ${Number(o.total_amount).toLocaleString()}</span></div>
        </div>`;
    }
    html += `</div>`;
  }

  if (d.recent_deliveries && d.recent_deliveries.length) {
    html += `<div class="card"><div class="card-title" style="margin-bottom:8px">✅ Recent Deliveries</div>`;
    for (const r of d.recent_deliveries) {
      html += `<div class="list-item"><div class="li-icon">✅</div><div class="li-content"><div class="li-title">${escapeHtml(r.customer_name)}</div><div class="li-sub">${r.fuel_type} · ${r.quantity}L · ${r.completed_at}</div></div><div class="li-right"><span style="font-size:14px;font-weight:600;color:var(--success)">TZS ${Number(r.driver_earning).toLocaleString()}</span></div></div>`;
    }
    html += `</div>`;
  }

  content.innerHTML = html;
  updateHeader("Driver Dashboard", false, {
    label: d.on_duty ? "🟢 On" : "🔴 Off",
    onclick: toggleDuty,
  });
}

window.toggleDuty = async function () {
  try {
    const res = await API.toggleDuty();
    if (res.status === "success") {
      showToast(res.on_duty ? "You're now ON DUTY" : "You're now OFF DUTY", res.on_duty ? "success" : "error");
      renderPage();
    }
  } catch (e) { showToast(e.message, "error"); }
};

async function renderDriverOrders(content) {
  updateHeader("Assigned Orders");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  const data = await API.driverOrders();
  if (data.status !== "success") return;

  if (!data.orders || !data.orders.length) {
    content.innerHTML = `<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-title">No orders assigned</div><div class="empty-sub">Waiting for new deliveries...</div></div>`;
    return;
  }

  let html = `<div class="search-bar"><input type="text" placeholder="Search orders..." oninput="filterDriverOrders(this.value)"></div><div id="driver-orders-list">`;
  for (const o of data.orders) {
    html += `
      <div class="card order-card" data-search="${escapeHtml(o.customer_name).toLowerCase()} ${o.fuel_type.toLowerCase()}">
        <div class="oc-row">
          <span class="oc-title">📍 ${escapeHtml(o.customer_name)}</span>
          ${statusBadge(o.status)}
        </div>
        <div class="oc-sub">⛽ ${escapeHtml(o.station_name)} · ${o.fuel_type} · ${o.quantity}L</div>
        <div class="oc-sub">📞 ${escapeHtml(o.customer_phone)}</div>
        <div class="oc-sub">🏠 ${escapeHtml(o.delivery_address)}</div>
        <div class="oc-actions">
          ${o.status === "assigned" ? `<button class="btn btn-primary btn-sm" onclick="driverUpdateStatus(${o.id},'picked_up')">Start Delivery</button>` : ""}
          ${o.status === "picked_up" ? `<button class="btn btn-primary btn-sm" onclick="driverUpdateStatus(${o.id},'delivering')">Mark Delivering</button>` : ""}
          ${o.status === "delivering" ? `<button class="btn btn-success btn-sm" onclick="driverUpdateStatus(${o.id},'delivered')">Mark Delivered</button>` : ""}
        </div>
      </div>`;
  }
  html += `</div>`;
  content.innerHTML = html;
  window.filterDriverOrders = function (q) {
    qsa("#driver-orders-list .order-card").forEach(el => {
      el.style.display = !q || el.dataset.search.includes(q.toLowerCase()) ? "block" : "none";
    });
  };
}

window.driverUpdateStatus = async function (orderId, status) {
  try {
    showLoading(true);
    const res = await API.updateOrderStatus(orderId, status);
    showLoading(false);
    if (res.status === "success") {
      showToast(`Status updated to ${status}`, "success");
      renderPage();
    }
  } catch (e) { showLoading(false); showToast(e.message, "error"); }
};

async function renderDriverActive(content) {
  updateHeader("Active Delivery");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  cleanupMap("driverRouteMap");
  const data = await API.driverActive();
  if (data.status !== "success") return;
  const o = data.active_order;

  if (!o) {
    content.innerHTML = `<div class="empty-state"><div class="empty-icon">📍</div><div class="empty-title">No Active Delivery</div><div class="empty-sub">Check assigned orders</div><button class="btn btn-primary" style="margin-top:16px" onclick="navigate('#/driver/orders')">View Orders</button></div>`;
    return;
  }

  const statusOrder = ["assigned", "picked_up", "delivering", "delivered"];
  const currentIdx = statusOrder.indexOf(o.status);

  let html = `
    <div class="card">
      <div class="card-header"><span class="card-title">Order #${o.display_id}</span>${statusBadge(o.status)}</div>
      <div style="font-size:14px;font-weight:500">${escapeHtml(o.customer_name)}</div>
      <div style="font-size:13px;color:var(--text2);margin-top:4px">📞 ${escapeHtml(o.customer_phone)}</div>
      <div style="font-size:13px;color:var(--text2)">⛽ ${escapeHtml(o.station_name)}</div>
      <div style="font-size:13px;color:var(--text2)">📍 ${escapeHtml(o.delivery_address)}</div>
      <div style="font-size:13px;color:var(--text2);margin-top:4px">${o.fuel_type} · ${o.quantity}L · TZS ${Number(o.total_amount).toLocaleString()}</div>
    </div>
    <div class="card"><div class="card-title" style="margin-bottom:12px">Progress</div><ul class="stepper">`;

  const stepLabels = ["Assigned", "Picked Up", "Delivering", "Delivered"];
  for (let i = 0; i < stepLabels.length; i++) {
    const cls = i < currentIdx ? "completed" : (i === currentIdx ? "active" : "");
    html += `<li class="step ${cls}"><div class="step-dot">${i < currentIdx ? "✓" : (i === currentIdx ? "●" : "")}</div><div class="step-content"><div class="step-label">${stepLabels[i]}</div></div></li>`;
  }
  html += `</ul></div>`;

  if (o.customer_lat && o.customer_lng && o.station_lat && o.station_lng) {
    const midLat = (o.station_lat + o.customer_lat) / 2;
    const midLng = (o.station_lng + o.customer_lng) / 2;
    const dist = haversine(o.station_lat, o.station_lng, o.customer_lat, o.customer_lng).toFixed(1);
    html += `
      <div class="card">
        <div class="card-title" style="margin-bottom:8px">🗺️ Route (${dist} km)</div>
        <div id="driver-route-map" style="height:260px;border-radius:var(--radius-sm);overflow:hidden"></div>
        <div style="margin-top:8px;display:flex;gap:12px;font-size:12px;color:var(--text2);flex-wrap:wrap">
          <span><span style="display:inline-block;width:12px;height:12px;background:#22c55e;border-radius:50%;vertical-align:middle;margin-right:4px"></span> ${escapeHtml(o.station_name)}</span>
          <span><span style="display:inline-block;width:12px;height:12px;background:#ef4444;border-radius:50%;vertical-align:middle;margin-right:4px"></span> ${escapeHtml(o.customer_name)}</span>
          <a href="https://www.openstreetmap.org/directions?from=${o.station_lat}%2C${o.station_lng}&to=${o.customer_lat}%2C${o.customer_lng}" target="_blank" style="color:var(--primary)">Open in Maps ↗</a>
        </div>
      </div>`;
  }

  html += `<div style="display:flex;flex-direction:column;gap:8px;margin-top:8px">`;
  if (o.status === "assigned") html += `<button class="btn btn-primary btn-block" onclick="driverUpdateStatus(${o.id},'picked_up')">📥 Picked Up Fuel</button>`;
  if (o.status === "picked_up") html += `<button class="btn btn-primary btn-block" onclick="driverUpdateStatus(${o.id},'delivering')">🚚 Start Delivery</button>`;
  if (o.status === "delivering") html += `<button class="btn btn-success btn-block" onclick="driverUpdateStatus(${o.id},'delivered')">✅ Mark Delivered</button>`;
  html += `</div>`;

  content.innerHTML = html;

  if (o.customer_lat && o.customer_lng && o.station_lat && o.station_lng) {
    setTimeout(() => {
      const midLat2 = (o.station_lat + o.customer_lat) / 2;
      const midLng2 = (o.station_lng + o.customer_lng) / 2;
      const map = L.map("driver-route-map", { zoomControl: true, scrollWheelZoom: true }).setView([midLat2, midLng2], 13);
      osmLayer().addTo(map);
      L.marker([o.station_lat, o.station_lng], { icon: routeStartIcon() }).addTo(map).bindPopup(`<strong>⛽ ${escapeHtml(o.station_name)}</strong>`);
      L.marker([o.customer_lat, o.customer_lng], { icon: routeEndIcon() }).addTo(map).bindPopup(`<strong>📍 ${escapeHtml(o.customer_name)}</strong><br>${escapeHtml(o.delivery_address)}`);
      const latlngs = [[o.station_lat, o.station_lng], [o.customer_lat, o.customer_lng]];
      L.polyline(latlngs, { color: "#f97316", weight: 3, opacity: 0.7, dashArray: "8, 8" }).addTo(map);
      window.driverRouteMap = map;
      setTimeout(() => map.invalidateSize(), 200);
    }, 100);
  }

  if (o.status === "delivering") {
    const sendLocation = async () => {
      try {
        const pos = await requestLocation();
        if (pos && pos.lat && pos.lng) {
          await API.updateLocation(pos.lat, pos.lng);
        }
      } catch {}
    };
    sendLocation();
    App.driverLocationInterval = setInterval(sendLocation, 8000);
  }
}

async function renderDriverEarnings(content) {
  updateHeader("Earnings");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  const data = await API.driverEarnings();
  if (data.status !== "success") return;
  const d = data;

  let html = `
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-icon">💰</div><div class="stat-value" style="font-size:18px">TZS ${Number(d.today_earnings).toLocaleString()}</div><div class="stat-label">Today</div></div>
      <div class="stat-card"><div class="stat-icon">📅</div><div class="stat-value" style="font-size:18px">TZS ${Number(d.weekly_earnings).toLocaleString()}</div><div class="stat-label">This Week</div></div>
      <div class="stat-card"><div class="stat-icon">📆</div><div class="stat-value" style="font-size:18px">TZS ${Number(d.monthly_earnings).toLocaleString()}</div><div class="stat-label">This Month</div></div>
      <div class="stat-card"><div class="stat-icon">📦</div><div class="stat-value">${d.total_deliveries}</div><div class="stat-label">Deliveries</div></div>
    </div>
    <div class="card"><div class="card-title" style="margin-bottom:8px">Weekly Earnings</div>
      <div class="bar-chart">`;
  for (const ed of d.earnings_data) {
    html += `<div class="bar-item"><div class="bar" style="height:${ed.pct}%"></div><div class="bar-label">${ed.day}</div></div>`;
  }
  html += `</div><div style="display:flex;justify-content:space-around;font-size:12px;color:var(--text2)">`;
  for (const ed of d.earnings_data) {
    html += `<span>TZS ${ed.amount.toLocaleString()}</span>`;
  }
  html += `</div></div>`;
  content.innerHTML = html;
}

async function renderDriverHistory(content) {
  updateHeader("Delivery History");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  const data = await API.driverHistory();
  if (data.status !== "success") return;

  if (!data.deliveries || !data.deliveries.length) {
    content.innerHTML = `<div class="empty-state"><div class="empty-icon">📜</div><div class="empty-title">No deliveries yet</div></div>`;
    return;
  }

  let html = ``;
  for (const d of data.deliveries) {
    html += `
      <div class="card order-card">
        <div class="oc-row"><span class="oc-title">${escapeHtml(d.customer_name)}</span><span style="font-size:14px;font-weight:600;color:var(--success)">TZS ${Number(d.driver_earning).toLocaleString()}</span></div>
        <div class="oc-sub">${d.fuel_type} · ${d.quantity}L · ${escapeHtml(d.delivery_address)}</div>
        <div class="oc-sub">✅ ${d.completed_at}</div>
      </div>`;
  }
  content.innerHTML = html;
}

async function renderDriverProfile(content) {
  updateHeader("My Profile");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  const data = await API.driverProfile();
  if (data.status !== "success") return;
  const p = data.profile;
  const s = data.stats;

  let html = `
    <div style="text-align:center;margin-bottom:16px">
      <div class="avatar">${(p.name || "D")[0].toUpperCase()}</div>
      <div style="font-size:18px;font-weight:600">${escapeHtml(p.name)}</div>
      <div style="font-size:13px;color:var(--text2)">${escapeHtml(p.email)}</div>
      <div style="margin-top:8px">
        <span class="duty-indicator ${p.on_duty ? 'duty-on' : 'duty-off'}"><span class="duty-dot"></span> ${p.on_duty ? "On Duty" : "Off Duty"}</span>
      </div>
    </div>
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">⭐ ${p.rating}</div><div class="stat-label">Rating</div></div>
      <div class="stat-card"><div class="stat-value">${s.total_deliveries}</div><div class="stat-label">Deliveries</div></div>
      <div class="stat-card"><div class="stat-value">${s.on_time_pct}%</div><div class="stat-label">On Time</div></div>
      <div class="stat-card"><div class="stat-value" style="font-size:12px">${escapeHtml(p.station_name || "Unassigned")}</div><div class="stat-label">Station</div></div>
    </div>
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">Edit Profile</div>
      <div class="form-group"><label>First Name</label><input type="text" id="dp-fname" value="${escapeHtml(p.first_name || "")}"></div>
      <div class="form-group"><label>Last Name</label><input type="text" id="dp-lname" value="${escapeHtml(p.last_name || "")}"></div>
      <div class="form-group"><label>Email</label><input type="email" id="dp-email" value="${escapeHtml(p.email)}"></div>
      <div class="form-group"><label>Phone</label><input type="tel" id="dp-phone" value="${escapeHtml(p.phone || "")}"></div>
      <div class="form-group"><label>Plate Number</label><input type="text" id="dp-plate" value="${escapeHtml(p.plate_number || "")}"></div>
      <button class="btn btn-primary btn-block" onclick="updateDriverProfile()">Save Changes</button>
    </div>
    <button class="btn btn-danger btn-block" style="margin-top:8px" onclick="logoutUser()">Logout</button>`;

  content.innerHTML = html;
}

window.updateDriverProfile = async function () {
  try {
    showLoading(true);
    const res = await API.updateDriverProfile({
      first_name: $id("dp-fname").value,
      last_name: $id("dp-lname").value,
      email: $id("dp-email").value,
      phone: $id("dp-phone").value,
      plate_number: $id("dp-plate").value,
    });
    showLoading(false);
    if (res.status === "success") showToast("Profile updated!", "success");
  } catch (e) { showLoading(false); showToast(e.message, "error"); }
};

async function renderDriverNotifications(content) {
  updateHeader("Notifications");
  content.innerHTML = `<div class="loading"><span class="spinner"></span> Loading...</div>`;
  const data = await API.driverNotifications();
  if (data.status !== "success") return;

  let html = `<div style="text-align:right;margin-bottom:8px">`;
  if (data.unread_count > 0) html += `<button class="btn btn-sm btn-outline" onclick="markAllRead()">Mark All Read</button>`;
  html += `</div><div id="notif-list">`;

  if (!data.notifications || !data.notifications.length) {
    html += `<div class="empty-state"><div class="empty-icon">🔔</div><div class="empty-title">No notifications</div></div>`;
  } else {
    for (const n of data.notifications) {
      html += `
        <div class="notif-item ${n.is_read ? "" : "unread"}">
          <div class="notif-title">${escapeHtml(n.title)}</div>
          <div class="notif-message">${escapeHtml(n.message)}</div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px">
            <span class="notif-time">${n.time}</span>
            ${n.is_read ? "" : `<button class="btn btn-sm btn-outline" onclick="dismissNotif(${n.id})">Dismiss</button>`}
          </div>
        </div>`;
    }
  }
  html += `</div>`;
  content.innerHTML = html;
}

window.logoutUser = async function () {
  try {
    await API.logout();
    App.user = null;
    App.role = null;
    showAuth();
    renderAuth();
    location.hash = "";
  } catch {}
};

// ─── AUTH UI ──────────────────────────────────────────
function renderAuth() {
  let html = `
    <div class="auth-logo">⛽</div>
    <div class="auth-title">FuelGo</div>
    <div class="auth-subtitle">Fuel delivery at your doorstep</div>
    <div class="auth-tabs">
      <button class="auth-tab active" onclick="switchAuthTab('login')">Sign In</button>
      <button class="auth-tab" onclick="switchAuthTab('register')">Sign Up</button>
    </div>
    <div id="auth-form-container"></div>`;
  $id("auth-screen").innerHTML = html;
  renderLoginForm();
}

window.switchAuthTab = function (tab) {
  qsa(".auth-tab").forEach(t => t.classList.toggle("active", t.textContent.toLowerCase().includes(tab === "login" ? "sign in" : "sign up")));
  if (tab === "login") renderLoginForm();
  else renderRegisterForm();
};

function renderLoginForm() {
  $id("auth-form-container").innerHTML = `
    <div class="auth-form">
      <div class="auth-error" id="login-error"></div>
      <div class="form-group"><label>Email</label><input type="email" id="login-email" placeholder="you@example.com" autocomplete="email"></div>
      <div class="form-group"><label>Password</label><input type="password" id="login-password" placeholder="Enter password" autocomplete="current-password"></div>
      <button class="btn btn-primary btn-block" onclick="handleLogin()">Sign In</button>
    </div>`;
}

function renderRegisterForm() {
  $id("auth-form-container").innerHTML = `
    <div class="auth-form">
      <div class="auth-error" id="register-error"></div>
      <div class="form-group"><label>First Name</label><input type="text" id="reg-fname" placeholder="John"></div>
      <div class="form-group"><label>Last Name</label><input type="text" id="reg-lname" placeholder="Doe"></div>
      <div class="form-group"><label>Email</label><input type="email" id="reg-email" placeholder="you@example.com"></div>
      <div class="form-group"><label>Phone</label><input type="tel" id="reg-phone" placeholder="+255 7XX XXX XXX"></div>
      <div class="form-group"><label>Password</label><input type="password" id="reg-password" placeholder="Min 8 characters"></div>
      <div class="form-group">
        <label>I am a</label>
        <div class="role-selector">
          <div class="role-option selected" data-role="customer" onclick="selectRole(this)">👤 Customer</div>
          <div class="role-option" data-role="driver" onclick="selectRole(this)">🚚 Driver</div>
        </div>
      </div>
      <button class="btn btn-primary btn-block" onclick="handleRegister()">Create Account</button>
    </div>`;
}

window.selectRole = function (el) {
  qsa(".role-option").forEach(r => r.classList.remove("selected"));
  el.classList.add("selected");
};

window.handleLogin = async function () {
  const email = $id("login-email").value;
  const password = $id("login-password").value;
  const err = $id("login-error");
  if (!email || !password) { err.textContent = "Please fill all fields"; err.style.display = "block"; return; }
  try {
    showLoading(true);
    const res = await API.login(email, password);
    showLoading(false);
    if (res.status === "success") {
      App.user = res.user;
      App.role = res.user.role;
      showApp();
      navigate();
    }
  } catch (e) {
    showLoading(false);
    err.textContent = e.message;
    err.style.display = "block";
  }
};

window.handleRegister = async function () {
  const data = {
    first_name: $id("reg-fname").value,
    last_name: $id("reg-lname").value,
    email: $id("reg-email").value,
    phone: $id("reg-phone").value,
    password: $id("reg-password").value,
    role: qs(".role-option.selected")?.dataset.role || "customer",
  };
  const err = $id("register-error");
  if (!data.first_name || !data.last_name || !data.email || !data.password) {
    err.textContent = "Please fill all required fields"; err.style.display = "block"; return;
  }
  if (data.password.length < 8) {
    err.textContent = "Password must be at least 8 characters"; err.style.display = "block"; return;
  }
  try {
    showLoading(true);
    const res = await API.register(data);
    showLoading(false);
    if (res.status === "success") {
      showToast("Account created! Please sign in.", "success");
      switchAuthTab("login");
    }
  } catch (e) {
    showLoading(false);
    err.textContent = e.message;
    err.style.display = "block";
  }
};

// ─── Init ─────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const appHtml = `
  <div id="toast" class="toast"></div>
  <div id="loading-overlay" style="position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:300;display:none;align-items:center;justify-content:center">
    <div style="text-align:center"><div class="spinner" style="width:40px;height:40px;border-width:4px;margin:0 auto 12px"></div><div style="color:var(--text2);font-size:14px">Loading...</div></div>
  </div>
  <div id="auth-screen"></div>
  <div id="app" style="display:none">
    <header id="app-header">
      <button class="back-btn" onclick="window.history.back()">‹</button>
      <h1>FuelGo</h1>
      <button class="header-action" style="display:none"></button>
    </header>
    <main id="app-content"></main>
  </div>
  <nav id="bottom-nav"></nav>`;
  document.body.innerHTML = appHtml;
  init();
});
