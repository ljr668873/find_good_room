import { ref } from "vue";
import { defineStore } from "pinia";
import { getMe } from "../api";

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("fgr_token") || "");
  const user = ref(null);

  function setToken(t) {
    token.value = t;
    localStorage.setItem("fgr_token", t);
  }

  function logout() {
    token.value = "";
    user.value = null;
    localStorage.removeItem("fgr_token");
  }

  async function loadUser() {
    if (!token.value) return;
    try {
      user.value = await getMe();
    } catch {
      logout();
    }
  }

  return { token, user, setToken, logout, loadUser };
});
