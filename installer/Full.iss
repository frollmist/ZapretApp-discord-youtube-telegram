; Build the ONEDIR target of ZapretTG.spec before compiling this setup.
#define Product "ZapretApp-discord-youtube-telegram"
#ifndef TelegramBinary
  #error Pass /DTelegramBinary=<path to the official TgWsProxy_windows.exe 1.12.0>
#endif
#if LowerCase(GetSHA256OfFile(TelegramBinary)) != "859575ced24c65fadfa189bef8c75611f3f0a149633e553320434625fa84d67a"
  #error Unexpected Telegram WS Proxy binary
#endif

[Setup]
AppId={#Product}
AppName=ZapretApp
AppVersion=1.0 BETA
DefaultDirName={sd}\{#Product}
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes
DisableReadyPage=yes
DirExistsWarning=no
UsePreviousAppDir=no
AllowRootDirectory=yes
AppendDefaultDirName=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
AppMutex=Local\ZapretTG-mutex
SetupMutex=ZapretApp-full-install
Uninstallable=no
CreateUninstallRegKey=no
ShowLanguageDialog=no
WizardStyle=modern dark windows11 hidebevels
WizardBackColor=#181B2C
WizardImageBackColor=#181B2C
WizardImageFile=..\resources\app_icon.png
WizardSmallImageFile=..\resources\app_icon.png
Compression=lzma2/fast
SolidCompression=yes
SetupIconFile=..\build_assets\app.ico
OutputDir=..\release
OutputBaseFilename=ZapretApp-1.0-BETA-Setup-r4

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Messages]
ru.WelcomeLabel1=Установка ZapretApp
en.WelcomeLabel1=Install ZapretApp
ru.WelcomeLabel2=Версия 1.0 BETA%n%nВ комплект входят Zapret и Telegram WS Proxy. На следующем шаге можно выбрать папку и создать ярлык.
en.WelcomeLabel2=Version 1.0 BETA%n%nIncludes Zapret and Telegram WS Proxy. Next, choose a folder and whether to create a desktop shortcut.
ru.WizardSelectDir=Место установки
en.WizardSelectDir=Install location
ru.SelectDirDesc=Выберите, где хранить ZapretApp и его компоненты.
en.SelectDirDesc=Choose where to keep ZapretApp and its components.
ru.SelectDirLabel3=Установщик создаст папку приложения на выбранном диске.
en.SelectDirLabel3=Setup will create the application folder on the selected drive.
ru.SelectDirBrowseLabel=Папка установки
en.SelectDirBrowseLabel=Installation folder
ru.WizardInstalling=Установка ZapretApp
en.WizardInstalling=Installing ZapretApp
ru.InstallingLabel=Zapret и Telegram WS Proxy
en.InstallingLabel=Zapret and Telegram WS Proxy
ru.StatusExtractFiles=Распаковка файлов
en.StatusExtractFiles=Extracting files
ru.FinishedHeadingLabel=ZapretApp установлен
en.FinishedHeadingLabel=ZapretApp is installed
ru.FinishedLabel=Zapret и Telegram WS Proxy готовы к работе.
en.FinishedLabel=Zapret and Telegram WS Proxy are ready to use.
ru.FinishedLabelNoIcons=Zapret и Telegram WS Proxy готовы к работе.
en.FinishedLabelNoIcons=Zapret and Telegram WS Proxy are ready to use.

[CustomMessages]
ru.DesktopShortcut=Создать ярлык ZapretApp на рабочем столе
en.DesktopShortcut=Create a ZapretApp desktop shortcut
ru.PreparingFiles=Подготовка компонентов, настроек и папок загрузок…
en.PreparingFiles=Preparing components, settings and download folders…
ru.InstallError=Не удалось подготовить файлы в выбранной папке.
en.InstallError=Could not prepare the files in the selected folder.

[Files]
Source: "..\build\PrepareDirectory.exe"; Flags: dontcopy
Source: "..\dist\ZapretTG\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\build_assets\app.ico"; DestDir: "{app}\_internal\resources"; DestName: "ZapretApp.ico"; Flags: ignoreversion
Source: "{#TelegramBinary}"; DestDir: "{app}\components\telegram"; DestName: "TgWsProxy_windows.exe"; Flags: ignoreversion; AfterInstall: PrepareComponents

[Icons]
Name: "{commondesktop}\ZapretApp"; Filename: "{app}\{#Product}.exe"; WorkingDir: "{app}"; Check: WantsDesktopShortcut

[Run]
Filename: "{app}\{#Product}.exe"; WorkingDir: "{app}"; Flags: nowait postinstall runascurrentuser skipifsilent; Description: "{cm:LaunchProgram,ZapretApp}"

[Code]
var
  DesktopShortcut: TNewCheckBox;
  ProgressPercent: TNewStaticText;

function WantsDesktopShortcut: Boolean;
begin
  Result := DesktopShortcut.Checked;
end;

procedure NormalizeDirectory;
var
  Dir: String;
begin
  Dir := RemoveBackslashUnlessRoot(WizardForm.DirEdit.Text);
  if CompareText(ExtractFileName(Dir), '{#Product}') <> 0 then
    Dir := AddBackslash(Dir) + '{#Product}';
  WizardForm.DirEdit.Text := Dir;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  if CurPageID = wpSelectDir then NormalizeDirectory;
  Result := True;
end;

procedure CenterBrandIcon(Image: TBitmapImage);
var
  Side: Integer;
begin
  Side := Image.Width * 3 div 4;
  Image.Anchors := [akLeft, akTop];
  Image.SetBounds(Image.Left + (Image.Width - Side) div 2,
                  Image.Top + (Image.Height - Side) div 2, Side, Side);
end;

procedure InitializeWizard;
begin
  CenterBrandIcon(WizardForm.WizardBitmapImage);
  CenterBrandIcon(WizardForm.WizardBitmapImage2);

  DesktopShortcut := TNewCheckBox.Create(WizardForm);
  DesktopShortcut.Parent := WizardForm.SelectDirPage;
  DesktopShortcut.Caption := CustomMessage('DesktopShortcut');
  DesktopShortcut.SetBounds(WizardForm.DirEdit.Left, WizardForm.DirEdit.Top + WizardForm.DirEdit.Height + ScaleY(18),
    WizardForm.DirBrowseButton.Left + WizardForm.DirBrowseButton.Width - WizardForm.DirEdit.Left, ScaleY(24));
  DesktopShortcut.Anchors := [akLeft, akTop, akRight];

  ProgressPercent := TNewStaticText.Create(WizardForm);
  ProgressPercent.Parent := WizardForm.InstallingPage;
  ProgressPercent.Font.Size := 18;
  ProgressPercent.Font.Style := [fsBold];
  ProgressPercent.Left := WizardForm.ProgressGauge.Left;
  ProgressPercent.Top := WizardForm.ProgressGauge.Top + WizardForm.ProgressGauge.Height + ScaleY(10);
  ProgressPercent.Caption := '0 %';
end;

procedure CurInstallProgressChanged(CurProgress, MaxProgress: Integer);
begin
  if MaxProgress > 0 then
    ProgressPercent.Caption := IntToStr(Round(100.0 * CurProgress / MaxProgress)) + ' %';
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ExitCode: Integer;
begin
  NormalizeDirectory;
  ExtractTemporaryFile('PrepareDirectory.exe');
  if not Exec(ExpandConstant('{tmp}\PrepareDirectory.exe'), '"' + WizardDirValue + '"', '',
              SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then
    Result := CustomMessage('InstallError') + ' ' + WizardDirValue;
end;

procedure PrepareComponents;
var
  ExitCode: Integer;
begin
  WizardForm.StatusLabel.Caption := CustomMessage('PreparingFiles');
  if not Exec(ExpandConstant('{app}\{#Product}.exe'), '--prepare-install', ExpandConstant('{app}'),
              SW_HIDE, ewWaitUntilTerminated, ExitCode) or (ExitCode <> 0) then
    RaiseException(CustomMessage('InstallError') + ' ' + ExpandConstant('{app}\logs\app.log'));
end;
