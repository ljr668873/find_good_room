<script setup>
import { onMounted, ref } from "vue";
import { useCityStore } from "./stores/city";
import { useAuthStore } from "./stores/auth";

const cityStore = useCityStore();
const authStore = useAuthStore();
const showCity = ref(false);

onMounted(() => {
  cityStore.load();
  authStore.loadUser();
});

function pickCity(item) {
  cityStore.set(item.name);
  showCity.value = false;
}
</script>

<template>
  <div class="app">
    <header class="header">
      <div class="brand" @click="$router.push('/')">找好房</div>
      <div class="header-right">
        <div v-if="authStore.user?.is_admin" class="mine" @click="$router.push('/admin')">管理</div>
        <div class="mine" @click="$router.push(authStore.token ? '/my/listings' : '/login')">
          {{ authStore.token ? "我的房源" : "房东登录" }}
        </div>
        <div class="city" @click="showCity = true">{{ cityStore.current || "选择城市" }} ▾</div>
      </div>
    </header>

    <van-action-sheet
      v-model:show="showCity"
      :actions="cityStore.cities.map((c) => ({ name: c.name }))"
      cancel-text="取消"
      close-on-click-action
      @select="pickCity"
    />

    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<style>
body {
  margin: 0;
  background: #f7f8fa;
  font-family: -apple-system, "PingFang SC", "Helvetica Neue", Arial, sans-serif;
  color: #323233;
}
a { text-decoration: none; color: inherit; }

.app {
  max-width: 720px;
  margin: 0 auto;
  min-height: 100vh;
}

.header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #ebedf0;
}
.brand {
  font-size: 18px;
  font-weight: 700;
  color: #07c160;
  cursor: pointer;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.mine {
  font-size: 14px;
  cursor: pointer;
}
.city {
  font-size: 14px;
  cursor: pointer;
}

.main {
  padding-bottom: 32px;
}
</style>
