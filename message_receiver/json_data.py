import json
import os
import logging


def load_data(file_path: str) -> dict[str, any]:
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


def save_data(file_path: str, data: dict[str, any]) -> bool:
    """
    将数据保存到指定JSON文件

    Args:
        data: 要保存的数据
        file_path: 数据文件路径

    Returns:
        操作是否成功
    """
    try:
        # 获取文件的绝对路径
        abs_file_path = os.path.abspath(file_path)
        dir_name = os.path.dirname(abs_file_path)

        # 确保目录存在（只有非空目录名才创建）
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            logging.info(f"创建目录 {dir_name}")
        else:
            # 如果没有目录部分，则使用当前目录
            dir_name = '.'

        with open(abs_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        logging.error(f"保存数据到 {file_path} 时出错: {e}")
        return False
