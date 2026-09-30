<script setup>
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { showFailToast } from "vant";
import { login } from "../api";
import { useAuthStore } from "../stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const submitting = ref(false);

const form = reactive({ username: "", password: "" });

async function onSubmit() {
  if (!form.username || !form.password) {
    showFailToast("请输入用户名和密码");
    return;
  }
  submitting.value = true;
  try {
    const res = await login({ ...form });
    authStore.setToken(res.token);
    await authStore.loadUser();
    router.replace(route.query.redirect || "/my/listings");
  } catch {
    /* 拦截器已 toast */
  }
  submitting.value = false;
}
</script>

<template>
  <div class="auth">
    <h2 class="auth-title">房东登录</h2>
    <van-cell-group inset>
      <van-field v-model="form.username" label="用户名" placeholder="请输入用户名" clearable />
      <van-field v-model="form.password" type="password" label="密码" placeholder="请输入密码" />
    </van-cell-group>
    <div class="btn-wrap">
      <van-button round block type="primary" color="#07c160" :loading="submitting" @click="onSubmit">
        登录
      </van-button>
    </div>
  </div>
</template>

<style scoped>
.auth {
  padding-top: 40px;
}
.auth-title {
  text-align: center;
  font-size: 20px;
}
.btn-wrap {
  padding: 24px 16px 0;
}
.switch {
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
  color: #1989fa;
  cursor: pointer;
}
</style>
