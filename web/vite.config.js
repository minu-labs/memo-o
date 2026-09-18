import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// AdSense 게시자 ID가 설정되어 있으면 빌드 결과에 ads.txt 를 생성한다.
function adsTxt(client) {
  return {
    name: 'ads-txt',
    generateBundle() {
      const pub = (client || '').replace(/^ca-/, '')
      if (!pub) return
      this.emitFile({
        type: 'asset',
        fileName: 'ads.txt',
        source: `google.com, ${pub}, DIRECT, f08c47fec0942fa0\n`,
      })
    },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  return {
    plugins: [vue(), adsTxt(env.VITE_ADSENSE_CLIENT)],
  }
})
