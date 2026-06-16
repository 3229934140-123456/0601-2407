# -*- coding: utf-8 -*-
"""
存档与排行榜存储模块
Save & Leaderboard Storage
"""

import json
import os
import pickle
import time
import copy
from typing import List, Optional, Dict, Any

from .models import GameState, ScoreRecord, Level


SAVES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'saves')
LEADERBOARD_FILE = os.path.join(SAVES_DIR, 'leaderboard.json')


class SaveManager:
    """存档管理器"""

    @staticmethod
    def _ensure_dir():
        if not os.path.exists(SAVES_DIR):
            os.makedirs(SAVES_DIR, exist_ok=True)

    @staticmethod
    def list_saves() -> List[str]:
        """列出所有存档文件"""
        SaveManager._ensure_dir()
        saves = []
        for f in os.listdir(SAVES_DIR):
            if f.endswith('.sav'):
                saves.append(f[:-4])
        return sorted(saves)

    @staticmethod
    def save_game(slot_name: str, game_state: GameState, level_id: str,
                  custom_level_path: Optional[str] = None) -> bool:
        """保存游戏"""
        SaveManager._ensure_dir()
        try:
            file_path = os.path.join(SAVES_DIR, f'{slot_name}.sav')
            data = {
                'level_id': level_id,
                'custom_level_path': custom_level_path,
                'saved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'state': {
                    'current_room_id': game_state.current_room_id,
                    'inventory': list(game_state.inventory),
                    'visited_rooms': list(game_state.visited_rooms),
                    'notes': list(game_state.notes),
                    'hints_used': game_state.hints_used,
                    'steps': game_state.steps,
                    'elapsed_seconds': game_state.elapsed_seconds,
                    'solved_puzzles': list(game_state.solved_puzzles),
                    'triggered_mechanisms': list(game_state.triggered_mechanisms),
                    'room_item_states': copy.deepcopy(game_state.room_item_states),
                    'exit_states': copy.deepcopy(game_state.exit_states),
                }
            }
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    @staticmethod
    def load_game(slot_name: str) -> Optional[Dict[str, Any]]:
        """加载存档，返回 (level_id, game_state_dict) 或 None"""
        SaveManager._ensure_dir()
        file_path = os.path.join(SAVES_DIR, f'{slot_name}.sav')
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            return data
        except Exception as e:
            print(f"加载存档失败: {e}")
            return None

    @staticmethod
    def delete_save(slot_name: str) -> bool:
        """删除存档"""
        file_path = os.path.join(SAVES_DIR, f'{slot_name}.sav')
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    @staticmethod
    def get_save_info(slot_name: str) -> Optional[Dict[str, Any]]:
        """获取存档基本信息"""
        data = SaveManager.load_game(slot_name)
        if not data:
            return None
        return {
            'level_id': data.get('level_id', 'unknown'),
            'saved_at': data.get('saved_at', 'unknown'),
            'steps': data.get('state', {}).get('steps', 0),
            'hints_used': data.get('state', {}).get('hints_used', 0),
        }


class LeaderboardManager:
    """排行榜管理器"""

    MAX_RECORDS = 20

    @staticmethod
    def _ensure_file():
        SaveManager._ensure_dir()
        if not os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_records() -> List[ScoreRecord]:
        """加载排行榜记录"""
        LeaderboardManager._ensure_file()
        try:
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [ScoreRecord.from_dict(r) for r in data]
        except Exception:
            return []

    @staticmethod
    def save_records(records: List[ScoreRecord]):
        """保存排行榜记录"""
        LeaderboardManager._ensure_file()
        try:
            with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
                json.dump([r.to_dict() for r in records], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存排行榜失败: {e}")

    @staticmethod
    def add_record(record: ScoreRecord) -> int:
        """添加记录并返回排名 (1-based)，返回 -1 表示未上榜"""
        records = LeaderboardManager.load_records()
        records.append(record)
        records.sort(key=lambda r: r.score, reverse=True)
        rank = -1
        for i, r in enumerate(records):
            if r is record or (r.timestamp == record.timestamp and r.player_name == record.player_name):
                rank = i + 1
                break
        if len(records) > LeaderboardManager.MAX_RECORDS:
            records = records[:LeaderboardManager.MAX_RECORDS]
            if rank > LeaderboardManager.MAX_RECORDS:
                rank = -1
        LeaderboardManager.save_records(records)
        return rank

    @staticmethod
    def get_records_by_level(level_id: Optional[str] = None) -> List[ScoreRecord]:
        """获取排行榜，可按关卡筛选"""
        records = LeaderboardManager.load_records()
        if level_id:
            records = [r for r in records if r.level_id == level_id]
        records.sort(key=lambda r: r.score, reverse=True)
        return records

    @staticmethod
    def calculate_score(steps: int, hints_used: int, elapsed_seconds: float,
                        solved_puzzles: int, discovered_rooms: int,
                        total_rooms: int, total_puzzles: int) -> int:
        """计算通关分数"""
        base_score = 10000

        step_penalty = steps * 10
        hint_penalty = hints_used * 500
        time_penalty = int(elapsed_seconds) * 2

        puzzle_bonus = solved_puzzles * 500 if total_puzzles > 0 else 0
        exploration_bonus = int((discovered_rooms / max(total_rooms, 1)) * 2000)

        score = base_score - step_penalty - hint_penalty - time_penalty + puzzle_bonus + exploration_bonus
        return max(score, 0)
