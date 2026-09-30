<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { showSuccessToast, showToast } from "vant";
import { getAds, getListing, postReport } from "../api";
import AdBanner from "../components/AdBanner.vue";
import ImageViewer from "../components/ImageViewer.vue";

const route = useRoute();
const router = useRouter();
const listing = ref(null);
const notFound = ref(false);
const showReport = ref(false);
const ads = ref([]);

// 轮播与全屏查看器
const swipeRef = ref();
const swipeIndex = ref(0);
const viewerShow = ref(false);
const detailPhotos = computed(() => (listing.value ? listing.value.photos.slice(1) : []));

function openViewer(i) {
  viewerShow.value = true;
  swipeIndex.value = i;
}

const REPORT_REASONS = [
  { name: "虚假房源", value: "fake" },
  { name: "已租出", value: "rented" },
  { name: "信息错误", value: "wrong" },
  { name: "其他", value: "other" },
];

onMounted(async () => {
  getAds().then((res) => (ads.value = res)).catch(() => {});
  try {
    listing.value = await getListing(route.params.id);
  } catch {
    notFound.value = true;
  }
});

function copyWechat() {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(listing.value.wechat).then(() => showSuccessToast("已复制微信号"));
  } else {
    showToast(listing.value.wechat);
  }
}

async function report(item) {
  showReport.value = false;
  try {
    await postReport({ listing_id: listing.value.id, reason: item.value });
    showSuccessToast("已收到反馈，感谢举报");
  } catch {
    /* 拦截器已 toast */
  }
}
</script>

<template>
  <div v-if="listing" class="detail">
    <div class="swipe-wrap">
      <van-swipe
        ref="swipeRef"
        :loop="false"
        lazy-render
        indicator-color="#fff"
        @change="(i) => (swipeIndex = i)"
      >
        <van-swipe-item v-for="(p, i) in detailPhotos" :key="i" @click="openViewer(i)">
          <img class="photo" :src="p" alt="" />
        </van-swipe-item>
      </van-swipe>
      <div v-if="detailPhotos.length > 1" class="nav prev" @click="swipeRef?.prev()">‹</div>
      <div v-if="detailPhotos.length > 1" class="nav next" @click="swipeRef?.next()">›</div>
    </div>

    <div class="panel">
      <div class="price-row">
        <span class="rent">¥{{ listing.rent }}</span><span class="unit">/月</span>
        <span class="deposit">{{ listing.deposit_type }}</span>
      </div>
      <h1 class="title">{{ listing.title }}</h1>
      <div class="tags">
        <van-tag plain type="primary">{{ listing.layout }}</van-tag>
        <van-tag plain :type="listing.private_bathroom ? 'success' : 'danger'">
          {{ listing.private_bathroom ? "独立卫浴" : "公共卫浴" }}
        </van-tag>
        <van-tag v-if="listing.has_elevator" plain type="primary">电梯房</van-tag>
      </div>
    </div>

    <van-cell-group inset class="panel">
      <van-cell title="面积" :value="`${listing.area} ㎡`" />
      <van-cell title="楼层" :value="`${listing.floor}/${listing.floor_total} 层`" />
      <van-cell v-if="listing.facing" title="朝向采光" :value="listing.facing" />
      <van-cell title="可入住" :value="listing.available_date" />
    </van-cell-group>

    <div class="panel">
      <div class="section-title">费用明细</div>
      <div class="fee-grid">
        <div class="fee"><span class="v">{{ listing.water_price }}</span><span class="k">水费(元/吨)</span></div>
        <div class="fee"><span class="v">{{ listing.electric_price }}</span><span class="k">电费(元/度)</span></div>
      </div>
    </div>

    <div class="panel">
      <div class="section-title">位置</div>
      <div class="loc">{{ listing.city }} · {{ listing.village }} · {{ listing.address }}</div>
      <div v-if="listing.metro_station" class="loc metro">
        {{ listing.metro_line }}{{ listing.metro_station }} 步行约 {{ listing.walk_minutes }} 分钟
      </div>
      <div v-if="listing.surroundings" class="loc">{{ listing.surroundings }}</div>
    </div>

    <AdBanner :ads="ads" />

    <div class="panel links">
      <span @click="router.push(`/landlord/${listing.landlord_id}`)">看 TA 的全部房源 →</span>
      <span class="report" @click="showReport = true">举报</span>
    </div>

    <div class="bottom">
      <div class="contact">
        <div class="phone">{{ listing.phone }}</div>
        <div v-if="listing.wechat" class="wechat" @click="copyWechat">微信 {{ listing.wechat }} 📋</div>
      </div>
      <a class="call-btn" :href="`tel:${listing.phone}`">拨打电话</a>
    </div>

    <van-action-sheet
      v-model:show="showReport"
      :actions="REPORT_REASONS"
      cancel-text="取消"
      close-on-click-action
      @select="report"
    />

    <ImageViewer
      v-model:show="viewerShow"
      :images="detailPhotos"
      :start="swipeIndex"
    />
  </div>

  <van-empty v-else-if="notFound" description="房源不存在或已下架">
    <van-button round type="primary" color="#07c160" size="small" @click="router.push('/')">回首页</van-button>
  </van-empty>
</template>

<style scoped>
/* 给固定底栏留空间，避免遮挡最后一块内容 */
.detail {
  padding-bottom: 92px;
}

.swipe-wrap {
  position: relative;
}
.photo {
  width: 100%;
  aspect-ratio: 4 / 3; /* 列表态适中高度；点击进全屏查看器看完整大图 */
  object-fit: cover;
  display: block;
  background: #ebedf0;
  cursor: zoom-in;
}
.nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  color: #fff;
  font-size: 22px;
  cursor: pointer;
  z-index: 5;
}
.nav.prev {
  left: 0;
  border-radius: 0 6px 6px 0;
}
.nav.next {
  right: 0;
  border-radius: 6px 0 0 6px;
}

.panel {
  background: #fff;
  margin: 10px 12px;
  border-radius: 8px;
  padding: 14px 16px;
}

.price-row .rent {
  color: #ee0a24;
  font-size: 26px;
  font-weight: 700;
}
.unit {
  color: #969799;
  font-size: 13px;
  margin-right: 10px;
}
.deposit {
  font-size: 13px;
  color: #07c160;
}
.title {
  margin: 6px 0;
  font-size: 17px;
}
.tags {
  display: flex;
  gap: 6px;
}

.section-title {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 10px;
}
.fee-grid {
  display: flex;
  gap: 12px;
}
.fee {
  flex: 1;
  background: #f7f8fa;
  border-radius: 6px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.fee .v {
  font-size: 20px;
  font-weight: 700;
  color: #07c160;
}
.fee .k {
  font-size: 12px;
  color: #969799;
  margin-top: 4px;
}

.loc {
  font-size: 14px;
  line-height: 1.8;
  color: #323233;
}
.metro {
  color: #1989fa;
}

.links {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #1989fa;
}
.links span {
  cursor: pointer;
}
.links .report {
  color: #969799;
}

.bottom {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px calc(10px + env(safe-area-inset-bottom));
  background: #fff;
  border-top: 1px solid #ebedf0;
  /* ponytail: max-width 与 .app 一致，宽屏居中 */
  max-width: 720px;
  margin: 0 auto;
}
.contact {
  flex: 1;
  line-height: 1.3;
}
.phone {
  font-size: 17px;
  font-weight: 700;
}
.wechat {
  font-size: 12px;
  color: #969799;
  cursor: pointer;
}
.call-btn {
  background: #07c160;
  color: #fff;
  border-radius: 20px;
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
  flex-shrink: 0;
}
</style>
