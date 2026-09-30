<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { showFailToast, showSuccessToast } from "vant";
import { useCityStore } from "../stores/city";
import { HOT_CITIES } from "../constants/cities";
import { createListing, getMyListing, updateListing, uploadPhotos } from "../api";
import ImageViewer from "../components/ImageViewer.vue";

const route = useRoute();
const router = useRouter();
const cityStore = useCityStore();

const editId = route.query.edit ? Number(route.query.edit) : null; // 编辑：PUT
const copyId = route.query.copy ? Number(route.query.copy) : null; // 复制重发：POST
const heading = editId ? "编辑房源" : copyId ? "复制发布" : "发布房源";

const step = ref(0);
const submitting = ref(false);

const LAYOUTS = ["单间", "一房一厅", "两房", "隔断间"];
const DEPOSITS = ["押一付一", "押一付三", "押二付一"];

const form = ref({
  city: "",
  village: "",
  rent: "",
  deposit_type: "",
  layout: "",
  area: "",
  floor: "",
  floor_total: "",
  has_elevator: false,
  facing: "",
  private_bathroom: true,
  water_price: "",
  electric_price: "",
  available_date: "",
  metro_line: "",
  metro_station: "",
  walk_minutes: "",
  surroundings: "",
  phone: "",
  wechat: "",
  title: "",
});

// 照片：fileList 统一管理（编辑回读的旧图 + 新上传），第一张即封面，可删除可重排拖入
const fileList = ref([]);

const finalPhotos = computed(() => {
  if (!fileList.value.length) return [];
  const first = fileList.value[0];
  // photos 约定：[封面缩略图, ...原图]；旧图非首位没有缩略图文件时用原图兜底
  return [first.thumbUrl || first.url, ...fileList.value.map((i) => i.url)];
});

async function uploadOne(rawFile, item) {
  const fd = new FormData();
  fd.append("files", rawFile);
  try {
    const res = await uploadPhotos(fd);
    if (item) {
      item.url = res.photos[1];
      item.thumbUrl = res.photos[0];
      item.status = "done";
      item.message = "";
    } else {
      fileList.value.push({ url: res.photos[1], thumbUrl: res.photos[0] });
    }
  } catch {
    if (item) {
      item.status = "failed";
      item.message = "上传失败";
    }
    /* 拦截器已 toast */
  }
}

const dragActive = ref(false);

// 图片预览：禁用 vant 默认全屏预览（无关闭入口），改用自带 ImageViewer（✕/Esc/点背景关闭）
const viewerShow = ref(false);
const viewerIndex = ref(0);

function openViewer(file, detail) {
  // vant click-preview 参数为 (file, { name, index })
  viewerIndex.value = detail?.index ?? 0;
  viewerShow.value = true;
}

async function afterRead(files) {
  const list = Array.isArray(files) ? files : [files];
  for (const f of list) {
    f.status = "uploading";
    f.message = "上传中";
    uploadOne(f.file, f);
  }
}

async function onDrop(e) {
  dragActive.value = false;
  const files = [...e.dataTransfer.files].filter((f) => f.type.startsWith("image/"));
  if (!files.length) return;
  for (const f of files) {
    await uploadOne(f);
  }
}

// ---- 弹层选择器 ----
const showCityPicker = ref(false);
const showLayoutPicker = ref(false);
const showDepositPicker = ref(false);
const showDatePicker = ref(false);

// 城市选择：热门列表 + 搜索过滤 + 无匹配时自由输入
const cityQuery = ref("");
const cityCandidates = computed(() => {
  const q = cityQuery.value.trim();
  const list = q ? HOT_CITIES.filter((c) => c.includes(q)) : HOT_CITIES;
  const exact = list.includes(q) || !q;
  return { list, exact, q };
});

function pickCity(name) {
  if (!name) return;
  form.value.city = name;
  showCityPicker.value = false;
  cityQuery.value = "";
}
function onLayoutConfirm({ selectedOptions }) {
  form.value.layout = selectedOptions[0]?.text || "";
  showLayoutPicker.value = false;
}
function onDepositConfirm({ selectedOptions }) {
  form.value.deposit_type = selectedOptions[0]?.text || "";
  showDepositPicker.value = false;
}
function onDateConfirm({ selectedValues }) {
  form.value.available_date = selectedValues.join("-");
  showDatePicker.value = false;
}

// ---- 分步校验 ----
function num(v) {
  return v === "" || v == null ? null : Number(v);
}

function validateStep(n) {
  const f = form.value;
  if (n === 0) {
    if (!f.city) return "请选择城市";
    if (!f.village) return "请填写村名";
    if (!num(f.rent)) return "请填写租金";
    if (!f.layout) return "请选择户型";
    if (!f.deposit_type) return "请选择押付方式";
    if (!num(f.area)) return "请填写面积";
    if (f.floor === "" || f.floor === null) return "请填写所在楼层";
    if (!num(f.floor_total)) return "请填写总层数";
  }
  if (n === 1) {
    if (num(f.water_price) == null) return "请填写水费单价";
    if (num(f.electric_price) == null) return "请填写电费单价";
    if (!f.available_date) return "请选择可入住日期";
    if (Boolean(f.metro_line) !== Boolean(f.metro_station)) return "地铁线路和站名需成对填写";
  }
  if (n === 2) {
    if (!finalPhotos.value.length) return "请至少上传 1 张照片";
    if (!f.phone) return "请填写联系电话";
  }
  return "";
}

