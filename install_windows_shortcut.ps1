$ErrorActionPreference = 'Stop'

$project = (Resolve-Path (Join-Path $PSScriptRoot '.')).Path
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop 'KSA ENGINE.lnk'
$target = Join-Path $project 'launch_ksa_engine.bat'
$icon = Join-Path $project 'assets\ksa-engine-k.ico'

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $project
$shortcut.Description = 'KSA ENGINE Game Creator'
if (Test-Path $icon) {
    $shortcut.IconLocation = "$icon,0"
}
$shortcut.Save()

Write-Host "تم إنشاء الاختصار: $shortcutPath"
