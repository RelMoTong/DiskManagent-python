import psutil
import tkinter as tk
from tkinter import messagebox, ttk
import time
import json
import os
import sys
import logging
import argparse
import threading
import queue
from PIL import Image, ImageDraw
import pystray
from language import get_text, TRANSLATIONS

# 添加单例检查所需的模块
import ctypes
import tempfile
import weakref

class SingleInstance:
    """
    单例模式实现，确保程序只有一个实例在运行
    """
    def __init__(self, app_name):
        self.app_name = app_name
        self.mutex_name = f'Global\\{app_name}'
        self.mutex = None
        
    def check(self):
        """
        检查是否已有实例在运行
        返回：True表示这是唯一实例，False表示已有实例在运行
        """
        try:
            # 尝试创建命名互斥体
            self.mutex = ctypes.windll.kernel32.CreateMutexW(None, False, self.mutex_name)
            last_error = ctypes.windll.kernel32.GetLastError()
            
            # 如果互斥体已存在，说明已有实例在运行
            if last_error == 183:  # ERROR_ALREADY_EXISTS
                logging.warning("程序已经在运行中，拒绝启动新实例")
                return False
            return True
        except Exception as e:
            logging.error(f"检查单例时发生错误: {e}", exc_info=True)
            # 出错时允许程序继续运行
            return True
            
    def release(self):
        """释放互斥体"""
        if self.mutex:
            try:
                ctypes.windll.kernel32.ReleaseMutex(self.mutex)
                ctypes.windll.kernel32.CloseHandle(self.mutex)
                self.mutex = None
            except Exception as e:
                logging.error(f"释放互斥体时发生错误: {e}", exc_info=True)

