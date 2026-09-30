<script setup>
import { onMounted, reactive, ref } from "vue";
import { showConfirmDialog, showFailToast, showSuccessToast } from "vant";
import {
  createAdminAd,
  deleteAdminAd,
  getAdminAds,
  updateAdminAd,
} from "../api";

const items = ref([]);
const loading = ref(true);
const showEdit = ref(false);
const editing = ref(null); // null = 新增

const PRESET_COLORS = ["#1989fa", "#07c160", "#ff976a", "#ee0a24", "#7232dd", "#5a6a8a"];

const form = reactive({
  title: "", desc: "", link: "#", color: "#1989fa", image: "", sort: 0, enabled: true,
});

async function load() {
  loading.value = true;
  try {
    items.value = await getAdminAds();
  } catch {
    /* 拦截器已 toast */
  }
  loading.value = false;
}
onMounted(load);

function openCreate() {
  editing.value = null;
  Object.assign(form, { title: "", desc: "", link: "#", color: "#1989fa", image: "", sort: 0, enabled: true });
  showEdit.value = true;
}

function openEdit(ad) {
  editing.value = ad;
  Object.assign(form, {
    title: ad.title, desc: ad.desc, link: ad.link, color: ad.color,
    image: ad.image || "", sort: ad.sort, enabled: ad.enabled,
  });
  showEdit.value = true;
}

async function save() {
  if (!form.title) {
    showFailToast("请填写广告标题");
    showEdit.value = true;
    return;
  }
  const payload = { ...form, image: form.image || null, link: form.link || "#" };
  try {
    if (editing.value) {
      await updateAdminAd(editing.value.id, payload);
    } else {
      await createAdminAd(payload);
    }
    showSuccessToast(editing.value ? "已保存" : "已创建");
    load();
  } catch {
    /* 拦截器已 toast */
  }
}

async function toggle(ad) {
  try {
    await updateAdminAd(ad.id, {
      title: ad.title, desc: ad.desc, link: ad.link, color: ad.color,
      image: ad.image, sort: ad.sort, enabled: !ad.enabled,
    });
    ad.enabled = !ad.enabled;
  } catch {
    /* 拦截器已 toast */
  }
}

async function remove(ad) {
  try {
    await showConfirmDialog({ title: "删除广告", message: `确认删除「${ad.title}」？` });
  } catch {
    return;
  }
  try {
    await deleteAdminAd(ad.id);
    showSuccessToast("已删除");
    load();
  } catch {
    /* 拦截器已 toast */
  }
}
</script>

<template>
  <div class="ads-admin">
    <div class="toolbar">
      <span class="tip">详情页广告位（轮播展示；全部下架或无广告时不显示广告位）</span>
      <van-button size="small" round type="primary" color="#07c160" @click="openCreate">新增广告</van-button>
    </div>

    <div v-if="loading" class="loading"><van-loading size="24" /></div>
    <van-empty v-else-if="!items.length" description="暂无广告" />

    <div v-for="ad in items" v-else :key="ad.id" class="row">
      <span class="dot" :style="{ background: ad.color }"></span>
      <div class="info">
        <div class="t">
          {{ ad.title }}
          <span class="count">{{ ad.click_count }} 次点击</span>
        </div>
        <div class="meta van-ellipsis">{{ ad.desc || "—" }} · {{ ad.link }}</div>
        <div class="meta">排序 {{ ad.sort }}</div>
      </div>
      <div class="ops">
        <van-switch :model-value="ad.enabled" size="18" @update:model-value="toggle(ad)" />
        <span @click="openEdit(ad)">编辑</span>
        <span class="danger" @click="remove(ad)">删除</span>
      </div>
    </div>

    <van-dialog
      v-model:show="showEdit"
      :title="editing ? `编辑：${editing.title}` : '新增广告'"
      show-cancel-button
      @confirm="save"
    >
      <van-field v-model="form.title" label="标题" placeholder="如 搬家优惠" />
      <van-field v-model="form.desc" label="副文案" placeholder="如 新客首单立减 50 元" />
      <van-field v-model="form.link" label="跳转链接" placeholder="https://... 点击时按此链接跳转" />
      <van-field v-model="form.image" label="图片URL" placeholder="选填，留空用纯色底" />
      <van-field v-model="form.sort" type="digit" label="排序" placeholder="数字小的靠前" />
      <van-field name="color" label="底色">
        <template #input>
          <div class="color-row">
            <span
              v-for="c in PRESET_COLORS" :key="c"
              class="dot pick" :class="{ active: form.color === c }"
              :style="{ background: c }" @click="form.color = c"
            ></span>
            <input type="color" v-model="form.color" class="color-input" />
          </div>
        </template>
      </van-field>
    </van-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
}
.tip {
  font-size: 12px;
  color: #969799;
  max-width: 65%;
}
.loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
.row {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  margin: 8px 12px;
  padding: 12px 14px;
  border-radius: 8px;
}
.dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}
.info {
  flex: 1;
  min-width: 0;
}
.t {
  font-size: 15px;
  font-weight: 600;
}
.count {
  font-size: 11px;
  color: #07c160;
  margin-left: 8px;
  font-weight: 400;
}
.meta {
  font-size: 12px;
  color: #969799;
  margin-top: 2px;
}
.ops {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  flex-shrink: 0;
}
.ops span {
  cursor: pointer;
  color: #1989fa;
}
.ops .danger {
  color: #ee0a24;
}
.color-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot.pick {
  width: 22px;
  height: 22px;
  cursor: pointer;
  border: 2px solid transparent;
}
.dot.pick.active {
  border-color: #323233;
}
.color-input {
  width: 28px;
  height: 28px;
  border: none;
  padding: 0;
  background: none;
  cursor: pointer;
}
</style>
