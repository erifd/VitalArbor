; VitalArbor Installer Script
; NSIS Modern User Interface

;--------------------------------
; Includes

!include "MUI2.nsh"
!include "LogicLib.nsh"

;--------------------------------
; General

Name "VitalArbor"
OutFile "VitalArbor-Setup.exe"
Unicode True

; Default installation folder
InstallDir "$LOCALAPPDATA\VitalArbor"

; Get installation folder from registry if available
InstallDirRegKey HKCU "Software\VitalArbor" ""

; Request application privileges
RequestExecutionLevel user

;--------------------------------
; Interface Settings

!define MUI_ABORTWARNING
!define MUI_ICON "App\Logo.ico"
!define MUI_UNICON "App\Logo.ico"

;--------------------------------
; Pages

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
;Create a License.txt page for the project
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
; Languages

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Installer Sections

Section "VitalArbor" SecMain

  SetOutPath "$INSTDIR"
  
  ; Copy all files
  File /r "App"
  File /r "backend"
  File /r "Pipelines"
  File /r "public"
  File "backend\package.json"
  File "backend\package-lock.json"
  
  ; Create the launcher batch script
  FileOpen $0 "$INSTDIR\VitalArbor.bat" w
  FileWrite $0 "@echo off$\r$\n"
  FileWrite $0 "echo ========================================$\r$\n"
  FileWrite $0 "echo VitalArbor Launcher$\r$\n"
  FileWrite $0 "echo ========================================$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 ":: Get the directory where this script is located$\r$\n"
  FileWrite $0 "set SCRIPT_DIR=%~dp0$\r$\n"
  FileWrite $0 "echo [DEBUG] Script directory: %SCRIPT_DIR%$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 ":: Set the service account key path$\r$\n"
  FileWrite $0 "set SERVICE_KEY=%SCRIPT_DIR%backend\serviceAccountKey.json$\r$\n"
  FileWrite $0 "echo [DEBUG] Service account key path: %SERVICE_KEY%$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 ":: Check if service account key exists$\r$\n"
  FileWrite $0 'if not exist "%SERVICE_KEY%" ($\r$\n'
  FileWrite $0 "    echo [ERROR] Service account key not found at: %SERVICE_KEY%$\r$\n"
  FileWrite $0 "    echo [ERROR] Please ensure serviceAccountKey.json is in the backend folder$\r$\n"
  FileWrite $0 "    pause$\r$\n"
  FileWrite $0 "    exit /b 1$\r$\n"
  FileWrite $0 ")$\r$\n"
  FileWrite $0 "echo [INFO] Service account key found$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 ":: Set environment variable$\r$\n"
  FileWrite $0 "set GOOGLE_APPLICATION_CREDENTIALS=%SERVICE_KEY%$\r$\n"
  FileWrite $0 "echo [DEBUG] GOOGLE_APPLICATION_CREDENTIALS set to: %GOOGLE_APPLICATION_CREDENTIALS%$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 ":: Check if Node.js is installed$\r$\n"
  FileWrite $0 "where node >nul 2>&1$\r$\n"
  FileWrite $0 "if %ERRORLEVEL% neq 0 ($\r$\n"
  FileWrite $0 "    echo [ERROR] Node.js is not installed or not in PATH$\r$\n"
  FileWrite $0 "    echo [ERROR] Please install Node.js from https://nodejs.org/$\r$\n"
  FileWrite $0 "    pause$\r$\n"
  FileWrite $0 "    exit /b 1$\r$\n"
  FileWrite $0 ")$\r$\n"
  FileWrite $0 "echo [INFO] Node.js found$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 ":: Check if Java is installed$\r$\n"
  FileWrite $0 "where java >nul 2>&1$\r$\n"
  FileWrite $0 "if %ERRORLEVEL% neq 0 ($\r$\n"
  FileWrite $0 "    echo [ERROR] Java is not installed or not in PATH$\r$\n"
  FileWrite $0 "    echo [ERROR] Please install Java JRE/JDK$\r$\n"
  FileWrite $0 "    pause$\r$\n"
  FileWrite $0 "    exit /b 1$\r$\n"
  FileWrite $0 ")$\r$\n"
  FileWrite $0 "echo [INFO] Java found$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 ":: Change to installation directory$\r$\n"
  FileWrite $0 "cd /d %SCRIPT_DIR%$\r$\n"
  FileWrite $0 "echo [DEBUG] Changed directory to: %CD%$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 ":: Start the backend server in a new window$\r$\n"
  FileWrite $0 "echo [INFO] Starting VitalArbor backend server...$\r$\n"
  FileWrite $0 'start "VitalArbor Backend" cmd /k "cd /d %SCRIPT_DIR% && echo [INFO] Starting backend server... && node backend\server.js"$\r$\n'
  FileWrite $0 "echo [INFO] Backend server starting in new window$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 ":: Wait a few seconds for server to start$\r$\n"
  FileWrite $0 "echo [INFO] Waiting 5 seconds for backend to initialize...$\r$\n"
  FileWrite $0 "timeout /t 5 /nobreak >nul$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 ":: Find the compiled Java class$\r$\n"
  FileWrite $0 "set LAUNCHER_CLASS=App.Launcher$\r$\n"
  FileWrite $0 "echo [DEBUG] Looking for compiled Launcher class...$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 ":: Check if .class file exists$\r$\n"
  FileWrite $0 'if exist "App\Launcher.class" ($\r$\n'
  FileWrite $0 "    echo [INFO] Found compiled Launcher.class$\r$\n"
  FileWrite $0 "    echo [INFO] Starting VitalArbor launcher...$\r$\n"
  FileWrite $0 "    java -cp . %LAUNCHER_CLASS%$\r$\n"
  FileWrite $0 ") else ($\r$\n"
  FileWrite $0 "    echo [ERROR] Launcher.class not found in App folder$\r$\n"
  FileWrite $0 "    echo [ERROR] Please compile Launcher.java first$\r$\n"
  FileWrite $0 '    echo [INFO] Run: javac App\Launcher.java$\r$\n'
  FileWrite $0 "    pause$\r$\n"
  FileWrite $0 "    exit /b 1$\r$\n"
  FileWrite $0 ")$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "echo [INFO] VitalArbor closed$\r$\n"
  FileWrite $0 "pause$\r$\n"
  FileClose $0
  
  ; Store installation folder
  WriteRegStr HKCU "Software\VitalArbor" "" $INSTDIR
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\VitalArbor"
  CreateShortcut "$SMPROGRAMS\VitalArbor\VitalArbor.lnk" "$INSTDIR\VitalArbor.bat" "" "$INSTDIR\App\Logo.png"
  CreateShortcut "$SMPROGRAMS\VitalArbor\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  
  ; Create Desktop shortcut
  CreateShortcut "$DESKTOP\VitalArbor.lnk" "$INSTDIR\VitalArbor.bat" "" "$INSTDIR\App\Logo.png"
  
  ; Write uninstall information to registry
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VitalArbor" "DisplayName" "VitalArbor"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VitalArbor" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VitalArbor" "DisplayIcon" "$INSTDIR\App\Logo.png"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VitalArbor" "Publisher" "VitalArbor"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VitalArbor" "DisplayVersion" "1.0.0"
  
  MessageBox MB_OK "VitalArbor has been installed successfully!$\r$\n$\r$\nIMPORTANT:$\r$\n1. Ensure Node.js is installed$\r$\n2. Place serviceAccountKey.json in the backend folder$\r$\n3. Compile Launcher.java if not already compiled$\r$\n$\r$\nYou can now run VitalArbor from the Start Menu or Desktop shortcut."

SectionEnd

;--------------------------------
; Uninstaller Section

Section "Uninstall"

  ; Remove files and directories
  RMDir /r "$INSTDIR\App"
  RMDir /r "$INSTDIR\backend"
  RMDir /r "$INSTDIR\Pipelines"
  RMDir /r "$INSTDIR\website"
  RMDir /r "$INSTDIR\public"
  Delete "$INSTDIR\package.json"
  Delete "$INSTDIR\package-lock.json"
  Delete "$INSTDIR\VitalArbor.bat"
  Delete "$INSTDIR\Uninstall.exe"
  
  ; Remove shortcuts
  Delete "$SMPROGRAMS\VitalArbor\VitalArbor.lnk"
  Delete "$SMPROGRAMS\VitalArbor\Uninstall.lnk"
  RMDir "$SMPROGRAMS\VitalArbor"
  Delete "$DESKTOP\VitalArbor.lnk"
  
  ; Remove registry keys
  DeleteRegKey HKCU "Software\VitalArbor"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VitalArbor"
  
  ; Remove installation directory if empty
  RMDir "$INSTDIR"
  
  MessageBox MB_OK "VitalArbor has been uninstalled successfully."

SectionEnd