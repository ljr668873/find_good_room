<script setup>
import { onMounted, reactive, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useCityStore } from "../stores/city";
import { useListingList } from "../composables/useListingList";
import { getListings } from "../api";
import FilterBar from "../components/FilterBar.vue";
import ListingCard from "../components/ListingCard.vue";

const route = useRoute();
const router = useRouter();
const cityStore = useCityStore();

const filters = reactive({
  keyword: "",
  village: "",
  metro_station: "",
  rent_min: null,
  rent_max: null,
  layout: "",
  deposit_type: "",
  private_bathroom: null,
  has_elevator: null,
});

function params(page) {
  const p = { city: cityStore.current, page, page_size: 20 };
  if (filters.keyword) p.keyword = filters.keyword;
  if (filters.village) p.village = filters.village;
  if (filters.metro_station) p.metro_station = filters.metro_station;
  if (filters.rent_min != null) p.rent_min = filters.rent_min;
  if (filters.rent_max != null) p.rent_max = filters.rent_max;
  if (filters.layout) p.layout = filters.layout;
  if (filters.deposit_type) p.deposit_type = filters.deposit_type;
  if (filters.private_bathroom != null) p.private_bathroom = filters.private_bathroom;
  if (filters.has_elevator != null) p.has_elevator = filters.has_elevator;
  return p;
}

// 解构取 ref（顶层 ref 模板自动解包；不解构则 list.items 是普通对象包 ref，模板不解包）
const { items, loading, finished, error, reset, onLoad } = useListingList((page) =>
  getListings(params(page)),
);

function fromQuery() {
  const q = route.query;
  filters.keyword = q.keyword || "";
  filters.village = q.village || "";
  filters.metro_station = q.metro_station || "";
  filters.rent_min = q.rent_min != null ? Number(q.rent_min) : null;
  filters.rent_max = q.rent_max != null ? Number(q.rent_max) : null;
  filters.layout = q.layout || "";
  filters.deposit_type = q.deposit_type || "";
  filters.private_bathroom = q.private_bathroom == null ? null : q.private_bathroom === "true";
  filters.has_elevator = q.has_elevator == null ? null : q.has_elevator === "true";
}

function reload() {
  const q = {};
  for (const [k, v] of Object.entries(filters)) {
    if (v !== "" && v != null) q[k] = String(v);
  }
  router.replace({ query: q });
  reset();
  onLoad();
}

onMounted(async () => {
  await cityStore.load();
  fromQuery();
});

watch(() => cityStore.current, () => reload());
</script>

<template>
  <div>
    <van-search
      v-model="filters.keyword"
      placeholder="搜索村名 / 地铁站 / 标题"
      @search="reload"
      @clear="reload"
    />
    <FilterBar :filters="filters" @change="reload" />

    <van-list
      v-if="cityStore.current"
      v-model:loading="loading"
      v-model:error="error"
      :finished="finished"
      finished-text="没有更多了"
      error-text="加载失败，点击重试"
      @load="onLoad"
    >
      <ListingCard v-for="l in items" :key="l.id" :listing="l" />
    </van-list>

    <van-empty v-if="finished && !items.length" description="没有符合条件的房源" />
  </div>
</template>
