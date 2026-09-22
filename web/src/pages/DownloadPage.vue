<template>
  <section class="hero">
    <div class="wrap hero-inner">
      <div class="hero-text">
        <p class="eyebrow">Windows 10 / 11 · 무료</p>
        <h1>말하면 기록이 되는<br />오프라인 녹음 메모</h1>
        <p class="lead">
          MemoO는 녹음이 끝나면 자동으로 텍스트로 바꿔주는 Windows 프로그램입니다.
          <strong>인터넷 없이 PC 안에서만</strong> 동작하므로 음성이 외부로 전송되지 않습니다.
        </p>
        <div class="cta-row">
          <a :href="DOWNLOAD_URL" class="btn btn-primary btn-lg">
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M12 3a1 1 0 0 1 1 1v9.59l3.3-3.3a1 1 0 1 1 1.4 1.42l-5 5a1 1 0 0 1-1.4 0l-5-5a1 1 0 1 1 1.4-1.42l3.3 3.3V4a1 1 0 0 1 1-1Zm-8 15a1 1 0 0 1 1 1v1h14v-1a1 1 0 1 1 2 0v2a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-2a1 1 0 0 1 1-1Z" />
            </svg>
            무료 다운로드
          </a>
          <div class="cta-meta">v{{ APP_VERSION }} · 64비트 설치 파일 · {{ INSTALLER_SIZE }}</div>
        </div>
        <p class="hero-note">회원가입·광고·사용 기록 수집 없음</p>
      </div>
      <div class="hero-shots" aria-hidden="true">
        <img src="/screens/main.png" alt="" class="shot shot-back" width="440" height="640" />
        <img src="/screens/detail.png" alt="" class="shot shot-front" width="440" height="640" />
      </div>
    </div>
  </section>

  <section id="features" class="section">
    <div class="wrap">
      <h2>이런 분께 필요합니다</h2>
      <div class="usecases">
        <div class="usecase" v-for="u in usecases" :key="u.title">
          <div class="usecase-title">{{ u.title }}</div>
          <div class="usecase-desc">{{ u.desc }}</div>
        </div>
      </div>

      <div class="features">
        <div class="feature" v-for="f in features" :key="f.title">
          <svg class="feature-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path fill="currentColor" :d="f.icon" />
          </svg>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section section-alt">
    <div class="wrap two-col">
      <div>
        <h2>사용 방법</h2>
        <ol class="steps">
          <li><b>설치 파일 실행</b> — 바탕화면에 MemoO 아이콘이 생깁니다.</li>
          <li><b>빨간 버튼 클릭</b> — 녹음이 시작됩니다. 다시 누르면 저장됩니다.</li>
          <li><b>자동 텍스트 변환</b> — 녹음을 저장하면 PC에서 바로 텍스트로 바뀝니다.</li>
          <li><b>찾아보고 내보내기</b> — 문장을 누르면 그 부분부터 재생되고, txt·srt로 저장할 수 있습니다.</li>
        </ol>
        <p class="small"><RouterLink to="/memo-o/guide">전체 사용법 보기 →</RouterLink></p>
      </div>
      <div>
        <h2>시스템 요구사항</h2>
        <table class="spec">
          <tbody>
            <tr><th>운영체제</th><td>Windows 10 / 11 (64비트)</td></tr>
            <tr><th>메모리</th><td>4GB 이상 (8GB 권장)</td></tr>
            <tr><th>저장 공간</th><td>약 1GB + 녹음 파일 (1시간 ≈ 115MB)</td></tr>
            <tr><th>마이크</th><td>내장 또는 외장 마이크</td></tr>
            <tr><th>인터넷</th><td>필요 없음 (다운로드 시에만)</td></tr>
            <tr><th>GPU</th><td>선택 사항 (NVIDIA CUDA 지원 시 자동 가속)</td></tr>
          </tbody>
        </table>
        <p class="muted small">
          텍스트 변환 속도는 PC 사양에 따라 다릅니다. 일반 사무용 PC(CPU)에서는
          보통 녹음 길이보다 짧은 시간 안에 변환이 끝납니다.
        </p>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="notice">
        <h2>개인정보와 법적 고지</h2>
        <p>
          <b>음성은 PC 밖으로 나가지 않습니다.</b> MemoO는 인터넷에 연결하지 않으며, 녹음 파일과 변환된 텍스트는
          사용자 PC(<code>%LOCALAPPDATA%\MemoO</code>)에만 저장됩니다. 앱 안에는 광고나 사용 기록 수집 기능이 없습니다.
        </p>
        <p>
          <b>녹음은 적법하게 사용해주세요.</b> 통신비밀보호법에 따라 본인이 참여한 대화의 녹음은 상대방의 동의 없이도
          가능하지만, <b>본인이 참여하지 않은 타인 간의 대화를 몰래 녹음하는 것은 불법</b>이며 형사처벌 대상입니다.
          녹음 기능의 사용과 그 결과에 대한 책임은 사용자에게 있습니다.
        </p>
      </div>
    </div>
  </section>

  <section id="faq" class="section section-alt">
    <div class="wrap narrow">
      <h2>자주 묻는 질문</h2>
      <details v-for="q in faq" :key="q.q" class="faq">
        <summary>{{ q.q }}</summary>
        <p v-html="q.a"></p>
      </details>
    </div>
  </section>

  <section id="licenses" class="section">
    <div class="wrap narrow">
      <h2>오픈소스 라이선스</h2>
      <p class="muted">MemoO는 다음 오픈소스 소프트웨어 덕분에 만들어졌습니다.</p>
      <ul class="licenses">
        <li v-for="l in licenses" :key="l.name">
          <a :href="l.url" rel="noopener">{{ l.name }}</a> <span class="muted">— {{ l.license }}</span>
        </li>
      </ul>
    </div>
  </section>

  <section class="section final-cta">
    <div class="wrap">
      <h2>지금 바로 기록을 시작하세요</h2>
      <a :href="DOWNLOAD_URL" class="btn btn-primary btn-lg">MemoO 무료 다운로드</a>
      <p class="muted small">
        이전 버전과 변경 내역은 <a :href="RELEASES_URL" rel="noopener">GitHub Releases</a>에서 볼 수 있습니다.
      </p>
    </div>
  </section>
