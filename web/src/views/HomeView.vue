<script setup>
// 分享制模式：本站不做公开全量列表，租客通过房东分享的 /landlord/{id} 链接访问房源
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();
</script>

<template>
  <div class="gate">
    <div class="logo">管</div>
    <h1 class="name">管好房</h1>
    <p class="desc">本站房源仅通过房东分享链接开放</p>
    <p class="sub">请向您的房东索取主页链接，或扫描房东发给您的二维码</p>

    <van-button
      v-if="authStore.token"
      round type="primary" color="#07c160" block
      @click="router.push('/my/listings')"
    >
      房东登录后管理房源
    </van-button>
    <van-button v-else round plain block @click="router.push('/login')">
      我是房东，去登录
    </van-button>
  </div>
</template>

<style scoped>
.gate {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100px 40px 0;
  gap: 14px;
}
.logo {
  width: 88px;
  height: 88px;
  border-radius: 24px;
  background: #07c160;
  color: #fff;
  font-size: 44px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}
.name {
  font-size: 26px;
  margin: 8px 0 0;
}
.desc {
  font-size: 16px;
  color: #323233;
  margin: 12px 0 0;
}
.sub {
  font-size: 13px;
  color: #969799;
  margin: 0 0 40px;
  text-align: center;
}
</style>
