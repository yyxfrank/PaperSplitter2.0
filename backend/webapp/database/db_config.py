"""
MySQL 数据库连接配置
=====================
所有连接 MySQL 的模块都从这里读取配置，避免密码散落在各个文件里。
首次使用前请把 `config.py` 复制为 `config.local.py` 并修改密码。
"""
import os
import configparser
from pathlib import Path

# 项目根目录
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

# 数据库配置（默认值）
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "Guo20071116#"),
    "database": os.environ.get("MYSQL_DATABASE", "exam_system"),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "use_pure": True,
}

# 拼接 MySQL 连接 URL（供需要 URL 的库使用）
MYSQL_URL = (
    f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset=utf8mb4"
)
