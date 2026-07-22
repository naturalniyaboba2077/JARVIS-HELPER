

$ErrorActionPreference = "Stop"

$jarvisDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw   = Join-Path $env:LOCALAPPDATA "Programs\Python\Python310\pythonw.exe"
$script    = Join-Path $jarvisDir "jarvis.py"
$icon      = Join-Path $jarvisDir "ui\jarvis.ico"
$lnk       = Join-Path ([Environment]::GetFolderPath("Desktop")) "J.A.R.V.I.S..lnk"

foreach ($p in @($pythonw, $script, $icon)) {
    if (-not (Test-Path $p)) { throw "Не найдено: $p" }
}

$shell = New-Object -ComObject WScript.Shell
$s = $shell.CreateShortcut($lnk)
$s.TargetPath       = $pythonw
$s.Arguments        = "`"$script`""
$s.WorkingDirectory = $jarvisDir
$s.IconLocation     = "$icon,0"
$s.Description      = "J.A.R.V.I.S. — голосовой помощник"
$s.WindowStyle      = 1
$s.Save()

Write-Host "Ярлык создан: $lnk"
Write-Host "Запуск: $pythonw `"$script`""
