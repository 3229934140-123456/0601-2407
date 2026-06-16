# -*- coding: utf-8 -*-
"""
默认关卡：古老图书馆的秘密
Default Level: The Secret of the Ancient Library
"""


def get_default_level() -> dict:
    """返回默认关卡的数据字典"""
    return {
        "id": "ancient_library",
        "name": "古老图书馆的秘密",
        "description": (
            "传说在城市中心的古老图书馆深处，隐藏着一本失落已久的智慧之书。\n"
            "  无数探险家曾来寻找，但都迷失在布满谜题的房间中...\n"
            "  今天，你带着好奇与勇气，推开了图书馆那扇吱呀作响的大门。"
        ),
        "start_room_id": "hall",
        "max_hints": 5,
        "combine_recipes": {
            "matches+candle": "lit_candle",
            "scroll_piece_a+scroll_piece_b": "complete_map",
        },
        "items": [
            {
                "id": "brass_key",
                "name": "黄铜钥匙",
                "description": "一把古朴的黄铜钥匙，上面刻着奇怪的符号。似乎能打开某扇门。",
                "aliases": ["钥匙", "key", "铜钥匙"],
            },
            {
                "id": "matches",
                "name": "火柴",
                "description": "一盒旧火柴，还剩几根。也许可以点燃什么。",
                "aliases": ["火柴盒", "match", "matches"],
            },
            {
                "id": "candle",
                "name": "蜡烛",
                "description": "一支未点燃的白色蜡烛，似乎能在黑暗中提供照明。",
                "aliases": ["烛", "candle", "candles"],
            },
            {
                "id": "lit_candle",
                "name": "点燃的蜡烛",
                "description": "一支正在燃烧的蜡烛，温暖的光芒驱散了黑暗。",
                "aliases": ["燃烧的蜡烛", "lit candle", "burning candle"],
                "can_pickup": True,
            },
            {
                "id": "magnifier",
                "name": "放大镜",
                "description": "一个精致的铜框放大镜，可以看清微小的文字。",
                "aliases": ["扩大镜", "透镜", "magnifier", "magnifying glass", "glass"],
            },
            {
                "id": "scroll_piece_a",
                "name": "羊皮纸碎片（左半）",
                "description": "半张破旧的羊皮纸，上面画着奇怪的地图线条。",
                "aliases": ["碎片a", "碎片1", "左半碎片", "左碎片", "scroll a", "piece a", "fragment a"],
            },
            {
                "id": "scroll_piece_b",
                "name": "羊皮纸碎片（右半）",
                "description": "半张破旧的羊皮纸，上面标着神秘的符号。",
                "aliases": ["碎片b", "碎片2", "右半碎片", "右碎片", "scroll b", "piece b", "fragment b"],
            },
            {
                "id": "complete_map",
                "name": "完整的羊皮纸地图",
                "description": "将两张碎片拼在一起后，一张完整的地图出现了！\n"
                             "  地图上标注着：「宝藏在北下，暗门在书架后」",
                "aliases": ["地图", "完整地图", "map", "羊皮纸地图"],
            },
            {
                "id": "old_book",
                "name": "破旧的古书",
                "description": "一本皮革封面的古书，扉页上写着：\n"
                             "  「我有城市却无人烟，有森林却无树木，\n"
                             "   有江河却无水流。我是什么？」",
                "aliases": ["古书", "书", "book", "old book"],
            },
            {
                "id": "silver_key",
                "name": "银色钥匙",
                "description": "一把闪闪发亮的银色钥匙，比黄铜钥匙精致得多。",
                "aliases": ["银钥匙", "silver key"],
            },
            {
                "id": "gem",
                "name": "发光的宝石",
                "description": "一颗散发着柔和蓝光的宝石，握在手里暖暖的。",
                "aliases": ["宝石", "蓝宝石", "蓝宝", "gem", "gemstone", "sapphire"],
            },
            {
                "id": "wisdom_book",
                "name": "智慧之书",
                "description": "传说中的智慧之书！封面镶嵌着金色纹路，散发着古老而神圣的气息。",
                "aliases": ["智慧书", "圣书", "wisdom book", "book of wisdom"],
            },
        ],
        "rooms": [
            {
                "id": "hall",
                "name": "图书馆大厅",
                "description": (
                    "你站在一个宏伟的大厅中央。高耸的穹顶上画着斑驳的壁画，\n"
                    "  几束阳光透过彩色玻璃窗洒落，照亮了满是灰尘的地面。\n"
                    "  前方是一个长长的借阅台，后面的墙上布满了书架。"
                ),
                "items": ["matches"],
                "exits": [
                    {"direction": "north", "target_room_id": "reading_room",
                     "description": "通往阅读室的拱门"},
                    {"direction": "east", "target_room_id": "librarian_office",
                     "description": "一扇刻着花纹的木门，似乎是管理员办公室"},
                    {"direction": "west", "target_room_id": "ancient_room",
                     "locked": True, "lock_reason": "一扇厚重的铁门，需要黄铜钥匙才能打开",
                     "unlock_item": "brass_key", "description": "通往古籍室的铁门"},
                ],
                "puzzles": [],
                "mechanisms": [],
            },
            {
                "id": "reading_room",
                "name": "阅读室",
                "description": (
                    "一间宽敞的阅读室，排列着整齐的长桌和木椅。桌上散落着几本翻开的书，\n"
                    "  仿佛阅读者刚刚离开。壁炉已经熄灭很久了，旁边立着一个烛台。"
                ),
                "items": ["candle", "scroll_piece_a"],
                "exits": [
                    {"direction": "south", "target_room_id": "hall",
                     "description": "返回大厅"},
                    {"direction": "north", "target_room_id": "dark_room",
                     "locked": True,
                     "lock_reason": "前方一片漆黑，伸手不见五指，需要光源才能进入",
                     "unlock_item": "lit_candle",
                     "description": "通向一个黑暗的房间"},
                    {"direction": "east", "target_room_id": "bookshelf_room",
                     "description": "一排排书架延伸过去"},
                ],
                "puzzles": [],
                "mechanisms": [],
            },
            {
                "id": "librarian_office",
                "name": "管理员办公室",
                "description": (
                    "这是图书管理员的私人办公室。办公桌上堆满了文件，墙上挂着一幅肖像画。\n"
                    "  桌子的抽屉似乎被锁住了。角落里有一个奇怪的机关装置。"
                ),
                "items": ["magnifier"],
                "exits": [
                    {"direction": "west", "target_room_id": "hall",
                     "description": "返回大厅"},
                ],
                "puzzles": [
                    {
                        "id": "drawer_puzzle",
                        "prompt": (
                            "桌上有一个上锁的抽屉，锁上刻着一个谜语：\n"
                            "  「我有城市却无人烟，有森林却无树木，\n"
                            "   有江河却无水流。我是什么？」"
                        ),
                        "answers": ["地图", "map", "一幅地图", "一张地图"],
                        "hint": "想想什么东西上面有城市、森林和江河，但都是画上去的...",
                        "reward_item": "brass_key",
                        "reward_message": "咔哒一声，抽屉打开了！里面有一把黄铜钥匙！",
                    },
                ],
                "mechanisms": [
                    {
                        "id": "portrait_mech",
                        "name": "肖像画机关",
                        "description": (
                            "墙上挂着一幅老管理员的肖像画，画框似乎有些松动。\n"
                            "  也许用什么东西可以撬动它？"
                        ),
                        "trigger_item": "magnifier",
                        "trigger_message": (
                            "你用放大镜的手柄撬动画框，肖像画突然翻转过来！\n"
                            "  后面出现了一个暗格！"
                        ),
                        "reveal_item": "old_book",
                    },
                ],
            },
            {
                "id": "bookshelf_room",
                "name": "书架长廊",
                "description": (
                    "高耸的书架从地面一直延伸到天花板，形成一条看不到尽头的长廊。\n"
                    "  空气中弥漫着旧纸张特有的霉味。地上散落着一些书页。\n"
                    "  你注意到有一处书架似乎和其他的不太一样..."
                ),
                "items": ["scroll_piece_b"],
                "exits": [
                    {"direction": "west", "target_room_id": "reading_room",
                     "description": "返回阅读室"},
                    {"direction": "south", "target_room_id": "secret_study",
                     "hidden": True,
                     "description": "书架后面的暗门"},
                ],
                "mechanisms": [
                    {
                        "id": "bookshelf_mech",
                        "name": "奇怪的书架",
                        "description": (
                            "这一排书架上的书似乎摆得很刻意，像是某种密码锁。\n"
                            "  如果按照正确的顺序抽书，也许能触发什么...\n"
                            "  也许需要先找到地图或提示？"
                        ),
                        "trigger_item": "complete_map",
                        "trigger_message": (
                            "你按照地图上的标注，抽出了正确位置的书。\n"
                            "  书架发出沉重的轰隆声，缓缓向一侧移动，\n"
                            "  露出了一个隐藏的房间入口！"
                        ),
                        "reveal_exit": "south",
                    },
                ],
                "puzzles": [],
            },
            {
                "id": "ancient_room",
                "name": "古籍室",
                "description": (
                    "这是存放珍贵古籍的房间。四周的书架上摆满了皮革封面的古书，\n"
                    "  每一本都散发着古老的气息。房间中央有一个石质基座，\n"
                    "  上面有一个宝石形状的凹槽。"
                ),
                "items": [],
                "exits": [
                    {"direction": "east", "target_room_id": "hall",
                     "description": "返回大厅"},
                    {"direction": "down", "target_room_id": "basement",
                     "locked": True,
                     "lock_reason": "地面上有一个被石板盖住的入口，石板太重推不动",
                     "unlock_item": "silver_key",
                     "description": "通往地下的神秘入口"},
                ],
                "mechanisms": [
                    {
                        "id": "pedestal_mech",
                        "name": "宝石基座",
                        "description": (
                            "一个古老的石质基座，上面有一个完美契合宝石的凹槽。\n"
                            "  似乎需要放入一颗宝石才能激活什么..."
                        ),
                        "trigger_item": "gem",
                        "trigger_message": (
                            "你将发光的宝石放入凹槽，宝石的光芒骤然变亮！\n"
                            "  基座咔哒一声打开，弹出了一把银色钥匙！"
                        ),
                        "reveal_item": "silver_key",
                        "unlock_exit": "down",
                    },
                ],
                "puzzles": [],
            },
            {
                "id": "dark_room",
                "name": "档案室",
                "description": (
                    "在蜡烛的光芒下，你看清这是一间古老的档案室。\n"
                    "  高大的档案柜整齐排列，空气中漂浮着尘埃。\n"
                    "  一个玻璃展柜在房间尽头，里面似乎放着什么珍贵物品。"
                ),
                "items": ["gem"],
                "exits": [
                    {"direction": "south", "target_room_id": "reading_room",
                     "description": "返回阅读室"},
                ],
                "mechanisms": [],
                "puzzles": [],
            },
            {
                "id": "secret_study",
                "name": "秘密书房",
                "description": (
                    "这是一间隐藏的秘密书房！墙上挂满了古老的卷轴，\n"
                    "  书桌上摆着复杂的星象图和炼金器材。\n"
                    "  正北方有一扇华丽的金色大门，门上镶嵌着智慧之书的浮雕，\n"
                    "  这里一定就是传说中存放智慧之书的地方！"
                ),
                "items": [],
                "hidden": True,
                "exits": [
                    {"direction": "north", "target_room_id": "treasure_room",
                     "description": "通往最终房间的金色大门"},
                    {"direction": "south", "target_room_id": "bookshelf_room",
                     "description": "返回书架长廊"},
                ],
                "mechanisms": [],
                "puzzles": [],
            },
            {
                "id": "basement",
                "name": "地下密室",
                "description": (
                    "你沿着石阶走下，来到了一间潮湿的地下密室。\n"
                    "  墙壁上燃烧着永不熄灭的蓝色火焰，照亮了整个房间。\n"
                    "  你注意到北边还有一条通道... 也许这就是通往智慧之书的捷径？"
                ),
                "items": [],
                "hidden": False,
                "exits": [
                    {"direction": "up", "target_room_id": "ancient_room",
                     "description": "返回古籍室"},
                    {"direction": "north", "target_room_id": "treasure_room",
                     "description": "通往更深处的神秘通道"},
                ],
                "mechanisms": [],
                "puzzles": [],
            },
            {
                "id": "treasure_room",
                "name": "圣殿",
                "description": (
                    "你来到了一座宏伟的圣殿。柔和的光芒从四面八方汇聚而来，\n"
                    "  照亮了房间正中央的石坛。石坛上，一本散发着金光的书籍静静躺着——\n"
                    "  那就是传说中的智慧之书！"
                ),
                "items": ["wisdom_book"],
                "is_end": True,
                "end_message": (
                    "你缓缓伸出双手，捧起了智慧之书。一瞬间，无数知识涌入脑海...\n"
                    "  恭喜你，勇敢的探险家！你解开了古老图书馆的全部秘密！\n"
                    "  你的名字，将被铭刻在这座圣殿的历史之中。"
                ),
                "exits": [],
                "mechanisms": [],
                "puzzles": [],
            },
        ],
    }
