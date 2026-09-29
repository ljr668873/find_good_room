import { ref } from "vue";

/**
 * 无限滚动列表逻辑，首页与房东主页复用。
 * fetchPage(page) 需返回 { items, total, page }
 */
export function useListingList(fetchPage) {
  const items = ref([]);
  const page = ref(0);
  const total = ref(0);
  const loading = ref(false);
  const finished = ref(false);
  const error = ref(false);

  function reset() {
    items.value = [];
    page.value = 0;
    total.value = 0;
    finished.value = false;
    error.value = false;
  }

  async function onLoad() {
    loading.value = true;
    try {
      const res = await fetchPage(page.value + 1);
      items.value.push(...res.items);
      total.value = res.total;
      page.value = res.page;
      finished.value = items.value.length >= res.total;
      error.value = false;
    } catch {
      error.value = true;
    }
    loading.value = false;
  }

  return { items, total, loading, finished, error, reset, onLoad };
}
