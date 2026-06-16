# -*- coding: utf-8 -*-
"""
核心游戏引擎模块
Core Game Engine
"""

import os
import sys
import time
import copy
import json
from typing import List, Optional, Dict, Any, Tuple
from collections import deque

from .models import (
    Level, Room, Item, Exit, Puzzle, Mechanism, GameState, ScoreRecord,
    DIRECTIONS, DIRECTION_NAMES, DIRECTION_OPPOSITES,
)
from .level_loader import LevelLoader
from .storage import SaveManager, LeaderboardManager, LevelProfileManager, LevelChecker, LevelManager
from . import ui
from .ui import c
from . import default_level


class Game:
    """语义迷宫游戏主类"""

    MAX_UNDO_STEPS = 50

    def __init__(self):
        self.level: Optional[Level] = None
        self.current_room_id: str = ""
        self.inventory: List[str] = []
        self.visited_rooms: List[str] = []
        self.notes: List[str] = []
        self.hints_used: int = 0
        self.steps: int = 0
        self.start_time: float = 0.0
        self.elapsed_before_pause: float = 0.0
        self.is_playing: bool = False
        self.game_finished: bool = False
        self.history: deque = deque(maxlen=self.MAX_UNDO_STEPS)
        self.custom_level_path: Optional[str] = None

    def run(self):
        """游戏主循环"""
        ui.banner()

        while True:
            try:
                if self.is_playing and not self.game_finished:
                    prompt = "语义迷宫 > "
                else:
                    prompt = "语义迷宫 (主菜单) > "

                raw_input = input(prompt).strip()
                if not raw_input:
                    continue

                self._process_command(raw_input)

            except (EOFError, KeyboardInterrupt):
                print()
                ui.info("再见！感谢游玩语义迷宫。")
                break

    def _process_command(self, raw_input: str):
        """解析并执行命令"""
        parts = raw_input.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in DIRECTIONS:
            self._cmd_move(cmd)
            return

        command_map = {
            'start': self._cmd_start,
            'new': self._cmd_start,
            'load': self._cmd_load,
            'loadlevel': self._cmd_load_level,
            'save': self._cmd_save,
            'quit': self._cmd_quit,
            'exit': self._cmd_quit,
            'help': self._cmd_help,
            '?': self._cmd_help,
            'look': self._cmd_look,
            'l': self._cmd_look,
            'examine': self._cmd_look,
            'x': self._cmd_look,
            'move': self._cmd_move,
            'go': self._cmd_move,
            'walk': self._cmd_move,
            'map': self._cmd_map,
            'take': self._cmd_take,
            'get': self._cmd_take,
            'pick': self._cmd_take,
            'grab': self._cmd_take,
            'drop': self._cmd_drop,
            'inventory': self._cmd_inventory,
            'inv': self._cmd_inventory,
            'i': self._cmd_inventory,
            'bag': self._cmd_inventory,
            'use': self._cmd_use,
            'combine': self._cmd_combine,
            'merge': self._cmd_combine,
            'answer': self._cmd_answer,
            'solve': self._cmd_answer,
            'ans': self._cmd_answer,
            'note': self._cmd_note,
            'notes': self._cmd_notes,
            'hint': self._cmd_hint,
            'undo': self._cmd_undo,
            'rank': self._cmd_rank,
            'leaderboard': self._cmd_rank,
            'status': self._cmd_status,
            'saves': self._cmd_saves,
            'ls': self._cmd_saves,
            'clear': self._cmd_clear,
            'cls': self._cmd_clear,
            'checklevel': self._cmd_checklevel,
            'check': self._cmd_checklevel,
            'profile': self._cmd_profiles,
            'profiles': self._cmd_profiles,
            'stats': self._cmd_profiles,
        }

        handler = command_map.get(cmd)
        if handler:
            handler(args)
        else:
            ui.error(f"未知命令: {cmd}。输入 'help' 查看命令列表。")

    def _require_playing(self) -> bool:
        """检查是否正在游戏中"""
        if not self.is_playing or not self.level:
            ui.error("请先使用 'start' 开始新游戏或 'load' 读取存档。")
            return False
        if self.game_finished:
            ui.warn("游戏已经结束，请使用 'start' 开始新游戏。")
            return False
        return True

    def _get_current_room(self) -> Optional[Room]:
        """获取当前房间"""
        if not self.level:
            return None
        return self.level.get_room(self.current_room_id)

    def _get_inventory_items(self) -> List[Item]:
        """获取背包中的物品对象列表"""
        if not self.level:
            return []
        items = []
        for item_id in self.inventory:
            item = self.level.get_item(item_id)
            if item:
                items.append(item)
        return items

    def _find_item_in_inventory(self, name: str) -> Optional[Item]:
        """在背包中按名称或ID查找物品"""
        name_lower = name.lower()
        for item in self._get_inventory_items():
            if item.id.lower() == name_lower or item.has_alias(name_lower):
                return item
        return None

    def _find_item_in_room(self, name: str) -> Optional[Item]:
        """在当前房间按名称或ID查找物品"""
        room = self._get_current_room()
        if not room or not self.level:
            return None
        name_lower = name.lower()
        for item_id in room.items:
            item = self.level.get_item(item_id)
            if item and not item.hidden:
                if item.id.lower() == name_lower or item.has_alias(name_lower):
                    return item
        return None

    def _save_snapshot(self):
        """保存当前状态快照（用于撤销）"""
        if not self.level:
            return
        state = self._collect_state()
        self.history.append(state)

    def _get_elapsed(self) -> float:
        """获取已用时间（秒）"""
        if self.start_time <= 0:
            return self.elapsed_before_pause
        return self.elapsed_before_pause + (time.time() - self.start_time)

    def _start_timer(self):
        """开始计时"""
        self.start_time = time.time()

    def _pause_timer(self):
        """暂停计时"""
        if self.start_time > 0:
            self.elapsed_before_pause += time.time() - self.start_time
            self.start_time = 0

    def _total_rooms(self) -> int:
        if not self.level:
            return 0
        return len([r for r in self.level.rooms.values() if not r.hidden])

    def _total_puzzles(self) -> int:
        if not self.level:
            return 0
        count = 0
        for room in self.level.rooms.values():
            count += len(room.puzzles)
        return count

    def _solved_puzzles_count(self) -> int:
        if not self.level:
            return 0
        count = 0
        for room in self.level.rooms.values():
            for p in room.puzzles:
                if p.solved:
                    count += 1
        return count

    def _check_end(self, room: Room) -> bool:
        """检查是否到达终点"""
        if room.is_end:
            self._pause_timer()
            self.game_finished = True
            self._handle_end_game()
            return True
        return False

    # ===== 命令实现 =====

    def _cmd_start(self, args: str):
        """开始新游戏"""
        ui.clear_screen()

        if args and os.path.exists(args):
            self._start_custom_level(args)
            return

        custom_levels = LevelManager.list_level_files()

        ui.title("开始新游戏")
        print("  请选择关卡:")
        print(c("    1. ", ui.Color.YELLOW) + "默认关卡：古老图书馆的秘密" +
              c("  (内置)", ui.Color.DIM))
        idx = 2
        for lv in custom_levels:
            room_info = f"{lv.get('room_count', 0)}房间"
            size_info = f"{lv.get('size_kb', 0):.1f}KB"
            name_display = lv.get('level_name', lv['filename'])
            print(c(f"    {idx}. ", ui.Color.YELLOW) + f"{name_display}" +
                  c(f"  [{lv['filename']}] ({room_info}, {size_info})", ui.Color.DIM))
            idx += 1
        print()

        choice = input("  选择 [1]: ").strip() or "1"

        if choice == "1":
            level_data = default_level.get_default_level()
            self.level = LevelLoader.load_from_dict(level_data)
            self.custom_level_path = None
        elif choice.isdigit():
            ci = int(choice)
            if 2 <= ci < idx:
                lv = custom_levels[ci - 2]
                self._start_custom_level(lv['path'])
                return
            else:
                ui.error("无效的选择编号。")
                return
        elif os.path.exists(choice):
            self._start_custom_level(choice)
            return
        else:
            ui.error("无效的输入，请输入关卡编号或文件路径。")
            return

        if not self.level:
            result = LevelChecker.check_file(os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "semantic_maze", "default_level.py"
            ))
            ui.error(f"默认关卡加载失败: {result.get('errors', ['未知错误'])[0]}")
            return

        self._init_new_game()

    def _start_custom_level(self, file_path: str):
        """从自定义文件开始新游戏"""
        check_result = LevelChecker.check_file(file_path)
        if not check_result['valid']:
            ui.warn("检测到关卡存在问题:")
            for err in check_result['errors'][:5]:
                ui.error(err.replace("❌ ", "", 1))
            if len(check_result['errors']) > 5:
                ui.warn(f"还有 {len(check_result['errors']) - 5} 个错误未显示")
            ui.warn("继续尝试加载...")

        self.level = LevelLoader.load_from_file(file_path)
        if not self.level:
            ui.separator()
            ui.error("关卡加载失败！以下是问题详情：")
            print(LevelChecker.format_report(check_result))
            return

        if not check_result['valid']:
            ui.warn(f"关卡已加载，但仍存在 {len(check_result['errors'])} 个错误，游玩中可能遇到问题。")

        self.custom_level_path = file_path
        self._init_new_game()

    def _init_new_game(self):
        """初始化新游戏状态"""
        self.current_room_id = self.level.start_room_id
        self.inventory = []
        self.visited_rooms = []
        self.notes = []
        self.hints_used = 0
        self.steps = 0
        self.elapsed_before_pause = 0.0
        self.is_playing = True
        self.game_finished = False
        self.history.clear()

        for room in self.level.rooms.values():
            room.visited = False
            for p in room.puzzles:
                p.solved = False
            for m in room.mechanisms:
                m.triggered = False

        self._start_timer()

        profile = LevelProfileManager.update_profile_on_start(self.level.id, self.level.name)
        if profile.get('completion_count', 0) > 0:
            ui.hint(f"这是你第 {profile['play_count']} 次挑战此关。")
            best = profile.get('best_score', 0)
            if best:
                self._format_time = lambda s: (
                    f"{int(s//60)}分{int(s%60)}秒" if s < 3600
                    else f"{int(s//3600)}时{int(s%3600//60)}分"
                )
                best_steps = profile.get('best_steps')
                best_time = profile.get('best_time')
                best_str = f"最佳得分 {best}"
                if best_steps:
                    best_str += f" | 最少步数 {best_steps}"
                if best_time:
                    best_str += f" | 最快用时 {self._format_time(best_time)}"
                ui.info(f"历史纪录: {best_str}")
                ui.info("加油，看看能否刷新纪录！")
        elif profile.get('play_count', 1) == 1:
            ui.hint("首次挑战此关卡，祝你好运！")

        ui.title(f"{self.level.name}")
        if self.level.description:
            ui.story(self.level.description)

        self._visit_room(self.current_room_id, show_desc=True)

    def _cmd_load_level(self, args: str):
        """加载自定义关卡文件并开始新游戏"""
        if not args:
            ui.error("请指定关卡 JSON 文件路径。用法: loadlevel <文件路径>")
            return
        if not os.path.exists(args):
            ui.error(f"文件不存在: {args}")
            return
        self._start_custom_level(args)

    def _cmd_load(self, args: str):
        """读取存档"""
        saves = SaveManager.list_saves()
        if not saves:
            ui.info("暂无存档。")
            return

        if not args:
            ui.display_saves(saves, SaveManager.get_save_info)
            choice = input("  选择要加载的存档编号或名称: ").strip()
            if not choice:
                return
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(saves):
                    args = saves[idx]
                else:
                    ui.error("无效的编号。")
                    return
            else:
                args = choice

        data = SaveManager.load_game(args)
        if not data:
            ui.error(f"无法加载存档: {args}")
            return

        level_id = data.get('level_id')
        state_dict = data.get('state')
        custom_level_path = data.get('custom_level_path')
        if not level_id or not state_dict:
            ui.error("存档数据损坏。")
            return

        if custom_level_path:
            if not os.path.exists(custom_level_path):
                ui.error(f"存档关联的自定义关卡文件不存在: {custom_level_path}")
                return
            self.level = LevelLoader.load_from_file(custom_level_path)
            self.custom_level_path = custom_level_path
        else:
            level_data = default_level.get_default_level()
            self.level = LevelLoader.load_from_dict(level_data)
            self.custom_level_path = None

        if not self.level or self.level.id != level_id:
            ui.error(f"存档关卡不匹配 (期望 {level_id}，实际 {self.level.id if self.level else 'None'})。")
            return

        self._restore_state(state_dict)
        self.is_playing = True
        self.game_finished = False
        self._start_timer()

        ui.success(f"已加载存档: {args}")
        self._visit_room(self.current_room_id, show_desc=True)

    def _restore_state(self, state_dict: Dict[str, Any]):
        """从存档字典恢复状态"""
        self.current_room_id = state_dict.get('current_room_id', self.level.start_room_id)
        self.inventory = list(state_dict.get('inventory', []))
        self.visited_rooms = list(state_dict.get('visited_rooms', []))
        self.notes = list(state_dict.get('notes', []))
        self.hints_used = state_dict.get('hints_used', 0)
        self.steps = state_dict.get('steps', 0)
        self.elapsed_before_pause = state_dict.get('elapsed_seconds', 0.0)

        solved_puzzles = set(state_dict.get('solved_puzzles', []))
        triggered_mechanisms = set(state_dict.get('triggered_mechanisms', []))
        for room in self.level.rooms.values():
            room.visited = room.id in self.visited_rooms
            for p in room.puzzles:
                p.solved = p.id in solved_puzzles
            for m in room.mechanisms:
                m.triggered = m.id in triggered_mechanisms

        room_item_states = state_dict.get('room_item_states', {})
        for room_id, items in room_item_states.items():
            room = self.level.get_room(room_id)
            if room:
                room.items = list(items)

        exit_states = state_dict.get('exit_states', {})
        for room_id, exits in exit_states.items():
            room = self.level.get_room(room_id)
            if not room:
                continue
            for direction, state in exits.items():
                exit_obj = room.get_exit(direction)
                if exit_obj:
                    exit_obj.locked = state.get('locked', exit_obj.locked)
                    exit_obj.hidden = state.get('hidden', exit_obj.hidden)

        self.history.clear()

    def _collect_state(self) -> GameState:
        """收集当前完整游戏状态"""
        room_item_states = {}
        for room_id, room in self.level.rooms.items():
            room_item_states[room_id] = list(room.items)

        exit_states = {}
        for room_id, room in self.level.rooms.items():
            exit_states[room_id] = {}
            for direction, exit_obj in room.exits.items():
                exit_states[room_id][direction] = {
                    'locked': exit_obj.locked,
                    'hidden': exit_obj.hidden,
                }

        solved_puzzles = []
        triggered_mechanisms = []
        for room in self.level.rooms.values():
            for p in room.puzzles:
                if p.solved:
                    solved_puzzles.append(p.id)
            for m in room.mechanisms:
                if m.triggered:
                    triggered_mechanisms.append(m.id)

        return GameState(
            current_room_id=self.current_room_id,
            inventory=list(self.inventory),
            visited_rooms=list(self.visited_rooms),
            notes=list(self.notes),
            hints_used=self.hints_used,
            steps=self.steps,
            elapsed_seconds=self._get_elapsed(),
            solved_puzzles=solved_puzzles,
            triggered_mechanisms=triggered_mechanisms,
            room_item_states=room_item_states,
            exit_states=exit_states,
        )

    def _cmd_save(self, args: str):
        """保存游戏"""
        if not self._require_playing():
            return

        if not args:
            saves = SaveManager.list_saves()
            if saves:
                ui.display_saves(saves, SaveManager.get_save_info)
            default_name = f"save_{int(time.time())}"
            args = input(f"  存档名称 [{default_name}]: ").strip() or default_name

        state = self._collect_state()

        if SaveManager.save_game(args, state, self.level.id, self.custom_level_path):
            ui.success(f"游戏已保存为: {args}")
        else:
            ui.error("保存失败。")

    def _cmd_quit(self, args: str):
        """退出游戏"""
        if self.is_playing and not self.game_finished:
            confirm = input("  游戏进行中，确定要退出吗？(y/N): ").strip().lower()
            if confirm not in ('y', 'yes'):
                return
        ui.info("再见！感谢游玩语义迷宫。")
        sys.exit(0)

    def _cmd_help(self, args: str):
        """显示帮助"""
        ui.display_help()

    def _cmd_look(self, args: str):
        """查看房间或物品"""
        if not self._require_playing():
            return

        if not args:
            room = self._get_current_room()
            if room:
                ui.display_room(room, self.level)
            return

        target = args.strip()
        item = self._find_item_in_inventory(target) or self._find_item_in_room(target)
        if item:
            ui.section(f"查看: {item.name}")
            ui.story(item.description)
            return

        room = self._get_current_room()
        for mech in room.mechanisms:
            if mech.name.lower() == target.lower() or target.lower() in mech.name.lower():
                ui.section(f"查看机关: {mech.name}")
                ui.story(mech.description)
                if mech.trigger_item:
                    trigger_item = self.level.get_item(mech.trigger_item)
                    if trigger_item:
                        ui.hint(f"也许可以用 {trigger_item.name} 试试？")
                return

        ui.error(f"这里没有 '{target}'。")

    def _visit_room(self, room_id: str, show_desc: bool = True):
        """访问一个房间"""
        room = self.level.get_room(room_id)
        if not room:
            return

        first_visit = room_id not in self.visited_rooms
        if first_visit:
            self.visited_rooms.append(room_id)
            room.visited = True
            LevelProfileManager.record_discovery(
                self.level.id, [room_id], [p.id for p in room.puzzles if p.solved]
            )

        if show_desc:
            ui.display_room(room, self.level, first_visit=first_visit)

        self._check_end(room)

    def _cmd_move(self, args: str):
        """向某个方向移动"""
        if not self._require_playing():
            return

        if not args:
            ui.error("请指定方向。用法: move <n/s/e/w/u/d/ne/nw/se/sw>")
            return

        parts = args.split()
        direction_key = parts[0].lower()
        direction = DIRECTIONS.get(direction_key)

        if not direction:
            ui.error(f"无效的方向: {direction_key}")
            return

        room = self._get_current_room()
        if not room:
            return

        exit_obj = room.get_exit(direction)
        if not exit_obj or exit_obj.hidden:
            dir_name = DIRECTION_NAMES.get(direction, direction)
            ui.error(f"{dir_name}没有出口。")
            return

        if exit_obj.locked:
            dir_name = DIRECTION_NAMES.get(direction, direction)
            if exit_obj.unlock_item and exit_obj.unlock_item in self.inventory:
                self._save_snapshot()
                exit_obj.locked = False
                unlock_item = self.level.get_item(exit_obj.unlock_item)
                ui.success(f"你使用 {unlock_item.name} 打开了{dir_name}的通道！")
                self.steps += 1
            else:
                reason = exit_obj.lock_reason or "通道被锁住了。"
                ui.warn(f"{dir_name}: {reason}")
                if exit_obj.unlock_item:
                    unlock_item = self.level.get_item(exit_obj.unlock_item)
                    if unlock_item:
                        ui.hint(f"需要 {unlock_item.name} 才能打开。")
                return

        self._save_snapshot()
        self.current_room_id = exit_obj.target_room_id
        self.steps += 1
        self._visit_room(self.current_room_id, show_desc=True)

    def _cmd_map(self, args: str):
        """显示地图"""
        if not self._require_playing():
            return
        ui.display_map(self.level, self.current_room_id, self.visited_rooms)

    def _cmd_take(self, args: str):
        """拾取物品"""
        if not self._require_playing():
            return
        if not args:
            ui.error("请指定要拾取的物品。用法: take <物品名>")
            return

        item = self._find_item_in_room(args.strip())
        if not item:
            ui.error(f"这里没有 '{args}'。")
            return
        if not item.can_pickup:
            ui.warn(f"{item.name} 无法被拾取。")
            return

        self._save_snapshot()
        room = self._get_current_room()
        room.remove_item(item.id)
        self.inventory.append(item.id)
        self.steps += 1
        ui.success(f"你拾取了 {item.name}。")

    def _cmd_drop(self, args: str):
        """丢弃物品"""
        if not self._require_playing():
            return
        if not args:
            ui.error("请指定要丢弃的物品。用法: drop <物品名>")
            return

        item = self._find_item_in_inventory(args.strip())
        if not item:
            ui.error(f"你的背包里没有 '{args}'。")
            return

        self._save_snapshot()
        self.inventory.remove(item.id)
        room = self._get_current_room()
        room.add_item(item.id)
        self.steps += 1
        ui.success(f"你放下了 {item.name}。")

    def _cmd_inventory(self, args: str):
        """查看背包"""
        if not self._require_playing():
            return
        ui.display_inventory(self._get_inventory_items())

    def _cmd_use(self, args: str):
        """使用物品"""
        if not self._require_playing():
            return
        if not args:
            ui.error("请指定要使用的物品。用法: use <物品> 或 use <A> with <B>")
            return

        parts = args.lower().split(' with ')
        if len(parts) == 2:
            self._use_item_on(parts[0].strip(), parts[1].strip())
            return

        item_name = args.strip()
        item = self._find_item_in_inventory(item_name)
        if not item:
            ui.error(f"你的背包里没有 '{item_name}'。")
            return

        self._save_snapshot()

        room = self._get_current_room()

        if item.usable_in_rooms and room.id not in item.usable_in_rooms:
            ui.warn(f"{item.name} 在这里似乎没有用处。")
            self.history.pop()
            return

        used = False

        for mech in room.mechanisms:
            if not mech.triggered and mech.trigger_item == item.id:
                mech.triggered = True
                ui.success(mech.trigger_message)
                if mech.reveal_item:
                    room.add_item(mech.reveal_item)
                    reveal_item = self.level.get_item(mech.reveal_item)
                    if reveal_item:
                        ui.info(f"出现了: {reveal_item.name}")
                if mech.reveal_exit and mech.reveal_exit in room.exits:
                    room.exits[mech.reveal_exit].hidden = False
                    ui.info("你发现了一个新的出口！")
                if mech.unlock_exit and mech.unlock_exit in room.exits:
                    room.exits[mech.unlock_exit].locked = False
                    ui.info("某个出口的锁被打开了！")
                used = True
                break

        for direction, exit_obj in room.exits.items():
            if exit_obj.locked and exit_obj.unlock_item == item.id:
                exit_obj.locked = False
                dir_name = DIRECTION_NAMES.get(direction, direction)
                ui.success(f"你用 {item.name} 打开了{dir_name}的通道！")
                used = True
                break

        if not used:
            if item.use_on:
                for target_id, result in item.use_on.items():
                    if room.id == target_id or target_id in room.items:
                        ui.success(result)
                        used = True
                        break

        if not used:
            ui.warn(f"{item.name} 在这里似乎没有什么反应。")
            self.history.pop()
            return

        self.steps += 1

    def _use_item_on(self, a_name: str, b_name: str):
        """把物品A用在物品B上"""
        item_a = self._find_item_in_inventory(a_name)
        if not item_a:
            ui.error(f"你的背包里没有 '{a_name}'。")
            return

        item_b = self._find_item_in_inventory(b_name) or self._find_item_in_room(b_name)
        if not item_b:
            ui.error(f"找不到 '{b_name}'。")
            return

        if item_a.id in item_b.use_with or item_b.id in item_a.use_with:
            self._save_snapshot()

            recipe1 = f"{item_a.id}+{item_b.id}"
            recipe2 = f"{item_b.id}+{item_a.id}"
            result_id = self.level.combine_recipes.get(recipe1) or self.level.combine_recipes.get(recipe2)

            if result_id:
                self.inventory.remove(item_a.id)
                if item_b.id in self.inventory:
                    self.inventory.remove(item_b.id)
                else:
                    room = self._get_current_room()
                    room.remove_item(item_b.id)
                self.inventory.append(result_id)
                result_item = self.level.get_item(result_id)
                ui.success(f"你将 {item_a.name} 和 {item_b.name} 组合成了 {result_item.name}！")
                self.steps += 1
                return

        ui.warn(f"{item_a.name} 和 {item_b.name} 似乎不能这样组合。")

    def _cmd_combine(self, args: str):
        """组合两个物品"""
        if not self._require_playing():
            return
        if not args:
            ui.error("请指定两个物品。用法: combine <物品A> <物品B>")
            return

        parts = args.split()
        if len(parts) < 2:
            ui.error("请指定两个物品。用法: combine <物品A> <物品B>")
            return

        item_a = self._find_item_in_inventory(parts[0])
        item_b = self._find_item_in_inventory(parts[1])

        if not item_a:
            ui.error(f"你的背包里没有 '{parts[0]}'。")
            return
        if not item_b:
            ui.error(f"你的背包里没有 '{parts[1]}'。")
            return

        recipe1 = f"{item_a.id}+{item_b.id}"
        recipe2 = f"{item_b.id}+{item_a.id}"
        result_id = self.level.combine_recipes.get(recipe1) or self.level.combine_recipes.get(recipe2)

        if not result_id:
            ui.warn(f"{item_a.name} 和 {item_b.name} 无法组合。")
            return

        self._save_snapshot()
        self.inventory.remove(item_a.id)
        self.inventory.remove(item_b.id)
        self.inventory.append(result_id)
        result_item = self.level.get_item(result_id)
        ui.success(f"你将 {item_a.name} 和 {item_b.name} 组合成了 {result_item.name}！")
        self.steps += 1

    def _cmd_answer(self, args: str):
        """输入谜题答案"""
        if not self._require_playing():
            return
        if not args:
            ui.error("请输入答案。用法: answer <答案>")
            return

        room = self._get_current_room()
        unsolved = [p for p in room.puzzles if not p.solved]

        if not unsolved:
            ui.info("这里没有需要解答的谜题。")
            return

        answer = args.strip().lower()
        for puzzle in unsolved:
            if answer in [a.lower() for a in puzzle.answers]:
                self._save_snapshot()
                puzzle.solved = True
                ui.success(puzzle.reward_message)
                if puzzle.reward_item:
                    self.inventory.append(puzzle.reward_item)
                    reward_item = self.level.get_item(puzzle.reward_item)
                    if reward_item:
                        ui.info(f"你获得了: {reward_item.name}")
                if puzzle.unlocks_room:
                    for direction, exit_obj in room.exits.items():
                        if exit_obj.target_room_id == puzzle.unlocks_room:
                            exit_obj.locked = False
                            exit_obj.hidden = False
                            dir_name = DIRECTION_NAMES.get(direction, direction)
                            ui.info(f"{dir_name}的通道被解锁了！")
                self.steps += 1
                return

        ui.warn("答案不正确，再想想？")

    def _cmd_note(self, args: str):
        """记录笔记 / 删除笔记 / 搜索笔记"""
        if not self._require_playing():
            return

        if not args:
            ui.error("用法: note <内容> 添加笔记, note del <编号> 删除, note search <关键词> 搜索")
            ui.info("查看所有笔记: notes 或 note list")
            return

        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower()

        if subcmd == 'list' or subcmd == 'ls':
            self._cmd_notes(parts[1] if len(parts) > 1 else '')
            return

        if subcmd == 'del' or subcmd == 'delete' or subcmd == 'rm' or subcmd == 'remove':
            target = parts[1].strip() if len(parts) > 1 else ""
            if not target or not target.isdigit():
                ui.error("请指定要删除的笔记编号。用法: note del <编号>")
                return
            idx = int(target) - 1
            if 0 <= idx < len(self.notes):
                removed = self.notes.pop(idx)
                ui.success(f"已删除笔记 [{idx + 1}]: {removed[:40]}{'...' if len(removed) > 40 else ''}")
            else:
                ui.error(f"无效的笔记编号，共有 {len(self.notes)} 条。")
            return

        if subcmd == 'search' or subcmd == 'find' or subcmd == 'grep':
            keyword = (parts[1] if len(parts) > 1 else "").strip().lower()
            if not keyword:
                ui.error("请指定搜索关键词。用法: note search <关键词>")
                return
            self._cmd_notes(f"search {keyword}")
            return

        if subcmd == 'clear' or subcmd == 'empty':
            if not self.notes:
                ui.info("笔记本来就是空的。")
                return
            confirm = input(f"  确定删除全部 {len(self.notes)} 条笔记吗？(y/N): ").strip().lower()
            if confirm in ('y', 'yes'):
                self.notes.clear()
                ui.success("已清空所有笔记。")
            return

        self.notes.append(args.strip())
        ui.success(f"已记录笔记 [{len(self.notes)}]: {args.strip()[:50]}{'...' if len(args.strip()) > 50 else ''}")

    def _cmd_notes(self, args: str):
        """查看笔记 / 搜索笔记"""
        if not self._require_playing():
            return

        if not self.notes:
            ui.info("你还没有记录任何笔记。")
            return

        if args:
            parts = args.split(maxsplit=1)
            sub = parts[0].lower()
            if sub == 'search' or sub == 'find':
                keyword = (parts[1] if len(parts) > 1 else "").strip().lower()
                if not keyword:
                    ui.error("请输入搜索关键词。")
                    return
                matches = []
                for i, note in enumerate(self.notes):
                    if keyword in note.lower():
                        matches.append((i + 1, note))
                if not matches:
                    ui.info(f"没有找到包含 '{keyword}' 的笔记。")
                    return
                ui.section(f"笔记搜索结果 (关键词: {keyword}, {len(matches)} 条)")
                for i, note in matches:
                    highlighted = note
                    print(c(f"  [{i}] ", ui.Color.DIM) + highlighted)
                print(c(f"  共 {len(matches)} / {len(self.notes)} 条匹配", ui.Color.DIM))
                return

        ui.section("笔记")
        for i, note in enumerate(self.notes, 1):
            print(c(f"  [{i}] ", ui.Color.DIM) + note)
        print(c(f"  共 {len(self.notes)} 条笔记", ui.Color.DIM))
        ui.info("提示: note del <编号> 删除，note search <关键词> 搜索")

    def _cmd_hint(self, args: str):
        """获取提示"""
        if not self._require_playing():
            return

        if self.hints_used >= self.level.max_hints:
            ui.warn(f"你已经用完了所有 {self.level.max_hints} 次提示机会。")
            return

        room = self._get_current_room()
        hint_text = None

        for puzzle in room.puzzles:
            if not puzzle.solved and puzzle.hint:
                hint_text = puzzle.hint
                break

        if not hint_text:
            for mech in room.mechanisms:
                if not mech.triggered and mech.trigger_item:
                    trigger_item = self.level.get_item(mech.trigger_item)
                    if trigger_item:
                        if trigger_item.id in self.inventory:
                            hint_text = f"试试对 {mech.name} 使用 {trigger_item.name}。"
                        else:
                            hint_text = f"{mech.name} 需要一件特定的物品来触发，仔细找找吧。"
                        break

        if not hint_text and room.exits:
            for direction, exit_obj in room.exits.items():
                if exit_obj.locked and exit_obj.unlock_item:
                    unlock_item = self.level.get_item(exit_obj.unlock_item)
                    if unlock_item:
                        dir_name = DIRECTION_NAMES.get(direction, direction)
                        if unlock_item.id in self.inventory:
                            hint_text = f"试试用 {unlock_item.name} 打开{dir_name}的通道。"
                        else:
                            hint_text = f"{dir_name}的通道被锁住了，你需要 {unlock_item.name}。"
                        break

        if not hint_text:
            inventory_items = self._get_inventory_items()
            combinable = []
            for i, a in enumerate(inventory_items):
                for b in inventory_items[i + 1:]:
                    recipe1 = f"{a.id}+{b.id}"
                    recipe2 = f"{b.id}+{a.id}"
                    if recipe1 in self.level.combine_recipes or recipe2 in self.level.combine_recipes:
                        combinable.append((a, b))
            if combinable:
                a, b = combinable[0]
                hint_text = f"也许可以试试组合 {a.name} 和 {b.name}？"

        if not hint_text:
            hint_text = "仔细查看房间描述，注意那些被提到的细节。向各个方向探索试试。"

        self.hints_used += 1
        ui.hint(f"[{self.hints_used}/{self.level.max_hints}] {hint_text}")

    def _cmd_undo(self, args: str):
        """撤销上一步"""
        if not self._require_playing():
            return
        if not self.history:
            ui.warn("没有可撤销的操作。")
            return

        state = self.history.pop()
        self._restore_state({
            'current_room_id': state.current_room_id,
            'inventory': state.inventory,
            'visited_rooms': state.visited_rooms,
            'notes': state.notes,
            'hints_used': state.hints_used,
            'steps': state.steps,
            'elapsed_seconds': state.elapsed_seconds,
            'solved_puzzles': state.solved_puzzles,
            'triggered_mechanisms': state.triggered_mechanisms,
            'room_item_states': state.room_item_states,
            'exit_states': state.exit_states,
        })
        ui.success("已撤销上一步操作。")
        self._visit_room(self.current_room_id, show_desc=True)

    def _cmd_rank(self, args: str):
        """显示排行榜"""
        level_filter = args.strip() if args else None
        records = LeaderboardManager.get_records_by_level(level_filter)
        ui.display_leaderboard(records, level_filter)

    def _cmd_status(self, args: str):
        """显示游戏状态"""
        if not self._require_playing():
            return
        ui.display_status(
            self.steps, self.hints_used, self.level.max_hints,
            self._get_elapsed(), len(self.visited_rooms), self._total_rooms(),
            self._solved_puzzles_count(), self._total_puzzles(),
        )

    def _cmd_saves(self, args: str):
        """列出存档"""
        saves = SaveManager.list_saves()
        ui.display_saves(saves, SaveManager.get_save_info)

    def _cmd_clear(self, args: str):
        """清屏"""
        ui.clear_screen()

    def _cmd_checklevel(self, args: str):
        """校验关卡文件"""
        if not args:
            ui.error("请指定关卡文件路径。用法: checklevel <文件路径>")
            custom_levels = LevelManager.list_level_files()
            if custom_levels:
                ui.info("检测到以下自定义关卡文件:")
                for lv in custom_levels:
                    print(c(f"    - {lv['filename']}", ui.Color.CYAN) +
                          c(f" ({lv.get('level_name', '?')}, {lv.get('room_count', 0)}房间)", ui.Color.DIM))
            return

        path = args.strip()
        if not os.path.exists(path):
            guess_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "levels", path)
            if os.path.exists(guess_path):
                path = guess_path
            else:
                ui.error(f"关卡文件不存在: {path}")
                return

        ui.info(f"正在校验: {path}")
        result = LevelChecker.check_file(path)
        print()
        print(LevelChecker.format_report(result))

    def _cmd_profiles(self, args: str):
        """显示关卡探索档案"""
        all_profiles = LevelProfileManager.list_profiles()
        current_id = self.level.id if self.level else None

        if args:
            target_id = args.strip()
            all_profiles = [p for p in all_profiles if p.get('level_id') == target_id or p.get('level_name', '').find(target_id) >= 0]

        if not all_profiles:
            ui.info("还没有任何关卡的探索档案。\n  通关至少一个关卡后，档案就会自动建立。")
            if self.level and current_id:
                p = LevelProfileManager.get_profile(current_id)
                if p.get('discovered_rooms') or p.get('solved_puzzles'):
                    ui.info(f"当前关卡 '{self.level.name}' 已有部分探索记录:")
                    ui.info(f"  已发现房间: {len(p.get('discovered_rooms', []))}")
                    ui.info(f"  已解谜题: {len(p.get('solved_puzzles', []))}")
            return

        ui.title("关卡探索档案")
        for i, p in enumerate(all_profiles, 1):
            lvl_name = p.get('level_name', p.get('level_id', '?'))
            mark = c("  ← 当前关卡", ui.Color.GREEN) if p.get('level_id') == current_id else ""
            print(c(f"  {i}. ", ui.Color.DIM) + bold(lvl_name) + mark)
            print(c(f"     ID: {p.get('level_id', '?')}  ", ui.Color.DIM) +
                  c(f"挑战次数: {p.get('play_count', 0)}  ", ui.Color.CYAN) +
                  c(f"通关次数: {p.get('completion_count', 0)}", ui.Color.YELLOW))
            discovered = len(p.get('discovered_rooms', []))
            solved = len(p.get('solved_puzzles', []))
            total_r = 0
            total_p = 0
            try:
                if p.get('level_id') == 'ancient_library':
                    total_r = 9
                    total_p = 1
                elif self.level and self.level.id == p.get('level_id'):
                    total_r = self._total_rooms()
                    total_p = self._total_puzzles()
            except Exception:
                pass
            disc_str = f"{discovered}/{total_r}" if total_r else str(discovered)
            solv_str = f"{solved}/{total_p}" if total_p else str(solved)
            print(c(f"     发现房间: {disc_str}  ", ui.Color.WHITE) +
                  c(f"已解谜题: {solv_str}", ui.Color.WHITE))
            best_score = p.get('best_score', 0)
            best_steps = p.get('best_steps', '-')
            best_time = p.get('best_time')
            if best_time:
                m, s = divmod(int(best_time), 60)
                h, m = divmod(m, 60)
                best_time_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
            else:
                best_time_str = '-'
            print(c(f"     最高分: {best_score}  ", ui.Color.GREEN) +
                  c(f"最少步数: {best_steps}  ", ui.Color.BLUE) +
                  c(f"最快用时: {best_time_str}", ui.Color.MAGENTA))
            print()

    def _handle_end_game(self):
        """处理游戏通关"""
        score = LeaderboardManager.calculate_score(
            steps=self.steps,
            hints_used=self.hints_used,
            elapsed_seconds=self._get_elapsed(),
            solved_puzzles=self._solved_puzzles_count(),
            discovered_rooms=len(self.visited_rooms),
            total_rooms=self._total_rooms(),
            total_puzzles=self._total_puzzles(),
        )

        LevelProfileManager.record_discovery(
            self.level.id, list(self.visited_rooms),
            [p.id for room in self.level.rooms.values() for p in room.puzzles if p.solved]
        )
        profile_result = LevelProfileManager.update_profile_on_end(
            self.level.id, self.steps, self._get_elapsed(), score
        )
        profile = profile_result['profile']
        improvements = profile_result['improvements']
        is_first = profile_result['is_first']

        room = self._get_current_room()
        ui.story(room.end_message)

        if improvements or is_first:
            print()
            if is_first:
                ui.success("🎉 首次通关！已建立探索档案。")
            else:
                ui.success("📊 成绩对比：")
            for kind, old, new in improvements:
                if kind == 'score':
                    ui.info(f"  🏆 得分刷新纪录！{old} → {new} (+{new-old})")
                elif kind == 'steps':
                    ui.info(f"  👟 步数刷新纪录！{old} 步 → {new} 步 (-{old-new})")
                elif kind == 'time':
                    def fmt(s):
                        m, s = divmod(int(s), 60)
                        h, m = divmod(m, 60)
                        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
                    delta = int(old - new)
                    ui.info(f"  ⏱️  用时刷新纪录！{fmt(old)} → {fmt(new)} (-{delta}秒)")
            if not improvements and not is_first:
                pass

        player_name = ""
        while not player_name:
            player_name = input("  输入你的名字上榜: ").strip()
            if len(player_name) > 12:
                ui.warn("名字最多12个字符。")
                player_name = ""

        record = ScoreRecord(
            player_name=player_name,
            level_id=self.level.id,
            level_name=self.level.name,
            score=score,
            steps=self.steps,
            hints_used=self.hints_used,
            elapsed_seconds=self._get_elapsed(),
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
        )
        rank = LeaderboardManager.add_record(record)

        ui.display_end(
            score=score,
            rank=rank,
            steps=self.steps,
            hints=self.hints_used,
            elapsed=self._get_elapsed(),
            solved_puzzles=self._solved_puzzles_count(),
            discovered_rooms=len(self.visited_rooms),
        )
