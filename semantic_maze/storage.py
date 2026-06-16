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

from .models import GameState, ScoreRecord, Level, DIRECTION_OPPOSITES


SAVES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'saves')
LEVELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'levels')
LEADERBOARD_FILE = os.path.join(SAVES_DIR, 'leaderboard.json')
LEVEL_PROFILES_FILE = os.path.join(SAVES_DIR, 'level_profiles.json')


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


class LevelProfileManager:
    """关卡探索档案管理器 - 记录每个关卡的累计探索进度和最佳成绩"""

    @staticmethod
    def _ensure_file():
        SaveManager._ensure_dir()
        if not os.path.exists(LEVEL_PROFILES_FILE):
            with open(LEVEL_PROFILES_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_profiles() -> Dict[str, Any]:
        """加载所有关卡档案"""
        LevelProfileManager._ensure_file()
        try:
            with open(LEVEL_PROFILES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def save_profiles(profiles: Dict[str, Any]):
        """保存所有关卡档案"""
        LevelProfileManager._ensure_file()
        try:
            with open(LEVEL_PROFILES_FILE, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存关卡档案失败: {e}")

    @staticmethod
    def get_profile(level_id: str) -> Dict[str, Any]:
        """获取指定关卡的档案"""
        profiles = LevelProfileManager.load_profiles()
        return profiles.get(level_id, {
            'level_id': level_id,
            'play_count': 0,
            'discovered_rooms': [],
            'solved_puzzles': [],
            'best_steps': None,
            'best_time': None,
            'best_score': 0,
            'last_score': None,
            'last_steps': None,
            'last_time': None,
            'completion_count': 0,
        })

    @staticmethod
    def update_profile_on_start(level_id: str, level_name: str = "") -> Dict[str, Any]:
        """开始新游戏时更新档案的累计探索历史"""
        profiles = LevelProfileManager.load_profiles()
        if level_id not in profiles:
            profiles[level_id] = {
                'level_id': level_id,
                'level_name': level_name,
                'play_count': 0,
                'discovered_rooms': [],
                'solved_puzzles': [],
                'best_steps': None,
                'best_time': None,
                'best_score': 0,
                'last_score': None,
                'last_steps': None,
                'last_time': None,
                'completion_count': 0,
            }
        if level_name:
            profiles[level_id]['level_name'] = level_name
        profiles[level_id]['play_count'] += 1
        LevelProfileManager.save_profiles(profiles)
        return profiles[level_id]

    @staticmethod
    def record_discovery(level_id: str, discovered_rooms: List[str],
                         solved_puzzles: List[str]):
        """记录一次游戏中的发现（累计合并）"""
        profiles = LevelProfileManager.load_profiles()
        if level_id not in profiles:
            return
        p = profiles[level_id]
        for rid in discovered_rooms:
            if rid not in p['discovered_rooms']:
                p['discovered_rooms'].append(rid)
        for pid in solved_puzzles:
            if pid not in p['solved_puzzles']:
                p['solved_puzzles'].append(pid)
        LevelProfileManager.save_profiles(profiles)

    @staticmethod
    def update_profile_on_end(level_id: str, steps: int, elapsed: float,
                              score: int) -> Dict[str, Any]:
        """通关时更新最佳成绩，返回比较结果"""
        profiles = LevelProfileManager.load_profiles()
        if level_id not in profiles:
            profiles[level_id] = LevelProfileManager.get_profile(level_id)
        p = profiles[level_id]

        improvements = []
        if p['best_steps'] is None or steps < p['best_steps']:
            if p['best_steps'] is not None:
                improvements.append(('steps', p['best_steps'], steps))
            p['best_steps'] = steps
        if p['best_time'] is None or elapsed < p['best_time']:
            if p['best_time'] is not None:
                improvements.append(('time', p['best_time'], elapsed))
            p['best_time'] = elapsed
        if score > p['best_score']:
            if p['best_score'] > 0:
                improvements.append(('score', p['best_score'], score))
            p['best_score'] = score

        p['last_score'] = score
        p['last_steps'] = steps
        p['last_time'] = elapsed
        p['completion_count'] = p.get('completion_count', 0) + 1

        LevelProfileManager.save_profiles(profiles)
        return {
            'profile': p,
            'improvements': improvements,
            'is_first': p['completion_count'] == 1,
        }

    @staticmethod
    def list_profiles() -> List[Dict[str, Any]]:
        """列出所有有档案的关卡"""
        profiles = LevelProfileManager.load_profiles()
        return sorted(profiles.values(), key=lambda p: p.get('play_count', 0), reverse=True)


class LevelChecker:
    """关卡校验器 - 检查关卡文件的完整性"""

    @staticmethod
    def _load_json(path: str) -> Optional[Dict[str, Any]]:
        if not os.path.exists(path):
            return None, f"文件不存在: {path}"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f), None
        except json.JSONDecodeError as e:
            return None, f"JSON 解析错误: 第{e.lineno}行, {e.msg}"
        except Exception as e:
            return None, f"读取文件失败: {e}"

    @staticmethod
    def check_file(path: str) -> Dict[str, Any]:
        """校验一个关卡文件，返回详细报告"""
        data, err = LevelChecker._load_json(path)
        result = {
            'file': path,
            'valid': False,
            'errors': [],
            'warnings': [],
            'info': [],
        }
        if err:
            result['errors'].append(f"❌ {err}")
            return result

        errors = result['errors']
        warnings = result['warnings']
        info = result['info']

        required_fields = ['id', 'name', 'start_room_id', 'rooms']
        for fld in required_fields:
            if fld not in data:
                errors.append(f"❌ 缺少必需字段: {fld}")
        if errors:
            return result

        level_id = data['id']
        level_name = data['name']
        info.append(f"关卡名: {level_name} (id={level_id})")

        room_ids = set()
        rooms = data.get('rooms', [])
        info.append(f"房间数量: {len(rooms)}")
        for room in rooms:
            rid = room.get('id')
            rname = room.get('name', '(无名称)')
            if not rid:
                errors.append(f"❌ 有一个房间缺少 id 字段 (name={rname})")
                continue
            if rid in room_ids:
                errors.append(f"❌ 房间 id 重复: {rid} ({rname})")
            room_ids.add(rid)

        start_id = data['start_room_id']
        if start_id not in room_ids:
            errors.append(f"❌ 起始房间 '{start_id}' 不存在，共有房间: {sorted(room_ids)}")

        end_count = 0
        for room in rooms:
            rid = room.get('id')
            rname = room.get('name', '(无名称)')
            if room.get('is_end'):
                end_count += 1

            for exit_data in room.get('exits', []):
                target = exit_data.get('target_room_id')
                direction = exit_data.get('direction')
                if not target:
                    errors.append(f"❌ 房间 {rid} 的 {direction} 出口缺少 target_room_id")
                    continue
                if target not in room_ids:
                    errors.append(f"❌ 房间 {rid} 的 {direction} 出口指向不存在的房间: {target}")

            for item_id in room.get('items', []):
                all_items = {it.get('id'): it for it in data.get('items', [])}
                if item_id not in all_items:
                    errors.append(f"❌ 房间 {rid} 里引用了未定义物品: {item_id}")

            for mech in room.get('mechanisms', []):
                for key in ('trigger_item', 'reveal_item'):
                    val = mech.get(key)
                    if val:
                        all_items = {it.get('id') for it in data.get('items', [])}
                        if val not in all_items:
                            errors.append(f"❌ 房间 {rid} 机关 '{mech.get('id','?')}' 的 {key}='{val}' 物品未定义")
                if mech.get('reveal_exit'):
                    ex_dirs = {e.get('direction') for e in room.get('exits', [])}
                    if mech['reveal_exit'] not in ex_dirs:
                        warnings.append(f"⚠️ 房间 {rid} 机关 reveal_exit='{mech['reveal_exit']}' 无对应出口定义")

            for puzzle in room.get('puzzles', []):
                reward = puzzle.get('reward_item')
                if reward:
                    all_items = {it.get('id') for it in data.get('items', [])}
                    if reward not in all_items:
                        errors.append(f"❌ 房间 {rid} 谜题 '{puzzle.get('id','?')}' 奖励物品 '{reward}' 未定义")
                unlock = puzzle.get('unlocks_room')
                if unlock and unlock not in room_ids:
                    warnings.append(f"⚠️ 房间 {rid} 谜题 unlocks_room='{unlock}' 指向不存在的房间")

        items = data.get('items', [])
        item_ids = set()
        for it in items:
            iid = it.get('id')
            if not iid:
                errors.append(f"❌ 有一个物品缺少 id 字段 (name={it.get('name','?')})")
                continue
            if iid in item_ids:
                errors.append(f"❌ 物品 id 重复: {iid} ({it.get('name','?')})")
            item_ids.add(iid)
        info.append(f"物品数量: {len(items)}")

        for recipe, recipe_result in data.get('combine_recipes', {}).items():
            parts = recipe.split('+')
            if len(parts) != 2:
                errors.append(f"❌ 组合配方格式错误: {recipe} (应为 item_a+item_b)")
                continue
            for pid in parts:
                if pid not in item_ids:
                    errors.append(f"❌ 组合配方 {recipe} 中的物品 '{pid}' 未定义")
            if recipe_result not in item_ids:
                errors.append(f"❌ 组合配方 {recipe} 的产出物品 '{recipe_result}' 未定义")

        if end_count == 0:
            errors.append("❌ 没有设置终点房间 (is_end=true)，玩家无法通关")
        elif end_count > 1:
            warnings.append(f"⚠️ 有 {end_count} 个终点房间，请确认是否符合设计意图")
        info.append(f"终点房间数: {end_count}")

        if not errors and start_id in room_ids:
            reachable = LevelChecker._find_reachable(data, start_id)
            end_rooms = [r for r in data['rooms'] if r.get('is_end')]
            for end_room in end_rooms:
                if end_room['id'] not in reachable:
                    errors.append(f"❌ 终点房间 '{end_room.get('name', end_room['id'])}' 从起点无法到达"
                                  f" (注意: 静态连通性检查不考虑机关/锁，请检查初始可通行出口是否有通路)")
        info.append(f"从起点出发的初始可达房间: {len(reachable) if 'reachable' in locals() else 'N/A'}")

        result['valid'] = len(errors) == 0
        return result

    @staticmethod
    def _find_reachable(data: Dict[str, Any], start_id: str) -> set:
        """BFS 计算初始可达房间（忽略锁、隐藏出口的静态连通性）"""
        room_map = {r['id']: r for r in data['rooms']}
        visited = {start_id}
        queue = [start_id]
        while queue:
            cur = queue.pop(0)
            room = room_map.get(cur)
            if not room:
                continue
            for exit_data in room.get('exits', []):
                target = exit_data.get('target_room_id')
                if target and target not in visited:
                    visited.add(target)
                    queue.append(target)
        return visited

    @staticmethod
    def format_report(result: Dict[str, Any]) -> str:
        """把校验结果格式化为可读字符串"""
        lines = []
        lines.append(f"📋 关卡校验报告: {result['file']}")
        lines.append("-" * 60)
        for info in result.get('info', []):
            lines.append(f"  ℹ️  {info}")
        if result.get('warnings'):
            lines.append("")
            for w in result['warnings']:
                lines.append(f"  {w}")
        if result.get('errors'):
            lines.append("")
            for e in result['errors']:
                lines.append(f"  {e}")
        lines.append("")
        if result['valid']:
            lines.append(f"  ✅ 校验通过！关卡可以正常游玩。")
            if result.get('warnings'):
                lines.append(f"  ⚠️  有 {len(result['warnings'])} 个警告，建议检查。")
        else:
            lines.append(f"  ❌ 校验未通过，共 {len(result['errors'])} 个错误。")
        return "\n".join(lines)


class LevelManager:
    """关卡文件管理器 - 扫描 levels 目录"""

    @staticmethod
    def list_level_files() -> List[Dict[str, str]]:
        """列出 levels 目录下的所有关卡文件，返回 [{path, name, size, ...}]"""
        result = []
        if not os.path.exists(LEVELS_DIR):
            return result
        for f in sorted(os.listdir(LEVELS_DIR)):
            if f.lower().endswith('.json'):
                path = os.path.join(LEVELS_DIR, f)
                size_kb = os.path.getsize(path) / 1024
                info = {
                    'path': path,
                    'filename': f,
                    'size_kb': size_kb,
                }
                try:
                    with open(path, 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                    info['level_id'] = data.get('id', '?')
                    info['level_name'] = data.get('name', f[:-5])
                    info['room_count'] = len(data.get('rooms', []))
                except Exception:
                    info['level_id'] = 'N/A'
                    info['level_name'] = f[:-5]
                    info['room_count'] = 0
                result.append(info)
        return result
