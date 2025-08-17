import logging
import time
from threading import Thread

from json_data import save_data, load_data


class CharacterInfo:
    name: str
    max_hp: int = 0
    current_hp: int = 0
    skills: dict[str, int] = {}

    def __init__(self, name: str) -> None:
        self.name = name

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "skills": self.skills
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CharacterInfo':
        character = cls(data["name"])
        character.max_hp = data.get("max_hp", 0)
        character.current_hp = data.get("current_hp", 0)
        character.skills = data.get("skills", {})
        return character

    def set_max_hp(self, max_hp: int) -> None:
        self.max_hp = max_hp

    def set_hp(self, current_hp: int) -> None:
        if current_hp > self.max_hp:
            current_hp = self.max_hp
        self.current_hp = current_hp

    def get_current_hp(self) -> int:
        return self.current_hp

    def get_max_hp(self) -> int:
        return self.max_hp

    def get_skill_value(self, skill_name: str) -> int:
        if skill_name in self.skills:
            return self.skills[skill_name]
        return 0

    def set_skill_value(self, skill_name: str, value: int) -> None:
        self.skills[skill_name] = value

    def remove_skill(self, skill_name: str) -> None:
        if skill_name in self.skills:
            del self.skills[skill_name]


class UserInfo:
    user_id: int
    nickname: str
    # 点数
    points: int = 0
    # 上次获取点数的时间，以纳秒为单位
    last_point_get_time: int = 0
    # 幸运点数
    lucky_points: int = 50
    # 上次检查幸运点数时间，以纳秒为单位
    last_lucky_point_check_time: int = 0
    characters: dict[str, CharacterInfo] = {}
    current_character_name: str or None = None

    def __init__(self, user_id: int, nickname: str) -> None:
        self.user_id = user_id
        self.nickname = nickname

    def file_path(self) -> str:
        return f"users/{self.user_id}.json"

    def sync_to_file(self) -> None:
        characters_dict = {name: char.to_dict() for name, char in self.characters.items()}
        save_data(self.file_path(), {
            "nickname": self.nickname,
            "points": self.points,
            "last_point_get_time": self.last_point_get_time,
            "lucky_points": self.lucky_points,
            "last_lucky_point_check_time": self.last_lucky_point_check_time,
            "characters": characters_dict,
            "current_character_name": self.current_character_name,
        })

    def sync_from_file(self) -> None:
        data = load_data(self.file_path())
        self.nickname = data.get("nickname", self.nickname)
        self.points = data.get("points", self.points)
        self.last_point_get_time = data.get("last_point_get_time", self.last_point_get_time)
        self.lucky_points = data.get("lucky_points", self.lucky_points)
        self.last_lucky_point_check_time = data.get("last_lucky_point_check_time", self.last_lucky_point_check_time)
        characters_data = data.get("characters", {})
        self.characters = {name: CharacterInfo.from_dict(char_data) for name, char_data in characters_data.items()}
        self.current_character_name = data.get("current_character_name", self.current_character_name)

    def increase_points(self, points: int) -> None:
        self.points += points

    def decrease_points(self, points: int) -> None:
        self.points -= points

    def set_current_character(self, character_name: str) -> None:
        if character_name not in self.characters:
            self.characters[character_name] = CharacterInfo(character_name)
        self.current_character_name = character_name

    def get_current_character_info(self) -> CharacterInfo or None:
        if self.current_character_name is None:
            return None
        if self.current_character_name not in self.characters:
            return None
        return self.characters[self.current_character_name]

    def get_character_info(self, character_name: str) -> CharacterInfo or None:
        if character_name not in self.characters:
            return None
        return self.characters[character_name]

    def remove_character(self, character_name: str) -> None:
        if self.current_character_name == character_name:
            self.current_character_name = None
        if character_name in self.characters:
            del self.characters[character_name]


class UserInfoStore:
    """
    用户信息管理类
    维护用户信息字典，定期保存到文件并清理长时间未使用的用户信息
    """
    user_dict: dict[int, UserInfo] = {}
    last_access_time: dict[int, float] = {}
    running: bool
    clean_thread: Thread

    def __init__(self) -> None:
        # 清理线程运行标志
        self.running = True
        # 启动后台清理线程
        self.clean_thread = Thread(target=self._clean_save_loop, daemon=True)
        self.clean_thread.start()

    def get_user(self, user_id: int, nickname: str) -> UserInfo:
        """
        获取用户信息，如果不存在则创建新用户
        更新用户的最后访问时间
        """
        if user_id not in self.user_dict:
            user = UserInfo(user_id, nickname)
            user.sync_from_file()
            self.user_dict[user_id] = user
            self.last_access_time[user_id] = time.time()
        else:
            user = self.user_dict[user_id]
            self.last_access_time[user_id] = time.time()
        return user

    def save_all_users(self) -> None:
        """
        将所有用户信息保存到文件
        """
        for user in self.user_dict.values():
            try:
                user.sync_to_file()
            except Exception as e:
                logging.error(f"保存用户 {user} 时出错: {e}")

    def _clean_save_loop(self) -> None:
        """
        后台清理循环，定期检查并清理长时间未访问的用户信息
        """
        while self.running:
            time.sleep(60)  # 每20秒检查一次
            self.save_all_users()
            self._clean_expired_users()

    def _clean_expired_users(self) -> None:
        """
        清理超过1小时未访问的用户信息
        """
        current_time = time.time()
        expired_users = []

        # 找出超过一段时间未访问的用户
        for user_id, last_access in self.last_access_time.items():
            if current_time - last_access > 3600:  # 3600秒
                expired_users.append(user_id)

        # 保存并移除过期用户
        for user_id in expired_users:
            del self.user_dict[user_id]
            del self.last_access_time[user_id]

    def stop(self) -> None:
        """
        停止清理线程并保存所有用户数据
        """
        self.running = False
        self.save_all_users()
        logging.info(f"用户信息存储已关闭")
