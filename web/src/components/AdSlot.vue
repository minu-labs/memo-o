<template>
  <aside v-if="enabled" class="ad-slot" aria-label="광고">
    <ins
      ref="ins"
      class="adsbygoogle"
      style="display: block"
      :data-ad-client="ADSENSE_CLIENT"
      :data-ad-slot="adSlot"
      data-ad-format="auto"
      data-full-width-responsive="true"
    ></ins>
  </aside>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ADSENSE_CLIENT } from '../config.js'

const props = defineProps({ adSlot: { type: String, default: '' } })
const enabled = Boolean(ADSENSE_CLIENT && props.adSlot)
const ins = ref(null)

onMounted(() => {
  if (!enabled) return
  try {
    ;(window.adsbygoogle = window.adsbygoogle || []).push({})
  } catch {
    // 광고 차단기 등으로 실패해도 페이지는 정상 동작
  }
})
</script>
