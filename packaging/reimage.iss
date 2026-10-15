; ReImage Windows installer.
; Build the bundle first, then compile this script:
;   python -m PyInstaller packaging/reimage.spec
;   iscc packaging/reimage.iss
;
; The wizard installs for the current user and offers a checkbox to add
; "Rename images with ReImage" to the folder right-click menu.

#define MyAppName "ReImage"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "HugoFernandoColmenares"
#define MyAppURL "https://github.com/HugoFernandoColmenares"
#define MyAppExeName "reimage.exe"

[Setup]
AppId={{7C4E9A21-5B18-4F63-9D0A-2E6B8C41F7A3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\ReImage
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\windows
OutputBaseFilename=ReImage-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
CloseApplications=no

[Tasks]
Name: contextmenu; Description: "Add ReImage to the folder right-click menu"; GroupDescription: "Explorer integration:"; Flags: checkedonce

[Files]
Source: "..\dist\windows\reimage\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Rename images in a folder"

[Registry]
Root: HKCU; Subkey: "Software\Classes\Directory\shell\ReImage"; ValueType: string; ValueName: ""; ValueData: "Rename images with ReImage"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\ReImage"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName}"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\ReImage\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --folder ""%1"""; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\ReImage"; ValueType: string; ValueName: ""; ValueData: "Rename images with ReImage"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\ReImage"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName}"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\ReImage\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" --folder ""%V"""; Tasks: contextmenu

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  { Drop a previous registration before the task entries run, so an upgrade
    that clears the checkbox does not leave a stale menu item. }
  if CurStep = ssInstall then
  begin
    RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER, 'Software\Classes\Directory\shell\ReImage');
    RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER, 'Software\Classes\Directory\Background\shell\ReImage');
  end;
end;
