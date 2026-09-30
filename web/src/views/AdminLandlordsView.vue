<script setup>
import { onMounted, reactive, ref } from "vue";
import { showConfirmDialog, showFailToast, showSuccessToast } from "vant";
import {
  createAdminLandlord,
  deleteAdminLandlord,
  getAdminLandlords,
  updateAdminLandlord,
} from "../api";

const items = ref([]);
const total = ref(0);
const loading = ref(true);
const keyword = ref("");

const showEdit = ref(false);
const editing = ref(null); // null = 新增
const form = reactive({ username: "", password: "" });

async function load() {
  loading.value = true;
  try {
    const res = await getAdminLandlords({ keyword: keyword.value || undefined, page: 1, page_size: 100 });
    items.value = res.items;
    total.value = res.total;
  } catch {
    /* 拦截器已 toast */
  }
  loading.value = false;
}
onMounted(load);

function openCreate() {
  editing.value = null;
  form.username = "";
  form.password = "";
  showEdit.value = true;
}

function openEdit(u) {
  editing.value = u;
  form.username = u.username;
  form.password = "";
  showEdit.value = true;
}

async function save() {
  const isNew = !editing.value;
  const badName = !form.username || form.username.length < 2;
  const badPass = isNew
    ? form.password.length < 6
    : form.password !== "" && form.password.length < 6;
  if (badName || badPass) {
    showFailToast(isNew ? "请填写用户名和至少 6 位密码" : "用户名 2 位起；改密码则至少 6 位");
    showEdit.value = true; // van-dialog confirm 会自动关，校验失败重开继续编辑
    return;
  }
  try {
    if (editing.value) {
      await updateAdminLandlord(editing.value.id, {
        username: form.username,
        ...(form.password ? { password: form.password } : {}),
      });
    } else {
      await createAdminLandlord({ username: form.username, password: form.password });
    }
    showSuccessToast(editing.value ? "已保存" : "已创建");
    load();
  } catch {
    /* 拦截器已 toast */
  }
}

async function remove(u) {
  try {
    await showConfirmDialog({ title: "删除账号", message: `确认删除 ${u.username}？名下有房源时无法删除。` });
  } catch {
    return;
  }
  try {
    await deleteAdminLandlord(u.id);
    showSuccessToast("已删除");
    load();
  } catch {
    /* 拦截器已 toast */
  }
}
</script>

<template>
  <div class="landlords">
    <div class="toolbar">
      <van-search v-model="keyword" placeholder="搜索用户名" @search="load" @clear="load" />
      <div class="btn-wrap">
        <van-button size="small" round type="primary" color="#07c160" @click="openCreate">新增账号</van-button>
      </div>
    </div>

    <div v-if="loading" class="loading"><van-loading size="24" /></div>
    <van-empty v-else-if="!items.length" description="暂无账号" />

    <div v-for="u in items" v-else :key="u.id" class="row">
      <div class="info">
        <div class="name">
          {{ u.username }}
          <van-tag v-if="u.is_admin" type="warning" size="small">管理员</van-tag>
        </div>
        <div class="meta">房源 {{ u.listing_count }} 套 · {{ new Date(u.created_at).toLocaleDateString() }}</div>
      </div>
      <div class="ops">
        <span @click="openEdit(u)">编辑</span>
        <span v-if="!u.is_admin" class="danger" @click="remove(u)">删除</span>
      </div>
    </div>

    <van-dialog
      v-model:show="showEdit"
      :title="editing ? `编辑 ${editing.username}` : '新增账号'"
      show-cancel-button
      @confirm="save"
    >
      <van-field v-model="form.username" label="用户名" placeholder="2-32 位" />
      <van-field
        v-model="form.password" type="password" label="密码"
        :placeholder="editing ? '留空则不改密码' : '至少 6 位'"
      />
    </van-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  background: #fff;
}
.toolbar :deep(.van-search) {
  flex: 1;
  padding: 8px 6px 8px 12px;
}
.btn-wrap {
  padding-right: 12px;
}
.loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  margin: 8px 12px;
  padding: 12px 14px;
  border-radius: 8px;
}
.name {
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
.meta {
  font-size: 12px;
  color: #969799;
  margin-top: 3px;
}
.ops {
  display: flex;
  gap: 14px;
  font-size: 14px;
}
.ops span {
  cursor: pointer;
  color: #1989fa;
}
.ops .danger {
  color: #ee0a24;
}
</style>
