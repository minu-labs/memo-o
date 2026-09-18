<template>
  <header class="nav">
    <div class="wrap nav-inner">
      <RouterLink to="/memo-o" class="brand">
        <span class="dot" aria-hidden="true"></span>MemoO
      </RouterLink>
      <nav class="nav-links">
        <RouterLink to="/memo-o#features">기능</RouterLink>
        <RouterLink to="/memo-o#faq">FAQ</RouterLink>
        <a :href="DOWNLOAD_URL" class="nav-cta">다운로드</a>
      </nav>
    </div>
  </header>
  <main>
    <RouterView />
  </main>
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
import { DOWNLOAD_URL, GITHUB_REPO, REPO_URL } from './config.js'
const year = new Date().getFullYear()
</script>