class ConfigWindow(tk.Toplevel):
    def __init__(self, monitor, parent=None):
        try:
            super().__init__(parent)
            logging.info("配置窗口初始化")
            self.title(monitor._("settings_title"))
            self.geometry("600x800")  # 增加窗口尺寸，确保所有内容可见
            self.minsize(600, 800)    # 添加最小窗口大小限制
            self.resizable(True, True)  # 允许调整大小
            self.monitor = monitor
            self.config = monitor.config
            # 记录当前语言，用于检测变化
            self.current_language = self.config.get("language", "zh_CN")
            # 预先初始化列表，确保toggle_drive_selection方法总是有效
            self.drive_checkbuttons = []
            self.drive_vars = {}
            self.create_widgets()
            # 窗口居中
            self.update_idletasks()
            width = self.winfo_width()
            height = self.winfo_height()
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            self.geometry(f'{width}x{height}+{x}+{y}')
            self.focus_set()
            logging.info("配置窗口创建成功")
        except Exception as e:
            logging.error(f"配置窗口初始化失败: {e}", exc_info=True)
            raise
    
    def create_widgets(self):
        # 创建一个包含所有内容的主框架，该框架可滚动
        # 这样可以确保内容过多时，按钮始终可见
        main_container = tk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建内容部分的画布，可滚动
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient=tk.VERTICAL, command=canvas.yview)
        
        # 创建将放置所有控件的可滚动框架
        main_frame = tk.Frame(canvas)
        
        # 配置画布滚动区域
        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # 设置画布的初始大小和滚动性能参数
        canvas.configure(width=430, height=550)  # 设置合适的初始大小
        
        # 创建画布窗口并放置框架
        canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # 当主容器调整大小时，调整画布窗口大小
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)
        
        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # 绑定鼠标滚轮事件到画布
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 当离开窗口时解绑鼠标滚轮事件，避免影响其他窗口
        def _unbind_mousewheel(e):
            canvas.unbind_all("<MouseWheel>")
        
        # 当进入窗口时重新绑定鼠标滚轮事件
        def _bind_mousewheel(e):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 绑定鼠标进入离开事件
        #canvas.bind("<Enter>", _bind_mousewheel)
        #canvas.bind("<Leave>", _unbind_mousewheel)
        
        # 绑定鼠标滚轮事件到整个窗口和其子组件
        self.bind_all("<MouseWheel>", _on_mousewheel)

        # 当窗口关闭时解绑鼠标滚轮事件
        self.bind("<Destroy>", lambda e: self.unbind_all("<MouseWheel>"))

        # 配置画布和滚动条的关联
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 放置画布和滚动条
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 阈值设置区域
        threshold_frame = tk.LabelFrame(main_frame, text=self.monitor._("threshold_settings"), padx=10, pady=10)
        threshold_frame.pack(fill=tk.X, pady=5)

        # 严重警告阈值
        tk.Label(threshold_frame, text=self.monitor._("critical_threshold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.critical_threshold = tk.Entry(threshold_frame, width=10)
        self.critical_threshold.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.critical_threshold.insert(0, str(self.config.get("critical_threshold", 90)))
        
        # 警告阈值
        tk.Label(threshold_frame, text=self.monitor._("warning_threshold")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.warning_threshold = tk.Entry(threshold_frame, width=10)
        self.warning_threshold.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.warning_threshold.insert(0, str(self.config.get("warning_threshold", 75)))
        
        # 提示阈值
        tk.Label(threshold_frame, text=self.monitor._("notice_threshold")).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.notice_threshold = tk.Entry(threshold_frame, width=10)
        self.notice_threshold.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.notice_threshold.insert(0, str(self.config.get("notice_threshold", 60)))
        
        # 时间设置区域
        time_frame = tk.LabelFrame(main_frame, text=self.monitor._("time_settings"), padx=10, pady=10)
        time_frame.pack(fill=tk.X, pady=5)
        
        # 检查间隔
        tk.Label(time_frame, text=self.monitor._("check_interval")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.check_interval = tk.Entry(time_frame)
        self.check_interval.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        self.check_interval.insert(0, str(self.config.get("check_interval", 5)))

        # 驱动器选择区域
        drives_frame = tk.LabelFrame(main_frame, text=self.monitor._("monitor_drives"), padx=10, pady=10)
        drives_frame.pack(fill=tk.X, pady=5)
        
        # 获取所有可用驱动器
        self.available_drives = self.monitor.get_available_drives()
        self.drive_vars = {}
        
        # 驱动器复选框 - 监控所有驱动器选项
        self.all_drives_var = tk.BooleanVar()
        self.all_drives_var.set(not self.config.get("drives_to_monitor", []))
        self.all_drives_cb = tk.Checkbutton(drives_frame, text=self.monitor._("monitor_all_drives"), 
                                          variable=self.all_drives_var, 
                                          command=self.toggle_drive_selection)
        self.all_drives_cb.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 单独的滚动框架，专门用于显示驱动器列表
        drive_list_frame = tk.Frame(drives_frame)
        drive_list_frame.grid(row=1, column=0, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 添加每个驱动器的复选框
        self.drive_checkbuttons = []  # 保存复选框引用
        for i, drive in enumerate(self.available_drives):
            var = tk.BooleanVar()
            var.set(drive in self.config.get("drives_to_monitor", []))
            self.drive_vars[drive] = var
            cb = tk.Checkbutton(drive_list_frame, text=drive, variable=var)
            cb.grid(row=i, column=0, sticky=tk.W, padx=20, pady=2)
            self.drive_checkbuttons.append(cb)  # 保存引用
        
        # 语言设置区域
        language_frame = tk.LabelFrame(main_frame, text=self.monitor._("language_settings"), padx=10, pady=10)
        language_frame.pack(fill=tk.X, pady=5)

        self.language_var = tk.StringVar(value=self.config.get("language", "zh_CN"))
        tk.Radiobutton(language_frame, text="简体中文", variable=self.language_var, value="zh_CN").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        tk.Radiobutton(language_frame, text="English", variable=self.language_var, value="en_US").grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # 其他选项区域
        options_frame = tk.LabelFrame(main_frame, text=self.monitor._("other_options"), padx=10, pady=10)
        options_frame.pack(fill=tk.X, pady=5)
        
        self.silent_mode_var = tk.BooleanVar()
        self.silent_mode_var.set(self.config.get("silent_mode", False))
        self.silent_mode_cb = tk.Checkbutton(options_frame, text=self.monitor._("silent_mode"), 
                                           variable=self.silent_mode_var)
        self.silent_mode_cb.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.startup_var = tk.BooleanVar()
        self.startup_var.set(self.config.get("run_at_startup", False))
        self.startup_cb = tk.Checkbutton(options_frame, text=self.monitor._("run_at_startup"), 
                                       variable=self.startup_var)
        self.startup_cb.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 按钮区域 - 使用单独的框架确保按钮总是可见
        button_container = tk.Frame(self)  # 此框架不在滚动区域内，确保始终可见
        button_container.pack(fill='both', expand=True)
        button_container.pack_propagate(False)
        button_container.grid_propagate(False)  # 确保grid布局也不会改变容器大小

        
        # 分隔线
        separator = ttk.Separator(button_container, orient='horizontal')
        separator.pack(fill=tk.X, pady=5)
        
        # 按钮区域
        button_frame = tk.Frame(button_container)
        button_frame.pack(fill='both', expand=True)

        # 配置button_frame的列权重，确保按钮均匀分布
        button_frame.columnconfigure(0, weight=1)  # 左边按钮区域
        button_frame.columnconfigure(1, weight=1)  # 中间间隔
        button_frame.columnconfigure(2, weight=1)  # 取消按钮区域
        button_frame.columnconfigure(3, weight=1)  # 保存按钮区域
        
        button_frame.rowconfigure(0, weight=1)  # 确保按钮垂直居中
        # 创建按钮，确保它们足够大并且具有鲜明的颜色
        apply_button = tk.Button(button_frame, text=self.monitor._("apply"), command=self.apply_config, 
                       width=15, height=2, bg="#4CAF50", fg="white", 
                       relief=tk.RAISED, bd=3, font=("Arial", 10, "bold"))
        apply_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        cancel_button = tk.Button(button_frame, text=self.monitor._("cancel"), command=self.destroy, 
                        width=15, height=2, font=("Arial", 10, "bold"))
        cancel_button.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

        save_button = tk.Button(button_frame, text=self.monitor._("save_and_close"), command=self.save_config, 
                      width=15, height=2, bg="#2196F3", fg="white", 
                      relief=tk.RAISED, bd=3, font=("Arial", 10, "bold"))
        save_button.grid(row=0, column=3, padx=10, pady=5, sticky="ew")
        
        # 立即更新驱动器选择状态
        self.toggle_drive_selection()


    def toggle_drive_selection(self):
        """切换所有驱动器选择状态"""
        all_selected = self.all_drives_var.get()
        for drive, var in self.drive_vars.items():
            if all_selected:
                # 当选择"监控所有驱动器"时，重置所有驱动器的选择状态为未选中
                var.set(False)
        
        for cb in self.drive_checkbuttons:
            if all_selected:
                cb.config(state=tk.DISABLED)
            else:
                cb.config(state=tk.NORMAL)
    
    def apply_config(self):
        """应用设置但不关闭窗口"""
        try:
            # 验证并保存设置
            if not self._validate_and_save_config():
                return
            
            # 检查语言是否变更，若变更则刷新界面
            if self.current_language != self.language_var.get():
                self.refresh_ui()
                
            messagebox.showinfo(self.monitor._("success"), self.monitor._("config_applied"))
            logging.info("用户应用了配置")
        except Exception as e:
            logging.error(f"应用配置时出错: {e}")
            messagebox.showerror(self.monitor._("error"), self.monitor._("error_occurred").format(e))
        
    def save_config(self):
        """验证、保存设置并关闭窗口"""
        try:
            # 验证并保存设置
            if not self._validate_and_save_config():
                return
                
            messagebox.showinfo(self.monitor._("success"), self.monitor._("config_saved"))
            logging.info("用户保存了配置")
            self.destroy()
        except Exception as e:
            logging.error(f"保存配置时出错: {e}")
            messagebox.showerror(self.monitor._("error"), self.monitor._("error_occurred").format(e))
            
    def refresh_ui(self):
        """在语言切换后刷新UI"""
        # 保存当前配置值
        configs = {
            'critical': self.critical_threshold.get(),
            'warning': self.warning_threshold.get(),
            'notice': self.notice_threshold.get(),
            'interval': self.check_interval.get(),
            'all_drives': self.all_drives_var.get(),
            'silent': self.silent_mode_var.get(),
            'startup': self.startup_var.get(),
            'language': self.language_var.get()
        }
        
        # 清除当前界面内容
        for widget in self.winfo_children():
            widget.destroy()
        
        # 更新当前语言
        self.current_language = configs['language']
        
        # 重新创建界面组件
        self.create_widgets()
        
        # 恢复配置值
        self.critical_threshold.delete(0, tk.END)
        self.critical_threshold.insert(0, configs['critical'])
        
        self.warning_threshold.delete(0, tk.END)
        self.warning_threshold.insert(0, configs['warning'])
        
        self.notice_threshold.delete(0, tk.END)
        self.notice_threshold.insert(0, configs['notice'])
        
        self.check_interval.delete(0, tk.END)
        self.check_interval.insert(0, configs['interval'])
        
        self.all_drives_var.set(configs['all_drives'])
        self.silent_mode_var.set(configs['silent'])
        self.startup_var.set(configs['startup'])
        self.language_var.set(configs['language'])
        
        # 更新窗口标题
        self.title(self.monitor._("settings_title"))
        
        # 更新驱动器选择状态
        self.toggle_drive_selection()
            
    def _validate_and_save_config(self):
        """验证输入并保存配置"""
        try:
            # 验证输入值，增强对非数字输入的处理
            try:
                # 处理可能的空白字符串或非数字输入
                critical_str = self.critical_threshold.get().strip()
                warning_str = self.warning_threshold.get().strip()
                notice_str = self.notice_threshold.get().strip()
                
                if not critical_str or not warning_str or not notice_str:
                    raise ValueError(self.monitor._("threshold_empty"))
                
                critical = int(critical_str)
                warning = int(warning_str)
                notice = int(notice_str)
                
                if not (0 < notice < warning < critical <= 100):
                    raise ValueError(self.monitor._("threshold_invalid"))
                
                check_interval_str = self.check_interval.get().strip()
                
                if not check_interval_str:
                    raise ValueError(self.monitor._("interval_empty"))
                
                try:
                    check_interval = float(check_interval_str)
                except ValueError:
                    raise ValueError(self.monitor._("invalid_number"))
                
                if check_interval <= 0:
                    raise ValueError(self.monitor._("interval_too_small"))
                
            except ValueError as e:
                messagebox.showerror(self.monitor._("input_error"), str(e))
                return False
            
            # 收集配置
            new_config = {
                "critical_threshold": critical,
                "warning_threshold": warning,
                "notice_threshold": notice,
                "check_interval": check_interval,  # 以分钟为单位
                "silent_mode": self.silent_mode_var.get(),
                "run_at_startup": self.startup_var.get(),
                "language": self.language_var.get()
            }
            
            # 收集驱动器选择
            if not self.all_drives_var.get():
                selected_drives = [drive for drive, var in self.drive_vars.items() if var.get()]
                new_config["drives_to_monitor"] = selected_drives
            else:
                new_config["drives_to_monitor"] = []
            
            # 保存到配置文件
            with open(self.monitor.config_file, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=4, ensure_ascii=False)
            
            # 更新监视器配置
            self.monitor.config = new_config
            self.monitor.apply_config()
            
            return True
        except Exception as e:
            logging.error(f"验证和保存配置时出错: {e}")
            messagebox.showerror(self.monitor._("error"), self.monitor._("config_error"))
            return False

class SimpleDiskMonitor:
    def __init__(self, config_file=None):
        # 初始化单例检查
        self.single_instance = SingleInstance("SimpleDiskMonitor")
        if not self.single_instance.check():
            messagebox.showwarning("程序已在运行", "磁盘监控器已经在运行中，请勿重复启动。")
            sys.exit(0)
        
        # 区分配置目录和日志目录
        self.app_data_dir = self._get_app_data_dir()  # 存放配置文件
        self.program_dir = self._get_program_dir()    # 存放日志文件
        
        # 确保目录存在
        os.makedirs(self.app_data_dir, exist_ok=True)
        
        # 日志保存在程序所在目录
        log_file = os.path.join(self.program_dir, "disk_monitor.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            encoding='utf-8'
        )
        logging.info("磁盘监控器启动")
        logging.info(f"应用数据目录: {self.app_data_dir}")
        logging.info(f"日志文件目录: {self.program_dir}")
        
        # 配置文件仍然保存在用户数据目录
        self.config_file = config_file or os.path.join(
            self.app_data_dir, 
            "simple_disk_monitor_config.json"
        )
        
        # 默认配置 - 删除提醒频率，修改检查间隔单位
        self.default_config = {
            "critical_threshold": 90,  # 严重警告阈值（百分比）
            "warning_threshold": 75,   # 警告阈值（百分比）
            "notice_threshold": 60,    # 提示阈值（百分比）
            "check_interval": 5,       # 检查间隔（分钟）
            "drives_to_monitor": [],   # 要监控的驱动器，空列表表示监控所有驱动器
            "silent_mode": False,      # 静默模式
            "run_at_startup": False,   # 开机自启动
            "language": "zh_CN"        # 默认语言为简体中文
        }
        
        # 加载配置
        self.config = self.load_config()
        
        # 线程同步锁
        self.lock = threading.Lock()
        
        # 监控状态
        with self.lock:
            self.running = False
            self.silent_mode = False  # 增加静默模式变量的显式初始化
            
            # 添加磁盘报警状态字典，用于防止重复弹窗
            # 格式: {drive_path: {"critical": False, "warning": False, "notice": False}}
            self.alert_states = {}
            # 添加弹窗实例字典，用于跟踪当前打开的弹窗
            # 格式: {drive_path: {"critical": window_instance, "warning": window_instance, "notice": window_instance}}
            self.alert_windows = {}
            
        self.monitor_thread = None
        
        # UI通信队列
        self.ui_queue = queue.Queue()
        
        # Tkinter根窗口（隐藏）
        self.root = None
        
        # 初始化托盘图标
        self.setup_tray_icon()
    
    def _get_program_dir(self):
        """获取程序所在目录，用于存放日志文件"""
        try:
            if getattr(sys, 'frozen', False):
                # PyInstaller创建的exe
                return os.path.dirname(sys.executable)
            else:
                # 源码运行
                return os.path.dirname(os.path.abspath(__file__))
        except Exception as e:
            logging.error(f"获取程序目录出错: {e}", exc_info=True)
            # 如果无法确定，使用当前工作目录
            return os.getcwd()
    
    def _get_app_data_dir(self):
        """
        获取应用程序数据目录，用于存放配置文件
        在Windows上使用%APPDATA%\SimpleDiskMonitor
        在其他系统上使用~/.SimpleDiskMonitor
        """
        try:
            # 根据平台决定数据目录的基础路径
            if sys.platform == 'win32':
                base_dir = os.environ.get('APPDATA')
                if not base_dir:
                    base_dir = os.path.expanduser('~')
                app_data_dir = os.path.join(base_dir, 'SimpleDiskMonitor')
            else:
                app_data_dir = os.path.expanduser('~/.SimpleDiskMonitor')
            
            # 确保目录存在
            os.makedirs(app_data_dir, exist_ok=True)
            return app_data_dir
        
        except Exception as e:
            # 如果出错，回退到程序所在目录
            logging.error(f"获取应用程序数据目录出错: {e}", exc_info=True)
            return self._get_program_dir()
    
    def apply_config(self):
        """应用新配置，例如设置开机自启动"""
        try:
            # 检测语言是否变更，如果变更则更新托盘图标
            with self.lock:
                current_language = self.config.get("language", "zh_CN")
                
            if hasattr(self, 'last_language') and self.last_language != current_language:
                self.update_tray_icon()
            
            # 保存当前语言，用于下次检测变更
            self.last_language = current_language
            
            # 处理开机自启动
            self.set_autostart(self.config.get("run_at_startup", False))
            
            # 更新静默模式状态
            with self.lock:
                self.silent_mode = self.config.get("silent_mode", False)
                logging.info(f"应用新配置: 静默模式={'启用' if self.silent_mode else '禁用'}")
        except Exception as e:
            logging.error(f"应用配置时出错: {e}", exc_info=True)
    
    def set_autostart(self, enable):
        """设置开机自启动"""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "SimpleDiskMonitor"
            
            # 获取当前程序的路径
            if getattr(sys, 'frozen', False):
                # PyInstaller 创建的可执行文件
                app_path = f'"{sys.executable}"'
            else:
                # 正常的 Python 脚本
                app_path = f'pythonw "{os.path.abspath(__file__)}"'
            
            # 打开注册表键
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                
                if enable:
                    # 添加到启动项
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                    logging.info("已添加到开机自启动")
                else:
                    # 从启动项中移除
                    try:
                        winreg.DeleteValue(key, app_name)
                        logging.info("已从开机自启动中移除")
                    except FileNotFoundError:
                        # 如果键不存在，忽略错误
                        pass
                
                winreg.CloseKey(key)
            except Exception as e:
                logging.error(f"访问注册表时出错: {e}")
        except Exception as e:
            logging.error(f"设置开机自启动时出错: {e}")
    
    def load_config(self):
        """从配置文件加载配置，如果不存在则使用默认配置"""
        try:
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        logging.info("已加载配置文件")
                        return {**self.default_config, **config}  # 合并默认值和已保存配置
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logging.error(f"配置文件格式错误: {e}")
                    return self.default_config
                except PermissionError as e:
                    logging.error(f"无权限读取配置文件: {e}")
                    return self.default_config
            else:
                # 保存默认配置到文件
                try:
                    # 确保目录存在
                    os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                    with open(self.config_file, 'w', encoding='utf-8') as f:
                        json.dump(self.default_config, f, indent=4, ensure_ascii=False)
                    logging.info(f"已创建默认配置文件: {self.config_file}")
                except (PermissionError, IOError) as e:
                    logging.error(f"无法创建配置文件: {e}")
                return self.default_config
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}", exc_info=True)
            return self.default_config
    
    def get_available_drives(self):
        """获取所有可用的驱动器 - 使用更全面的实现方式"""
        drives = []
        
        try:
            # 输出更详细的日志，帮助诊断
            all_partitions = psutil.disk_partitions(all=True)
            logging.info(f"系统发现的所有分区: {[p.mountpoint for p in all_partitions]}")
            
            for part in all_partitions:
                try:
                    # 放宽检测条件，确保能检测到所有物理驱动器
                    # 排除一些典型的非物理驱动器路径
                    if (part.mountpoint and 
                        not any(part.mountpoint.startswith(p) for p in ["/proc", "/sys", "/dev", "/run"])):
                        drives.append(part.mountpoint)
                        logging.info(f"添加驱动器: {part.mountpoint} (类型: {part.fstype}, 选项: {part.opts})")
                    else:
                        logging.debug(f"忽略分区: {part.mountpoint} (类型: {part.fstype}, 选项: {part.opts})")
                except Exception as e:
                    logging.error(f"处理分区 {part.mountpoint} 时出错: {e}")
                    continue
                    
            logging.info(f"最终检测到的可用驱动器: {drives}")
        except Exception as e:
            logging.error(f"获取驱动器列表时出错: {e}", exc_info=True)
                
        return drives
    
    def get_drives_to_monitor(self):
        """获取需要监控的驱动器列表"""
        with self.lock:
            configured_drives = self.config.get("drives_to_monitor", [])
        
        if not configured_drives:
            # 如果没有指定驱动器，则监控所有可用驱动器
            return self.get_available_drives()
        else:
            # 过滤出实际存在的驱动器
            available_drives = self.get_available_drives()
            return [drive for drive in configured_drives if drive in available_drives]
    
    def get_disk_usage(self, drive):
        """获取指定驱动器的使用情况"""
        try:
            usage = psutil.disk_usage(drive)
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            }
        except Exception as e:
            logging.error(f"获取驱动器 {drive} 使用情况失败: {e}")
            return None
    
    def check_disk_usage(self):
        """检查所有监控的驱动器使用情况，返回不同级别的警告列表"""
        try:
            with self.lock:
                critical_threshold = self.config.get("critical_threshold", 90)
                warning_threshold = self.config.get("warning_threshold", 75)
                notice_threshold = self.config.get("notice_threshold", 60)
            
            critical_drives = []  # 严重级别
            warning_drives = []   # 警告级别
            notice_drives = []    # 提示级别
            
            for drive in self.get_drives_to_monitor():
                try:
                    usage = self.get_disk_usage(drive)
                    if not usage:
                        continue
                    
                    percent = usage["percent"]
                    logging.info(f"磁盘 {drive} 使用率: {percent:.1f}%")
                    
                    # 使用统一的逻辑进行分类
                    if percent >= critical_threshold:
                        critical_drives.append({
                            "drive": drive,
                            "usage": usage,
                            "level": "critical"
                        })
                    elif percent >= warning_threshold:
                        warning_drives.append({
                            "drive": drive,
                            "usage": usage,
                            "level": "warning"
                        })
                    elif percent >= notice_threshold:
                        notice_drives.append({
                            "drive": drive,
                            "usage": usage,
                            "level": "notice"
                        })
                except Exception as e:
                    logging.error(f"检查驱动器 {drive} 时出错: {e}")
                    # 继续检查下一个驱动器，而不是中断整个过程
                    continue
            
            # 返回所有需要提醒的驱动器
            return {
                "critical": critical_drives,
                "warning": warning_drives,
                "notice": notice_drives
            }
        except Exception as e:
            logging.error(f"检查磁盘使用情况时出错: {e}", exc_info=True)
            return {"critical": [], "warning": [], "notice": []}
    
    def show_alert(self, drive_info):
        """显示磁盘警告窗口"""
        with self.lock:
            drive = drive_info["drive"]
            level = drive_info["level"]
        
            if self.silent_mode:
                logging.info(f"静默模式下跳过警告: {drive}")
                return
            
            # 检查该磁盘是否初始化了状态
            if drive not in self.alert_states:
                self.alert_states[drive] = {"critical": False, "warning": False, "notice": False}
            
            if drive not in self.alert_windows:
                self.alert_windows[drive] = {"critical": None, "warning": None, "notice": None}
            
            # 检查当前是否已经有相同类型的弹窗
            if self.alert_states[drive][level]:
                # 检查窗口是否还存在
                window = self.alert_windows[drive][level]
                if window and window() and window().winfo_exists():
                    logging.info(f"磁盘 {drive} 的 {level} 级别报警窗口已存在，跳过")
                    return
                else:
                    # 窗口已被销毁但状态未重置
                    logging.warning(f"磁盘 {drive} 的 {level} 级别窗口已销毁但状态未重置，重新弹窗")
                    self.alert_states[drive][level] = False
                    self.alert_windows[drive][level] = None
                
            # 设置报警状态为True，表示已经弹出窗口
            self.alert_states[drive][level] = True
        
        # 将警告放入队列，由主线程处理
        self.ui_queue.put(("show_alert", drive_info))

    def start_monitoring(self):
        """开始监控磁盘使用情况"""
        with self.lock:
            if self.running:
                logging.warning("监控已经在运行中")
                return
            
            self.running = True
        
        self.monitor_thread = threading.Thread(target=self._monitor_thread)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logging.info("磁盘监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        with self.lock:
            if not self.running:
                logging.info("监控已经停止")
                return
            self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            try:
                self.monitor_thread.join(2.0)  # 给线程2秒时间正常退出
                if self.monitor_thread.is_alive():
                    logging.warning("监控线程未能及时退出")
            except Exception as e:
                logging.error(f"停止监控线程时出错: {e}")
        
        logging.info("磁盘监控已停止")
    
    def _monitor_thread(self):
        """监控线程函数 - 简化为每次检查后直接显示警告"""
        try:
            logging.info("监控线程已启动，开始循环检测磁盘使用情况")
            while True:
                # 线程安全检查运行状态
                with self.lock:
                    if not self.running:
                        logging.info("监控线程收到停止信号，退出循环")
                        break
                
                try:
                    # 检查磁盘使用情况
                    disk_status = self.check_disk_usage()
                    
                    # 处理严重级别的警告 - 直接显示警告，不考虑上次提醒时间
                    for drive_info in disk_status["critical"]:
                        self.show_alert(drive_info)
                    
                    # 处理警告级别
                    for drive_info in disk_status["warning"]:
                        self.show_alert(drive_info)
                    
                    # 处理提示级别
                    for drive_info in disk_status["notice"]:
                        self.show_alert(drive_info)
                except Exception as e:
                    logging.error(f"监控过程中处理磁盘状态时出错: {e}", exc_info=True)
                
                try:
                    # 获取检查间隔（分钟转换为秒）
                    with self.lock:
                        check_interval = int(self.config.get("check_interval", 5) * 60)
                    logging.info(f"磁盘检查完成，下次检查将在 {check_interval/60:.1f} 分钟后进行...")
                    
                    # 分段睡眠，使得在停止监控时能更快响应
                    # 每1秒检查一次是否需要停止，提高响应性
                    for _ in range(check_interval):
                        with self.lock:
                            if not self.running:
                                logging.info("睡眠过程中收到停止信号，提前退出")
                                break
                        time.sleep(1)
                except Exception as e:
                    logging.error(f"监控线程等待时出错: {e}", exc_info=True)
                    # 如果出错，等待短时间后继续
                    time.sleep(5)
                    
            logging.info("监控线程正常退出")
        except Exception as e:
            logging.error(f"监控过程中出错: {e}", exc_info=True)
            with self.lock:
                self.running = False
    
    def create_disk_icon(self):
        """创建磁盘图标"""
        img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        
        # 绘制一个简单的磁盘图标
        d.rectangle((10, 25, 54, 45), fill=(0, 120, 215), outline=(255, 255, 255))
        d.rectangle((20, 15, 44, 25), fill=(0, 70, 170), outline=(255, 255, 255))
        
        for i in range(3):
            y = 30 + i * 5
            d.line((15, y, 49, y), fill=(200, 200, 200))
        
        return img

    def setup_tray_icon(self):
        """设置系统托盘图标 - 确保线程安全"""
        # 创建图标图像
        icon_image = self.create_disk_icon()
        
        # 保存当前语言，用于检测变更
        self.last_language = self.config.get("language", "zh_CN")
        
        # 创建托盘图标
        self.create_tray_icon(icon_image)
        
        # 在单独的线程中运行图标
        logging.info("启动系统托盘图标")
        threading.Thread(target=self.icon.run, daemon=True).start()
    
    def create_tray_icon(self, icon_image):
        """创建托盘图标 - 封装为方法便于更新"""
        # 创建菜单项 - 确保所有UI操作都通过队列处理
        def open_config_window():
            # 线程安全：通过队列将UI操作传递到主线程
            logging.info("用户点击了配置设置")
            with self.lock:  # 加锁确保线程安全
                self.ui_queue.put(("open_config",))
        
        def check_now():
            # 线程安全：通过队列启动磁盘检查
            logging.info("用户点击了立即检查磁盘")
            with self.lock:  # 加锁确保线程安全
                # 不要直接在非主线程启动新线程，而是通过队列请求
                self.ui_queue.put(("run_disk_check",))
        
        def safe_exit():
            # 线程安全：通过队列请求退出程序
            logging.info("用户通过托盘菜单请求退出")
            with self.lock:  # 加锁确保线程安全
                self.ui_queue.put(("exit_app",))
        
        # 创建托盘图标菜单，使用翻译后的文本
        menu = pystray.Menu(
            pystray.MenuItem(self._("check_now"), check_now),
            pystray.MenuItem(self._("settings"), open_config_window),
            pystray.MenuItem(self._("exit"), safe_exit)
        )
        
        # 创建托盘图标
        self.icon = pystray.Icon(
            "disk_monitor",
            icon_image,
            self._("app_name"),
            menu
        )
    
    def update_tray_icon(self):
        """在语言变更后更新托盘图标"""
        try:
            # 先停止现有托盘图标
            if hasattr(self, 'icon') and self.icon:
                try:
                    self.icon.stop()
                    # 等待托盘图标完全停止
                    time.sleep(0.5)
                    logging.info("已停止旧托盘图标")
                except Exception as e:
                    logging.error(f"停止旧托盘图标时出错: {e}", exc_info=True)
            
            # 创建新图标
            icon_image = self.create_disk_icon()
            self.create_tray_icon(icon_image)
            
            # 重新启动托盘图标
            threading.Thread(target=self.icon.run, daemon=True).start()
            logging.info("托盘图标已更新为新语言")
        except Exception as e:
            logging.error(f"更新托盘图标时出错: {e}", exc_info=True)
    
    def _check_disk_and_queue(self):
        """检查磁盘并将结果放入UI队列"""
        try:
            logging.info("开始执行磁盘检查")
            disk_status = self.check_disk_usage()
            
            # 收集所有驱动器的状态
            all_drives = []
            all_drives.extend(disk_status["critical"])
            all_drives.extend(disk_status["warning"])
            all_drives.extend(disk_status["notice"])
            
            if not all_drives:
                # 如果没有达到任何阈值的驱动器，显示所有驱动器的状态
                drives = self.get_drives_to_monitor()
                for drive in drives:
                    usage = self.get_disk_usage(drive)
                    if usage:
                        all_drives.append({"drive": drive, "usage": usage, "level": "normal"})
            
            # 将结果放入队列供主线程处理
            self.ui_queue.put(("show_disk_status", all_drives))
            logging.info("磁盘检查完成，结果已入队")
            
        except Exception as e:
            logging.error(f"立即检查磁盘时出错: {e}", exc_info=True)
            # 通知UI线程显示错误
            self.ui_queue.put(("show_error", str(e)))
    
    def check_queue(self):
        """检查UI队列，处理UI事件 - 增强错误处理和添加新任务类型"""
        try:
            while not self.ui_queue.empty():  # 处理队列中的所有任务
                try:
                    # 非阻塞方式获取队列中的任务
                    task = self.ui_queue.get(block=False)
                    
                    try:
                        # 任务处理加上错误捕获
                        if task[0] == "open_config":
                            # 创建配置窗口
                            self._create_config_window()
                        elif task[0] == "show_disk_status":
                            # 显示磁盘状态窗口
                            self._show_disk_status_window(task[1])
                        elif task[0] == "show_error":
                            # 显示错误消息
                            self._show_error_dialog(task[1])
                        elif task[0] == "show_alert":
                            # 显示磁盘警告
                            self._show_alert_window(task[1])
                        elif task[0] == "run_disk_check":
                            # 处理磁盘检查请求
                            self._handle_disk_check_request()
                        elif task[0] == "exit_app":
                            # 处理退出请求
                            self._handle_exit_request()
                        else:
                            logging.warning(f"未知任务类型: {task[0]}")
                    except Exception as e:
                        logging.error(f"处理UI任务 {task[0]} 时出错: {e}", exc_info=True)
                    finally:
                        # 无论成功还是失败，都标记任务完成
                        self.ui_queue.task_done()
                        
                except queue.Empty:
                    # 队列为空，跳出循环
                    break
                except Exception as e:
                    logging.error(f"处理队列时出错: {e}", exc_info=True)
                    break
        except Exception as e:
            logging.error(f"检查队列过程出错: {e}", exc_info=True)
        
        # 安排下一次检查，如果root窗口仍然存在
        if self.root and self.root.winfo_exists():
            self.root.after(100, self.check_queue)
        else:
            logging.warning("根窗口不存在，停止队列检查")
    
    # 添加一个新方法处理托盘菜单中的磁盘检查请求
    def _handle_disk_check_request(self):
        """处理来自托盘菜单的磁盘检查请求"""
        # 在主线程中安全地启动一个新线程
        threading.Thread(target=self._check_disk_and_queue, daemon=True).start()

    # 添加处理退出应用请求的方法
    def _handle_exit_request(self):
        """处理来自托盘菜单的退出请求"""
        self.exit_app()
    
    def _create_config_window(self):
        """在主线程中创建配置窗口"""
        try:
            logging.info("创建配置窗口")
            config_window = ConfigWindow(self, self.root)
            # 不调用mainloop()，因为这已经由主Tk实例处理
            logging.info("配置窗口创建成功")
        except Exception as e:
            logging.error(f"创建配置窗口失败: {e}", exc_info=True)
            self._show_error_dialog(self._("config_window_error").format(e))
    
    def _show_disk_status_window(self, drives_info):
        """在主线程中显示磁盘状态窗口"""
        try:
            self.show_disk_status_window(drives_info)
        except Exception as e:
            logging.error(f"显示磁盘状态窗口失败: {e}", exc_info=True)
            self._show_error_dialog(self._("config_window_error").format(e))
    
    def _show_error_dialog(self, error_message):
        """显示错误对话框"""
        try:
            messagebox.showerror(self._("error"), self._("error_occurred").format(error_message))
        except Exception as e:
            logging.error(f"显示错误对话框时出错: {e}", exc_info=True)
    
    def _show_alert_window(self, drive_info):
        """根据报警级别显示不同的弹窗"""
        try:
            drive = drive_info["drive"]
            usage = drive_info["usage"]
            level = drive_info["level"]
            
            # 确保字典已初始化
            with self.lock:
                if drive not in self.alert_states:
                    self.alert_states[drive] = {"critical": False, "warning": False, "notice": False}
                if drive not in self.alert_windows:
                    self.alert_windows[drive] = {"critical": None, "warning": None, "notice": None}
                
                # 再次检查是否需要显示弹窗 (防止队列处理延迟导致的重复弹窗)
                if self.alert_states[drive][level]:
                    window = self.alert_windows[drive][level]
                    if window and window() and window().winfo_exists():
                        logging.info(f"处理队列时跳过已存在的弹窗: 磁盘 {drive} 的 {level} 级别")
                        return

            percent = usage["percent"]
            total_gb = usage["total"] / (1024**3)
            used_gb = usage["used"] / (1024**3)
            free_gb = usage["free"] / (1024**3)

            if level == "critical":
                self._show_critical_alert(drive, percent, total_gb, used_gb, free_gb)
            elif level == "warning":
                self._show_warning_alert(drive, percent, total_gb, used_gb, free_gb)
            elif level == "notice":
                self._show_notice_alert(drive, percent, total_gb, used_gb, free_gb)
        except Exception as e:
            logging.error(f"显示警告窗口时出错: {e}", exc_info=True)
            # 出错时也要重置状态，避免卡死
            with self.lock:
                if drive in self.alert_states and level in self.alert_states[drive]:
                    self.alert_states[drive][level] = False
                if drive in self.alert_windows and level in self.alert_windows[drive]:
                    self.alert_windows[drive][level] = None

    def _show_notice_alert(self, drive, percent, total_gb, used_gb, free_gb):
        """提示级别的弹窗"""
        title = self._("notice_title")
        message = self._("notice_message", drive, percent, total_gb, used_gb, free_gb)
        
        # 创建信息窗口而不是使用messagebox，这样可以更好地控制窗口事件
        notice_window = tk.Toplevel(self.root)
        notice_window.title(title)
        notice_window.geometry("400x200")
        
        # 窗口居中
        notice_window.update_idletasks()
        width = notice_window.winfo_width()
        height = notice_window.winfo_height()
        x = (notice_window.winfo_screenwidth() // 2) - (width // 2)
        y = (notice_window.winfo_screenheight() // 2) - (height // 2)
        notice_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # 添加消息内容
        tk.Label(notice_window, text=message, wraplength=380, justify=tk.LEFT).pack(pady=20, padx=10)
        
        # 添加确认按钮
        def on_close():
            with self.lock:
                if drive in self.alert_states:
                    self.alert_states[drive]["notice"] = False
                    self.alert_windows[drive]["notice"] = None
                    logging.debug(f"重置磁盘 {drive} 的notice报警状态")
            notice_window.destroy()
            
        tk.Button(notice_window, text=self._("ok"), command=on_close).pack(pady=10)
        
        # 绑定窗口关闭事件
        notice_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # 保存窗口引用
        with self.lock:
            self.alert_windows[drive]["notice"] = weakref.ref(notice_window)
        
        logging.info(f"显示提示: 磁盘 {drive} 使用率 {percent:.1f}%")

    def _show_warning_alert(self, drive, percent, total_gb, used_gb, free_gb):
        """警告级别的弹窗"""
        title = self._("warning_title")
        message = self._("warning_message", drive, percent, total_gb, used_gb, free_gb)

        # 创建警告窗口
        warning_window = tk.Toplevel(self.root)
        warning_window.title(title)
        warning_window.geometry("400x200")
        
        # 窗口居中
        warning_window.update_idletasks()
        width = warning_window.winfo_width()
        height = warning_window.winfo_height()
        x = (warning_window.winfo_screenwidth() // 2) - (width // 2)
        y = (warning_window.winfo_screenheight() // 2) - (height // 2)
        warning_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # 添加消息内容
        tk.Label(warning_window, text=message, wraplength=380, justify=tk.LEFT).pack(pady=20, padx=10)
        
        # 二次确认信息
        confirm_message = self._("warning_confirm", drive)
        tk.Label(warning_window, text=confirm_message, wraplength=380, justify=tk.LEFT).pack(pady=10, padx=10)
        
        # 确认按钮框架
        button_frame = tk.Frame(warning_window)
        button_frame.pack(pady=10, fill=tk.X)
        
        def on_yes():
            with self.lock:
                if drive in self.alert_states:
                    self.alert_states[drive]["warning"] = False
                    self.alert_windows[drive]["warning"] = None
                    logging.debug(f"重置磁盘 {drive} 的warning报警状态 (确认)")
            warning_window.destroy()
            logging.info(f"用户确认了警告级别的弹窗: {drive}")
            
        def on_no():
            with self.lock:
                if drive in self.alert_states:
                    self.alert_states[drive]["warning"] = False
                    self.alert_windows[drive]["warning"] = None
                    logging.debug(f"重置磁盘 {drive} 的warning报警状态 (取消)")
            warning_window.destroy()
            logging.info(f"用户取消了警告级别的弹窗: {drive}")
        
        # 添加确认和取消按钮
        yes_button = tk.Button(button_frame, text=self._("yes"), command=on_yes)
        yes_button.pack(side=tk.LEFT, padx=20, expand=True)
        
        no_button = tk.Button(button_frame, text=self._("no"), command=on_no)
        no_button.pack(side=tk.RIGHT, padx=20, expand=True)
        
        # 绑定窗口关闭事件
        def on_close():
            with self.lock:
                if drive in self.alert_states:
                    self.alert_states[drive]["warning"] = False
                    self.alert_windows[drive]["warning"] = None
                    logging.debug(f"重置磁盘 {drive} 的warning报警状态 (窗口关闭)")
            warning_window.destroy()
        
        warning_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # 保存窗口引用
        with self.lock:
            self.alert_windows[drive]["warning"] = weakref.ref(warning_window)
            
        logging.info(f"显示警告: 磁盘 {drive} 使用率 {percent:.1f}%")

    def _show_critical_alert(self, drive, percent, total_gb, used_gb, free_gb):
        """严重级别的弹窗"""
        title = self._("critical_title")
        message = self._("critical_message", drive, percent, total_gb, used_gb, free_gb)

        # 创建非模态窗口
        critical_window = tk.Toplevel(self.root)
        critical_window.title(title)
        
        # 设置窗口位置为右下角
        screen_width = critical_window.winfo_screenwidth()
        screen_height = critical_window.winfo_screenheight()
        window_width = 400
        window_height = 250
        x_position = screen_width - window_width - 20
        y_position = screen_height - window_height - 50
        critical_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # 添加消息内容
        tk.Label(critical_window, text=message, wraplength=380, justify=tk.LEFT).pack(pady=10)
        
        def on_confirm():
            """用户点击确认后的回调函数"""
            # 重置报警状态
            with self.lock:
                if drive in self.alert_states:
                    self.alert_states[drive]["critical"] = False
                    self.alert_windows[drive]["critical"] = None
                    logging.debug(f"重置磁盘 {drive} 的critical报警状态 (确认清理)")
            
            # 立即重新检查磁盘使用情况
            new_usage = self.get_disk_usage(drive)
            
            if new_usage and new_usage["percent"] >= self.config.get("critical_threshold", 90):
                # 如果仍然超过阈值，继续显示弹窗
                logging.info(f"磁盘 {drive} 仍然超过阈值，继续显示弹窗")
                critical_window.destroy()
                self._show_critical_alert(drive, new_usage["percent"], 
                                         new_usage["total"] / (1024**3), 
                                         new_usage["used"] / (1024**3), 
                                         new_usage["free"] / (1024**3))
            else:
                # 如果低于阈值，关闭弹窗
                logging.info(f"磁盘 {drive} 已清理，关闭弹窗")
                critical_window.destroy()
        
        # 添加确认按钮
        confirm_button = tk.Button(
            critical_window, 
            text=self._("clean_confirm"),
            command=on_confirm
        )
        confirm_button.pack(pady=10)
        
        # 添加关闭窗口时的处理函数
        def on_close():
            with self.lock:
                if drive in self.alert_states:
                    self.alert_states[drive]["critical"] = False
                    self.alert_windows[drive]["critical"] = None
                    logging.debug(f"窗口关闭时重置磁盘 {drive} 的critical报警状态")
            critical_window.destroy()
            
        # 绑定窗口关闭事件
        critical_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # 保存窗口引用
        with self.lock:
            self.alert_windows[drive]["critical"] = weakref.ref(critical_window)
        
        logging.warning(f"显示严重警告: 磁盘 {drive} 使用率 {percent:.1f}%")

    def reset_alert_state(self, drive=None, level=None):
        """重置指定驱动器的报警状态，如果不指定则重置所有"""
        with self.lock:
            if drive is None:
                # 重置所有驱动器的所有级别报警状态
                for d in list(self.alert_states.keys()):
                    # 检查并关闭所有窗口
                    if d in self.alert_windows:
                        for lvl in ["critical", "warning", "notice"]:
                            window_ref = self.alert_windows[d][lvl]
                            if window_ref and window_ref() and window_ref().winfo_exists():
                                try:
                                    window_ref().destroy()
                                    logging.debug(f"重置状态时关闭磁盘 {d} 的 {lvl} 窗口")
                                except Exception as e:
                                    logging.error(f"关闭窗口时出错: {e}")
                # 清空字典
                self.alert_states = {}
                self.alert_windows = {}
                logging.debug("重置所有磁盘的报警状态")
            elif drive in self.alert_states:
                if level is None:
                    # 重置指定驱动器的所有级别报警状态
                    if drive in self.alert_windows:
                        for lvl in ["critical", "warning", "notice"]:
                            window_ref = self.alert_windows[drive][lvl]
                            if window_ref and window_ref() and window_ref().winfo_exists():
                                try:
                                    window_ref().destroy()
                                    logging.debug(f"重置状态时关闭磁盘 {drive} 的 {lvl} 窗口")
                                except Exception as e:
                                    logging.error(f"关闭窗口时出错: {e}")
                    self.alert_states[drive] = {"critical": False, "warning": False, "notice": False}
                    self.alert_windows[drive] = {"critical": None, "warning": None, "notice": None}
                    logging.debug(f"重置磁盘 {drive} 的所有报警状态")
                else:
                    # 重置指定驱动器的指定级别报警状态
                    if level in self.alert_states[drive]:
                        if drive in self.alert_windows and level in self.alert_windows[drive]:
                            window_ref = self.alert_windows[drive][level]
                            if window_ref and window_ref() and window_ref().winfo_exists():
                                try:
                                    window_ref().destroy()
                                    logging.debug(f"重置状态时关闭磁盘 {drive} 的 {level} 窗口")
                                except Exception as e:
                                    logging.error(f"关闭窗口时出错: {e}")
                        self.alert_states[drive][level] = False
                        self.alert_windows[drive][level] = None
                        logging.debug(f"重置磁盘 {drive} 的 {level} 报警状态")

    def show_disk_status_window(self, drives_info):
        """显示所有监控的驱动器状态"""
        # 创建顶级窗口而不是根窗口
        disk_window = tk.Toplevel(self.root)
        disk_window.title(self._("disk_status"))
        disk_window.geometry("500x400")
        
        # 窗口居中
        disk_window.update_idletasks()
        width = disk_window.winfo_width()
        height = disk_window.winfo_height()
        x = (disk_window.winfo_screenwidth() // 2) - (width // 2)
        y = (disk_window.winfo_screenheight() // 2) - (height // 2)
        disk_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # 创建一个带有滚动条的框架
        main_frame = tk.Frame(disk_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 显示每个驱动器的状态
        row = 0
        for drive_info in drives_info:
            drive = drive_info["drive"]
            usage = drive_info["usage"]
            level = drive_info.get("level", "normal")
            
            percent = usage["percent"]
            total_gb = usage["total"] / (1024**3)
            used_gb = usage["used"] / (1024**3)
            free_gb = usage["free"] / (1024**3)
            
            # 创建驱动器状态框架
            drive_frame = tk.LabelFrame(scrollable_frame, text=f"{self._('drive')} {drive}")
            drive_frame.grid(row=row, column=0, padx=5, pady=5, sticky=tk.W+tk.E)
            
            # 设置颜色
            if level == "critical":
                bg_color = "#FFCCCC"  # 浅红色
            elif level == "warning":
                bg_color = "#FFFFCC"  # 浅黄色
            elif level == "notice":
                bg_color = "#CCE5FF"  # 浅蓝色
            else:
                bg_color = "#E8E8E8"  # 浅灰色
            
            drive_frame.configure(bg=bg_color)
            
            # 使用率进度条
            tk.Label(drive_frame, text=f"{self._('usage')}: {percent:.1f}%", bg=bg_color).grid(row=0, column=0, sticky=tk.W, padx=10, pady=2)
            progress = ttk.Progressbar(drive_frame, length=300, value=percent)
            progress.grid(row=0, column=1, padx=10, pady=2)
            
            # 空间信息
            tk.Label(drive_frame, text=f"{self._('total_space')}: {total_gb:.2f} GB", bg=bg_color).grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
            tk.Label(drive_frame, text=f"{self._('used_space')}: {used_gb:.2f} GB", bg=bg_color).grid(row=1, column=1, sticky=tk.W, padx=10, pady=2)
            tk.Label(drive_frame, text=f"{self._('free_space')}: {free_gb:.2f} GB", bg=bg_color).grid(row=2, column=0, sticky=tk.W, padx=10, pady=2)
            
            row += 1
        
        # 添加关闭按钮
        button_frame = tk.Frame(disk_window)
        button_frame.pack(fill=tk.X, pady=10)
        
        close_button = tk.Button(button_frame, text=self._("close"), command=disk_window.destroy, width=10)
        close_button.pack(side=tk.RIGHT, padx=10)
        
        # 不需要调用mainloop，因为主Tk实例已经运行了事件循环
    
    def exit_app(self):
        """退出应用程序"""
        logging.info("用户点击了退出按钮")
        try:
            # 停止监控线程
            self.stop_monitoring()
            
            # 重置所有报警状态 - 会关闭所有弹窗
            self.reset_alert_state()
            
            # 优雅地关闭系统托盘图标
            if hasattr(self, 'icon') and self.icon:
                try:
                    self.icon.stop()
                    # 等待托盘图标完全停止
                    time.sleep(0.5)
                    logging.info("系统托盘图标已关闭")
                except Exception as e:
                    logging.error(f"关闭托盘图标时出错: {e}", exc_info=True)
            
            # 清空队列
            try:
                while not self.ui_queue.empty():
                    self.ui_queue.get(block=False)
                    self.ui_queue.task_done()
            except Exception as e:
                logging.error(f"清空队列时出错: {e}")
            
            # 销毁Tkinter根窗口
            if self.root:
                try:
                    self.root.quit()
                    self.root.destroy()
                    logging.info("Tkinter根窗口已销毁")
                except Exception as e:
                    logging.error(f"销毁根窗口时出错: {e}")
            
            # 释放单例互斥体
            if hasattr(self, 'single_instance'):
                self.single_instance.release()
                logging.info("释放单例互斥体")
            
            logging.info("程序退出")
            sys.exit(0)
        except Exception as e:
            logging.error(f"退出程序时出错: {e}", exc_info=True)
            sys.exit(1)
    
    def run(self):
        """运行主事件循环"""
        try:
            # 创建Tkinter根窗口（隐藏）
            self.root = tk.Tk()
            self.root.withdraw()  # 隐藏窗口
            self.root.title(self._("app_name"))
            
            # 设置窗口关闭事件 - 改为调用exit_app方法
            self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
            
            # 首次启动队列检查
            self.root.after(100, self.check_queue)
            
            logging.info("启动Tkinter主循环")
            # 启动Tkinter主循环
            self.root.mainloop()
            
            logging.info("Tkinter主循环已退出")
            
        except Exception as e:
            logging.critical(f"运行主事件循环时出错: {e}", exc_info=True)
            sys.exit(1)

    def _(self, key, *args):
        """翻译方法"""
        return get_text(key, self.config.get("language", "zh_CN"), *args)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="磁盘监控器")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--silent", action="store_true", help="静默模式，不显示弹窗提示")
    parser.add_argument("--autostart", action="store_true", help="设置开机自启动")
    parser.add_argument("--no-autostart", action="store_true", help="禁用开机自启动")
    return parser.parse_args()

# 修改程序入口点
if __name__ == "__main__":
    try:
        args = parse_args()
        
        # 创建监控器实例
        monitor = SimpleDiskMonitor(args.config)
        
        # 应用命令行参数
        if args.silent:
            monitor.config["silent_mode"] = True
        
        if args.autostart:
            monitor.config["run_at_startup"] = True
            monitor.set_autostart(True)
        
        if args.no_autostart:
            monitor.config["run_at_startup"] = False
            monitor.set_autostart(False)
        
        # 应用配置
        monitor.apply_config()
        
        # 启动监控
        monitor.start_monitoring()
        
        # 启动主事件循环
        monitor.run()
        
    except KeyboardInterrupt:
        logging.info("用户中断，程序退出")
        # 确保释放互斥体
        if 'monitor' in locals() and hasattr(monitor, 'single_instance'):
            monitor.single_instance.release()
    except Exception as e:
        logging.critical(f"程序发生严重错误: {e}", exc_info=True)
        # 确保释放互斥体
        if 'monitor' in locals() and hasattr(monitor, 'single_instance'):
            monitor.single_instance.release()
        # 在程序出错时显示错误窗口
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("磁盘监控器错误", f"程序发生错误: {e}")
            root.destroy()
        except:
            pass
        sys.exit(1)
