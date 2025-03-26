import os
import sys
import shutil
from PIL import Image, ImageDraw

def create_icon():
    """创建应用程序图标"""
    print("正在创建应用图标...")
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disk_icon.ico")
    
    # 检查图标文件是否已存在
    if os.path.exists(icon_path):
        print(f"图标文件已存在: {icon_path}")
        return icon_path
    
    # 创建新的图标
    img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    
    # 绘制磁盘图标
    # 外框
    d.rectangle((50, 100, 206, 170), fill=(0, 120, 215), outline=(255, 255, 255), width=3)
    # 顶部
    d.rectangle((70, 70, 186, 100), fill=(0, 70, 170), outline=(255, 255, 255), width=3)
    # 指示灯
    d.ellipse((180, 80, 190, 90), fill=(255, 50, 50))
    
    # 磁盘纹理线
    for i in range(4):
        y = 115 + i * 15
        d.line((60, y, 196, y), fill=(200, 200, 200), width=2)
    
    # 保存为ICO格式
    img.save(icon_path, format='ICO')
    print(f"已创建图标: {icon_path}")
    return icon_path

def check_requirements():
    """检查必要的依赖是否已安装"""
    try:
        import PyInstaller
        print("PyInstaller 已安装")
    except ImportError:
        print("正在安装 PyInstaller...")
        os.system("pip install pyinstaller")
    
    # 确保其他依赖已安装
    requirements_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if os.path.exists(requirements_file):
        print("正在安装项目依赖...")
        os.system(f"pip install -r {requirements_file}")

def build_exe():
    """构建可执行文件"""
    print("\n开始构建可执行文件...")
    
    # 检查依赖
    check_requirements()
    
    # 创建图标
    icon_path = create_icon()
    
    # 构建命令
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simple_disk_monitor.py")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # PyInstaller命令
    cmd = f'pyinstaller --noconfirm --onefile --windowed --icon="{icon_path}" --name="磁盘监控器" '
    cmd += f'--hidden-import="PIL._tkinter_finder" '
    cmd += f'--add-data "{os.path.join(os.path.dirname(os.path.abspath(__file__)), "language.py")};." '
    cmd += f'"{script_path}"'
    
    print(f"执行命令: {cmd}")
    os.system(cmd)
    
    # 创建发布包
    create_release_package(output_dir)

def create_release_package(output_dir):
    """创建发布包，包含可执行文件和README"""
    print("\n创建发布包...")
    
    release_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "release")
    os.makedirs(release_dir, exist_ok=True)
    
    # 复制可执行文件
    exe_file = os.path.join(output_dir, "磁盘监控器.exe")
    if os.path.exists(exe_file):
        shutil.copy2(exe_file, release_dir)
        print(f"已复制可执行文件到: {release_dir}")
    else:
        print(f"错误：找不到生成的可执行文件: {exe_file}")
    
    # 创建简易说明文件
    readme_file = os.path.join(release_dir, "使用说明.txt")
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("磁盘监控器使用说明\n")
        f.write("==================\n\n")
        f.write("1. 直接双击'磁盘监控器.exe'即可运行程序\n")
        f.write("2. 程序启动后会在系统托盘区显示图标\n")
        f.write("3. 右键点击托盘图标可以:\n")
        f.write("   - 立即检查磁盘\n")
        f.write("   - 打开配置设置\n")
        f.write("   - 退出程序\n\n")
        f.write("4. 在配置窗口中可以设置:\n")
        f.write("   - 磁盘空间警告阈值\n")
        f.write("   - 检查间隔时间\n")
        f.write("   - 选择要监控的驱动器\n")
        f.write("   - 设置语言\n")
        f.write("   - 开启/关闭静默模式\n")
        f.write("   - 设置开机自启动\n\n")
        f.write("5. 命令行参数:\n")
        f.write("   --silent      启用静默模式\n")
        f.write("   --autostart   设置开机自启动\n")
        f.write("   --no-autostart 取消开机自启动\n\n")
        f.write("6. 配置文件存储位置:\n")
        f.write("   用户配置文件保存在 %APPDATA%\\SimpleDiskMonitor 目录下\n")
        f.write("   配置文件名为 simple_disk_monitor_config.json\n")
        f.write("   日志文件名为 disk_monitor.log\n")
    
    print(f"已创建使用说明文件: {readme_file}")
    print(f"\n发布包已创建完成: {release_dir}")
    print("你可以将此文件夹中的内容分享给其他用户使用。")

if __name__ == "__main__":
    try:
        build_exe()
        print("\n构建成功！")
    except Exception as e:
        print(f"\n构建过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")