function next() {
  const err = validateStep(step.value);
  if (err) {
    showFailToast(err);
    return;
  }
  step.value += 1;
}

// ---- 提交 ----
async function onSubmit() {
  const err = validateStep(2);
  if (err) {
    showFailToast(err);
    return;
  }
  const f = form.value;
  const payload = {
    ...f,
    rent: num(f.rent),
    area: num(f.area),
    floor: num(f.floor),
    floor_total: num(f.floor_total),
    water_price: num(f.water_price),
    electric_price: num(f.electric_price),
    walk_minutes: num(f.walk_minutes),
    facing: f.facing || null,
    metro_line: f.metro_line || null,
    metro_station: f.metro_station || null,
    surroundings: f.surroundings || null,
    wechat: f.wechat || null,
    title: f.title || null,
    photos: finalPhotos.value,
  };
  submitting.value = true;
  try {
    if (editId) {
      await updateListing(editId, payload);
    } else {
      await createListing(payload);
    }
    showSuccessToast(editId ? "已保存" : "已发布");
    router.replace("/my/listings");
  } catch {
    /* 拦截器已 toast */
  }
  submitting.value = false;
}

// ---- 回读（编辑/复制）----
onMounted(async () => {
  await cityStore.load();
  const id = editId || copyId;
  if (!id) {
    form.value.city = cityStore.current;
    return;
  }
  try {
    const data = await getMyListing(id);
    form.value = {
      ...data,
      area: String(data.area),
      water_price: String(data.water_price),
      electric_price: String(data.electric_price),
      floor: String(data.floor),
      floor_total: String(data.floor_total),
      rent: String(data.rent),
      walk_minutes: data.walk_minutes == null ? "" : String(data.walk_minutes),
    };
    // 旧图回读进统一 fileList：photos = [封面缩略图, ...原图]，首图带缩略图
    fileList.value = data.photos.slice(1).map((p, i) => ({
      url: p,
      thumbUrl: i === 0 ? data.photos[0] : null,
    }));
  } catch {
    router.replace("/my/listings");
  }
});
</script>

