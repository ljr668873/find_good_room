<script setup>
/**
 * 筛选栏：村名 / 地铁 / 租金 / 更多（户型·押付·独卫·电梯）。
 * filters 对象由父组件持有（引用传递，直接改字段），变更后 emit("change")，父组件负责重载列表。
 */
import { computed, onMounted, ref, watch } from "vue";
import { useCityStore } from "../stores/city";
import { getFilterOptions } from "../api";

const props = defineProps({
  filters: { type: Object, required: true },
});
const emit = defineEmits(["change"]);

const cityStore = useCityStore();
const villages = ref([]);
const metro = ref([]);

const villageItem = ref();
const metroItem = ref();
const rentItem = ref();
const moreItem = ref();

const RENT_OPTIONS = [
  { text: "租金不限", value: "" },
  { text: "800以下", value: "0-800" },
  { text: "800-1500", value: "800-1500" },
  { text: "1500-2500", value: "1500-2500" },
  { text: "2500以上", value: "2500-" },
];
const LAYOUTS = ["单间", "一房一厅", "两房", "隔断间"];
const DEPOSITS = ["押一付一", "押一付三", "押二付一"];

async function loadOptions() {
  if (!cityStore.current) return; // 城市未就绪时跳过，watch 会在就绪后重拉
  try {
    const data = await getFilterOptions(cityStore.current);
    villages.value = data.villages;
    metro.value = data.metro;
  } catch {
    /* 静默，下拉里显示空态 */
  }
}

onMounted(loadOptions);
watch(() => cityStore.current, loadOptions);

const rentValue = computed(() => {
  const min = props.filters.rent_min;
  const max = props.filters.rent_max;
  if (min == null && max == null) return "";
  return `${min ?? ""}-${max ?? ""}`;
});

const rentTitle = computed(
  () => RENT_OPTIONS.find((o) => o.value === rentValue.value)?.text || "租金",
);
const villageTitle = computed(() => props.filters.village || "村名");
const metroTitle = computed(() => props.filters.metro_station || "地铁");
const moreActive = computed(
  () =>
    props.filters.layout ||
    props.filters.deposit_type ||
    props.filters.private_bathroom != null ||
    props.filters.has_elevator != null,
);

function setVillage(name) {
  props.filters.village = name;
  villageItem.value?.toggle(false);
  emit("change");
}

function setMetro(name) {
  props.filters.metro_station = name;
  metroItem.value?.toggle(false);
  emit("change");
}

function setRent(value) {
  const [min, max] = value ? value.split("-") : ["", ""];
  props.filters.rent_min = min === "" ? null : Number(min);
  props.filters.rent_max = max === "" ? null : Number(max);
  rentItem.value?.toggle(false);
  emit("change");
}

function resetAll() {
  Object.assign(props.filters, {
    village: "",
    metro_station: "",
    rent_min: null,
    rent_max: null,
    layout: "",
    deposit_type: "",
    private_bathroom: null,
    has_elevator: null,
  });
  moreItem.value?.toggle(false);
  emit("change");
}

function confirmMore() {
  moreItem.value?.toggle(false);
  emit("change");
}
</script>

<template>
  <div class="filter-bar">
    <van-dropdown-menu>
      <van-dropdown-item ref="villageItem" :title="villageTitle">
        <div class="opt-list">
          <div class="opt" :class="{ active: !filters.village }" @click="setVillage('')">不限</div>
          <div
            v-for="v in villages"
            :key="v.name"
            class="opt"
            :class="{ active: filters.village === v.name }"
            @click="setVillage(v.name)"
          >
            {{ v.name }}<span class="count">{{ v.count }}</span>
          </div>
          <van-empty v-if="!villages.length" description="当前城市暂无房源" />
        </div>
      </van-dropdown-item>

      <van-dropdown-item ref="metroItem" :title="metroTitle">
        <div class="opt-list">
          <div class="opt" :class="{ active: !filters.metro_station }" @click="setMetro('')">不限</div>
          <div
            v-for="m in metro"
            :key="m.name"
            class="opt"
            :class="{ active: filters.metro_station === m.name }"
            @click="setMetro(m.name)"
          >
            {{ m.name }}<span class="count">{{ m.count }}</span>
          </div>
          <van-empty v-if="!metro.length" description="暂无地铁沿线房源" />
        </div>
      </van-dropdown-item>

      <van-dropdown-item ref="rentItem" :title="rentTitle">
        <div class="opt-wrap">
          <div
            v-for="o in RENT_OPTIONS"
            :key="o.value"
            class="chip"
            :class="{ active: rentValue === o.value }"
            @click="setRent(o.value)"
          >
            {{ o.text }}
          </div>
        </div>
      </van-dropdown-item>

      <van-dropdown-item ref="moreItem" :title="moreActive ? '筛选 •' : '筛选'">
        <div class="more">
          <div class="label">户型</div>
          <div class="opt-wrap">
            <div
              class="chip"
              :class="{ active: !filters.layout }"
              @click="filters.layout = ''"
            >不限</div>
            <div
              v-for="l in LAYOUTS"
              :key="l"
              class="chip"
              :class="{ active: filters.layout === l }"
              @click="filters.layout = l"
            >{{ l }}</div>
          </div>

          <div class="label">押付方式</div>
          <div class="opt-wrap">
            <div
              class="chip"
              :class="{ active: !filters.deposit_type }"
              @click="filters.deposit_type = ''"
            >不限</div>
            <div
              v-for="d in DEPOSITS"
              :key="d"
              class="chip"
              :class="{ active: filters.deposit_type === d }"
              @click="filters.deposit_type = d"
            >{{ d }}</div>
          </div>

          <div class="switch-row">
            <span>独立卫浴</span>
            <van-switch :model-value="filters.private_bathroom === true" @update:model-value="filters.private_bathroom = $event || null" />
          </div>
          <div class="switch-row">
            <span>有电梯</span>
            <van-switch :model-value="filters.has_elevator === true" @update:model-value="filters.has_elevator = $event || null" />
          </div>

          <div class="btns">
            <van-button size="small" plain @click="resetAll">重置</van-button>
            <van-button size="small" type="primary" color="#07c160" @click="confirmMore">确定</van-button>
          </div>
        </div>
      </van-dropdown-item>
    </van-dropdown-menu>
  </div>
</template>

<style scoped>
.filter-bar {
  background: #fff;
}

.opt-list {
  max-height: 320px;
  overflow-y: auto;
  padding: 4px 0;
}
.opt {
  padding: 10px 16px;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
}
.opt.active {
  color: #07c160;
  font-weight: 600;
}
.count {
  color: #969799;
  font-size: 12px;
}

.opt-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
}
.chip {
  padding: 5px 12px;
  border-radius: 14px;
  background: #f2f3f5;
  font-size: 13px;
}
.chip.active {
  background: #07c160;
  color: #fff;
}

.more {
  padding: 4px 0 12px;
}
.label {
  font-size: 13px;
  color: #969799;
  padding: 8px 16px 0;
}
.switch-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  font-size: 14px;
}
.btns {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 8px 16px 0;
}
</style>
