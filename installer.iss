; ─────────────────────────────────────────────────────────────
;  Inno Setup script for Bam Player
;  Builds a single-file installer that unpacks the app
;  into Program Files with Start Menu shortcuts.
;
;  The workflow stamps MyAppVersion before running ISCC.exe.
; ─────────────────────────────────────────────────────────────

#define MyAppName "Bam Player"
#define MyAppVersion "1.7.0"
#define MyAppPublisher "Yogisetiawan121"
#define MyAppURL "https://github.com/Yogisetiawan121/bam-player"
#define MyAppDirName "BamPlayer"         ; PyInstaller output folder name (no .exe)
#define MyAppExeName "BamPlayer.exe"

[Setup]
AppId={{B7F3A5C1-8D2E-4F6A-9B3C-1D5E7F8A2C4B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=.\dist
OutputBaseFilename=BamPlayer-{#MyAppVersion}-Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableProgramGroupPage=yes
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce

[Files]
; Core app
Source: "dist\{#MyAppDirName}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; VLC runtime and Python extension modules
Source: "dist\{#MyAppDirName}\*.dll"; DestDir: "{app}"; Flags: ignoreversion
; VLC plugins
Source: "dist\{#MyAppDirName}\plugins\*"; DestDir: "{app}\plugins"; Flags: ignoreversion recursesubdirs createallsubdirs
; PyInstaller internal bundle (present in PyInstaller 6+)
Source: "dist\{#MyAppDirName}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall
