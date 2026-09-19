"""验证阵眼机制、阻挡反噬，并用 DFS 求解确保九重关皆可在放尽全部飞剑的同时破阵。"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
pygame.init()
screen = pygame.display.set_mode((1, 1))

from config import LEVELS, MAX_MISTAKE, TOTAL_LEVELS
from board import Board
from arrow import Sword, trace_path
from particle import ParticleSystem


def settle(board, dt=0.032, max_frames=600):
    """帧推进直到所有 fly/blocked 动画结束。"""
    for _ in range(max_frames):
        board.update(dt)
        if not any(s.state in ("fly", "blocked") for s in board.swords):
            return True
    return False


def solve(cfg, node_cap=500_000):
    """DFS 求发射序列（剑索引序列）：须释放全部飞剑且解除全部阵眼；
    无解返回 None。"""
    swords = [tuple(s) for s in cfg["swords"]]
    eyes = {tuple(e) for e in cfg["eyes"]}
    nodes = 0

    memo = set()

    def dfs(remain, activated):
        nonlocal nodes
        if not remain:
            return [] if activated >= eyes else None
        key = (remain, frozenset(activated))
        if key in memo:
            return None
        nodes += 1
        if nodes > node_cap:
            return None
        for i in remain:
            r, c, d = swords[i]
            others = remain - {i}

            def occupied(rr, cc, others=others):
                return any(swords[j][0] == rr and swords[j][1] == cc
                           for j in others)

            blocked, path = trace_path(r, c, d, occupied)
            if blocked:
                continue
            gained = {(pr, pc) for (pr, pc) in path} & eyes
            seq = dfs(others, activated | gained)
            if seq is not None:
                return [i] + seq
        memo.add(key)
        return None

    return dfs(frozenset(range(len(swords))), frozenset())


def test_layouts_valid():
    """剑格唯一；剑与阵眼格位不重叠；每关至少有阵眼。"""
    for li, cfg in enumerate(LEVELS):
        sword_cells = [(r, c) for (r, c, _d) in cfg["swords"]]
        assert len(sword_cells) == len(set(sword_cells)), f"L{li+1} 剑格重复"
        eye_cells = {tuple(e) for e in cfg["eyes"]}
        assert eye_cells, f"L{li+1} 缺少阵眼"
        assert not (eye_cells & set(sword_cells)), f"L{li+1} 阵眼压在剑格上"
    print(f"  [OK] 全部 {TOTAL_LEVELS} 重天布局合法")


def test_blocked_and_miss():
    """对向飞剑互相阻拦 → 失误+1、剑不离场；点空不扣剑意。"""
    board = Board(ParticleSystem())
    board.level = 0
    board.load()
    board.swords = [
        Sword(2, 1, "right", particles=board.particles),
        Sword(2, 4, "left", particles=board.particles),
    ]
    board.eyes = {(2, 0): False}
    left = board.swords[0]
    assert board.handle_click((left.x, left.y)) == "blocked"
    assert board.mistakes == 1
    settle(board)
    assert left.state == "idle", "受阻飞剑应震剑后回到 idle"
    print("  [OK] 前方有剑阻拦 → 失一点剑意，飞剑不离场")

    # 点棋盘空白处
    from config import GRID_OFFSET_X, GRID_OFFSET_Y, CELL
    empty = (GRID_OFFSET_X + CELL * 5 + CELL // 2,
             GRID_OFFSET_Y + CELL * 0 + CELL // 2)
    assert board.handle_click(empty) == "ignore"
    assert board.mistakes == 1
    print("  [OK] 点空 → 不扣剑意")


def test_failure_and_restart():
    """剑意耗尽判负；重开本重天阵眼、飞剑、剑意全部复原。"""
    board = Board(ParticleSystem())
    board.level = 0
    board.load()
    board.swords = [
        Sword(2, 1, "right", particles=board.particles),
        Sword(2, 4, "left", particles=board.particles),
    ]
    left = board.swords[0]
    while not board.is_failed():
        board.handle_click((left.x, left.y))
        settle(board)
    assert board.is_failed()
    print(f"  [OK] 剑意耗尽 {MAX_MISTAKE} 点 → 剑阵反噬")

    board.restart_current()
    assert board.mistakes == 0
    assert all(s.state == "idle" for s in board.swords)
    assert not any(board.eyes.values())
    print("  [OK] 重开本重天 → 剑意复原，飞剑与阵眼归位")


def test_all_levels_solvable_and_play():
    """DFS 求序列 → 在真实棋盘上逐剑执行，验证零失误破阵。"""
    all_ok = True
    for li, cfg in enumerate(LEVELS):
        seq = solve(cfg)
        if seq is None:
            print(f"L{li+1} {cfg['name']}: 求解失败（不可解或超出搜索上限）")
            all_ok = False
            continue

        board = Board(ParticleSystem())
        board.level = li
        board.load()
        for si in seq:
            s = board.swords[si]
            result = board.handle_click((s.x, s.y))
            assert result == "hit", f"L{li+1} 第 {si} 把剑应可释放"
            assert settle(board), f"L{li+1} 飞剑动画未收敛"
        ok = board.is_cleared()
        assert board.remaining() == 0, f"L{li+1} 仍有飞剑未离场"
        mark = "破阵" if ok else "未破"
        print(f"L{li+1} {cfg['name']}: {mark}  "
              f"放剑 {len(seq)}/{len(cfg['swords'])} · 失误 {board.mistakes} · "
              f"阵眼 {board.activated_count()}/{board.total_eyes()}")
        if not ok or board.mistakes != 0:
            all_ok = False
    assert all_ok, "存在无法零失误破除的重天"


if __name__ == "__main__":
    print("== 布局与机制测试 ==")
    test_layouts_valid()
    test_blocked_and_miss()
    test_failure_and_restart()

    print("\n== 九重关可解性与实机通关测试 ==")
    test_all_levels_solvable_and_play()
    print("\n九重仙境，尽皆可破。")
