<template>
  <header class="nav">
    <div class="wrap nav-inner">
      <RouterLink to="/memo-o" class="brand">
        <svg class="brand-mark" width="22" height="22" viewBox="0 0 100 100" aria-hidden="true">
          <defs>
            <linearGradient id="brandGrad" x1="4" y1="4" x2="96" y2="96" gradientUnits="userSpaceOnUse">
              <stop offset="0" stop-color="#e2555a" />
              <stop offset="1" stop-color="#b92b2e" />
            </linearGradient>
          </defs>
          <rect x="4" y="4" width="92" height="92" rx="24" fill="url(#brandGrad)" />
          <rect x="24.75" y="37" width="11.5" height="26" rx="5.75" fill="#fff" />
          <rect x="44.25" y="27" width="11.5" height="46" rx="5.75" fill="#fff" />
          <rect x="63.75" y="33" width="11.5" height="34" rx="5.75" fill="#fff" />
        </svg>
        MemoO
      </RouterLink>
      <nav class="nav-links">
        <RouterLink to="/memo-o#features">기능</RouterLink>
        <RouterLink to="/memo-o/guide">사용법</RouterLink>
        <RouterLink to="/memo-o#faq">FAQ</RouterLink>
        <a :href="DOWNLOAD_URL" class="nav-cta">다운로드</a>
      </nav>
    </div>
  </header>
  <main>
    <RouterView />
  </main>
  <section v-if="showPromo" class="promo">
    <div class="wrap promo-inner">
      <div class="promo-text">
        <strong>MemoO</strong> — 인터넷 없이 PC 안에서 녹음하고 자동으로 텍스트로 바꿔주는 무료 Windows 프로그램입니다.
        음성 데이터는 이 PC 밖으로 나가지 않습니다.
      </div>
      <a :href="DOWNLOAD_URL" class="btn btn-primary promo-btn">MemoO 무료 다운로드</a>
    </div>
  </section>
  <footer class="footer">
    <div class="wrap footer-inner">
      <div>© {{ year }} minulog · MemoO는 무료 소프트웨어입니다.</div>
      <div class="footer-links">
        <RouterLink to="/memo-o/privacy">개인정보처리방침</RouterLink>
        <RouterLink to="/memo-o#licenses">오픈소스 라이선스</RouterLink>
        <a v-if="GITHUB_REPO" :href="REPO_URL" rel="noopener">GitHub</a>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DOWNLOAD_URL, GITHUB_REPO, REPO_URL } from './config.js'

const route = useRoute()
// 다운로드 페이지 자체에는 이미 같은 목적의 큰 CTA가 있어 중복 노출을 피한다.
const showPromo = computed(() => route.path !== '/memo-o')
const year = new Date().getFullYear()
</script>
