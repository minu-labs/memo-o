; MemoO 설치 프로그램 (Inno Setup 6)
; build.ps1 이 dist\memo-o 를 만든 뒤 컴파일한다.

#define AppName "MemoO"
#define AppVersion "1.0.0"
#define AppExe "memo-o.exe"
#define AppURL "https://minulog.com"

[Setup]
AppId={{6C1E4B7A-3F0D-4E55-9A2B-8D1C0F7E5A31}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=minulog
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; 관리자 권한 없이 사용자 폴더에 설치 가능 (설치 시 선택)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist\installer
OutputBaseFilename=memo-o-setup-{#AppVersion}
SetupIconFile=..\memo_o\resources\memo-o.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
LZMANumBlockThreads=4
WizardStyle=modern
; Windows 표시 언어로 자동 선택 (한국어가 아니면 영어)
ShowLanguageDialog=no
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"; LicenseFile: "notice_en.txt"
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"; LicenseFile: "notice_ko.txt"

[CustomMessages]
english.DeleteDataPrompt=Also delete your recordings and transcripts?%n(%1)%n%nChoose [No] to keep them for the next install.
korean.DeleteDataPrompt=녹음 파일과 변환된 텍스트도 함께 삭제할까요?%n(%1)%n%n[아니요]를 선택하면 다음 설치 때 그대로 사용할 수 있습니다.

[Tasks]
; 바탕화면 아이콘은 기본으로 생성 (체크 해제 가능)
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\memo-o\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Code]
// 녹음 데이터(%LOCALAPPDATA%\MemoO)는 제거 시 삭제 여부를 묻는다.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{localappdata}\MemoO');
    if DirExists(DataDir) then
      if MsgBox(FmtMessage(CustomMessage('DeleteDataPrompt'), [DataDir]),
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(DataDir, True, True, True);
  end;
end;
