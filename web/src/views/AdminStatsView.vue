<script setup>
import { computed, onMounted, ref } from "vue";
import { getStatsHourly, getStatsSummary, getStatsTopListings } from "../api";

const today = new Date().toISOString().slice(0, 10);
const dateStr = ref(today);
const showDatePicker = ref(false);

const summary = ref({ uv: 0, pv: 0, listing_pv: 0 });
const hourly = ref([]);
const hourFilter = ref(""); // "" = 全天
const topListings = ref([]);
const loading = ref(false);

const maxPv = computed(() => Math.max(1, ...hourly.value.map((h) => h.pv)));

async function load() {
  loading.value = true;
  try {
    [summary.value, hourly.value] = await Promise.all([
      getStatsSummary(dateStr.value),
      getStatsHourly(dateStr.value),
    ]);
    await loadTop();
  } catch {
    /* 拦截器已 toast */
  }
  loading.value = false;
}

async function loadTop() {
  const params = { date: dateStr.value, limit: 20 };
  if (hourFilter.value !== "") params.hour = hourFilter.value;
  topListings.value = await getStatsTopListings(params);
}

function onDateConfirm({ selectedValues }) {
  dateStr.value = selectedValues.join("-");
  showDatePicker.value = false;
  load();
}

onMounted(load);
</script>

<template>
  <div class="stats">
    <div class="date-bar">
      <span class="label">统计日期</span>
      <span class="date" @click="showDatePicker = true">{{ dateStr }} ▾</span>
    </div>

    <div v-if="loading" class="loading"><van-loading size="24" /></div>
    <template v-else>
      <div class="cards">
        <div class="card">
          <div class="num">{{ summary.uv }}</div>
          <div class="k">访客 UV（去重）</div>
        </div>
        <div class="card">
          <div class="num">{{ summary.pv }}</div>
          <div class="k">访问 PV</div>
        </div>
        <div class="card">
          <div class="num">{{ summary.listing_pv }}</div>
          <div class="k">房源详情查看</div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">每小时访问（UV / PV）</div>
        <div v-for="h in hourly" :key="h.hour" class="bar-row">
          <span class="h">{{ String(h.hour).padStart(2, "0") }}时</span>
          <div class="bar-track">
            <div class="bar" :style="{ width: (h.pv / maxPv) * 100 + '%' }"></div>
          </div>
          <span class="v">{{ h.uv }} / {{ h.pv }}</span>
        </div>
        <div v-if="!summary.pv" class="empty-tip">当日暂无访问</div>
      </div>

      <div class="panel">
        <div class="panel-title row-between">
          <span>房源访问排行</span>
          <select v-model="hourFilter" class="hour-select" @change="loadTop">
            <option value="">全天</option>
            <option v-for="h in 24" :key="h" :value="h - 1">{{ h - 1 }}时</option>
          </select>
        </div>
        <div v-for="(t, i) in topListings" :key="t.listing_id" class="rank-row">
          <span class="rank" :class="{ top3: i < 3 }">{{ i + 1 }}</span>
          <span class="title van-ellipsis">{{ t.title }}</span>
          <span class="count">{{ t.count }} 次</span>
        </div>
        <div v-if="!topListings.length" class="empty-tip">暂无房源访问记录</div>
      </div>
    </template>

    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-date-picker
        title="选择日期"
        :max-date="new Date()"
        @confirm="onDateConfirm"
        @cancel="showDatePicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.date-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 12px 16px;
}
.label {
  font-size: 14px;
  font-weight: 600;
}
.date {
  font-size: 14px;
  color: #1989fa;
  cursor: pointer;
}

.cards {
  display: flex;
  gap: 8px;
  padding: 8px 12px 0;
}
.card {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 14px 0;
  text-align: center;
}
.num {
  font-size: 22px;
  font-weight: 700;
  color: #07c160;
}
.k {
  font-size: 11px;
  color: #969799;
  margin-top: 2px;
}

.panel {
  background: #fff;
  margin: 10px 12px;
  border-radius: 8px;
  padding: 14px;
}
.panel-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 10px;
}
.row-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.h {
  width: 34px;
  font-size: 11px;
  color: #969799;
  text-align: right;
  flex-shrink: 0;
}
.bar-track {
  flex: 1;
  height: 12px;
  background: #f2f3f5;
  border-radius: 6px;
  overflow: hidden;
}
.bar {
  height: 100%;
  background: #07c160;
  border-radius: 6px;
  min-width: 2px;
  transition: width 0.3s;
}
.v {
  width: 64px;
  font-size: 11px;
  color: #323233;
  flex-shrink: 0;
}

.rank-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #f7f8fa;
}
.rank-row:last-child {
  border-bottom: none;
}
.rank {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #f2f3f5;
  color: #969799;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.rank.top3 {
  background: #07c160;
  color: #fff;
}
.rank-title {
  flex: 1;
  min-width: 0;
}
.title {
  flex: 1;
  min-width: 0;
  font-size: 14px;
}
.count {
  font-size: 12px;
  color: #969799;
  flex-shrink: 0;
}

.hour-select {
  border: 1px solid #ebedf0;
  border-radius: 6px;
  padding: 3px 6px;
  font-size: 13px;
  color: #323233;
  background: #fff;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
.empty-tip {
  text-align: center;
  color: #969799;
  font-size: 13px;
  padding: 8px 0;
}
</style>
