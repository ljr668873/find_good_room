<script setup>
import { onMounted, ref } from "vue";
import { getAdminReports, forceListingStatus, resolveReport } from "../api";

const items = ref([]);
const loading = ref(true);

const REASON_LABEL = { fake: "虚假房源", rented: "已租出", wrong: "信息错误", other: "其他" };

async function load() {
  loading.value = true;
  try {
    const res = await getAdminReports({ status: "pending", page: 1, page_size: 100 });
    items.value = res.items;
  } catch {
    /* 拦截器已 toast */
  }
  loading.value = false;
}
onMounted(load);

async function done(id) {
  await resolveReport(id);
  load();
}

async function offline(listingId) {
  await forceListingStatus(listingId, "offline");
  load();
}
</script>

<template>
  <div class="admin">
    <h2 class="title">举报处理</h2>

    <div v-if="loading" class="loading"><van-loading size="24" /></div>
    <van-empty v-else-if="!items.length" description="没有待处理的举报" />

    <div v-for="r in items" v-else :key="r.id" class="report">
      <div class="row">
        <van-tag type="danger">{{ REASON_LABEL[r.reason] || r.reason }}</van-tag>
        <span class="when">{{ new Date(r.created_at).toLocaleString() }}</span>
      </div>
      <div class="listing">
        <div class="l-title">{{ r.listing_title }}</div>
        <div class="l-meta">
          {{ r.listing_city }}·{{ r.listing_village }} · 房源状态 {{ r.listing_status }} · 房东
          {{ r.landlord_username }}
        </div>
        <div class="l-meta">
          <a :href="`/listing/${r.listing_id}`" target="_blank">查看房源</a>
        </div>
      </div>
      <div class="ops">
        <van-button size="small" plain round @click="done(r.id)">标记已处理</van-button>
        <van-button
          v-if="r.listing_status === 'active'"
          size="small" type="danger" plain round
          @click="offline(r.listing_id)"
        >
          强制下架
        </van-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin {
  padding-bottom: 32px;
}
.title {
  font-size: 18px;
  text-align: center;
  padding: 12px 0 4px;
}
.loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
.report {
  background: #fff;
  margin: 8px 12px;
  padding: 12px 14px;
  border-radius: 8px;
}
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.when {
  font-size: 12px;
  color: #969799;
}
.listing {
  margin: 10px 0;
}
.l-title {
  font-size: 15px;
  font-weight: 600;
}
.l-meta {
  font-size: 12px;
  color: #969799;
  margin-top: 4px;
}
.l-meta a {
  color: #1989fa;
}
.ops {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
</style>
