# MemoO 빌드: exe(PyInstaller) → 모델 동봉 → 설치 프로그램(Inno Setup)
#   powershell -ExecutionPolicy Bypass -File build.ps1 [-SkipInstaller]
param([switch]$SkipInstaller)
$ErrorActionPreference = "Stop"
$root = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).ProviderPath }
Set-Location $root
$py = Join-Path $root ".venv\Scripts\python.exe"
$work = Join-Path $env:TEMP "memo-o-build"

Write-Host "== 1/3 PyInstaller" -ForegroundColor Cyan
& $py -m PyInstaller memo-o.spec --noconfirm --clean --workpath $work --distpath dist
if ($LASTEXITCODE -ne 0) { throw "PyInstaller 실패" }

Write-Host "== 2/3 모델 동봉 (models\small → int8)" -ForegroundColor Cyan
# 설치 파일 용량을 줄이기 위해 small 모델 가중치를 int8로 저장해 넣는다 (484MB → 245MB).
# CPU에서는 원래 int8로 연산하므로 결과가 같고, GPU에서는 불러올 때 float16으로 변환된다.
$model = Join-Path $root "models\small\model.bin"
$q = Join-Path $root "models\small-int8"
if (-not (Test-Path (Join-Path $q "model.bin"))) {
    if (-not (Test-Path $model)) { & $py -m scripts.download_model small }
    & $py -m scripts.quantize_model models\small models\small-int8
    if ($LASTEXITCODE -ne 0) { throw "모델 int8 변환 실패" }
}
$dest = Join-Path $root "dist\memo-o\models\small"
New-Item -ItemType Directory -Force $dest | Out-Null
# \\wsl.localhost 브리지로 큰 파일(model.bin, ~500MB)을 Windows 쪽에서 복사하면
# 크기는 같지만 내용이 손상되는 경우가 있다. WSL 안에 체크아웃된 프로젝트라면
# wsl.exe로 리눅스 파일시스템 안에서 직접 cp해 브리지를 우회하고,
# 일반 Windows 경로라면 robocopy(/J, 미버퍼링 I/O)를 사용한다.
if ($root -match '^\\\\wsl(\.localhost|\$)\\([^\\]+)\\(.+)$') {
    $wslDistro = $Matches[2]
    $wslPath = "/" + ($Matches[3] -replace '\\', '/')
    & wsl.exe -d $wslDistro -- bash -lc "cp -f '$wslPath/models/small-int8/'*.bin '$wslPath/models/small-int8/'*.json '$wslPath/models/small-int8/'*.txt '$wslPath/dist/memo-o/models/small/'"
    if ($LASTEXITCODE -ne 0) { throw "모델 파일 복사 실패 (wsl cp, exit $LASTEXITCODE)" }
} else {
    robocopy $q $dest /J /R:3 /W:2 /NFL /NDL /NJH /NJS
    if ($LASTEXITCODE -ge 8) { throw "모델 파일 복사 실패 (robocopy 종료 코드 $LASTEXITCODE)" }
}
$srcHash = (Get-FileHash (Join-Path $q "model.bin") -Algorithm SHA256).Hash
$dstHash = (Get-FileHash (Join-Path $dest "model.bin") -Algorithm SHA256).Hash
if ($srcHash -ne $dstHash) { throw "모델 파일 복사 후 체크섬 불일치 (파일 손상)" }

if ($SkipInstaller) { Write-Host "완료: dist\memo-o\memo-o.exe"; exit 0 }

Write-Host "== 3/3 Inno Setup" -ForegroundColor Cyan
$iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup 6(ISCC.exe)을 찾을 수 없습니다. https://jrsoftware.org/isdl.php 에서 설치하세요." }
& $iscc "installer\memo-o.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup 실패" }
Write-Host "완료: dist\installer\" -ForegroundColor Green
