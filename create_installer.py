import os
import sys
import winreg

def find_nsis():
    """尝试从注册表找到NSIS安装路径"""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\NSIS") as key:
            return winreg.QueryValueEx(key, "")[0]
    except:
        return None

def create_nsis_script():
    """创建NSIS安装脚本"""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "installer.nsi")
    release_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "release")
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disk_icon.ico")
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('''
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
InstallDir "$PROGRAMFILES\\${APP_NAME}"
InstallDirRegKey HKCU "Software\\${APP_NAME}" ""

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
    File "release\\磁盘监控器.exe"
    File "release\\使用说明.txt"
    
    CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${MAIN_APP_EXE}"
    CreateShortCut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${MAIN_APP_EXE}"
    
    WriteRegStr HKCU "Software\\${APP_NAME}" "" "$INSTDIR"
    WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayVersion" "${VERSION}"
    WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "Publisher" "${COMP_NAME}"
    WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayIcon" "$INSTDIR\\${MAIN_APP_EXE}"
    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section Uninstall
    Delete "$INSTDIR\\${MAIN_APP_EXE}"
    Delete "$INSTDIR\\使用说明.txt"
    Delete "$INSTDIR\\uninstall.exe"
    
    Delete "$DESKTOP\\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\\${APP_NAME}"
    
    RMDir "$INSTDIR"
    
    DeleteRegKey HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
    DeleteRegKey HKCU "Software\\${APP_NAME}"
SectionEnd
''')
    
    return script_path

def build_installer():
    """构建安装程序"""
    print("开始创建安装程序...")
    
    # 确保release目录存在并包含所需文件
    release_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "release")
    exe_file = os.path.join(release_dir, "磁盘监控器.exe")
    
    if not os.path.exists(exe_file):
        print("错误：找不到可执行文件，请先运行build.py生成可执行文件")
        return False
    
    # 创建NSIS脚本
    script_path = create_nsis_script()
    print(f"已创建NSIS脚本: {script_path}")
    
    # 查找NSIS安装路径
    nsis_path = find_nsis()
    if not nsis_path:
        print("错误：找不到NSIS安装，请安装NSIS后再试")
        print("您可以从 https://nsis.sourceforge.io/Download 下载安装NSIS")
        return False
    
    # 构建安装程序
    makensis_exe = os.path.join(nsis_path, "makensis.exe")
    if not os.path.exists(makensis_exe):
        print(f"错误：找不到makensis.exe: {makensis_exe}")
        return False
    
    cmd = f'"{makensis_exe}" "{script_path}"'
    print(f"执行命令: {cmd}")
    os.system(cmd)
    
    # 检查是否生成安装程序
    installer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "磁盘监控器安装程序.exe")
    if os.path.exists(installer_path):
        print(f"\n安装程序已成功创建: {installer_path}")
        return True
    else:
        print(f"错误：安装程序创建失败")
        return False

if __name__ == "__main__":
    try:
        build_installer()
    except Exception as e:
        print(f"\n创建安装程序过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")
