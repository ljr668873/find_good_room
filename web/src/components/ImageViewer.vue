<script setup>
/**
 * 全屏图片查看器：滚轮/双击缩放、双指捏合、拖拽平移、90° 旋转、左右切换、Esc 关闭。
 * 每次打开重置变换；切换图片重置变换。
 */
import { computed, ref, watch } from "vue";

const props = defineProps({
  show: { type: Boolean, default: false },
  images: { type: Array, default: () => [] },
  start: { type: Number, default: 0 },
});
const emit = defineEmits(["update:show"]);

const current = ref(0);
const scale = ref(1);
const rotate = ref(0);
const tx = ref(0);
const ty = ref(0);

watch(
  () => props.show,
  (open) => {
    if (open) {
      current.value = props.start;
      reset();
      window.addEventListener("keydown", onKey);
    } else {
      window.removeEventListener("keydown", onKey);
    }
  },
);

function reset() {
  scale.value = 1;
  rotate.value = 0;
  tx.value = 0;
  ty.value = 0;
}

function close() {
  emit("update:show", false);
}

function onKey(e) {
  if (e.key === "Escape") close();
  if (e.key === "ArrowLeft") go(-1);
  if (e.key === "ArrowRight") go(1);
}

function go(delta) {
  current.value = (current.value + delta + props.images.length) % props.images.length;
  reset();
}

const imgStyle = computed(() => ({
  transform: `translate(${tx.value}px, ${ty.value}px) scale(${scale.value}) rotate(${rotate.value}deg)`,
}));

function clampScale(v) {
  return Math.min(8, Math.max(0.3, v));
}

function onWheel(e) {
  e.preventDefault();
  scale.value = clampScale(scale.value * (e.deltaY < 0 ? 1.15 : 0.87));
}

function onDblClick() {
  scale.value = scale.value > 1.5 ? 1 : 2.5;
  tx.value = 0;
  ty.value = 0;
}

// ---- 拖拽（Pointer Events，鼠标/单指统一）----
let dragging = false;
let moved = false;
let sx = 0;
let sy = 0;
let baseTx = 0;
let baseTy = 0;

function onPointerDown(e) {
  if (e.isPrimary === false) return;
  dragging = true;
  moved = false;
  sx = e.clientX;
  sy = e.clientY;
  baseTx = tx.value;
  baseTy = ty.value;
  e.target.setPointerCapture?.(e.pointerId);
}

function onPointerMove(e) {
  if (!dragging) return;
  const dx = e.clientX - sx;
  const dy = e.clientY - sy;
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) moved = true;
  tx.value = baseTx + dx;
  ty.value = baseTy + dy;
}

function onPointerUp() {
  dragging = false;
}

// 背景点击关闭（有拖拽位移时不关）
function onBackdropClick(e) {
  if (e.target === e.currentTarget && !moved) close();
}

// ---- 双指捏合 ----
let pinchBase = 0;
let pinchScale = 1;

function onTouchStart(e) {
  if (e.touches.length === 2) {
    pinchBase = dist(e.touches);
    pinchScale = scale.value;
  }
}

function onTouchMove(e) {
  if (e.touches.length === 2) {
    e.preventDefault();
    if (pinchBase > 0) {
      scale.value = clampScale(pinchScale * dist(e.touches) / pinchBase);
    }
  }
}

function dist(touches) {
  const dx = touches[0].clientX - touches[1].clientX;
  const dy = touches[0].clientY - touches[1].clientY;
  return Math.hypot(dx, dy) || 1;
}
</script>

<template>
  <teleport to="body">
    <div
      v-if="show"
      class="viewer"
      @wheel="onWheel"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @click="onBackdropClick"
    >
      <img
        :src="images[current]"
        class="viewer-img"
        :style="imgStyle"
        draggable="false"
        alt=""
        @dblclick="onDblClick"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
      />

      <div class="counter">{{ current + 1 }} / {{ images.length }}</div>
      <div class="btn close" @click="close">✕</div>
      <div class="btn rot" @click="rotate = (rotate + 90) % 360">⟳</div>
      <div class="btn left" @click="go(-1)">‹</div>
      <div class="btn right" @click="go(1)">›</div>
    </div>
  </teleport>
</template>

<style scoped>
.viewer {
  position: fixed;
  inset: 0;
  z-index: 3000;
  background: rgba(0, 0, 0, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  touch-action: none;
  user-select: none;
}
.viewer-img {
  max-width: 92vw;
  max-height: 88vh;
  will-change: transform;
  cursor: grab;
}
.viewer-img:active {
  cursor: grabbing;
}

.counter {
  position: absolute;
  top: calc(12px + env(safe-area-inset-top));
  left: 50%;
  transform: translateX(-50%);
  color: #fff;
  font-size: 14px;
  background: rgba(0, 0, 0, 0.4);
  padding: 2px 12px;
  border-radius: 12px;
}
.btn {
  position: absolute;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  font-size: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.btn:active {
  background: rgba(255, 255, 255, 0.3);
}
.close {
  top: calc(12px + env(safe-area-inset-top));
  right: 12px;
  font-size: 16px;
}
.rot {
  bottom: calc(20px + env(safe-area-inset-bottom));
  right: 16px;
  font-size: 20px;
}
.left {
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
}
.right {
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
}
</style>
