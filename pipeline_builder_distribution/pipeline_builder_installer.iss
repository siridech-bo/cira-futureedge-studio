; CiRA Pipeline Builder - Simplified Installer Script
; Minimal version to avoid runtime errors

#define MyAppName "CiRA Pipeline Builder"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "CiRA FutureEdge Studio"
#define MyAppExeName "pipeline_builder.exe"

[Setup]
AppId={{B8F3A4E2-9D1C-4F5B-8E2A-1C3D4E5F6A7B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=CiRA_Pipeline_Builder_Setup_v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable
Source: "pipeline_builder.exe"; DestDir: "{app}"; Flags: ignoreversion

; MinGW Runtime DLLs
Source: "libgcc_s_seh-1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "libstdc++-6.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "libssh.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "libwinpthread-1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "libcrypto-3-x64.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "libssl-3-x64.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "zlib1.dll"; DestDir: "{app}"; Flags: ignoreversion

; Templates and fonts
Source: "templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "fonts\*"; DestDir: "{app}\fonts"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
