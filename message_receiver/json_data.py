import json
import os
import logging
from typing import Dict, Any


def load_data(file_path: str) -> Dict[str, Any]:
    """
    从指定JSON文件加载数据

    Args:
        file_path: 数据文件路径

    Returns:
        加载的数据字典
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"加载数据文件 {file_path} 时出错: {e}")
            return {}
    return {}


def save_data(file_path: str, data: Dict[str, Any]) -> bool:
    """
    将数据保存到指定JSON文件

    Args:
        data: 要保存的数据
        file_path: 数据文件路径

    Returns:
        操作是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        logging.error(f"保存数据到 {file_path} 时出错: {e}")
        return False
