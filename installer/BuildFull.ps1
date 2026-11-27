param(
    [Parameter(Mandatory)][string]$TelegramBinary,
    [string]$Python = 'python',
    [string]$Compiler = 'ISCC.exe'
)
$ErrorActionPreference = 'Stop'
$telegram = (Resolve-Path -LiteralPath $TelegramBinary).Path
$pythonExe = (Get-Command $Python).Source
$iscc = (Get-Command $Compiler).Source
$previousMode = $env:ONEDIR
$previousPath = $env:PYTHONPATH
Push-Location (Split-Path $PSScriptRoot)
try {
    $env:ONEDIR = '1'
    $env:PYTHONPATH = (Resolve-Path 'vendor/tgws').Path
    & $pythonExe -c "from PIL import Image; Image.open('resources/app_icon.png').save('build_assets/app.ico', format='ICO')"
    if ($LASTEXITCODE) { throw 'Could not generate the Windows icon from the application logo.' }
    & $pythonExe -m PyInstaller --noconfirm ZapretTG.spec
    if ($LASTEXITCODE) { throw 'Could not build the application.' }
    $csc = Join-Path $env:SystemRoot 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
    & $csc /nologo /target:exe '/out:build\PrepareDirectory.exe' '.\installer\PrepareDirectory.cs'
    if ($LASTEXITCODE) { throw 'Could not build the installation helper.' }
    & $iscc "/DTelegramBinary=$telegram" 'installer/Full.iss'
    if ($LASTEXITCODE) { throw 'Could not build the installer.' }
} finally {
    $env:ONEDIR = $previousMode
    $env:PYTHONPATH = $previousPath
    Pop-Location
}
