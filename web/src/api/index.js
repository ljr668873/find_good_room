import axios from "axios";
import { showToast } from "vant";

const http = axios.create({ baseURL: "/api", timeout: 10000 });

// 登录态直接读 localStorage，避免与 store 循环依赖
http.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("fgr_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// 统一错误提示（需自行处理的场景 catch 即可）
http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail;
    if (typeof msg === "string") {
      showToast(msg);
    }
    return Promise.reject(err);
  },
);

// 公开
export const getCities = () => http.get("/cities");
export const getFilterOptions = (city) => http.get("/filter-options", { params: { city } });
export const getListings = (params) => http.get("/listings", { params });
export const getListing = (id) => http.get(`/listings/${id}`);
export const getLandlordListings = (id, params) => http.get(`/landlords/${id}/listings`, { params });
export const postReport = (data) => http.post("/reports", data);
export const getAds = () => http.get("/ads");
export const adClick = (id) => http.post(`/ads/${id}/click`).catch(() => {});

// 房东
export const register = (data) => http.post("/auth/register", data);
export const login = (data) => http.post("/auth/login", data);
export const getMe = () => http.get("/auth/me");
export const getMyListings = (params) => http.get("/my/listings", { params });
export const getMyListing = (id) => http.get(`/my/listings/${id}`);
export const createListing = (data) => http.post("/my/listings", data);
export const updateListing = (id, data) => http.put(`/my/listings/${id}`, data);
export const setListingStatus = (id, action) => http.patch(`/my/listings/${id}/status`, { action });
export const uploadPhotos = (formData) => http.post("/my/upload/photos", formData);

// 管理员
export const getAdminReports = (params) => http.get("/admin/reports", { params });
export const resolveReport = (id) => http.patch(`/admin/reports/${id}`, { status: "done" });
export const forceListingStatus = (id, action) => http.patch(`/admin/listings/${id}/status`, { action });
export const getAdminLandlords = (params) => http.get("/admin/landlords", { params });
export const createAdminLandlord = (data) => http.post("/admin/landlords", data);
export const updateAdminLandlord = (id, data) => http.put(`/admin/landlords/${id}`, data);
export const deleteAdminLandlord = (id) => http.delete(`/admin/landlords/${id}`);
export const getStatsSummary = (date) => http.get("/admin/stats/summary", { params: { date } });
export const getStatsHourly = (date) => http.get("/admin/stats/hourly", { params: { date } });
export const getStatsTopListings = (params) => http.get("/admin/stats/top-listings", { params });
export const getAdminAds = () => http.get("/admin/ads");
export const createAdminAd = (data) => http.post("/admin/ads", data);
export const updateAdminAd = (id, data) => http.put(`/admin/ads/${id}`, data);
export const deleteAdminAd = (id) => http.delete(`/admin/ads/${id}`);
