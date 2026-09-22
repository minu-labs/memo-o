import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import DownloadPage from './pages/DownloadPage.vue'
import GuidePage from './pages/GuidePage.vue'
import PrivacyPage from './pages/PrivacyPage.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/memo-o' },
    { path: '/memo-o', component: DownloadPage, meta: { title: 'MemoO — 무료 오프라인 녹음 + 텍스트 변환 (Windows)' } },
    { path: '/memo-o/guide', component: GuidePage, meta: { title: '사용법 — MemoO' } },
    { path: '/memo-o/privacy', component: PrivacyPage, meta: { title: '개인정보처리방침 — MemoO' } },
    { path: '/:pathMatch(.*)*', redirect: '/memo-o' },
  ],
  scrollBehavior: (to) => (to.hash ? { el: to.hash, top: 16 } : { top: 0 }),
})
router.afterEach((to) => {
  if (to.meta.title) document.title = to.meta.title
})

createApp(App).use(router).mount('#app')
