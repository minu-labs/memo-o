# MemoO

Windows용 오프라인 녹음 + 텍스트 변환(STT) 프로그램. 녹음하면 PC 안에서 한국어 텍스트로 자동 변환되며, 음성 데이터는 외부로 전송되지 않는다.

## 폴더 구조

```
memo_o/                 앱 소스
  app.py                진입점 (로그, 단일 실행 잠금, 초기화)
  paths.py              데이터/모델 경로 (%LOCALAPPDATA%\MemoO)
  recorder.py           sounddevice 마이크 녹음 (16kHz mono)
  wavfile.py            강제 종료에도 복구 가능한 WAV 기록기
  stt.py                faster-whisper 래퍼 (로컬 모델만 사용, CUDA 자동 감지)
  transcription.py      백그라운드 변환 큐 + 시작 시 복구
  db.py                 SQLite (recordings, segments, settings)
  export.py             txt / srt 내보내기
  ui/                   PySide6 화면 (메인 / 목록 / 상세, UI_SPEC.md 기준)
  resources/            아이콘, 오픈소스 고지
tests/                  pytest
scripts/                개발 보조 스크립트 (모델 다운로드, 스모크 테스트, 아이콘 생성)
memo-o.spec             PyInstaller 설정 (onedir)
installer/memo-o.iss    Inno Setup 설치 프로그램 (바탕화면 아이콘 생성)
build.ps1               exe + 설치 파일 빌드
web/                    minulog.com 다운로드 페이지 (Vue 3 + Vite, Vercel)
```

## 개발 환경

Windows용 Python 3.12+ 에서 실행한다 (마이크 접근이 필요하므로 WSL의 리눅스 Python으로는 녹음 불가).

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m scripts.download_model small   # models\small (약 480MB)
.venv\Scripts\python -m memo_o                          # 앱 실행
.venv\Scripts\python -m pytest tests                    # 테스트
```

WSL에서 작업할 때는 `scripts/wpy` 가 프로젝트의 Windows venv 파이썬을 대신 실행한다.

```bash
scripts/wpy -m memo_o
scripts/wpy -m pytest -p no:cacheprovider tests
scripts/wpy -m scripts.ui_smoke      # 샘플 데이터로 전 화면 캡처 → shots/
```

## 데이터 위치

| 항목 | 경로 |
| --- | --- |
| DB | `%LOCALAPPDATA%\MemoO\memo-o.db` |
| 녹음 | `%LOCALAPPDATA%\MemoO\recordings\*.wav` |
| 로그 | `%LOCALAPPDATA%\MemoO\memo-o.log` |
| 기본 모델 (small) | `<설치 폴더>\models\small` |
| 추가 모델 (medium 등) | `%LOCALAPPDATA%\MemoO\models\<size>` |

환경 변수 `MEMOO_DATA_DIR` 로 데이터 폴더를 바꿀 수 있다 (테스트용).

## 빌드

사전 준비: [Inno Setup 6](https://jrsoftware.org/isdl.php)

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1              # exe + 설치 파일
powershell -ExecutionPolicy Bypass -File build.ps1 -SkipInstaller
```

- `dist\memo-o\memo-o.exe` — 설치 없이 실행 가능한 폴더 (모델 포함)
- `dist\installer\memo-o-setup-1.0.0.exe` — 설치 파일. 기본으로 바탕화면 아이콘을 만든다. 관리자 권한 없이 사용자 폴더에 설치할 수도 있다.

WSL에서는 `scripts/wbuild` (네트워크 경로의 .ps1 실행 제한을 우회).

### onedir을 쓰는 이유

단일 파일(onefile) exe는 실행할 때마다 수백 MB를 임시 폴더에 풀어 시작이 느리고 백신 오탐도 잦다. 어차피 설치 프로그램으로 배포하므로 폴더 형태로 두고, 사용자는 바탕화면의 `memo-o.exe` 아이콘으로 실행한다. Qt(LGPL) 라이브러리를 사용자가 교체할 수 있다는 라이선스 요건도 자연스럽게 충족한다.

## medium 모델 배포

medium 모델(약 1.5GB)은 기본 설치에 넣지 않는다. 앱은 네트워크를 쓰지 않으므로 자동 다운로드도 하지 않는다.

1. `scripts/wpy -m scripts.download_model medium` 으로 `models\medium` 생성
2. `medium` 폴더를 zip으로 묶어 GitHub Releases에 별도 업로드
3. 사용자는 압축을 풀어 `%LOCALAPPDATA%\MemoO\models\medium` 에 넣고 설정에서 선택

## 다운로드 페이지 (web/)

```bash
cd web
npm install
npm run dev          # http://localhost:5173/memo-o
npm run build        # web/dist
```

`/memo-o` (다운로드), `/memo-o/guide` (사용법), `/memo-o/privacy` (개인정보처리방침). 배포 전에 `.env.example` 을 참고해 Vercel 환경 변수를 설정한다.

| 변수 | 설명 |
| --- | --- |
| `VITE_GITHUB_REPO` | `owner/memo-o` — 다운로드 버튼이 `releases/latest/download/memo-o-setup-<버전>.exe` 로 연결됨 |
| `VITE_INSTALLER_SIZE` | 설치 파일 크기 표시 |
| `VITE_CONTACT_EMAIL` | 개인정보처리방침 문의처 |

사이트에는 광고가 없다. 기존 minulog.com(Vue 3) 프로젝트에 합치려면 `src/pages/*.vue`, `src/config.js`, `public/screens/` 를 옮기고 라우트 세 개를 추가하면 된다.

## 릴리스 체크리스트

1. `memo_o/__init__.py`, `version_info.txt`, `installer/memo-o.iss`, `web/src/config.js` 의 버전 갱신
2. `build.ps1` 실행 → 설치 파일로 새 PC(또는 VM)에서 설치·녹음·변환·제거 확인
3. GitHub Releases에 `memo-o-setup-<버전>.exe` 업로드 (파일명 유지 — 다운로드 링크가 이 이름을 가리킴)
4. `web/` 배포
