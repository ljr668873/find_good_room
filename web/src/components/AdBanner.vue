<script setup>
import { adClick } from "../api";

defineProps({
  ads: { type: Array, default: () => [] },
});

// 只认 http(s) 链接，填什么跳什么；无效/空则纯展示不跳转
const isLink = (ad) => /^https?:\/\//.test(ad.link || "");

function onClick(ad) {
  // fire-and-forget 点击计数，不阻塞跳转
  adClick(ad.id);
}
</script>

<template>
  <div v-if="ads.length" class="ad-banner">
    <van-swipe :autoplay="3500" indicator-color="#fff" class="ad-swipe">
      <van-swipe-item v-for="ad in ads" :key="ad.id">
        <component
          :is="isLink(ad) ? 'a' : 'div'"
          class="ad-item"
          v-bind="isLink(ad) ? { href: ad.link, target: '_blank', rel: 'noopener' } : {}"
          :style="{ background: ad.color || '#5a6a8a' }"
          @click="isLink(ad) && onClick(ad)"
        >
          <img v-if="ad.image" :src="ad.image" class="ad-img" alt="" />
          <div v-else class="ad-placeholder">
            <div class="ad-title">{{ ad.title }}</div>
            <div class="ad-desc">{{ ad.desc }}</div>
          </div>
          <span class="ad-tag">广告</span>
        </component>
      </van-swipe-item>
    </van-swipe>
  </div>
</template>

<style scoped>
.ad-banner {
  background: #fff;
  margin: 10px 12px;
  border-radius: 8px;
  overflow: hidden;
}
.ad-swipe {
  height: 76px;
}
.ad-item {
  display: block;
  position: relative;
  height: 76px;
  text-decoration: none;
}
.ad-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.ad-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 16px;
}
.ad-title {
  color: #fff;
  font-size: 16px;
  font-weight: 700;
}
.ad-desc {
  color: rgba(255, 255, 255, 0.85);
  font-size: 12px;
  margin-top: 4px;
}
.ad-tag {
  position: absolute;
  right: 8px;
  bottom: 6px;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 3px;
  padding: 0 4px;
}
</style>
