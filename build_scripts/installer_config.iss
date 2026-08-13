; Inno Setup Script for RouletVoc
; Generates a professional single-file Windows installer (.exe)

; Version is injected from CI via: ISCC /DAppVer=x.y.z
; Falls back to 1.0.0 if not provided
#ifndef AppVer
  #define AppVer "1.0.0"
#endif

[Setup]
AppName=RouletVoc
AppVersion={#AppVer}
AppPublisher=TRXS Org
DefaultDirName={autopf}\RouletVoc
DefaultGroupName=RouletVoc
UninstallDisplayIcon={app}\RouletVoc.exe
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=..\dist
OutputBaseFilename=RouletVoc_Setup_v{#AppVer}
SetupIconFile=..\assets\icons\app.ico
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Files]
; The executable and its dependencies from PyInstaller dist folder
Source: "..\dist\RouletVoc\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\RouletVoc"; Filename: "{app}\RouletVoc.exe"; IconFilename: "{app}\assets\icons\app.ico"
Name: "{group}\Uninstall RouletVoc"; Filename: "{uninstallexe}"
Name: "{autodesktop}\RouletVoc"; Filename: "{app}\RouletVoc.exe"; IconFilename: "{app}\assets\icons\app.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\RouletVoc.exe"; Description: "{cm:LaunchProgram,RouletVoc}"; Flags: nowait postinstall skipifsilent
