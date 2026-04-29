"""项目启动入口：

1. 创建 CookieManager，按配置文件 / 环境变量初始化账号任务
2. 在后台线程启动 FastAPI (reply_server) 提供管理与自动回复接口
3. 主协程保持运行
"""

import os
import sys
import shutil
from pathlib import Path

# 设置标准输出编码为UTF-8（Windows兼容）
def _setup_console_encoding():
    """设置控制台编码为UTF-8，避免Windows GBK编码问题"""
    if sys.platform == 'win32':
        try:
            # 方法1: 设置环境变量
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            # 方法2: 尝试设置控制台代码页为UTF-8
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleOutputCP(65001)  # UTF-8代码页
            except Exception:
                pass
            
            # 方法3: 重新包装stdout和stderr
            try:
                if hasattr(sys.stdout, 'buffer'):
                    import io
                    # 只在编码不是UTF-8时重新包装
                    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
                        sys.stdout = io.TextIOWrapper(
                            sys.stdout.buffer, 
                            encoding='utf-8', 
                            errors='replace',
                            line_buffering=True
                        )
                    if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
                        sys.stderr = io.TextIOWrapper(
                            sys.stderr.buffer, 
                            encoding='utf-8', 
                            errors='replace',
                            line_buffering=True
                        )
            except Exception:
                pass
        except Exception:
            pass

# 在程序启动时设置编码
_setup_console_encoding()

# 定义ASCII安全字符（备用方案）
_OK = '[OK]'
_WARN = '[WARN]'
_ERROR = '[ERROR]'
_INFO = '[INFO]'

# ==================== 在导入任何模块之前先迁移数据库 ====================
def _migrate_database_files_early():
    """在启动前检查并迁移数据库文件到data目录（使用print，因为logger还未初始化）
    
    注意：迁移完成后旧文件会被删除，请确保data目录有足够的磁盘空间。
    如果迁移失败，程序会尝试复制文件，原文件保留作为备份。
    """
    print("检查数据库文件位置...")
    
    # 确保data目录存在
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"{_OK} 创建 data 目录")
    
    # 定义需要迁移的文件
    files_to_migrate = [
        ("xianyu_data.db", "data/xianyu_data.db", "主数据库"),
        ("user_stats.db", "data/user_stats.db", "统计数据库"),
    ]
    
    migrated_files = []
    
    # 迁移主数据库和统计数据库
    for old_path, new_path, description in files_to_migrate:
        old_file = Path(old_path)
        new_file = Path(new_path)
        
        if old_file.exists():
            if not new_file.exists():
                # 新位置不存在，移动文件
                try:
                    shutil.move(str(old_file), str(new_file))
                    print(f"{_OK} 迁移{description}: {old_path} -> {new_path}")
                    migrated_files.append(description)
                except Exception as e:
                    print(f"{_WARN} 无法迁移{description}: {e}")
                    print(f"  尝试复制文件...")
                    try:
