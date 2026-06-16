# -*- coding: utf-8 -*-
"""
核心数据模型模块
Core Data Models
"""

import json
import copy
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple


DIRECTIONS = {
    'n': 'north', 'north': 'north',
    's': 'south', 'south': 'south',
    'e': 'east', 'east': 'east',
    'w': 'west', 'west': 'west',
    'u': 'up', 'up': 'up',
    'd': 'down', 'down': 'down',
    'ne': 'northeast', 'northeast': 'northeast',
    'nw': 'northwest', 'northwest': 'northwest',
    'se': 'southeast', 'southeast': 'southeast',
    'sw': 'southwest', 'southwest': 'southwest',
}

DIRECTION_NAMES = {
    'north': '北方', 'south': '南方', 'east': '东方', 'west': '西方',
    'up': '上方', 'down': '下方',
    'northeast': '东北方', 'northwest': '西北方',
    'southeast': '东南方', 'southwest': '西南方',
}

DIRECTION_OPPOSITES = {
    'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east',
    'up': 'down', 'down': 'up',
    'northeast': 'southwest', 'northwest': 'southeast',
    'southeast': 'northwest', 'southwest': 'northeast',
}


@dataclass
class Item:
    """物品数据模型"""
    id: str
    name: str
    description: str
    aliases: List[str] = field(default_factory=list)
    can_pickup: bool = True
    use_with: Dict[str, str] = field(default_factory=dict)  # {item_id: result_item_id}
    use_on: Dict[str, str] = field(default_factory=dict)  # {target_id: action_result}
    usable_in_rooms: List[str] = field(default_factory=list)  # 可在哪些房间使用
    hidden: bool = False

    def has_alias(self, name: str) -> bool:
        name_lower = name.lower()
        return (self.name.lower() == name_lower or
                any(alias.lower() == name_lower for alias in self.aliases))


@dataclass
class Exit:
    """房间出口数据模型"""
    direction: str
    target_room_id: str
    description: str = ""
    locked: bool = False
    lock_reason: str = ""
    unlock_item: Optional[str] = None  # 解锁需要的物品ID
    hidden: bool = False  # 隐藏出口，需要特殊条件发现
    discover_condition: Optional[Dict[str, Any]] = None


@dataclass
class Puzzle:
    """谜题数据模型"""
    id: str
    prompt: str
    answers: List[str]  # 多个可能的正确答案
    hint: str = ""
    solved: bool = False
    reward_item: Optional[str] = None  # 解谜奖励物品
    reward_message: str = "谜题解开了！"
    unlocks_room: Optional[str] = None  # 解锁的房间ID


@dataclass
class Mechanism:
    """机关数据模型"""
    id: str
    name: str
    description: str
    triggered: bool = False
    trigger_item: Optional[str] = None  # 触发物品
    trigger_message: str = "机关被触发了！"
    reveal_exit: Optional[str] = None  # 触发后显示的出口方向
    reveal_item: Optional[str] = None  # 触发后出现的物品
    unlock_exit: Optional[str] = None  # 触发后解锁的出口方向


@dataclass
class Room:
    """房间数据模型"""
    id: str
    name: str
    description: str
    exits: Dict[str, Exit] = field(default_factory=dict)
    items: List[str] = field(default_factory=list)  # 物品ID列表
    mechanisms: List[Mechanism] = field(default_factory=list)
    puzzles: List[Puzzle] = field(default_factory=list)
    is_end: bool = False
    end_message: str = "恭喜你通关了！"
    visited: bool = False
    hidden: bool = False  # 隐藏房间

    def get_exit(self, direction: str) -> Optional[Exit]:
        return self.exits.get(direction)

    def has_item(self, item_id: str) -> bool:
        return item_id in self.items

    def remove_item(self, item_id: str):
        if item_id in self.items:
            self.items.remove(item_id)

    def add_item(self, item_id: str):
        if item_id not in self.items:
            self.items.append(item_id)


@dataclass
class Level:
    """关卡数据模型"""
    id: str
    name: str
    description: str
    start_room_id: str
    items: Dict[str, Item] = field(default_factory=dict)
    rooms: Dict[str, Room] = field(default_factory=dict)
    max_hints: int = 5
    combine_recipes: Dict[str, str] = field(default_factory=dict)  # "item1_id+item2_id": result_id

    def get_item(self, item_id: str) -> Optional[Item]:
        return self.items.get(item_id)

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def find_item_by_name(self, name: str) -> Optional[Item]:
        name_lower = name.lower()
        for item in self.items.values():
            if item.id.lower() == name_lower or item.has_alias(name_lower):
                return item
        return None


@dataclass
class GameState:
    """游戏状态快照（用于撤销和存档）"""
    current_room_id: str
    inventory: List[str]
    visited_rooms: List[str]
    notes: List[str]
    hints_used: int
    steps: int
    elapsed_seconds: float
    solved_puzzles: List[str]
    triggered_mechanisms: List[str]
    room_item_states: Dict[str, List[str]]  # 每个房间的物品状态
    exit_states: Dict[str, Dict[str, Dict[str, Any]]]  # room_id -> direction -> state


@dataclass
class ScoreRecord:
    """排行榜记录"""
    player_name: str
    level_id: str
    level_name: str
    score: int
    steps: int
    hints_used: int
    elapsed_seconds: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoreRecord':
        return cls(**data)
