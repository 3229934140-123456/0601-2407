#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语义迷宫 - 益智解谜命令行游戏
Semantic Maze - A Puzzle Adventure CLI Game
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from semantic_maze.game import Game


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
