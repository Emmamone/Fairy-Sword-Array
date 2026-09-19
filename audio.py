
import pygame
import os


class AudioManager:
    """音乐音效管理。文件缺失时静默跳过，不影响游戏。"""

    # BGM 音量：平时 / 九重天全部通关时刻（通关瞬间抬高）
    MUSIC_VOLUME_NORMAL = 0.45
    MUSIC_VOLUME_VICTORY = 1.0

    # 音效名 → 文件名（位于 assets/sounds/，缺哪个就静默跳过）
    SOUND_FILES = {
        "click": "click.wav",           # 按钮点击 / 阵眼解除（可选）
        "shoot": "剑飞行音效.wav",       # 释放飞剑
        "fail": "失误音效.wav",          # 剑阻路 / 剑阵反噬
        "levelup": "小关卡通关音效.wav",  # 破阵升入下一重天
    }

    # 个别音效单独调音量，未列出的用默认 sound_volume
    SOUND_VOLUMES = {
        "fail": 1.0,    # 失误音效稍微抬高
    }

    def __init__(self):
        self.ok = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            self.ok = False
        self.music_volume = self.MUSIC_VOLUME_NORMAL
        self.sound_volume = 0.8
        self.sounds = {}
        self.current_music = None
        if self.ok:
            self.load_sounds()

    def load_sounds(self):
        for name, fname in self.SOUND_FILES.items():
            path = os.path.join("assets", "sounds", fname)
            if os.path.exists(path):
                try:
                    s = pygame.mixer.Sound(path)
                    s.set_volume(self.SOUND_VOLUMES.get(name,
                                                        self.sound_volume))
                    self.sounds[name] = s
                except pygame.error:
                    continue

    def play_sound(self, name):
        if not self.ok:
            return
        s = self.sounds.get(name)
        if s:
            s.play()

    def play_music(self, file, loop=-1):
        if not self.ok:
            return
        path = os.path.join("assets", "music", file)
        if not os.path.exists(path):
            return
        if self.current_music == file:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loop)
            self.current_music = file
        except pygame.error:
            pass

    def set_music_volume(self, volume):
        """实时调整正在播放的 BGM 音量（全部通关时刻抬高背景音乐）。"""
        self.music_volume = volume
        if self.ok:
            pygame.mixer.music.set_volume(volume)

    def stop_music(self):
        if not self.ok:
            return
        pygame.mixer.music.stop()
        self.current_music = None

    def fadeout_music(self, ms=800):
        if not self.ok:
            return
        pygame.mixer.music.fadeout(ms)
        self.current_music = None

    # ---- 场景切换 ----

    def play_scene(self, scene):
        """按场景切换 BGM：menu / cloudsea（游戏内） / victory。"""
        mapping = {
            "menu": "背景音乐.mp3",
            "cloudsea": "背景音乐.mp3",
            "victory": "victory.mp3",
        }
        f = mapping.get(scene)
        if f:
            self.play_music(f)
