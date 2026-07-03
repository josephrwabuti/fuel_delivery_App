function getCSRFToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : "";
}

const API = {
  async request(method, url, body) {
    const headers = { "Content-Type": "application/json" };
    if (method === "POST") {
      const token = getCSRFToken();
      if (token) headers["X-CSRFToken"] = token;
    }
    const opts = { method, headers, credentials: "same-origin" };
    if (body) opts.body = JSON.stringify(body);
    try {
      const res = await fetch(url, opts);
      const data = await res.json();
      if (!res.ok && data.status === "error") throw new Error(data.message);
      if (res.status === 403 && data.status === "error") throw new Error(data.message);
      return data;
    } catch (e) {
      if (e.message) throw e;
      throw new Error("Network error");
    }
  },

  get(url) { return this.request("GET", url); },
  post(url, body) { return this.request("POST", url, body); },

  // Auth
  login(email, password) { return this.post("/pwa/api/login/", { email, password }); },
  register(data) { return this.post("/pwa/api/register/", data); },
  logout() { return this.post("/pwa/api/logout/"); },
  getUser() { return this.get("/pwa/api/user/"); },

  // Customer
  customerDashboard() { return this.get("/pwa/api/customer/dashboard/"); },
  customerStations() { return this.get("/pwa/api/customer/stations/"); },
  createOrder(data) { return this.post("/pwa/api/customer/order/", data); },
  customerTracking() { return this.get("/pwa/api/customer/tracking/"); },
  customerHistory() { return this.get("/pwa/api/customer/history/"); },
  cancelOrder(id) { return this.post(`/pwa/api/customer/order/${id}/cancel/`); },
  confirmDelivery(id) { return this.post(`/pwa/api/customer/order/${id}/confirm/`); },
  customerProfile() { return this.get("/pwa/api/customer/profile/"); },
  updateCustomerProfile(data) { return this.post("/pwa/api/customer/profile/update/", data); },
  changePassword(data) { return this.post("/pwa/api/customer/profile/change-password/", data); },
  customerNotifications() { return this.get("/pwa/api/customer/notifications/"); },

  // Driver
  driverDashboard() { return this.get("/pwa/api/driver/dashboard/"); },
  driverOrders() { return this.get("/pwa/api/driver/orders/"); },
  driverActive() { return this.get("/pwa/api/driver/active/"); },
  updateOrderStatus(id, status) { return this.post(`/pwa/api/driver/order/${id}/update-status/`, { status }); },
  updateLocation(lat, lng) { return this.post("/pwa/api/driver/update-location/", { lat, lng }); },
  toggleDuty() { return this.post("/pwa/api/driver/toggle-duty/"); },
  driverEarnings() { return this.get("/pwa/api/driver/earnings/"); },
  driverHistory() { return this.get("/pwa/api/driver/history/"); },
  driverProfile() { return this.get("/pwa/api/driver/profile/"); },
  updateDriverProfile(data) { return this.post("/pwa/api/driver/profile/update/", data); },
  driverNotifications() { return this.get("/pwa/api/driver/notifications/"); },

  // Shared
  dismissNotification(id) { return this.post(`/pwa/api/notifications/${id}/dismiss/`); },
  markNotificationsRead() { return this.post("/pwa/api/notifications/mark-all-read/"); },
};
