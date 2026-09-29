<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { showFailToast } from "vant";
import { register } from "../api";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();
const submitting = ref(false);

const form = reactive({ username: "", password: "", confirm: "" });

async function onSubmit() {
  if (!form.username || !form.password) {
    showFailToast("请输入用户名和密码");
    return;
  }
  if (form.password.length < 6) {
    showFailToast("密码至少 6 位");
    return;
  }
  if (form.password !== form.confirm) {
    showFailToast("两次密码不一致");
    return;
  }
  submitting.value = true;
  try {
    await register({ username: form.username, password: form.password });
    router.replace("/login");
  } catch {
    /* 拦截器已 toast（用户名已存在等） */
  }
  submitting.value = false;
}
</script>

<template>
  <div class="auth">
    <h2 class="auth-title">房东注册</h2>
    <van-cell-group inset>
      <van-field v-model="form.username" label="用户名" placeholder="2-32 位，中英文数字" clearable />
      <van-field v-model="form.password" type="password" label="密码" placeholder="至少 6 位" />
      <van-field v-model="form.confirm" type="password" label="确认密码" placeholder="再次输入密码" />
    </van-cell-group>
    <div class="btn-wrap">
      <van-button round block type="primary" color="#07c160" :loading="submitting" @click="onSubmit">
        注册
      </van-button>
    </div>
    <div class="switch" @click="router.push('/login')">已有账号？去登录</div>
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
