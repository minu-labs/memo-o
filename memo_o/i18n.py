"""화면 문자열 (한국어/영어).

앱 시작 시 한 번 언어를 정하고(설정값 → 없으면 Windows 표시 언어), 바꾸면 재시작 후 적용된다.
언어를 추가하려면 UI_LANGS 와 _STRINGS 의 각 항목에 값을 추가하면 된다.
"""

UI_LANGS = ("ko", "en")
UI_LANG_NAMES = {"ko": "한국어", "en": "English"}

_lang = "en"


def system_lang() -> str:
    try:
        from PySide6.QtCore import QLocale
        return "ko" if QLocale.system().language() == QLocale.Language.Korean else "en"
    except Exception:
        return "en"


def resolve(setting: str | None) -> str:
    """설정값("auto"/None 이면 시스템 언어)을 실제 UI 언어 코드로."""
    return setting if setting in UI_LANGS else system_lang()


def set_language(code: str) -> None:
    global _lang
    _lang = code if code in UI_LANGS else "en"


def language() -> str:
    return _lang


def tr(key: str, **kw) -> str:
    text = _STRINGS[key][_lang]
    return text.format(**kw) if kw else text


_STRINGS: dict[str, dict[str, str]] = {
    # --- 공통 ---
    "common.delete": {"ko": "삭제", "en": "Delete"},
    "common.save": {"ko": "저장", "en": "Save"},
    "common.cancel": {"ko": "취소", "en": "Cancel"},

    # --- 앱 ---
    "app.unhandled_error": {
        "ko": "예상치 못한 오류가 발생했습니다.\n{exc}\n\n로그: {log}",
        "en": "An unexpected error occurred.\n{exc}\n\nLog: {log}",
    },
    "app.already_running": {"ko": "MemoO가 이미 실행 중입니다.", "en": "MemoO is already running."},

    # --- 마이크 / 녹음기 ---
    "mic.default": {"ko": "기본 마이크", "en": "Default microphone"},
    "mic.interrupted": {"ko": "마이크 입력이 중단되었습니다.", "en": "Microphone input was interrupted."},
    "system.unavailable": {
        "ko": "PC 소리를 녹음할 수 없어 마이크만 녹음합니다.",
        "en": "Couldn't capture PC audio. Recording the microphone only.",
    },
    "system.interrupted": {
        "ko": "PC 소리 녹음이 중단되어 마이크만 계속 녹음합니다.",
        "en": "PC audio capture stopped. Continuing with the microphone only.",
    },

    # --- 텍스트 변환 ---
    "stt.model_missing": {
        "ko": "'{size}' 모델을 찾을 수 없습니다. 설치 폴더 또는 데이터 폴더의 models\\{size} 에 모델 파일을 넣어주세요.",
        "en": "Could not find the '{size}' model. Put the model files in models\\{size} "
              "inside the install folder or the data folder.",
    },
    "stt.recover_failed": {"ko": "녹음 파일 복구 실패: {e}", "en": "Could not recover the recording file: {e}"},
    "stt.file_missing": {"ko": "녹음 파일이 없습니다.", "en": "The recording file is missing."},

    # --- 상태 배지 ---
    "status.done": {"ko": "완료", "en": "Done"},
    "status.transcribing": {"ko": "변환 중", "en": "Transcribing"},
    "status.transcribing_p": {"ko": "변환 중 {p}", "en": "Transcribing {p}"},
    "status.pending": {"ko": "변환 대기", "en": "Queued"},
    "status.recording": {"ko": "녹음 중", "en": "Recording"},
    "status.error": {"ko": "오류", "en": "Error"},

    # --- 타이틀바 / 창 ---
    "win.recording_title": {"ko": "● 녹음 중 - MemoO", "en": "● Recording - MemoO"},
    "tip.back_to_rec": {"ko": "녹음 화면으로 돌아가기", "en": "Back to the recording screen"},
    "tip.menu": {"ko": "메뉴", "en": "Menu"},
    "tip.minimize": {"ko": "최소화", "en": "Minimize"},
    "tip.maximize": {"ko": "최대화", "en": "Maximize"},
    "tip.restore": {"ko": "이전 크기로", "en": "Restore down"},
    "tip.close": {"ko": "닫기", "en": "Close"},
    "tip.record": {"ko": "녹음 시작/중지 (Space)", "en": "Start/stop recording (Space)"},

    # --- 메뉴 / 토스트 ---
    "menu.compact": {"ko": "컴팩트 모드로 전환", "en": "Switch to compact mode"},
    "menu.settings": {"ko": "설정", "en": "Settings"},
    "menu.reload_mics": {"ko": "마이크 목록 새로고침", "en": "Refresh microphone list"},
    "menu.open_data": {"ko": "데이터 폴더 열기", "en": "Open data folder"},
    "menu.import": {"ko": "파일 가져오기...", "en": "Import files..."},
    "menu.about": {"ko": "MemoO 정보", "en": "About MemoO"},
    "toast.stt_settings": {
        "ko": "다음 변환부터 새 설정이 적용됩니다.",
        "en": "The new settings apply from the next transcription.",
    },
    "toast.mic_busy": {
        "ko": "녹음 중에는 마이크를 바꿀 수 없습니다.",
        "en": "You can't change the microphone while recording.",
    },
    "toast.mics_reloaded": {"ko": "마이크 목록을 새로 불러왔습니다.", "en": "Microphone list refreshed."},
    "rec.not_found": {"ko": "녹음을 찾을 수 없습니다.", "en": "Recording not found."},
    "quit.title": {"ko": "녹음 중", "en": "Recording"},
    "quit.confirm": {
        "ko": "녹음 중입니다. 녹음을 저장하고 종료할까요?",
        "en": "A recording is in progress. Save it and quit?",
    },

    # --- 화면 1. 녹음 ---
    "rec.start": {"ko": "녹음 시작", "en": "Start recording"},
    "rec.stop": {"ko": "녹음 중지", "en": "Stop recording"},
    "rec.mic": {"ko": "마이크", "en": "Mic"},
    "rec.system_audio": {"ko": "PC 소리도 함께 녹음", "en": "Also record PC audio"},
    "rec.system_audio_tip": {
        "ko": "스피커·헤드폰으로 나오는 소리(온라인 회의 상대방 목소리, 영상 등)를 마이크와 함께 녹음합니다.\n"
              "스피커를 쓰면 마이크에도 소리가 들어가 겹칠 수 있어 헤드폰을 권장합니다.",
        "en": "Records the sound playing through your speakers or headphones "
              "(people in an online meeting, videos, etc.) together with the microphone.\n"
              "Headphones are recommended, since speaker sound can also be picked up by the microphone.",
    },
    "rec.recent": {"ko": "최근 녹음", "en": "Recent recordings"},
    "rec.view_all": {"ko": "녹음 목록 전체보기 >", "en": "View all recordings >"},
    "rec.empty": {
        "ko": "아직 녹음이 없습니다. 버튼을 눌러 첫 메모를 남겨보세요.",
        "en": "No recordings yet. Press the button to record your first memo.",
    },
    "rec.open": {"ko": "열기", "en": "Open"},
    "rec.start_failed_title": {"ko": "녹음 시작 실패", "en": "Couldn't start recording"},
    "rec.start_failed": {
        "ko": "마이크를 열 수 없습니다.\n마이크 연결과 Windows 개인정보 설정(마이크 접근 허용)을 확인해주세요.\n\n{e}",
        "en": "Couldn't open the microphone.\n"
              "Check the microphone connection and Windows privacy settings (microphone access).\n\n{e}",
    },
    "rec.default_title": {"ko": "녹음 {date}", "en": "Recording {date}"},
    "rec.status_recording": {"ko": "상태: <b>녹음 중...</b>", "en": "Status: <b>Recording...</b>"},
    "rec.status_idle": {"ko": "상태: <b>대기 중</b>", "en": "Status: <b>Ready</b>"},
    "rec.time": {"ko": "시간: <b>{t}</b>", "en": "Time: <b>{t}</b>"},
    "rec.save_title": {"ko": "녹음 저장", "en": "Save recording"},
    "rec.enter_title": {"ko": "제목을 입력하세요", "en": "Enter a title"},
    "rec.interrupted_title": {"ko": "녹음 중단", "en": "Recording stopped"},
    "rec.interrupted": {
        "ko": "{msg}\n그때까지 녹음된 내용은 저장되었습니다.",
        "en": "{msg}\nEverything recorded up to that point has been saved.",
    },

    # --- 컴팩트 창 ---
    "compact.title": {"ko": "MemoO - 녹음 중", "en": "MemoO - Recording"},
    "compact.minimize": {"ko": "작업표시줄로 최소화", "en": "Minimize to taskbar"},

    # --- 화면 2. 목록 ---
    "list.title": {"ko": "MemoO - 녹음 목록", "en": "MemoO - Recordings"},
    "list.search": {"ko": "검색 (제목, 내용)", "en": "Search (title, text)"},
    "list.new": {"ko": "+ 새 녹음", "en": "+ New"},
    "list.import": {"ko": "가져오기", "en": "Import"},
    "list.import_tip": {
        "ko": "PC의 음성·영상 파일을 텍스트로 변환합니다 (창에 끌어다 놓아도 됩니다)",
        "en": "Transcribe audio or video files from your PC (you can also drag them onto the window)",
    },
    "list.back_to_rec": {"ko": "● 녹음으로 돌아가기", "en": "● Back to recording"},
    "list.prev": {"ko": "< 이전", "en": "< Prev"},
    "list.next": {"ko": "다음 >", "en": "Next >"},
    "list.no_results": {"ko": "검색 결과가 없습니다.", "en": "No results."},
    "list.empty": {"ko": "아직 녹음이 없습니다.", "en": "No recordings yet."},
    "del.title": {"ko": "녹음 삭제", "en": "Delete recording"},
    "del.confirm": {
        "ko": "'{title}' 녹음과 변환된 텍스트를 삭제할까요?\n삭제한 녹음은 복구할 수 없습니다.",
        "en": "Delete '{title}' and its transcript?\nDeleted recordings can't be recovered.",
    },

    # --- 파일 가져오기 ---
    "import.dialog": {"ko": "변환할 파일 선택", "en": "Choose files to transcribe"},
    "import.filter_media": {"ko": "음성·영상 파일 ({exts})", "en": "Audio and video files ({exts})"},
    "import.filter_all": {"ko": "모든 파일 (*.*)", "en": "All files (*.*)"},
    "import.drop_hint": {
        "ko": "여기에 놓으면 텍스트로 변환합니다",
        "en": "Drop here to transcribe",
    },
    "import.started": {"ko": "파일 {n}개를 가져오는 중...", "en": "Importing {n} file(s)..."},
    "import.busy": {
        "ko": "이전 파일을 가져오는 중입니다. 잠시 후 다시 시도해주세요.",
        "en": "Still importing the previous files. Try again in a moment.",
    },
    "import.done": {
        "ko": "파일 {n}개를 가져왔습니다. 차례로 텍스트로 변환합니다.",
        "en": "Imported {n} file(s). They will be transcribed in order.",
    },
    "import.failed_title": {"ko": "가져오기 실패", "en": "Import failed"},
    "import.failed": {
        "ko": "다음 파일을 가져오지 못했습니다.\n\n{files}",
        "en": "The following files couldn't be imported.\n\n{files}",
    },
    "import.unsupported": {"ko": "지원하지 않는 파일 형식입니다.", "en": "This file type isn't supported."},
    "import.no_audio": {"ko": "소리가 들어 있지 않은 파일입니다.", "en": "This file has no audio."},
    "import.unreadable": {
        "ko": "파일을 읽을 수 없습니다. 손상되었거나 지원하지 않는 형식일 수 있습니다.",
        "en": "Couldn't read the file. It may be damaged or in an unsupported format.",
    },

    # --- 화면 3. 상세 ---
    "detail.back10": {"ko": "10초 뒤로", "en": "Back 10 seconds"},
    "detail.play": {"ko": "재생 / 일시정지", "en": "Play / Pause"},
    "detail.fwd10": {"ko": "10초 앞으로", "en": "Forward 10 seconds"},
    "detail.search": {"ko": "내용 검색", "en": "Search transcript"},
    "detail.export": {"ko": "내보내기", "en": "Export"},
    "detail.rename": {"ko": "제목 변경", "en": "Rename"},
    "detail.new_title": {"ko": "새 제목", "en": "New title"},
    "detail.no_match": {"ko": "'{q}' 검색 결과가 없습니다.", "en": "No results for '{q}'."},
    "detail.no_speech": {"ko": "인식된 음성이 없습니다.", "en": "No speech was detected."},
    "detail.failed": {"ko": "텍스트 변환에 실패했습니다.", "en": "Transcription failed."},
    "detail.retry": {"ko": "다시 변환하기", "en": "Try again"},
    "detail.transcribing": {
        "ko": "{status} — 텍스트로 변환하고 있습니다.<br>"
              "변환이 끝나면 이 화면에 자동으로 표시됩니다. 녹음은 지금 바로 재생할 수 있습니다.",
        "en": "{status} — converting speech to text.<br>"
              "The text will appear here automatically when it's done. You can play the recording now.",
    },
    "detail.pending": {
        "ko": "변환 대기 중입니다. 앞선 녹음의 변환이 끝나면 자동으로 시작됩니다.",
        "en": "Waiting to transcribe. It starts automatically after earlier recordings are done.",
    },
    "detail.recording": {"ko": "녹음 중입니다.", "en": "Recording in progress."},
    "detail.play_error_title": {"ko": "재생 오류", "en": "Playback error"},
    "detail.play_error": {"ko": "녹음 파일을 재생할 수 없습니다.\n{msg}", "en": "Can't play the recording file.\n{msg}"},
    "export.txt": {"ko": "텍스트 파일 (.txt)", "en": "Text file (.txt)"},
    "export.srt": {"ko": "자막 파일 (.srt)", "en": "Subtitle file (.srt)"},
    "export.copy": {"ko": "텍스트 복사 (클립보드)", "en": "Copy text (clipboard)"},
    "export.audio": {"ko": "음성 파일 ({ext})", "en": "Audio file ({ext})"},
    "export.filter_txt": {"ko": "텍스트 파일 (*.txt)", "en": "Text files (*.txt)"},
    "export.filter_srt": {"ko": "자막 파일 (*.srt)", "en": "Subtitle files (*.srt)"},
    "export.filter_audio": {"ko": "음성 파일 (*{ext})", "en": "Audio files (*{ext})"},
    "export.failed": {"ko": "내보내기 실패", "en": "Export failed"},
    "export.copied": {"ko": "텍스트를 클립보드에 복사했습니다.", "en": "Text copied to the clipboard."},

    # --- 안내 / 정보 대화상자 ---
    # 법적 고지: 한국어는 국내법(통신비밀보호법) 기준, 영어는 국가별로 다르다는 일반 고지.
    "notice.legal": {
        "ko": "<b>녹음 관련 법적 고지</b><br>"
              "통신비밀보호법에 따라 <b>본인이 참여한 대화</b>의 녹음은 상대방의 동의 없이도 가능하지만, "
              "<b>본인이 참여하지 않은 타인 간의 대화를 몰래 녹음하는 것은 불법</b>이며 형사처벌 대상입니다. "
              "온라인 회의·통화 등 PC 소리를 녹음할 때도 같습니다. "
              "녹음 기능의 사용과 그 결과에 대한 책임은 사용자에게 있습니다.",
        "en": "<b>Legal notice on recording</b><br>"
              "Laws on recording conversations differ by country and region. Some places allow you to record "
              "a conversation you take part in, while others require <b>everyone's consent</b>. "
              "<b>Secretly recording conversations you are not part of is illegal in most places.</b> "
              "This also applies to PC audio such as online meetings and calls. "
              "Check the laws where you live before recording. "
              "You are responsible for how you use the recording feature and its results.",
    },
    "notice.privacy": {
        "ko": "<b>개인정보 보호</b><br>"
              "MemoO는 인터넷에 연결하지 않습니다. 녹음 파일과 변환된 텍스트는 "
              "이 PC 안에서만 처리·저장되며 외부 서버로 전송되지 않습니다.",
        "en": "<b>Privacy</b><br>"
              "MemoO never connects to the internet. Recordings and transcripts are processed and "
              "stored only on this PC and are never sent to an external server.",
    },
    "notice.title": {"ko": "MemoO 사용 안내", "en": "Welcome to MemoO"},
    "notice.welcome": {
        "ko": "MemoO에 오신 것을 환영합니다. 사용 전에 아래 내용을 확인해주세요.",
        "en": "Welcome to MemoO. Please read the following before you start.",
    },
    "notice.agree": {"ko": "위 내용을 확인했습니다", "en": "I have read the above"},
    "notice.start": {"ko": "시작하기", "en": "Get started"},
    "about.tagline": {
        "ko": "오프라인 녹음 + 텍스트 변환(STT) 프로그램 · 무료",
        "en": "Offline recording + speech-to-text · Free",
    },
    "about.licenses": {"ko": "<b>오픈소스 라이선스</b>", "en": "<b>Open-source licenses</b>"},

    # --- 설정 ---
    "settings.ui_lang": {"ko": "<b>화면 언어</b>", "en": "<b>Display language</b>"},
    "settings.ui_auto": {"ko": "Windows 설정 따르기", "en": "Match Windows"},
    "settings.restart": {
        "ko": "화면 언어는 MemoO를 다시 시작하면 적용됩니다.",
        "en": "The display language will change after you restart MemoO.",
    },
    "settings.speech_lang": {"ko": "<b>음성 언어</b>", "en": "<b>Speech language</b>"},
    "settings.speech_auto": {"ko": "자동 감지 (여러 언어 섞여도 됨)", "en": "Auto-detect (mixed languages OK)"},
    "settings.speech_help": {
        "ko": "짧거나 잡음이 많은 녹음이 다른 언어로 인식되면 언어를 직접 지정하세요.",
        "en": "If a short or noisy recording comes out in the wrong language, choose the language here.",
    },
    "settings.model": {"ko": "<b>텍스트 변환 모델</b>", "en": "<b>Transcription model</b>"},
    "settings.model_small": {"ko": "small — 빠름, 일반 PC 권장", "en": "small — fast, recommended for most PCs"},
    "settings.model_medium": {
        "ko": "medium — 더 정확함, 느림 (고사양 PC 권장)",
        "en": "medium — more accurate, slower (for high-end PCs)",
    },
    "settings.model_missing": {"ko": "  (모델 없음)", "en": "  (not installed)"},
    "settings.model_help": {
        "ko": "medium 모델은 용량이 커서(약 1.4GB) 기본 설치에 포함되지 않습니다. 필요하면 따로 받아 추가할 수 있습니다.<br>"
              "변환 장치: {device}",
        "en": "The medium model is large (about 1.4GB), so it isn't included in the default install. "
              "You can download and add it separately.<br>Device: {device}",
    },
    "settings.get_medium": {"ko": "medium 모델 받기...", "en": "Get the medium model..."},
    "settings.open_models": {"ko": "모델 폴더 열기", "en": "Open model folder"},
    "settings.theme": {"ko": "<b>테마</b>", "en": "<b>Theme</b>"},

    # --- medium 모델 설치 안내 ---
    "medium.title": {"ko": "medium 모델 설치", "en": "Install the medium model"},
    "medium.intro": {
        "ko": "medium 모델은 small보다 정확하지만 2~3배 느리고 메모리를 더 사용합니다. "
              "사양이 높은 PC나 NVIDIA GPU가 있는 PC에 권장합니다. 아래 순서대로 설치하세요.",
        "en": "The medium model is more accurate than small, but 2–3× slower and uses more memory. "
              "It is recommended for high-end PCs or PCs with an NVIDIA GPU. Follow the steps below.",
    },
    "medium.step1": {
        "ko": "<b>1.</b> 아래 버튼을 누르면 브라우저에서 <b>memo-o-model-medium.zip</b>(약 1.4GB) 다운로드가 시작됩니다.",
        "en": "<b>1.</b> Click the button below to download <b>memo-o-model-medium.zip</b> (about 1.4GB) "
              "in your browser.",
    },
    "medium.download": {"ko": "다운로드 (약 1.4GB)", "en": "Download (about 1.4GB)"},
    "medium.step2": {
        "ko": "<b>2.</b> 받은 zip 파일의 압축을 아래 폴더에 풉니다. "
              "<b>models\\medium\\model.bin</b> 이 되면 됩니다.<br>{path}",
        "en": "<b>2.</b> Extract the zip file into the folder below, so that you end up with "
              "<b>models\\medium\\model.bin</b>.<br>{path}",
    },
    "medium.step3": {
        "ko": "<b>3.</b> [설치 확인]을 누르면 medium 모델을 선택할 수 있습니다. 다음 변환부터 적용됩니다.",
        "en": "<b>3.</b> Click [Check installation] to select the medium model. It applies from the next transcription.",
    },
    "medium.check": {"ko": "설치 확인", "en": "Check installation"},
    "medium.found": {"ko": "medium 모델을 찾았습니다.", "en": "Found the medium model."},
    "medium.not_found": {
        "ko": "아직 medium 모델을 찾을 수 없습니다.\n압축을 푼 위치를 확인해주세요.\n\n찾는 위치: {path}\\medium\\model.bin",
        "en": "The medium model wasn't found yet.\nCheck where you extracted the zip.\n\n"
              "Expected: {path}\\medium\\model.bin",
    },
    "settings.theme_light": {"ko": "라이트 (밝은 배경)", "en": "Light"},
    "settings.theme_dark": {"ko": "다크 (어두운 배경)", "en": "Dark"},
}
