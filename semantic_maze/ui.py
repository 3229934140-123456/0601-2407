# -*- coding: utf-8 -*-
"""
用户界面渲染模块
UI Rendering Module
"""

import os
import sys
from typing import List, Optional, Dict, Any

from .models import (
    Room, Item, Level, DIRECTION_NAMES, DIRECTION_OPPOSITES, ScoreRecord,
)


class Color:
    """ANSI 颜色代码"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'

    @staticmethod
    def support_color() -> bool:
        """检查是否支持颜色输出"""
        if os.environ.get('NO_COLOR'):
            return False
        if not sys.stdout.isatty():
            return False
        if os.name == 'nt':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                return False
        return True


USE_COLOR = Color.support_color()


def c(text: str, color: str) -> str:
    """带颜色的文本"""
    if not USE_COLOR:
        return text
    return f"{color}{text}{Color.RESET}"


def bold(text: str) -> str:
    return c(text, Color.BOLD)


def title(text: str):
    """显示标题"""
    width = 60
    line = "=" * width
    print()
    print(c(line, Color.CYAN))
    print(c(text.center(width), Color.BOLD + Color.CYAN))
    print(c(line, Color.CYAN))
    print()


def section(text: str):
    """显示段落标题"""
    print()
    print(c(f"【{text}】", Color.BOLD + Color.YELLOW))


def info(text: str):
    """显示信息"""
    print(c(text, Color.WHITE))


def success(text: str):
    """显示成功消息"""
    print(c(f"✓ {text}", Color.GREEN))


def warn(text: str):
    """显示警告消息"""
    print(c(f"! {text}", Color.YELLOW))


def error(text: str):
    """显示错误消息"""
    print(c(f"✗ {text}", Color.RED))


def hint(text: str):
    """显示提示"""
    print(c(f"💡 {text}", Color.MAGENTA))


def story(text: str):
    """显示故事文本"""
    print(c(f"  {text}", Color.CYAN))


def separator():
    print(c("-" * 60, Color.DIM))


def clear_screen():
    """清屏"""
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')


def display_room(room: Room, level: Level, show_items: bool = True,
                 show_exits: bool = True, first_visit: bool = False):
    """显示房间信息"""
    print()
    print(bold(c(f"◆ {room.name} ◆", Color.BLUE)))
    separator()
    story(room.description)

    if show_items and room.items:
        visible_items = []
        for item_id in room.items:
            item = level.get_item(item_id)
            if item and not item.hidden:
                visible_items.append(item)
        if visible_items:
            print()
            print(c("  你看到了:", Color.DIM))
            for item in visible_items:
                print(c(f"    · {item.name}", Color.WHITE))

    if room.mechanisms:
        for mech in room.mechanisms:
            if not mech.triggered:
                print()
                print(c(f"  发现机关: {mech.name}", Color.YELLOW))
                print(c(f"    {mech.description}", Color.DIM))

    if room.puzzles:
        for puzzle in room.puzzles:
            if not puzzle.solved:
                print()
                print(c(f"  有一个谜题等待解答", Color.MAGENTA))

    if show_exits and room.exits:
        visible_exits = []
        for direction, exit_obj in room.exits.items():
            if not exit_obj.hidden:
                visible_exits.append((direction, exit_obj))
        if visible_exits:
            print()
            print(c("  出口:", Color.DIM))
            for direction, exit_obj in visible_exits:
                dir_name = DIRECTION_NAMES.get(direction, direction)
                status = ""
                if exit_obj.locked:
                    status = c(" (锁定)", Color.RED)
                elif exit_obj.description:
                    status = c(f" ({exit_obj.description})", Color.DIM)
                print(c(f"    → {dir_name}{status}", Color.WHITE))

    print()


def display_inventory(items: List[Item]):
    """显示背包"""
    if not items:
        info("你的背包是空的。")
        return

    section("背包")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {bold(item.name)}")
        if item.description:
            print(c(f"     {item.description}", Color.DIM))
    print(c(f"  共 {len(items)} 件物品", Color.DIM))


def display_notes(notes: List[str]):
    """显示笔记"""
    if not notes:
        info("你还没有记录任何笔记。")
        return

    section("笔记")
    for i, note in enumerate(notes, 1):
        print(c(f"  [{i}] {note}", Color.WHITE))
    print(c(f"  共 {len(notes)} 条笔记", Color.DIM))


def display_map(level: Level, current_room_id: str, visited_rooms: List[str]):
    """显示简易地图（基于房间连接关系的文本地图）"""
    section("地图")

    room_positions = {}
    y = 0
    x = 0

    def assign_pos(room_id, cx, cy, visited):
        if room_id in visited or room_id not in level.rooms:
            return
        visited.add(room_id)
        room_positions[room_id] = (cx, cy)
        room = level.rooms[room_id]
        for direction, exit_obj in room.exits.items():
            if exit_obj.hidden and exit_obj.target_room_id not in visited_rooms:
                continue
            nx, ny = cx, cy
            if direction == 'north':
                ny -= 1
            elif direction == 'south':
                ny += 1
            elif direction == 'east':
                nx += 1
            elif direction == 'west':
                nx -= 1
            elif direction == 'northeast':
                nx += 1
                ny -= 1
            elif direction == 'northwest':
                nx -= 1
                ny -= 1
            elif direction == 'southeast':
                nx += 1
                ny += 1
            elif direction == 'southwest':
                nx -= 1
                ny += 1
            assign_pos(exit_obj.target_room_id, nx, ny, visited)

    assign_pos(level.start_room_id, 0, 0, set())

    if not room_positions:
        info("地图尚未绘制...")
        return

    min_x = min(p[0] for p in room_positions.values())
    max_x = max(p[0] for p in room_positions.values())
    min_y = min(p[1] for p in room_positions.values())
    max_y = max(p[1] for p in room_positions.values())

    grid_w = (max_x - min_x + 1) * 3
    grid_h = (max_y - min_y + 1) * 2
    grid = [[' ' for _ in range(grid_w + 2)] for _ in range(grid_h + 2)]

    for room_id, (rx, ry) in room_positions.items():
        room = level.rooms.get(room_id)
        if not room:
            continue
        is_visited = room_id in visited_rooms
        is_current = room_id == current_room_id
        gx = (rx - min_x) * 3 + 1
        gy = (ry - min_y) * 2 + 1

        if is_current:
            symbol = c('@', Color.BOLD + Color.RED)
        elif is_visited:
            if room.is_end:
                symbol = c('★', Color.BOLD + Color.GREEN)
            else:
                symbol = c('○', Color.BLUE)
        else:
            symbol = c('?', Color.DIM)

        grid[gy][gx] = symbol

        if is_visited or is_current:
            for direction, exit_obj in room.exits.items():
                if exit_obj.hidden and exit_obj.target_room_id not in visited_rooms:
                    continue
                if direction == 'north' and gy - 1 >= 0:
                    grid[gy - 1][gx] = c('│', Color.DIM)
                elif direction == 'south' and gy + 1 < len(grid):
                    grid[gy + 1][gx] = c('│', Color.DIM)
                elif direction == 'east' and gx + 1 < len(grid[0]):
                    grid[gy][gx + 1] = c('─', Color.DIM)
                elif direction == 'west' and gx - 1 >= 0:
                    grid[gy][gx - 1] = c('─', Color.DIM)
                elif direction == 'northeast':
                    if gx + 1 < len(grid[0]) and gy - 1 >= 0:
                        grid[gy - 1][gx + 1] = c('╱', Color.DIM)
                elif direction == 'northwest':
                    if gx - 1 >= 0 and gy - 1 >= 0:
                        grid[gy - 1][gx - 1] = c('╲', Color.DIM)
                elif direction == 'southeast':
                    if gx + 1 < len(grid[0]) and gy + 1 < len(grid):
                        grid[gy + 1][gx + 1] = c('╲', Color.DIM)
                elif direction == 'southwest':
                    if gx - 1 >= 0 and gy + 1 < len(grid):
                        grid[gy + 1][gx - 1] = c('╱', Color.DIM)

    for row in grid:
        print('  ' + ''.join(row))

    print()
    print(c("  图例: ", Color.DIM), end="")
    print(c("@", Color.BOLD + Color.RED) + c(" 当前位置  ", Color.DIM), end="")
    print(c("○", Color.BLUE) + c(" 已访问  ", Color.DIM), end="")
    print(c("?", Color.DIM) + c(" 未知  ", Color.DIM), end="")
    print(c("★", Color.BOLD + Color.GREEN) + c(" 终点", Color.DIM))
    print()


def display_status(steps: int, hints_used: int, max_hints: int, elapsed: float,
                   discovered: int, total_rooms: int, solved: int, total_puzzles: int):
    """显示游戏状态"""
    m, s = divmod(int(elapsed), 60)
    h, m = divmod(m, 60)
    time_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    section("状态")
    status_line = (
        c(f"  步数: {steps}", Color.WHITE) + "  |  " +
        c(f"提示: {hints_used}/{max_hints}", Color.MAGENTA) + "  |  " +
        c(f"时间: {time_str}", Color.CYAN) + "  |  " +
        c(f"房间: {discovered}/{total_rooms}", Color.YELLOW)
    )
    if total_puzzles > 0:
        status_line += "  |  " + c(f"谜题: {solved}/{total_puzzles}", Color.GREEN)
    print(status_line)


def display_help():
    """显示帮助信息"""
    title("命令帮助")

    print(bold("  游戏控制:"))
    print(c("    start              ", Color.YELLOW) + c("- 开始新游戏 (从关卡列表中选择)", Color.DIM))
    print(c("    start <路径>       ", Color.YELLOW) + c("- 直接从指定关卡文件开始", Color.DIM))
    print(c("    load [存档名]      ", Color.YELLOW) + c("- 读取存档", Color.DIM))
    print(c("    save [存档名]      ", Color.YELLOW) + c("- 保存游戏", Color.DIM))
    print(c("    quit / exit        ", Color.YELLOW) + c("- 退出游戏", Color.DIM))
    print(c("    help               ", Color.YELLOW) + c("- 显示此帮助", Color.DIM))
    print(c("    status             ", Color.YELLOW) + c("- 显示游戏当前状态", Color.DIM))
    print(c("    profiles / stats   ", Color.YELLOW) + c("- 查看关卡探索档案", Color.DIM))
    print()

    print(bold("  探索与移动:"))
    print(c("    look / l           ", Color.YELLOW) + c("- 查看当前房间", Color.DIM))
    print(c("    look <物品>        ", Color.YELLOW) + c("- 仔细查看物品", Color.DIM))
    print(c("    map                ", Color.YELLOW) + c("- 显示地图", Color.DIM))
    print(c("    move <方向>        ", Color.YELLOW) + c("- 向方向移动 (n/s/e/w/u/d/ne/nw/se/sw)", Color.DIM))
    print(c("    <方向>             ", Color.YELLOW) + c("- 简写: 直接输入方向即可移动", Color.DIM))
    print(c("    undo               ", Color.YELLOW) + c("- 撤销上一步操作", Color.DIM))
    print()

    print(bold("  物品交互:"))
    print(c("    take / get <物品>  ", Color.YELLOW) + c("- 拾取物品", Color.DIM))
    print(c("    drop <物品>        ", Color.YELLOW) + c("- 丢弃物品", Color.DIM))
    print(c("    inventory / inv / i", Color.YELLOW) + c("- 查看背包", Color.DIM))
    print(c("    use <物品>         ", Color.YELLOW) + c("- 使用物品", Color.DIM))
    print(c("    use <A> with <B>   ", Color.YELLOW) + c("- 把 A 用在 B 上", Color.DIM))
    print(c("    combine <A> <B>    ", Color.YELLOW) + c("- 组合 A 和 B", Color.DIM))
    print()

    print(bold("  谜题与笔记:"))
    print(c("    answer / solve <答案>", Color.YELLOW) + c("- 输入谜题答案", Color.DIM))
    print(c("    note <内容>        ", Color.YELLOW) + c("- 记录线索笔记", Color.DIM))
    print(c("    note del <编号>    ", Color.YELLOW) + c("- 删除指定笔记", Color.DIM))
    print(c("    note search <关键词>", Color.YELLOW) + c("- 按关键词搜索笔记", Color.DIM))
    print(c("    notes              ", Color.YELLOW) + c("- 查看所有笔记", Color.DIM))
    print(c("    hint               ", Color.YELLOW) + c("- 获取提示 (有限次数)", Color.DIM))
    print()

    print(bold("  排行榜:"))
    print(c("    rank               ", Color.YELLOW) + c("- 显示本地排行榜", Color.DIM))
    print(c("    rank <关卡>        ", Color.YELLOW) + c("- 显示指定关卡排行榜", Color.DIM))
    print()

    print(bold("  关卡编辑:"))
    print(c("    loadlevel <文件路径>", Color.YELLOW) + c("- 加载自定义关卡 JSON 文件", Color.DIM))
    print(c("    checklevel <路径>  ", Color.YELLOW) + c("- 校验关卡文件的完整性", Color.DIM))
    print()


def display_saves(saves: List[str], save_info_getter):
    """显示存档列表"""
    if not saves:
        info("暂无存档。")
        return

    section("存档列表")
    for i, name in enumerate(saves, 1):
        save_info = save_info_getter(name)
        if save_info:
            print(c(f"  {i}. ", Color.DIM) + bold(name) +
                  c(f"  [{save_info.get('level_id', '?')}] 步数:{save_info.get('steps', 0)} "
                    f"提示:{save_info.get('hints_used', 0)} 保存于:{save_info.get('saved_at', '?')}",
                    Color.DIM))
        else:
            print(c(f"  {i}. ", Color.DIM) + bold(name))


def display_leaderboard(records: List[ScoreRecord], level_filter: Optional[str] = None):
    """显示排行榜"""
    if level_filter:
        title(f"排行榜 - {level_filter}")
    else:
        title("全关卡排行榜")

    if not records:
        info("暂无记录。快去创造第一个记录吧！")
        return

    print(c(f"  {'排名':<4}{'玩家':<12}{'关卡':<16}{'分数':<8}{'步数':<6}{'提示':<6}{'用时':<10}",
            Color.BOLD + Color.YELLOW))
    separator()

    medals = ['🥇', '🥈', '🥉']
    for i, r in enumerate(records, 1):
        medal = medals[i - 1] if i <= 3 else f" {i}."
        m, s = divmod(int(r.elapsed_seconds), 60)
        h, m = divmod(m, 60)
        time_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
        print(c(f"  {medal:<4}{r.player_name:<12}{r.level_name:<16}"
                f"{r.score:<8}{r.steps:<6}{r.hints_used:<6}{time_str:<10}",
                Color.WHITE))
    print()


def display_end(score: int, rank: int, steps: int, hints: int, elapsed: float,
                solved_puzzles: int, discovered_rooms: int):
    """显示通关结算"""
    print()
    title("🎉 通关成功！")
    separator()

    m, s = divmod(int(elapsed), 60)
    h, m = divmod(m, 60)
    time_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    print(bold(f"  最终得分: {score}".center(58)))
    if rank > 0:
        print(c(f"  恭喜！你的排名是第 {rank} 名！".center(58), Color.GREEN))
    else:
        print(c(f"  继续努力，冲击排行榜！".center(58), Color.DIM))
    print()
    print(c(f"  总步数: {steps}    使用提示: {hints}    用时: {time_str}", Color.CYAN).center(58))
    print(c(f"  解开谜题: {solved_puzzles}    探索房间: {discovered_rooms}", Color.YELLOW).center(58))
    separator()
    print()


def banner():
    """显示游戏横幅"""
    clear_screen()
    art = r"""
   ____                    _   _          __  __              
  / ___|  ___  _ __ ___   | | (_)  __ _  |  \/  |  __ _   ___ 
  \___ \ / _ \| '_ ` _ \  | | | | / _` | | |\/| | / _` | / _ \
   ___) |  __/| | | | | | | | | || (_| | | |  | || (_| ||  __/
  |____/ \___||_| |_| |_| |_| |_| \__,_| |_|  |_| \__,_| \___|
                                                                  
    """
    print(c(art, Color.CYAN))
    print(c("        一款益智解谜语义迷宫命令行游戏".center(70), Color.BOLD + Color.YELLOW))
    print(c("        输入 'start' 开始新游戏，'help' 查看命令".center(70), Color.DIM))
    print()