<template>
  <div class="publish">
    <van-steps :active="step" active-color="#07c160">
      <van-step>基本信息</van-step>
      <van-step>费用与配套</van-step>
      <van-step>照片与联系</van-step>
    </van-steps>

    <!-- 第 1 步 -->
    <div v-show="step === 0">
      <van-cell-group inset title="房子在哪">
        <van-field
          v-model="form.city" is-link readonly label="城市" placeholder="选择或输入城市"
          @click="showCityPicker = true"
        />
        <van-field v-model="form.village" label="村名" placeholder="如 白石洲" />
        <van-field v-model="form.address" label="详细位置" placeholder="如 X 巷 X 号 3 楼" />
      </van-cell-group>

      <van-cell-group inset title="房子什么样">
        <van-field
          v-model="form.layout" is-link readonly label="户型" placeholder="选择户型"
          @click="showLayoutPicker = true"
        />
        <van-field
          v-model="form.deposit_type" is-link readonly label="押付方式" placeholder="选择押付方式"
          @click="showDepositPicker = true"
        />
        <van-field v-model="form.rent" type="digit" label="租金(元/月)" placeholder="如 1200" />
        <van-field v-model="form.area" type="number" label="面积(㎡)" placeholder="如 18.5" />
        <van-field v-model="form.floor" type="digit" label="所在楼层" placeholder="如 3" />
        <van-field v-model="form.floor_total" type="digit" label="总层数" placeholder="如 7" />
        <van-cell title="有电梯">
          <van-switch v-model="form.has_elevator" size="20" />
        </van-cell>
        <van-field v-model="form.facing" label="朝向采光" placeholder="选填，如 南向采光好" />
      </van-cell-group>
    </div>

    <!-- 第 2 步 -->
    <div v-show="step === 1">
      <van-cell-group inset title="城中村关键信息">
        <van-cell title="独立卫浴">
          <van-switch v-model="form.private_bathroom" size="20" />
        </van-cell>
        <van-field v-model="form.water_price" type="number" label="水费(元/吨)" placeholder="如 4.5" />
        <van-field v-model="form.electric_price" type="number" label="电费(元/度)" placeholder="如 1.5" />
        <van-field
          v-model="form.available_date" is-link readonly label="可入住日期" placeholder="选择日期"
          @click="showDatePicker = true"
        />
      </van-cell-group>

      <van-cell-group inset title="地铁与周边（选填）">
        <van-field v-model="form.metro_line" label="地铁线路" placeholder="如 3号线" />
        <van-field v-model="form.metro_station" label="地铁站" placeholder="如 客村站" />
        <van-field v-model="form.walk_minutes" type="digit" label="步行(分钟)" placeholder="如 8" />
        <van-field
          v-model="form.surroundings" type="textarea" rows="2" autosize label="周边"
          placeholder="如 楼下有超市、菜市场"
        />
      </van-cell-group>
    </div>

    <!-- 第 3 步 -->
    <div v-show="step === 2">
      <van-cell-group inset title="照片（第一张为封面，最多 9 张）">
        <div
          class="drop-zone"
          @dragover.prevent="dragActive = true"
          @dragleave.prevent="dragActive = false"
          @drop.prevent="onDrop($event)"
        >
          <van-uploader
            v-model="fileList"
            :after-read="afterRead"
            :max-count="9"
            multiple
            deletable
            :preview-full-image="false"
            upload-text="点击选择"
            @click-preview="openViewer"
          />
          <div class="drop-tip" :class="{ active: dragActive }">把图片拖到这里即可上传</div>
        </div>
      </van-cell-group>

      <van-cell-group inset title="联系方式">
        <van-field v-model="form.phone" type="digit" label="联系电话" placeholder="租客将拨打此号码" />
        <van-field v-model="form.wechat" label="微信号" placeholder="选填" />
        <van-field v-model="form.title" label="标题" placeholder="选填，不填自动生成" />
      </van-cell-group>
    </div>

    <!-- 底部操作 -->
    <div class="actions">
      <van-button v-if="step > 0" plain round size="normal" @click="step -= 1">上一步</van-button>
      <van-button v-if="step < 2" round size="normal" type="primary" color="#07c160" block @click="next">
        下一步
      </van-button>
      <van-button v-else round size="normal" type="primary" color="#07c160" block :loading="submitting" @click="onSubmit">
        {{ editId ? "保存" : "发布" }}
      </van-button>
    </div>

    <!-- 弹层：城市选择（热门 + 搜索 + 自由输入） -->
    <van-popup v-model:show="showCityPicker" position="bottom" round style="height: 68%">
      <div class="city-picker">
        <van-search
          v-model="cityQuery"
          placeholder="搜索城市，没有可直接输入城市名"
          :show-action="true"
          @cancel="showCityPicker = false"
        >
          <template #action>
            <span style="color: #969799" @click="showCityPicker = false">取消</span>
          </template>
        </van-search>
        <div class="city-list">
          <div
            v-for="c in cityCandidates.list"
            :key="c"
            class="city-chip"
            :class="{ active: form.city === c }"
            @click="pickCity(c)"
          >{{ c }}</div>
          <div
            v-if="cityCandidates.q && !cityCandidates.exact"
            class="city-chip add"
            @click="pickCity(cityCandidates.q)"
          >使用「{{ cityCandidates.q }}」</div>
          <van-empty
            v-if="!cityCandidates.list.length && !cityCandidates.q"
            description="输入城市名搜索"
          />
        </div>
      </div>
    </van-popup>
    <van-popup v-model:show="showLayoutPicker" position="bottom" round>
      <van-picker
        :columns="LAYOUTS.map((l) => ({ text: l, value: l }))"
        @confirm="onLayoutConfirm" @cancel="showLayoutPicker = false"
      />
    </van-popup>
    <van-popup v-model:show="showDepositPicker" position="bottom" round>
      <van-picker
        :columns="DEPOSITS.map((d) => ({ text: d, value: d }))"
        @confirm="onDepositConfirm" @cancel="showDepositPicker = false"
      />
    </van-popup>
    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-date-picker
        title="选择日期"
        :min-date="new Date()"
        @confirm="onDateConfirm" @cancel="showDatePicker = false"
      />
    </van-popup>

    <ImageViewer
      v-model:show="viewerShow"
      :images="fileList.map((f) => f.url)"
      :start="viewerIndex"
    />
  </div>
</template>

<style scoped>
.publish {
  padding-bottom: 32px;
}
.drop-zone {
  padding: 12px 16px 16px;
  border-radius: 8px;
}
.drop-tip {
  margin-top: 10px;
  text-align: center;
  font-size: 12px;
  color: #969799;
  border: 1px dashed #dcdee0;
  border-radius: 6px;
  padding: 8px 0;
  transition: all 0.2s;
}
.drop-tip.active {
  color: #07c160;
  border-color: #07c160;
  background: #f0fff6;
}

.city-picker {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
.city-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px 16px 20px;
  align-content: flex-start;
}
.city-chip {
  padding: 6px 16px;
  border-radius: 16px;
  background: #f2f3f5;
  font-size: 14px;
  cursor: pointer;
}
.city-chip.active {
  background: #07c160;
  color: #fff;
}
.city-chip.add {
  background: #fff;
  border: 1px dashed #07c160;
  color: #07c160;
}
.actions {
  display: flex;
  gap: 12px;
  padding: 24px 16px;
}
.actions .van-button:last-child {
  flex: 1;
}
</style>
