"""
提供多语言支持的模块
"""

# 翻译字典，包含所有支持的语言
TRANSLATIONS = {
    "zh_CN": {
        # 通用字符串
        "app_name": "磁盘监控器",
        "success": "成功",
        "error": "错误",
        "confirm": "确认",
        "cancel": "取消",
        "apply": "应用",
        "save_and_close": "保存并关闭",
        "close": "关闭",

        # 设置窗口
        "settings_title": "磁盘监控器 - 设置",
        "threshold_settings": "阈值设置",
        "critical_threshold": "严重警告阈值 (%):",
        "warning_threshold": "警告阈值 (%):",
        "notice_threshold": "提示阈值 (%):",
        "time_settings": "时间设置",
        "check_interval": "检查间隔 (分钟):",
        "monitor_drives": "监控驱动器",
        "monitor_all_drives": "监控所有驱动器",
        "language_settings": "语言设置 / Language Settings",
        "other_options": "其他选项",
        "silent_mode": "静默模式 (不显示弹窗提示)",
        "run_at_startup": "开机自启动",
        "config_applied": "配置已应用！将在下次检查时生效。",
        "config_saved": "配置已保存！将在下次检查时生效。",

        # 验证信息
        "threshold_empty": "阈值不能为空",
        "threshold_invalid": "阈值必须符合: 提示 < 警告 < 严重 且都在1-100之间",
        "interval_empty": "检查间隔不能为空",
        "invalid_number": "请输入有效的数字",
        "interval_too_small": "检查间隔必须大于0分钟",
        "input_error": "输入错误",
        "config_error": "保存配置时出错",

        # 磁盘状态窗口
        "disk_status": "磁盘状态",
        "drive": "驱动器",
        "usage": "使用率",
        "total_space": "总空间",
        "used_space": "已使用",
        "free_space": "剩余空间",

        # 警告窗口
        "notice_title": "磁盘空间提示",
        "notice_message": "提示: 磁盘 {} 使用率达到 {:.1f}%\n\n总空间: {:.2f} GB\n已使用: {:.2f} GB\n剩余空间: {:.2f} GB",
        "warning_title": "磁盘空间不足",
        "warning_message": "警告: 磁盘 {} 使用率达到 {:.1f}%\n\n总空间: {:.2f} GB\n已使用: {:.2f} GB\n剩余空间: {:.2f} GB\n\n请考虑清理磁盘空间。",
        "critical_title": "磁盘空间严重不足",
        "critical_message": "严重警告: 磁盘 {} 使用率达到 {:.1f}%！\n\n总空间: {:.2f} GB\n已使用: {:.2f} GB\n剩余空间: {:.2f} GB\n\n请立即清理磁盘空间！",
        "warning_confirm": "是否已经知晓磁盘 {} 详细状态？",
        "clean_confirm": "确定",

        # 托盘菜单
        "check_now": "立即检查磁盘",
        "settings": "配置设置",
        "exit": "退出",

        # 错误消息
        "error_occurred": "发生错误: {}",
        "config_window_error": "无法打开配置窗口: {}"
    },
    
    "en_US": {
        # General strings
        "app_name": "Disk Monitor",
        "success": "Success",
        "error": "Error",
        "confirm": "Confirm",
        "cancel": "Cancel",
        "apply": "Apply",
        "save_and_close": "Save & Close",
        "close": "Close",

        # Settings window
        "settings_title": "Disk Monitor - Settings",
        "threshold_settings": "Threshold Settings",
        "critical_threshold": "Critical Threshold (%):",
        "warning_threshold": "Warning Threshold (%):",
        "notice_threshold": "Notice Threshold (%):",
        "time_settings": "Time Settings",
        "check_interval": "Check Interval (minutes):",
        "monitor_drives": "Monitor Drives",
        "monitor_all_drives": "Monitor All Drives",
        "language_settings": "Language Settings / 语言设置",
        "other_options": "Other Options",
        "silent_mode": "Silent Mode (No Popups)",
        "run_at_startup": "Run at Startup",
        "config_applied": "Configuration applied! Will take effect on next check.",
        "config_saved": "Configuration saved! Will take effect on next check.",

        # Validation messages
        "threshold_empty": "Thresholds cannot be empty",
        "threshold_invalid": "Thresholds must follow: Notice < Warning < Critical and be between 1-100",
        "interval_empty": "Check interval cannot be empty",
        "invalid_number": "Please enter valid numbers",
        "interval_too_small": "Check interval must be greater than 0 minutes",
        "input_error": "Input Error",
        "config_error": "Error saving configuration",

        # Disk status window
        "disk_status": "Disk Status",
        "drive": "Drive",
        "usage": "Usage",
        "total_space": "Total Space",
        "used_space": "Used",
        "free_space": "Free Space",

        # Alert windows
        "notice_title": "Disk Space Notice",
        "notice_message": "Notice: Drive {} usage is at {:.1f}%\n\nTotal: {:.2f} GB\nUsed: {:.2f} GB\nFree: {:.2f} GB",
        "warning_title": "Low Disk Space",
        "warning_message": "Warning: Drive {} usage is at {:.1f}%\n\nTotal: {:.2f} GB\nUsed: {:.2f} GB\nFree: {:.2f} GB\n\nPlease consider freeing up some space.",
        "critical_title": "Critical Disk Space",
        "critical_message": "Critical Warning: Drive {} usage is at {:.1f}%!\n\nTotal: {:.2f} GB\nUsed: {:.2f} GB\nFree: {:.2f} GB\n\nPlease free up disk space immediately!",
        "warning_confirm": "Are you aware of the disk {} status details?",
        "clean_confirm": "Confirm",

        # Tray menu
        "check_now": "Check Disks Now",
        "settings": "Settings",
        "exit": "Exit",

        # Error messages
        "error_occurred": "Error occurred: {}",
        "config_window_error": "Cannot open settings window: {}"
    }
}

def get_text(key, language="zh_CN", *args):
    """
    获取指定语言的文本
    
    参数:
        key (str): 翻译键名
        language (str): 语言代码，默认为中文
        *args: 格式化参数
        
    返回:
        str: 翻译后的文本，如果找不到则返回键名
    """
    if language not in TRANSLATIONS:
        language = "zh_CN"  # 默认为中文
        
    text = TRANSLATIONS[language].get(key, key)
    
    if args:
        try:
            return text.format(*args)
        except:
            return text
    return text