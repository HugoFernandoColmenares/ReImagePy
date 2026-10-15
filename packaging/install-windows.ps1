# Installs the Windows bundle for the current user.
# Asks whether to add ReImage to the folder right-click menu.
#
#   powershell -ExecutionPolicy Bypass -File packaging\install-windows.ps1
#   powershell -ExecutionPolicy Bypass -File packaging\install-windows.ps1 -Uninstall

[CmdletBinding()]
param(
    [string]$Source,
    [string]$InstallDir,
    [string]$ShortcutPath,
    [switch]$ContextMenu,
    [switch]$NoContextMenu,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Source) {
    $Source = Join-Path $RepoRoot "dist\windows\reimage"
}
if (-not $InstallDir) {
    $InstallDir = Join-Path $env:LOCALAPPDATA "Programs\ReImage"
}
if (-not $ShortcutPath) {
    $ShortcutPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\ReImage.lnk"
}

$DirectoryKey = "HKCU:\Software\Classes\Directory\shell\ReImage"
$BackgroundKey = "HKCU:\Software\Classes\Directory\Background\shell\ReImage"

function Remove-ReImageContextMenu {
    foreach ($key in @($DirectoryKey, $BackgroundKey)) {
        if (Test-Path -LiteralPath $key) {
            Remove-Item -LiteralPath $key -Recurse -Force
        }
    }
}

function Install-ReImageContextMenu {
    param([string]$ExePath)
    Remove-ReImageContextMenu
    $entries = @(
        @{ Key = $DirectoryKey; Argument = "%1" },
        @{ Key = $BackgroundKey; Argument = "%V" }
    )
    foreach ($entry in $entries) {
        New-Item -Path $entry.Key -Force | Out-Null
        Set-Item -LiteralPath $entry.Key -Value "Rename images with ReImage"
        New-ItemProperty -LiteralPath $entry.Key -Name "Icon" -Value $ExePath -PropertyType String -Force | Out-Null
        $commandKey = Join-Path $entry.Key "command"
        New-Item -Path $commandKey -Force | Out-Null
        Set-Item -LiteralPath $commandKey -Value ('"{0}" --folder "{1}"' -f $ExePath, $entry.Argument)
    }
}

function Remove-ReImageShortcut {
    if (Test-Path -LiteralPath $ShortcutPath) {
        Remove-Item -LiteralPath $ShortcutPath -Force
    }
}

function Install-ReImageShortcut {
    param([string]$ExePath)
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $ExePath
    $shortcut.WorkingDirectory = $InstallDir
    $shortcut.Description = "Rename images in a folder"
    $shortcut.Save()
}

if ($Uninstall) {
    Remove-ReImageContextMenu
    Remove-ReImageShortcut
    if (Test-Path -LiteralPath $InstallDir) {
        Remove-Item -LiteralPath $InstallDir -Recurse -Force
    }
    Write-Output "ReImage was removed."
    return
}

$exeName = "reimage.exe"
$sourceExe = Join-Path $Source $exeName
if (-not (Test-Path -LiteralPath $sourceExe)) {
    throw "Windows bundle not found at $Source. Build it with: python -m PyInstaller packaging/reimage.spec"
}

$addMenu = $false
if ($NoContextMenu) {
    $addMenu = $false
}
elseif ($ContextMenu) {
    $addMenu = $true
}
elseif ([Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
    $answer = Read-Host "Add ReImage to the folder right-click menu? [Y/n]"
    $addMenu = [string]::IsNullOrWhiteSpace($answer) -or $answer -match "^[yY]"
}
else {
    $addMenu = $true
}

# A previous install is removed first so an upgrade that declines the menu
# does not leave the old command behind.
Remove-ReImageContextMenu
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path (Join-Path $Source "*") -Destination $InstallDir -Recurse -Force
$installedExe = Join-Path $InstallDir $exeName
Install-ReImageShortcut -ExePath $installedExe
if ($addMenu) {
    Install-ReImageContextMenu -ExePath $installedExe
    Write-Output "ReImage installed at $InstallDir"
    Write-Output "Right-click a folder and choose `"Rename images with ReImage`"."
}
else {
    Write-Output "ReImage installed at $InstallDir"
    Write-Output "The folder right-click menu was left unchanged."
}