</template>

<script setup>
import { APP_VERSION, DOWNLOAD_URL, INSTALLER_SIZE, RELEASES_URL } from '../config.js'

const usecases = [
  { title: '아이디어 메모', desc: '떠오른 생각을 말로 남기고 나중에 글로 정리' },
  { title: '강의 노트', desc: '수업·세미나를 녹음하고 필요한 부분만 검색' },
  { title: '상담 기록', desc: '상담 내용을 빠짐없이 기록 (본인 참여 대화)' },
  { title: '회의 기록', desc: '대면 회의를 녹음해 회의록 작성 부담 줄이기' },
]

const features = [
  {
    icon: 'M12 2a5 5 0 0 0-5 5v2H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2h-1V7a5 5 0 0 0-5-5Zm0 2a3 3 0 0 1 3 3v2H9V7a3 3 0 0 1 3-3Zm0 9a2 2 0 0 1 1 3.73V18a1 1 0 1 1-2 0v-1.27A2 2 0 0 1 12 13Z',
    title: '완전 오프라인',
    desc: '음성 인식 모델이 PC에 함께 설치됩니다. 인터넷이 끊겨도, 사내망에서도 그대로 동작합니다.',
  },
  {
    icon: 'M13.5 2 4 13.5a.75.75 0 0 0 .58 1.22h5.13l-1.2 7.06a.6.6 0 0 0 1.06.47L20 10.5a.75.75 0 0 0-.58-1.22h-5.13l1.2-7.06A.6.6 0 0 0 13.5 2Z',
    title: '녹음 후 자동 변환',
    desc: '버튼 한 번으로 녹음하고, 저장하면 한국어 텍스트로 자동 변환됩니다. 변환 중에도 바로 재생할 수 있습니다.',
  },
  {
    icon: 'M10.5 3a7.5 7.5 0 1 0 4.55 13.46l4.24 4.25a1.06 1.06 0 0 0 1.5-1.5l-4.25-4.24A7.5 7.5 0 0 0 10.5 3Zm0 2a5.5 5.5 0 1 1 0 11 5.5 5.5 0 0 1 0-11Z',
    title: '검색과 구간 재생',
    desc: '제목과 내용으로 녹음을 찾고, 문장을 클릭하면 그 시점부터 다시 들을 수 있습니다.',
  },
  {
    icon: 'M6 2a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8.83a2 2 0 0 0-.59-1.42l-4.82-4.82A2 2 0 0 0 13.17 2H6Zm7 1.5L18.5 9H14a1 1 0 0 1-1-1V3.5ZM8 12h8a1 1 0 1 1 0 2H8a1 1 0 1 1 0-2Zm0 4h8a1 1 0 1 1 0 2H8a1 1 0 1 1 0-2Z',
    title: '내보내기',
    desc: '타임스탬프가 붙은 텍스트(.txt), 자막(.srt), 원본 음성(.wav)으로 저장할 수 있습니다.',
  },
  {
    icon: 'M12 2 4 5.2v6.12c0 4.84 3.32 9.36 8 10.68 4.68-1.32 8-5.84 8-10.68V5.2L12 2Zm3.83 7.09a1 1 0 0 1 .08 1.32l-4.2 5a1 1 0 0 1-1.47.07l-2.3-2.24a1 1 0 0 1 1.4-1.44l1.52 1.49 3.52-4.19a1 1 0 0 1 1.45-.01Z',
    title: '강제 종료에도 안전',
    desc: '녹음 중 PC가 꺼지거나 프로그램이 종료돼도 그때까지의 녹음은 보존됩니다.',
  },
  {
    icon: 'M5 3a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H5Zm0 2h14v2.5H5V5Zm0 4.5h14V19H5V9.5Zm2.75 2a1 1 0 1 0 0 2h5.5a1 1 0 1 0 0-2h-5.5Z',
    title: '작고 단순한 화면',
    desc: '작은 창 하나로 녹음·목록·상세 화면만 담았습니다. 설정할 것이 거의 없습니다.',
  },
]

