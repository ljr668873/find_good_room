<script setup>
defineProps({
  listing: { type: Object, required: true },
});
</script>

<template>
  <router-link class="card" :to="`/listing/${listing.share_slug}`">
    <img class="cover" :src="listing.photos[0]" loading="lazy" alt="" />
    <div class="info">
      <div class="title van-ellipsis">{{ listing.title }}</div>
      <div class="meta">
        {{ listing.layout }} · {{ listing.area }}㎡ · {{ listing.floor }}/{{ listing.floor_total }}层
      </div>
      <div class="loc van-ellipsis">
        {{ listing.village }}
        <template v-if="listing.metro_station">
          · {{ listing.metro_line }}{{ listing.metro_station }} 步行{{ listing.walk_minutes }}分钟
        </template>
      </div>
      <div class="rent">
        ¥{{ listing.rent }}<span class="unit">/月</span>
        <span v-if="listing.private_bathroom" class="tag">独卫</span>
      </div>
    </div>
  </router-link>
</template>

<style scoped>
.card {
  display: flex;
  gap: 12px;
  background: #fff;
  padding: 12px;
  margin: 8px 12px;
  border-radius: 8px;
}
.cover {
  width: 120px;
  height: 90px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
  background: #ebedf0;
}
.info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.title {
  font-size: 15px;
  font-weight: 600;
}
.meta,
.loc {
  font-size: 12px;
  color: #969799;
}
.rent {
  color: #ee0a24;
  font-weight: 700;
  font-size: 18px;
}
.unit {
  font-size: 12px;
  font-weight: 400;
  color: #969799;
}
.tag {
  margin-left: 8px;
  font-size: 11px;
  color: #07c160;
  border: 1px solid #07c160;
  border-radius: 3px;
  padding: 0 3px;
  vertical-align: 2px;
}
</style>
