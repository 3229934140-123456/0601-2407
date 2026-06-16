# -*- coding: utf-8 -*-
"""
关卡数据加载器模块
Level Data Loader
"""

import json
import os
from typing import Optional, Dict, Any

from .models import (
    Level, Room, Item, Exit, Puzzle, Mechanism,
)


class LevelLoader:
    """关卡数据加载器"""

    @staticmethod
    def load_from_file(file_path: str) -> Optional[Level]:
        """从 JSON 文件加载关卡"""
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return LevelLoader._parse_level(data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"关卡文件加载错误: {e}")
            return None

    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> Optional[Level]:
        """从字典数据加载关卡"""
        try:
            return LevelLoader._parse_level(data)
        except (KeyError, TypeError) as e:
            print(f"关卡数据解析错误: {e}")
            return None

    @staticmethod
    def _parse_level(data: Dict[str, Any]) -> Level:
        """解析关卡数据"""
        level = Level(
            id=data.get('id', 'unknown'),
            name=data.get('name', '未知关卡'),
            description=data.get('description', ''),
            start_room_id=data.get('start_room_id', ''),
            max_hints=data.get('max_hints', 5),
            combine_recipes=data.get('combine_recipes', {}),
        )

        for item_data in data.get('items', []):
            item = LevelLoader._parse_item(item_data)
            level.items[item.id] = item

        for room_data in data.get('rooms', []):
            room = LevelLoader._parse_room(room_data)
            level.rooms[room.id] = room

        return level

    @staticmethod
    def _parse_item(data: Dict[str, Any]) -> Item:
        """解析物品数据"""
        return Item(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            aliases=data.get('aliases', []),
            can_pickup=data.get('can_pickup', True),
            use_with=data.get('use_with', {}),
            use_on=data.get('use_on', {}),
            usable_in_rooms=data.get('usable_in_rooms', []),
            hidden=data.get('hidden', False),
        )

    @staticmethod
    def _parse_room(data: Dict[str, Any]) -> Room:
        """解析房间数据"""
        room = Room(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            items=data.get('items', []),
            is_end=data.get('is_end', False),
            end_message=data.get('end_message', '恭喜你通关了！'),
            hidden=data.get('hidden', False),
        )

        for exit_data in data.get('exits', []):
            exit_obj = LevelLoader._parse_exit(exit_data)
            room.exits[exit_obj.direction] = exit_obj

        for mech_data in data.get('mechanisms', []):
            room.mechanisms.append(LevelLoader._parse_mechanism(mech_data))

        for puzzle_data in data.get('puzzles', []):
            room.puzzles.append(LevelLoader._parse_puzzle(puzzle_data))

        return room

    @staticmethod
    def _parse_exit(data: Dict[str, Any]) -> Exit:
        """解析出口数据"""
        return Exit(
            direction=data['direction'],
            target_room_id=data['target_room_id'],
            description=data.get('description', ''),
            locked=data.get('locked', False),
            lock_reason=data.get('lock_reason', ''),
            unlock_item=data.get('unlock_item'),
            hidden=data.get('hidden', False),
            discover_condition=data.get('discover_condition'),
        )

    @staticmethod
    def _parse_mechanism(data: Dict[str, Any]) -> Mechanism:
        """解析机关数据"""
        return Mechanism(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            trigger_item=data.get('trigger_item'),
            trigger_message=data.get('trigger_message', '机关被触发了！'),
            reveal_exit=data.get('reveal_exit'),
            reveal_item=data.get('reveal_item'),
            unlock_exit=data.get('unlock_exit'),
        )

    @staticmethod
    def _parse_puzzle(data: Dict[str, Any]) -> Puzzle:
        """解析谜题数据"""
        answers = data.get('answers', [])
        if isinstance(answers, str):
            answers = [answers]
        return Puzzle(
            id=data['id'],
            prompt=data.get('prompt', ''),
            answers=answers,
            hint=data.get('hint', ''),
            reward_item=data.get('reward_item'),
            reward_message=data.get('reward_message', '谜题解开了！'),
            unlocks_room=data.get('unlocks_room'),
        )
