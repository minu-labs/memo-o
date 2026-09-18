// 배포 전에 채워야 하는 값은 .env(VITE_*)로 넣는다. README 참고.
const env = import.meta.env

export const APP_VERSION = '1.0.0'
export const INSTALLER_SIZE = env.VITE_INSTALLER_SIZE || '약 400MB'
export const GITHUB_REPO = env.VITE_GITHUB_REPO || '' // 예: "username/memo-o"
export const CONTACT_EMAIL = env.VITE_CONTACT_EMAIL || ''
export const ADSENSE_CLIENT = env.VITE_ADSENSE_CLIENT || '' // 예: "ca-pub-1234567890123456"
export const ADSENSE_SLOTS = {
  top: env.VITE_ADSENSE_SLOT_TOP || '',
  bottom: env.VITE_ADSENSE_SLOT_BOTTOM || '',
}

export const DOWNLOAD_URL = GITHUB_REPO
  ? `https://github.com/${GITHUB_REPO}/releases/latest/download/memo-o-setup-${APP_VERSION}.exe`
  : '#'
export const RELEASES_URL = GITHUB_REPO ? `https://github.com/${GITHUB_REPO}/releases` : '#'
export const REPO_URL = GITHUB_REPO ? `https://github.com/${GITHUB_REPO}` : '#'
