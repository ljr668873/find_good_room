<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { showConfirmDialog, showSuccessToast } from "vant";
import QRCode from "qrcode";
import { getMyListings, setListingStatus } from "../api";
import { copyText } from "../utils/clipboard";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

// ---- 分享主页 ----
const showShare = ref(false);
const qrCanvas = ref();
const shareUrl = computed(() => `${location.origin}/landlord/${authStore.user?.share_slug}`);

async function openShare() {
  showShare.value = true;
  await nextTick();
  QRCode.toCanvas(qrCanvas.value, shareUrl.value, { width: 190, margin: 1 });
}

function copyShare() {
  copyText(shareUrl.value, "链接已复制");
}

const all = ref([]);
const loading = ref(true);
const activeTab = ref("active");

const STATUS_TABS = [
  { name: "active", label: "在租" },
  { name: "rented", label: "已租" },
  { name: "offline", label: "已下架" },
];
const STATUS_LABEL = { active: "在租", rented: "已租", offline: "已下架" };

const items = computed(() => all.value.filter((l) => l.status === activeTab.value));

async function load() {
  loading.value = true;
  try {
    const res = await getMyListings({ page: 1, page_size: 100 });
    all.value = res.items;
  } catch {
    /* 拦截器已 toast */
  }
  loading.value = false;
}
onMounted(load);

async function act(listing, action) {
  if (action === "rented") {
    try {
      await showConfirmDialog({ title: "标记已租", message: "标记后房源立即下架，租客不再可见。" });
    } catch {
      return;
    }
  }
  try {
    await setListingStatus(listing.id, action);
    showSuccessToast("操作成功");
    load();
  } catch {
    /* 拦截器已 toast */
  }
}
</script>

<template>
  <div class="my">
    <div class="topbar">
      <span class="hello">{{ authStore.user?.username || "我" }} 的房源</span>
      <div class="topbar-actions">
        <van-button size="small" round plain type="primary" color="#1989fa" @click="openShare">
          分享主页
        </van-button>
        <van-button size="small" round plain type="primary" color="#07c160" @click="router.push('/publish')">
          发布新房
        </van-button>
        <van-button size="small" round plain @click="authStore.logout(); router.push('/')">退出</van-button>
      </div>
    </div>

    <van-tabs v-model:active="activeTab">
      <van-tab v-for="t in STATUS_TABS" :key="t.name" :name="t.name" :title="t.label">
        <div v-if="loading" class="loading"><van-loading size="24" /></div>
        <template v-else-if="items.length">
          <div v-for="l in items" :key="l.id" class="item">
            <img class="cover" :src="l.photos[1] || l.photos[0]" alt="" />
            <div class="info">
              <div class="title van-ellipsis">{{ l.title }}</div>
              <div class="meta">¥{{ l.rent }}/月 · {{ l.village }}</div>
              <div class="ops">
                <template v-if="l.status === 'active'">
                  <span @click="act(l, 'offline')">下架</span>
                  <span class="danger" @click="act(l, 'rented')">标记已租</span>
                  <span @click="router.push(`/publish?edit=${l.id}`)">编辑</span>
                </template>
                <template v-else-if="l.status === 'offline'">
                  <span @click="act(l, 'active')">重新上架</span>
                  <span @click="router.push(`/publish?edit=${l.id}`)">编辑</span>
                </template>
                <template v-else>
                  <span class="primary" @click="router.push(`/publish?copy=${l.id}`)">复制重发</span>
                </template>
              </div>
            </div>
            <van-tag :type="l.status === 'active' ? 'success' : l.status === 'rented' ? 'primary' : 'default'">
              {{ STATUS_LABEL[l.status] }}
            </van-tag>
          </div>
        </template>
        <van-empty v-else :description="`暂无${STATUS_LABEL[activeTab]}房源`" />
      </van-tab>
    </van-tabs>

    <van-popup v-model:show="showShare" position="bottom" round style="max-width: 720px; left: 50%; transform: translateX(-50%)">
      <div class="share-box">
        <div class="share-title">我的房源主页</div>
        <canvas ref="qrCanvas"></canvas>
        <div class="share-url">{{ shareUrl }}</div>
        <div class="share-tip">租客扫码或打开链接，直达你名下全部在租房源</div>
        <van-button round block type="primary" color="#07c160" @click="copyShare">复制链接</van-button>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.share-box {
  padding: 28px 32px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.share-title {
  font-size: 17px;
  font-weight: 700;
}
.share-url {
  font-size: 13px;
  color: #1989fa;
  word-break: break-all;
  text-align: center;
}
.share-tip {
  font-size: 12px;
  color: #969799;
  margin-bottom: 8px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 12px 16px;
}
.hello {
  font-size: 16px;
  font-weight: 600;
}
.topbar-actions {
  display: flex;
  gap: 8px;
}
.loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
.item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  background: #fff;
  margin: 8px 12px;
  padding: 12px;
  border-radius: 8px;
  position: relative;
}
.item .van-tag {
  position: absolute;
  top: 8px;
  right: 8px;
}
.cover {
  width: 88px;
  height: 66px;
  object-fit: cover;
  border-radius: 6px;
  background: #ebedf0;
  flex-shrink: 0;
}
.info {
  flex: 1;
  min-width: 0;
}
.title {
  font-size: 14px;
  font-weight: 600;
}
.meta {
  font-size: 12px;
  color: #969799;
  margin: 4px 0 8px;
}
.ops {
  display: flex;
  gap: 14px;
  font-size: 13px;
}
.ops span {
  cursor: pointer;
  color: #1989fa;
}
.ops .danger {
  color: #ee0a24;
}
.ops .primary {
  color: #07c160;
}
</style>
