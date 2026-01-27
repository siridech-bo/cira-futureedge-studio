; CiRA FutureEdge Studio v1.0 - Installer Script
; Requires Inno Setup 6.x (free download from https://jrsoftware.org/isinfo.php)

#define MyAppName "CiRA FutureEdge Studio"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "CiRA Team"
#define MyAppURL "https://cira-fes.com"
#define MyAppExeName "pipeline_builder.exe"

[Setup]
; Basic application info
AppId={{E8F3A2B1-7C9D-4E5F-A3B2-1D8E9F0A2B3C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\CiRA FES
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output
OutputDir=D:\CiRA FES\distribution\installer_output
OutputBaseFilename=CiRA-FES-v1.0-Setup
Compression=lzma2/max
SolidCompression=yes

; Windows version requirements
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; UI
WizardStyle=modern
DisableWelcomePage=no
LicenseFile=D:\CiRA FES\distribution\CiRA-FES-v1.0\LICENSE.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "Create a &Quick Launch icon"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Pipeline Builder executable and dependencies
Source: "D:\CiRA FES\distribution\CiRA-FES-v1.0\bin\pipeline_builder.exe"; DestDir: "{app}\bin"; Flags: ignoreversion
Source: "D:\CiRA FES\distribution\CiRA-FES-v1.0\bin\templates\*"; DestDir: "{app}\bin\templates"; Flags: ignoreversion recursesubdirs createallsubdirs

; Runtime source code
Source: "D:\CiRA FES\distribution\CiRA-FES-v1.0\cira-block-runtime\*"; DestDir: "{app}\cira-block-runtime"; Flags: ignoreversion recursesubdirs createallsubdirs

; CiRA Studio Python source
Source: "D:\CiRA FES\distribution\CiRA-FES-v1.0\cira_studio_source\*"; DestDir: "{app}\cira_studio_source"; Flags: ignoreversion recursesubdirs createallsubdirs

; Examples
Source: "D:\CiRA FES\distribution\CiRA-FES-v1.0\examples\*"; DestDir: "{app}\examples"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "D:\CiRA FES\distribution\CiRA-FES-v1.0\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "D:\CiRA FES\distribution\CiRA-FES-v1.0\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\CiRA FES\distribution\CiRA-FES-v1.0\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

; Launcher scripts
Source: "D:\CiRA FES\distribution\CiRA-FES-v1.0\Launch_Pipeline_Builder.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\CiRA FES\distribution\CiRA-FES-v1.0\Launch_CiRA_Studio.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\Pipeline Builder"; Filename: "{app}\Launch_Pipeline_Builder.bat"; WorkingDir: "{app}"; IconFilename: "{app}\bin\pipeline_builder.exe"
Name: "{group}\CiRA Studio"; Filename: "{app}\Launch_CiRA_Studio.bat"; WorkingDir: "{app}"
Name: "{group}\Quick Start Guide"; Filename: "{app}\docs\QuickStart.md"
Name: "{group}\User Guide"; Filename: "{app}\docs\UserGuide.md"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcuts
Name: "{autodesktop}\Pipeline Builder"; Filename: "{app}\Launch_Pipeline_Builder.bat"; WorkingDir: "{app}"; IconFilename: "{app}\bin\pipeline_builder.exe"; Tasks: desktopicon
Name: "{autodesktop}\CiRA Studio"; Filename: "{app}\Launch_CiRA_Studio.bat"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Check for Python installation after main installation
Filename: "{app}\cira_studio_source\check_python.bat"; Description: "Check Python installation"; Flags: postinstall shellexec skipifsilent

; Offer to install CiRA Studio dependencies
Filename: "{app}\cira_studio_source\install.bat"; Description: "Install CiRA Studio dependencies (requires internet, 5-10 minutes)"; Flags: postinstall shellexec skipifsilent unchecked

; Offer to open Quick Start Guide
Filename: "{app}\docs\QuickStart.md"; Description: "Open Quick Start Guide"; Flags: postinstall shellexec skipifsilent nowait

[Code]
var
  PythonInstallPage: TInputOptionWizardPage;
  PythonPath: String;

function IsPythonInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure InitializeWizard();
begin
  // Create custom page for Python check
  PythonInstallPage := CreateInputOptionPage(wpWelcome,
    'Python Installation Check',
    'CiRA Studio requires Python 3.8 or higher',
    'The installer will check if Python is installed on your system.',
    False, False);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ResultCode: Integer;
  PythonVersion: String;
begin
  Result := True;

  if CurPageID = wpReady then
  begin
    // Check if Python is installed
    if not IsPythonInstalled() then
    begin
      if MsgBox('Python is not installed or not in PATH.' + #13#10 + #13#10 +
                'CiRA Studio requires Python 3.10 or higher.' + #13#10 +
                'Pipeline Builder will work without Python.' + #13#10 + #13#10 +
                'Do you want to continue installation?' + #13#10 +
                '(You can install Python later from python.org)',
                mbConfirmation, MB_YESNO) = IDNO then
      begin
        Result := False;
      end
      else
      begin
        MsgBox('Installation will continue.' + #13#10 + #13#10 +
               'After installation, please:' + #13#10 +
               '1. Install Python 3.10 from https://python.org' + #13#10 +
               '2. Check "Add Python to PATH" during installation' + #13#10 +
               '3. Run install.bat in cira_studio_source folder',
               mbInformation, MB_OK);
      end;
    end
    else
    begin
      MsgBox('Python detected!' + #13#10 + #13#10 +
             'After installation, you can run:' + #13#10 +
             'cira_studio_source\install.bat' + #13#10 +
             'to install CiRA Studio dependencies.',
             mbInformation, MB_OK);
    end;
  end;
end;
