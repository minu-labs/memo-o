import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import DownloadPage from './pages/DownloadPage.vue'
import PrivacyPage from './pages/PrivacyPage.vue'
import { ADSENSE_CLIENT } from './config.js'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/memo-o' },
    { path: '/memo-o', component: DownloadPage, meta: { title: 'MemoO — 무료 오프라인 녹음 + 텍스트 변환 (Windows)' } },
    { path: '/memo-o/privacy', component: PrivacyPage, meta: { title: '개인정보처리방침 — MemoO' } },
    { path: '/:pathMatch(.*)*', redirect: '/memo-o' },
  ],
  scrollBehavior: (to) => (to.hash ? { el: to.hash, top: 16 } : { top: 0 }),
})
router.afterEach((to) => {
  if (to.meta.title) document.title = to.meta.title
})

if (ADSENSE_CLIENT) {
  const s = document.createElement('script')
  s.async = true
  s.crossOrigin = 'anonymous'
  s.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(ADSENSE_CLIENT)}`
  document.head.appendChild(s)
}

createApp(App).use(router).mount('#app')
