<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { useCityStore } from "../stores/city";
import { useListingList } from "../composables/useListingList";
import { getLandlordListings } from "../api";
import FilterBar from "../components/FilterBar.vue";
import ListingCard from "../components/ListingCard.vue";

const route = useRoute();
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

const landlord = ref(null);

function params(page) {
  const p = { page, page_size: 20 };
  if (cityStore.current) p.city = cityStore.current;
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

// 解构取 ref（顶层 ref 模板自动解包）
const { items, total, loading, finished, error, reset, onLoad } = useListingList(async (page) => {
  const res = await getLandlordListings(route.params.id, params(page));
  landlord.value = res.landlord;
  return res;
});

function reload() {
  reset();
  onLoad();
}

onMounted(async () => {
  await cityStore.load();
});
</script>

<template>
  <div>
    <div class="landlord-head">
      <div class="avatar">{{ landlord?.username?.slice(0, 1) || "?" }}</div>
      <div>
        <div class="name">{{ landlord?.username || "..." }}</div>
        <div class="count">在租 {{ total }} 套房源</div>
      </div>
    </div>

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

    <van-empty v-if="finished && !items.length" description="该房东暂无在租房源" />
  </div>
</template>

<style scoped>
.landlord-head {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  padding: 16px;
  margin: 10px 12px;
  border-radius: 8px;
}
.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #07c160;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.name {
  font-size: 16px;
  font-weight: 600;
}
.count {
  font-size: 12px;
  color: #969799;
  margin-top: 2px;
}
</style>
