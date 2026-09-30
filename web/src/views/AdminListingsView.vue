<script setup>
import { computed, onMounted, ref } from "vue";
import { showConfirmDialog, showSuccessToast } from "vant";
import { deleteAdminListings, getAdminListings } from "../api";

const items = ref([]);
const total = ref(0);
const loading = ref(true);
const keyword = ref("");
const page = ref(1);
const finished = ref(false);
const checked = ref({}); // id -> true

const STATUS_TAG = { active: "success", rented: "primary", offline: "default" };
const STATUS_LABEL = { active: "在租", rented: "已租", offline: "下架" };

const checkedIds = computed(() => Object.keys(checked.value).filter((k) => checked.value[k]).map(Number));

let busy = false;

async function onLoad() {
  // tab 内 van-list 在 display:none 下不触发，onMounted 手动拉首页；busy 防 onMounted 与 van-list 双触发
  if (busy) return;
  busy = true;
  loading.value = true;
  try {
    const res = await getAdminListings({
      keyword: keyword.value || undefined,
      page: page.value,
      page_size: 50,
    });
    items.value.push(...res.items);
    total.value = res.total;
    page.value += 1;
    finished.value = items.value.length >= res.total;
  } catch {
    finished.value = true;
  }
  loading.value = false;
  busy = false;
}

onMounted(onLoad);

function reset() {
  page.value = 1;
  items.value = [];
  finished.value = false;
  checked.value = {};
  onLoad();
}

function search() {
  reset();
}

function toggle(id) {
  checked.value[id] = !checked.value[id];
}

function checkAll() {
  const on = checkedIds.value.length < items.value.length;
  for (const l of items.value) checked.value[l.id] = on;
}

async function removeSelected() {
  const ids = checkedIds.value;
  if (!ids.length) return;
  try {
    await showConfirmDialog({
      title: "批量删除",
      message: `确认删除选中的 ${ids.length} 套房源？连带删除相关举报，不可恢复。`,
    });
  } catch {
    return;
  }
  try {
    const res = await deleteAdminListings(ids);
    showSuccessToast(`已删除 ${res.deleted} 套`);
    reset();
  } catch {
    /* 拦截器已 toast */
  }
}
</script>

<template>
  <div class="listings-admin">
    <div class="toolbar">
      <van-search v-model="keyword" placeholder="搜索标题/村/城市/房东" @search="search" @clear="search" />
      <div class="actions">
        <van-button size="small" plain round @click="checkAll">
          {{ checkedIds.length < items.length ? "全选" : "全不选" }}
        </van-button>
        <van-button size="small" type="danger" round :disabled="!checkedIds.length" @click="removeSelected">
          删除({{ checkedIds.length }})
        </van-button>
      </div>
    </div>

    <div class="total">共 {{ total }} 套（含已租/下架）</div>

    <div class="row head">
      <span class="cb"></span>
      <span class="c-title">房源</span>
      <span class="c-status">状态</span>
      <span class="c-landlord">房东</span>
    </div>

    <van-list
      v-model:loading="loading"
      :finished="finished"
      finished-text="没有更多了"
      @load="onLoad"
    >
      <div v-for="l in items" :key="l.id" class="row" :class="{ picked: checked[l.id] }" @click="toggle(l.id)">
        <span class="cb">
          <van-checkbox :model-value="!!checked[l.id]" @click.stop />
        </span>
        <span class="c-title van-ellipsis">{{ l.title }}</span>
        <span class="c-status"><van-tag :type="STATUS_TAG[l.status]" size="small">{{ STATUS_LABEL[l.status] }}</van-tag></span>
        <span class="c-landlord van-ellipsis">{{ l.landlord_username }}</span>
      </div>
    </van-list>
    <van-empty v-if="finished && !items.length" description="没有房源" />
  </div>
</template>

<style scoped>
.toolbar {
  background: #fff;
}
.toolbar :deep(.van-search) {
  padding: 8px 12px;
}
.actions {
  display: flex;
  gap: 8px;
  padding: 0 12px 8px;
}
.total {
  font-size: 12px;
  color: #969799;
  padding: 8px 16px;
}
.row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  margin: 0 12px;
  padding: 10px 12px;
  border-bottom: 1px solid #f7f8fa;
  cursor: pointer;
}
.row.head {
  border-radius: 8px 8px 0 0;
  cursor: default;
  color: #969799;
  font-size: 12px;
  margin-top: 4px;
}
.row:last-of-type {
  border-radius: 0 0 8px 8px;
  border-bottom: none;
}
.row.picked {
  background: #f0fff6;
}
.cb {
  flex-shrink: 0;
  width: 22px;
}
.c-title {
  flex: 1;
  min-width: 0;
  font-size: 14px;
}
.c-status {
  flex-shrink: 0;
  width: 44px;
  text-align: center;
}
.c-landlord {
  flex-shrink: 0;
  width: 90px;
  font-size: 12px;
  color: #969799;
  text-align: right;
}
</style>
