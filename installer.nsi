
; 磁盘监控器安装脚本
Unicode True

!define APP_NAME "磁盘监控器"
!define COMP_NAME "Your Company"
!define VERSION "1.0.0"
!define COPYRIGHT "Copyright (c) 2023"
!define DESCRIPTION "磁盘空间监控工具"
!define INSTALLER_NAME "磁盘监控器安装程序.exe"
!define MAIN_APP_EXE "磁盘监控器.exe"

!include "MUI2.nsh"

Name "${APP_NAME}"
Caption "${APP_NAME} ${VERSION}"
OutFile "${INSTALLER_NAME}"
InstallDir "$PROGRAMFILES\${APP_NAME}"
InstallDirRegKey HKCU "Software\${APP_NAME}" ""

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimpChinese"

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    SetOverwrite ifnewer
    File "release\磁盘监控器.exe"
    File "release\使用说明.txt"
    
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${MAIN_APP_EXE}"
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${MAIN_APP_EXE}"
    
    WriteRegStr HKCU "Software\${APP_NAME}" "" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${VERSION}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${COMP_NAME}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\${MAIN_APP_EXE}"
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section Uninstall
    Delete "$INSTDIR\${MAIN_APP_EXE}"
    Delete "$INSTDIR\使用说明.txt"
    Delete "$INSTDIR\uninstall.exe"
    
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    
    RMDir "$INSTDIR"
    
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKCU "Software\${APP_NAME}"
SectionEnd