const faq = [
  {
    q: '정말 무료인가요?',
    a: '네. 기능 제한이나 기간 제한 없이 무료입니다.',
  },
  {
    q: '설치할 때 "Windows의 PC 보호" 경고가 나와요.',
    a: '개인이 배포하는 프로그램이라 코드 서명 인증서가 없어 나타나는 안내입니다. <b>추가 정보 → 실행</b>을 누르면 설치가 진행됩니다. 설치 파일은 GitHub Releases에서만 배포됩니다.',
  },
  {
    q: '녹음 파일은 어디에 저장되나요?',
    a: '<code>%LOCALAPPDATA%\\MemoO</code> 폴더에 저장됩니다. 프로그램의 메뉴(⋯) → <b>데이터 폴더 열기</b>로 바로 열 수 있습니다. 프로그램을 제거할 때 녹음을 함께 지울지 선택할 수 있습니다.',
  },
  {
    q: '변환 정확도를 높이고 싶어요.',
    a: '마이크를 말하는 사람 가까이에 두고 주변 소음을 줄이면 정확도가 크게 올라갑니다. 고사양 PC라면 더 정확한 medium 모델을 추가해 설정에서 선택할 수 있습니다.',
  },
  {
    q: '화상회의(Zoom, Teams) 소리도 녹음되나요?',
    a: '현재 버전은 마이크 입력만 녹음합니다. PC에서 나오는 소리를 직접 녹음하는 기능은 지원하지 않습니다.',
  },
  {
    q: 'Mac에서도 쓸 수 있나요?',
    a: 'MemoO는 Windows 전용입니다.',
  },
]

const licenses = [
  { name: 'faster-whisper', license: 'MIT', url: 'https://github.com/SYSTRAN/faster-whisper' },
  { name: 'CTranslate2', license: 'MIT', url: 'https://github.com/OpenNMT/CTranslate2' },
  { name: 'OpenAI Whisper (모델)', license: 'MIT', url: 'https://github.com/openai/whisper' },
  { name: 'Silero VAD', license: 'MIT', url: 'https://github.com/snakers4/silero-vad' },
  { name: 'ONNX Runtime', license: 'MIT', url: 'https://github.com/microsoft/onnxruntime' },
  { name: 'sounddevice / PortAudio', license: 'MIT', url: 'https://github.com/spatialaudio/python-sounddevice' },
  { name: 'NumPy', license: 'BSD-3-Clause', url: 'https://numpy.org' },
  { name: 'PyAV / FFmpeg', license: 'BSD-3-Clause / LGPL-2.1+', url: 'https://github.com/PyAV-Org/PyAV' },
  { name: 'Qt for Python (PySide6)', license: 'LGPL-3.0', url: 'https://www.qt.io/qt-for-python' },
]
</script>
