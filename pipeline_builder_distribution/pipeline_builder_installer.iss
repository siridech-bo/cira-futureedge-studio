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
; Main executable (installed to app root, which becomes pipeline_builder/ after we go up)
Source: "pipeline_builder.exe"; DestDir: "{app}"; Flags: ignoreversion

; MinGW Runtime DLLs
Source: "libgcc_s_seh-1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "libstdc++-6.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "libssh.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "libwinpthread-1.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "libcrypto-3-x64.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "libssl-3-x64.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "zlib1.dll"; DestDir: "{app}"; Flags: ignoreversion

; SSH password utility (required for password-based SSH authentication)
Source: "sshpass.exe"; DestDir: "{app}"; Flags: ignoreversion

; Templates and fonts
Source: "templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "fonts\*"; DestDir: "{app}\fonts"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion

; CiRA Block Runtime (CRITICAL - required for Setup Device and Deploy functions)
; Install to parent directory to match expected structure:
;   {app}\ = <install_root>\CiRA Pipeline Builder\
;   We need: <install_root>\CiRA Pipeline Builder\..\cira-block-runtime\
; Use {app}\.. to go up one level from app directory
Source: "cira-block-runtime\src\*"; DestDir: "{app}\..\cira-block-runtime\src"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "cira-block-runtime\include\*"; DestDir: "{app}\..\cira-block-runtime\include"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "cira-block-runtime\blocks\*"; DestDir: "{app}\..\cira-block-runtime\blocks"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "cira-block-runtime\web\*"; DestDir: "{app}\..\cira-block-runtime\web"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "cira-block-runtime\platforms\*"; DestDir: "{app}\..\cira-block-runtime\platforms"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "cira-block-runtime\tests\*"; DestDir: "{app}\..\cira-block-runtime\tests"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "cira-block-runtime\templates\*"; DestDir: "{app}\..\cira-block-runtime\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "cira-block-runtime\third_party\*"; DestDir: "{app}\..\cira-block-runtime\third_party"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "cira-block-runtime\CMakeLists.txt"; DestDir: "{app}\..\cira-block-runtime"; Flags: ignoreversion
Source: "cira-block-runtime\README.md"; DestDir: "{app}\..\cira-block-runtime"; Flags: ignoreversion
Source: "cira-block-runtime\*.md"; DestDir: "{app}\..\cira-block-runtime"; Flags: ignoreversion

; CiRA Block Runtime - Pre-built binaries (optional reference)
Source: "cira-block-runtime\build\cira-block-runtime.exe"; DestDir: "{app}\..\cira-block-runtime\build"; Flags: ignoreversion
Source: "cira-block-runtime\build\blocks\*.dll"; DestDir: "{app}\..\cira-block-runtime\build\blocks"; Flags: ignoreversion skipifsourcedoesntexist

; ONNX Runtime for Jetson (ARM64) - pre-downloaded for offline installation
Source: "cira-block-runtime\onnx_runtime\*"; DestDir: "{app}\..\cira-block-runtime\onnx_runtime"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
