import { ref } from "vue";
import { defineStore } from "pinia";
import { getCities } from "../api";

export const useCityStore = defineStore("city", () => {
  const cities = ref([]);
  const current = ref(localStorage.getItem("fgr_city") || "");

  async function load() {
    if (!cities.value.length) {
      cities.value = await getCities();
    }
    if (!current.value || !cities.value.some((c) => c.name === current.value)) {
      current.value = cities.value[0]?.name || "";
    }
  }

  function set(name) {
    current.value = name;
    localStorage.setItem("fgr_city", name);
  }

  return { cities, current, load, set };
});
