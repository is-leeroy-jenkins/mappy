#define MyAppName "Mappy"
#ifndef MyAppVersion
  #define MyAppVersion "0.2.0"
#endif

[Setup]
AppId={{5318A1BF-E53E-48DC-A7F3-0C52AC6C7DE7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=is-leeroy-jenkins
DefaultDirName={localappdata}\Programs\Mappy
DefaultGroupName=Mappy
OutputDir=..\dist-installer
OutputBaseFilename=Mappy-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
WizardStyle=modern
UninstallDisplayName=Mappy
UninstallDisplayIcon={app}\Mappy.exe
CloseApplications=yes

[Files]
Source: "..\dist\Mappy\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Icons]
Name: "{group}\Mappy"; Filename: "{app}\Mappy.exe"
Name: "{autodesktop}\Mappy"; Filename: "{app}\Mappy.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Mappy.exe"; Description: "Launch Mappy"; Flags: nowait postinstall skipifsilent
