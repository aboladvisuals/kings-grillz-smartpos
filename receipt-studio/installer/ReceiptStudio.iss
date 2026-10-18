#define MyAppName "KING'S GRILLZ Receipt Studio"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "KING'S GRILLZ"
#define MyAppExeName "KingsGrillzReceiptStudio.exe"

[Setup]
AppId={{7C4E9A21-6B18-4D55-8F03-A1C2D3E4F506}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\KingsGrillzReceiptStudio
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=KingsGrillzReceiptStudio-Setup-1.0.1
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\dist\KingsGrillzReceiptStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch KING'S GRILLZ Receipt Studio"; Flags: nowait postinstall skipifsilent
