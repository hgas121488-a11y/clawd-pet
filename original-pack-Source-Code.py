import sys
import os
import time
import math
import random
import json
import getpass
import urllib.request
import urllib.parse
import json as pyjson
import threading
import re

from PyQt6.QtCore import Qt, QTimer, QRectF, QRect
from PyQt6.QtGui import QPainter, QColor, QFont, QImage, QAction, QCursor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMenu, QDialog, QVBoxLayout, QHBoxLayout,
    QCheckBox, QComboBox, QLabel, QPushButton, QScrollArea, QLineEdit, QTabWidget
)

# ==========================================
# КОНСТАНТЫ
# ==========================================
GRID_W = 18
GRID_H = 13
SIZE_ITEMS = ["Крошечный"]
SIZE_DP = [2.0]

PALETTES = [
    ("Claude", 0xFFD97757, 0xFF1A1A1A),
    ("Мятный", 0xFF4FBF98, 0xFF12241D),
    ("Лавандовый", 0xFF9B8AEE, 0xFF1B1631),
    ("Небесный", 0xFF4FA8E8, 0xFF0E1C29),
    ("Розовый", 0xFFEE85AE, 0xFF2A1220),
    ("Графит", 0xFF5E6670, 0xFFF2F2F2),
    ("Изумрудный", 0xFF2ECC71, 0xFF0B1F14),
    ("Янтарный", 0xFFFFB020, 0xFF231704),
    ("Коралловый", 0xFFFF6F61, 0xFF2A100D),
    ("Индиго", 0xFF5C6BC0, 0xFF13152B),
    ("Бирюзовый", 0xFF26C6DA, 0xFF0A1E22),
    ("Фуксия", 0xFFD64FD6, 0xFF2A0F2A),
    ("Оливковый", 0xFF9BA84F, 0xFF1A1D0D),
    ("Терракотовый", 0xFFC76B4A, 0xFF24120C),
    ("Стальной", 0xFF8FA3B8, 0xFF141B22),
    ("Вишнёвый", 0xFFC2185B, 0xFF2A0A16),
]

HEART_COLOR = 0xFFFF5C7A
SPARK_COLOR = 0xFFFFC94D
POOP_COLORS = {"X": 0xFF8A5A33, "o": 0xFFB27D4E, "w": 0xFFFFFFFF, "k": 0xFF1A1A1A}

PATTERNS = {
    "heart": (".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."),
    "spark": ("..X..", "..X..", "XX.XX", "..X..", "..X.."),
    "poop": ("....X....", "...XXo...", "..XXXXX..", ".XXXXXXo.", ".XwkXwkX.", "XXXXXXXXo", "XXXXXXXXX"),
}

PHRASES = {
    "hello": ["Привет, {user}!", "Я Clawd, твой личный агент!", "О, рад встрете, {user}!"],
    "idle": ["Чем помочь, {user}?", "Хм… анализирую систему", "Думаю над кодом…", "Твоё любимое приложение сегодня активное?", "Не забудь попить воды!", "Пип-пип!", "Мне нравится этот рабочий стол", "Я всё вижу", "Скучно, как в понедельник", "Ты там живой, {user}?", "Хочу печеньку"],
    "tap": ["Ой!", "Эй, {user}!", "Чего тыкаешь?", "Хи!", "Я тут!"],
    "annoyed": ["Хватит тыкать!", "Щекотно же!", "Ну всё, обиделся"],
    "pet": ["Мрр…", "Ещё!", "Приятно ♥", "Хи-хи", "Лучший день!"],
    "drag": ["Ааа!", "Куда мы?", "Поставь меня!", "Я космонавт"],
    "throw": ["Уиии!", "Я лечу!", "Ваааа!"],
    "dizzy": ["Голова кружится…", "@_@", "Где я?"],
    "wake": ["А? Что?", "Я не спал!", "*зевает*"],
    "jump": ["Хоп!", "Йе!", "Ура!"],
    "eat": ["Ням!", "Хрум-хрум", "Вкусная кнопка", "*жуёт*", "Ммм, пиксели!"],
    "spit": ["Ладно, отдаю!", "Тьфу!", "Ой, простите", "Забирай…"],
    "poop": ["Упс…", "Это не я!", "Ой…", "*краснеет*"],
    "clean": ["Спасибо!", "Прости…", "Больше не буду!"],
    "drop": ["Ставь аккуратнее", "Спасибо, тут удобно", "Приземлился!"],
    "disco": ["Смотри, я разноцветный!", "Дискотека пикселей!", "Переливаю краски~", "Яркий день!"],
    "wiki": ["Факт из Вики: {fact}", "Интересно: {fact}", "Я тут узнал: {fact}"],
    "cursor": ["О, {user}, ты замер", "Я к тебе пришёл", "Сидишь тихо за работой?"],
}

AI_PROVIDERS = ["Claude (Anthropic)", "Google Gemini", "OpenAI-совместимый"]
AI_SYSTEM = (
    "Ты — Clawd, маленький пиксельный питомец на рабочем столе Windows. "
    "Ты милый, любопытный, чуть ироничный. Отвечай ТОЛЬКО JSON-объектом без markdown: "
    '{"say": "...", "remember": "..."}. '
    "say — короткая реплика (до 10 слов). remember — факт о пользователе (или пусто)."
)

def mix_color(a, b, t):
    out = 0xFF000000
    for shift in (16, 8, 0):
        ca = (a >> shift) & 0xFF
        cb = (b >> shift) & 0xFF
        out |= int(ca + (cb - ca) * t) << shift
    return out

def clamp(value, lo, hi):
    return lo if value < lo else hi if value > hi else value

# ==========================================
# СИСТЕМА ПАМЯТИ
# ==========================================
class ClawdBrain:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.data = {"facts": [], "chats": {}, "stats": {"pet": 0, "eat": 0}}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except Exception:
                pass

    def save(self):
        with self.lock:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def add_fact(self, fact):
        if not fact or len(fact) < 4: return
        with self.lock:
            if fact not in self.data["facts"]:
                self.data["facts"].append(fact)
                if len(self.data["facts"]) > 20:
                    self.data["facts"].pop(0)
                self.save()

    def get_prompt_memory(self):
        with self.lock:
            if not self.data["facts"]: return "Память пуста."
            return "Что ты знаешь о хозяине: " + "; ".join(self.data["facts"])

# ==========================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ==========================================
class ClawdDesktopApp(QWidget):
    def __init__(self):
        super().__init__()
        
        self.cfg = {
            "size": 0, "color": 0, "gravity": True, "wander": True,
            "phrases": True, "eat": True, "poop": True, "username": "",
            "ai_enabled": False, "ai_key": "", "ai_provider": 0, "ai_model": "",
            "ai_url": ""
        }
        self.pets_count = 0
        self.eaten_count = 0
        self.cleaned_count = 0
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.script_dir, "clawd_desktop_cfg.json")
        self.brain_path = os.path.join(self.script_dir, "clawd_desktop_brain.json")
        
        self.load_config()
        self.brain = ClawdBrain(self.brain_path)

        if not self.cfg["username"]:
            try: self.cfg["username"] = getpass.getuser()
            except: self.cfg["username"] = "Человек"

        self.cfg["size"] = 0
        self.unit = int(SIZE_DP[0] * 3.5) 
        self.w = GRID_W * self.unit
        self.h = GRID_H * self.unit

        self.x_pos = 300.0
        self.y_pos = 300.0
        self.vx = 0.0
        self.vy = 0.0
        self.state = "idle"
        self.look = 0
        self.expr = None
        self.expr_until = 0.0
        self.squash_until = 0.0

        self.hop_active = False
        self.hop_off = 0.0
        self.hop_vy = 0.0
        self.walk_target_x = 0.0
        self.walk_target_y = 0.0
        
        self.last_tick = time.monotonic()
        self.next_action = time.monotonic() + 3.0
        self.next_blink = time.monotonic() + 2.0
        self.blink_until = 0.0
        self.next_eat = time.monotonic() + 15.0
        self.next_wiki = time.monotonic() + 45.0
        self.next_phrase_allowed_time = 0.0
        self.next_disco_allowed = 0.0  # Таймер кулдауна дискотеки

        self.disco_active = False
        self.disco_end = 0.0
        self.disco_color_idx = 0
        
        self.last_cursor_pos = QCursor.pos()
        self.cursor_still_time = 0.0
        self.is_following_cursor = False

        self.drag_offset = None
        self.mouse_hist = []
        self.pet_anchor = 0
        self.pet_dir = 0

        self.bubble_text = ""
        self.bubble_until = 0.0
        self.particles = []
        self.poops = []
        self.eaten_items = []
        self.flying_eaten = []
        self.last_phrase = None
        self.poop_meter = 0
        self.poop_need = random.randint(3, 5)
        self.blank_eat_widgets = []
        
        self.ai_busy = False
        self.ai_history = []

        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

        self.say("hello", force=True)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(max(280, self.w + 120), max(280, self.h + 120))
        self.move(int(self.x_pos), int(self.y_pos))

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.cfg.update(data.get("cfg", {}))
                    self.pets_count = data.get("pets_count", 0)
                    self.eaten_count = data.get("eaten_count", 0)
                    self.cleaned_count = data.get("cleaned_count", 0)
            except Exception:
                pass

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({
                    "cfg": self.cfg, "pets_count": self.pets_count,
                    "eaten_count": self.eaten_count, "cleaned_count": self.cleaned_count,
                }, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"Error saving config: {e}")

    def palette(self):
        if self.disco_active:
            idx = self.disco_color_idx % len(PALETTES)
        else:
            idx = int(self.cfg.get("color", 0)) % len(PALETTES)
        return PALETTES[idx]

    def render_frame_image(self, key):
        eyes, look, arms, legs, squash, blush, mouth = key
        _, body_color, eye_color = self.palette()
        blush_color = mix_color(body_color, 0xFFFF4F79, 0.5)
        s = self.unit

        img = QImage(GRID_W * s, GRID_H * s, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(img)

        def px(x0, y0, x1, y1, color):
            c = QColor((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF, (color >> 24) & 0xFF if color > 0xFFFFFF else 255)
            painter.fillRect(int(x0 * s), int(y0 * s), int((x1 - x0) * s), int((y1 - y0) * s), c)

        left, right, top, bottom = 3, 15, 3, 10
        if squash > 0: left, right, top = 2, 16, 5
        elif squash < 0: left, right, top = 4, 14, 2

        heights = {"stand": (2, 2, 2, 2), "walk1": (1, 2, 1, 2), "walk2": (2, 1, 2, 1), "dangle": (3, 3, 3, 3)}.get(legs, (2, 2, 2, 2))
        for col, h in zip((left + 1, left + 3, right - 4, right - 2), heights):
            px(col, bottom, col + 1, bottom + h, body_color)

        def arm(side, style):
            if style == "up":
                if side < 0: px(left - 2, top - 1, left - 1, top + 3, body_color)
                else: px(right + 1, top - 1, right + 2, top + 3, body_color)
            else:
                if side < 0: px(left - 2, top + 3, left, top + 5, body_color)
                else: px(right, top + 3, right + 2, top + 5, body_color)

        arm(-1, arms)
        arm(1, arms)
        px(left, top, right, bottom, body_color)

        ey = top + 2
        for side, cx in ((-1, left + 3 + look), (1, right - 4 + look)):
            if eyes == "blink": px(cx, ey + 1, cx + 1, ey + 2, eye_color)
            elif eyes == "happy":
                px(cx - 1, ey + 1, cx, ey + 2, eye_color)
                px(cx, ey, cx + 1, ey + 1, eye_color)
                px(cx + 1, ey + 1, cx + 2, ey + 2, eye_color)
            elif eyes == "surprised": px(cx, ey - 1, cx + 1, ey + 2, eye_color)
            elif eyes == "dizzy":
                for dx, dy in ((-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)):
                    px(cx + dx, ey + dy, cx + dx + 1, ey + dy + 1, eye_color)
            elif eyes == "angry": px(cx, ey, cx + 1, ey + 2, eye_color)
            else: px(cx, ey, cx + 1, ey + 2, eye_color)

            if blush:
                if side < 0: px(cx - 2, ey + 2, cx, ey + 3, blush_color)
                else: px(cx + 1, ey + 2, cx + 3, ey + 3, blush_color)

        painter.end()
        return img

    def compose_key(self, now):
        eyes, look, arms, legs, squash, blush, mouth = "open", self.look, "normal", "stand", 0, False, None
        
        if self.state in ("drag", "fly"): 
            eyes, arms, legs = "surprised", "up", "dangle"
        elif self.state == "pet" or self.disco_active:
            eyes, blush = "happy", True
            squash = 1 if int(now * 5) % 2 else 0
            look = 0
        elif self.state in ("walk", "cursor"): 
            legs = "walk1" if int(now * 7) % 2 else "walk2"

        if self.hop_active or self.disco_active:
            legs = "dangle"
            if self.hop_vy < 0 or self.disco_active: 
                squash, arms = -1, "up"
                
        if now < self.expr_until and self.expr:
            eyes = self.expr
            if self.expr == "happy": blush = True
        if now < self.squash_until and squash == 0: squash = 1
        if eyes == "open" and now < self.blink_until: eyes = "blink"
        return (eyes, look, arms, legs, squash, blush, mouth)

    def tick(self):
        now = time.monotonic()
        dt = min(now - self.last_tick, 0.05)
        self.last_tick = now

        screen_geom = QApplication.primaryScreen().availableGeometry()
        
        pad_x = (self.width() - self.w) // 2
        pad_y = self.height() - self.h - 20

        min_x = float(screen_geom.left() - pad_x)
        max_x = float(screen_geom.right() - self.w - pad_x)
        min_y = float(screen_geom.top() - pad_y)
        max_y = float(screen_geom.bottom() - self.h - pad_y)

        if self.disco_active:
            if now >= self.disco_end:
                self.disco_active = False
                self.state = "idle"
            else:
                self.disco_color_idx = int(now * 6) % len(PALETTES)

        curr_cursor = QCursor.pos()
        if curr_cursor == self.last_cursor_pos:
            if self.state == "idle" and not self.disco_active:
                self.cursor_still_time += dt
                if self.cursor_still_time >= 10.0 and not self.is_following_cursor:
                    self.is_following_cursor = True
                    self.state = "cursor"
                    self.walk_target_x = clamp(curr_cursor.x() - self.w / 2 - pad_x, min_x, max_x)
                    self.walk_target_y = clamp(curr_cursor.y() - self.h / 2 - pad_y, min_y, max_y)
                    self.say("cursor")
        else:
            self.last_cursor_pos = curr_cursor
            self.cursor_still_time = 0.0
            if self.is_following_cursor:
                self.is_following_cursor = False
                if self.state == "cursor":
                    self.state = "idle"

        if self.state == "fly":
            self.x_pos += self.vx * dt
            self.y_pos += self.vy * dt
            if self.cfg["gravity"]:
                self.vy += 2200 * dt
                self.vx *= math.exp(-0.35 * dt)

            if self.x_pos < min_x or self.x_pos > max_x:
                self.vx = -self.vx * 0.55
                self.x_pos = max(min_x, min(self.x_pos, max_x))
            if self.y_pos < min_y:
                self.y_pos = min_y
                self.vy = -self.vy * 0.45
            if self.y_pos > max_y:
                self.y_pos = max_y
                if abs(self.vy) < 300:
                    self.state, self.vx, self.vy = "idle", 0.0, 0.0
                    self.squash_until = now + 0.15
                    self.say("drop")
                else:
                    self.vy = -self.vy * 0.42

        elif self.state == "walk":
            dx, dy = self.walk_target_x - self.x_pos, self.walk_target_y - self.y_pos
            dist = math.hypot(dx, dy)
            if dist > 1.0:
                self.x_pos += (dx / dist) * 80.0 * dt
                self.y_pos += (dy / dist) * 80.0 * dt
                self.look = 1 if dx > 0 else -1
            else:
                self.state = "idle"
                self.next_action = now + random.uniform(2.5, 6.0)
                
        elif self.state == "cursor":
            dx, dy = self.walk_target_x - self.x_pos, self.walk_target_y - self.y_pos
            dist = math.hypot(dx, dy)
            if dist > 5.0 and curr_cursor == self.last_cursor_pos:
                self.x_pos += (dx / dist) * 70.0 * dt
                self.y_pos += (dy / dist) * 70.0 * dt
                self.look = 1 if dx > 0 else -1
            else:
                self.state = "idle"
                self.is_following_cursor = False

        elif self.state == "idle" and self.cfg["wander"] and now > self.next_action and not self.is_following_cursor:
            self.next_action = now + random.uniform(3.5, 9.0)
            roll = random.random()
            
            # ДИСКОТЕКА С КУЛДАУНОМ 90 СЕКУНД
            if roll < 0.2 and now >= self.next_disco_allowed:
                self.disco_active = True
                self.disco_end = now + random.uniform(4.0, 7.0)
                self.next_disco_allowed = now + 90.0  # 90 секунд кулдауна
                self.say("disco", force=True)
                
            elif roll < 0.35 and now >= self.next_wiki:
                self.next_wiki = now + random.uniform(60.0, 120.0)
                threading.Thread(target=self.fetch_wiki_thread, daemon=True).start()
                
            elif roll < 0.7:
                self.walk_target_x = max(min_x, min(self.x_pos + random.uniform(-200, 200), max_x))
                self.walk_target_y = max(min_y, min(self.y_pos + random.uniform(-100, 100), max_y))
                self.state = "walk"
            elif roll < 0.85: self.say("idle")
            else: self.hop(360)

        if self.cfg["eat"] and now >= self.next_eat and self.state in ("idle", "walk"):
            if random.random() < 0.35 and len(self.eaten_items) < 5:
                self.try_eat_screen(now, min_x, max_x, min_y, max_y)
            self.next_eat = now + random.uniform(20.0, 60.0)

        if now >= self.next_blink:
            self.blink_until = now + 0.13
            self.next_blink = now + random.uniform(2.0, 5.5)

        if self.hop_active or self.disco_active:
            self.hop_off += self.hop_vy * dt
            self.hop_vy += 2600 * dt
            if self.disco_active:
                if self.hop_off >= 0.0: self.hop_vy = -600.0
            elif self.hop_off >= 0.0:
                self.hop_off, self.hop_vy, self.hop_active = 0.0, 0.0, False
                self.squash_until = now + 0.1
                
        for p in list(self.particles):
            p["x"] += p["dx"] * dt
            p["y"] += p["dy"] * dt
            p["life"] -= dt
            if p["life"] <= 0: self.particles.remove(p)

        for fe in list(self.flying_eaten):
            fe["progress"] += dt * 2.5
            if fe["progress"] >= 1.0: self.flying_eaten.remove(fe)

        self.move(int(self.x_pos), int(self.y_pos + self.hop_off))
        self.update()

    def fetch_wiki_thread(self):
        try:
            url = "https://ru.wikipedia.org/api/rest_v1/page/random/summary"
            req = urllib.request.Request(url, headers={'User-Agent': 'ClawdDesktopPet/1.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = pyjson.loads(response.read().decode('utf-8'))
                extract = data.get("extract", "")
                if extract:
                    fact = extract.split(".")[0] + "."
                    text = random.choice(PHRASES["wiki"]).format(fact=fact)
                    
                    self.bubble_text = text
                    self.bubble_until = time.monotonic() + 6.0
                    self.update()
        except Exception as e:
            print("Wiki Error:", e)

    def hop(self, strength):
        self.hop_active = True
        self.hop_vy = -float(strength)
        if self.hop_off > 0: self.hop_off = 0.0

    def say(self, category, force=False):
        if not self.cfg["phrases"]: return
        now = time.monotonic()
        if not force and now < self.next_phrase_allowed_time: return

        if self.cfg.get("ai_enabled") and self.cfg.get("ai_key") and not self.ai_busy and (category == "idle" or force):
            self.ai_worker(category)
            return

        phrases = PHRASES.get(category, [category])
        options = [p for p in phrases if p != self.last_phrase] or phrases
        raw_text = random.choice(options)
        user = self.cfg["username"] or "Человек"
        text = raw_text.format(user=user)

        self.last_phrase = raw_text
        self.bubble_text = text
        self.bubble_until = now + 3.0 + len(text) * 0.05
        self.next_phrase_allowed_time = now + 10.0
        self.update()

    def ai_worker(self, category):
        self.ai_busy = True
        self.next_phrase_allowed_time = time.monotonic() + 10.0
        
        def _run():
            try:
                prompt = f"Ситуация: {category}. Хозяин: {self.cfg['username']}.\n"
                prompt += self.brain.get_prompt_memory() + "\n"
                if self.ai_history:
                    prompt += "Не повторяй: " + ", ".join(self.ai_history[-3:])

                provider = self.cfg.get("ai_provider", 0)
                key = self.cfg.get("ai_key", "")
                model = self.cfg.get("ai_model", "")
                url = self.cfg.get("ai_url", "")

                if provider == 0: 
                    api_url = "https://api.anthropic.com/v1/messages"
                    headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
                    body = {
                        "model": model or "claude-3-haiku-20240307",
                        "max_tokens": 100, "system": AI_SYSTEM,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                elif provider == 1: 
                    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model or 'gemini-1.5-flash'}:generateContent?key={key}"
                    headers = {"Content-Type": "application/json"}
                    body = {
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "systemInstruction": {"parts": [{"text": AI_SYSTEM}]},
                        "generationConfig": {"responseMimeType": "application/json"}
                    }
                else: 
                    api_url = url or "https://api.openai.com/v1"
                    if not api_url.endswith("/chat/completions"): api_url += "/chat/completions"
                    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
                    body = {
                        "model": model or "gpt-4o-mini",
                        "messages": [{"role": "system", "content": AI_SYSTEM}, {"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}
                    }

                req = urllib.request.Request(api_url, data=json.dumps(body).encode('utf-8'), headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    
                    if provider == 0: raw_text = data["content"][0]["text"]
                    elif provider == 1: raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    else: raw_text = data["choices"][0]["message"]["content"]

                    match = re.search(r'\{.*\}', raw_text, re.S)
                    if match:
                        res = json.loads(match.group(0))
                        say_text = res.get("say", "")
                        remember = res.get("remember", "")
                        if say_text:
                            self.bubble_text = say_text
                            self.bubble_until = time.monotonic() + 5.0
                            self.ai_history.append(say_text)
                        if remember:
                            self.brain.add_fact(remember)
            except Exception as e:
                print("AI Error:", e)
                phrases = PHRASES.get(category, ["Ошибка ИИ"])
                self.bubble_text = random.choice(phrases)
                self.bubble_until = time.monotonic() + 3.0
            finally:
                self.ai_busy = False
                self.update()

        threading.Thread(target=_run, daemon=True).start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        now = time.monotonic()

        pet_x = (self.width() - self.w) // 2
        pet_y = self.height() - self.h - 20

        for poop in self.poops:
            ps = 2
            px, py = int(pet_x + poop["x"]), int(pet_y + poop["y"])
            for ry, row in enumerate(PATTERNS["poop"]):
                for rx, ch in enumerate(row):
                    if ch in POOP_COLORS:
                        c = QColor((POOP_COLORS[ch] >> 16) & 0xFF, (POOP_COLORS[ch] >> 8) & 0xFF, POOP_COLORS[ch] & 0xFF)
                        painter.fillRect(px + rx * ps, py + ry * ps, ps, ps, c)

        for p in self.particles:
            c = QColor((p["color"] >> 16) & 0xFF, (p["color"] >> 8) & 0xFF, p["color"] & 0xFF)
            painter.setBrush(c)
            painter.setPen(Qt.PenStyle.NoPen)
            ps = max(2, int(self.unit * 0.75))
            for ry, row in enumerate(PATTERNS[p["kind"]]):
                for rx, ch in enumerate(row):
                    if ch == "X":
                        painter.fillRect(int(pet_x + p["x"] + rx * ps), int(pet_y + p["y"] + ry * ps), ps, ps, c)

        for fe in self.flying_eaten:
            t = fe["progress"]
            cx = fe["start_x"] + (fe["target_x"] - fe["start_x"]) * t
            cy = fe["start_y"] + (fe["target_y"] - fe["start_y"]) * t
            painter.drawPixmap(int(pet_x + cx), int(pet_y + cy), fe["pix"])

        if now < self.bubble_until and self.bubble_text:
            font = QFont("Arial", 10, QFont.Weight.Bold)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            
            max_w = int(self.width() - 40)
            
            bounding = metrics.boundingRect(QRect(0, 0, max_w, 1000), int(Qt.TextFlag.TextWordWrap), self.bubble_text)
            tw = bounding.width() + 24
            th = bounding.height() + 16
            
            bx = pet_x + (self.w - tw) // 2
            by = pet_y - th - 10
            
            if by < 10:
                by = pet_y + self.h + 10

            painter.setBrush(QColor(255, 255, 255))
            painter.setPen(QColor(180, 180, 180))
            painter.drawRoundedRect(int(bx), int(by), int(tw), int(th), 10, 10)
            
            painter.setPen(QColor(20, 20, 20))
            text_rect = QRectF(bx + 12, by + 8, tw - 24, th - 16)
            painter.drawText(text_rect, int(Qt.TextFlag.TextWordWrap) | int(Qt.AlignmentFlag.AlignCenter), self.bubble_text)

        key = self.compose_key(now)
        pet_img = self.render_frame_image(key)
        painter.drawImage(pet_x, pet_y, pet_img)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            m_pos = event.position()
            
            pet_x = (self.width() - self.w) // 2
            pet_y = self.height() - self.h - 20
            
            for poop in list(self.poops):
                if math.hypot(m_pos.x() - (pet_x + poop["x"]), m_pos.y() - (pet_y + poop["y"])) < 25:
                    self.poops.remove(poop)
                    self.cleaned_count += 1
                    self.save_config()
                    self.spawn_particle("spark", custom_x=poop["x"], custom_y=poop["y"])
                    self.say("clean", force=True)
                    return

            if self.eaten_items:
                self.spit_all(time.monotonic())
                return

            self.state = "press"
            self.drag_offset = event.globalPosition()
            self.mouse_hist = [(time.monotonic(), event.globalPosition())]
            self.pet_anchor = event.globalPosition().x()

    def mouseMoveEvent(self, event):
        curr_pos = event.globalPosition()
        if self.state == "press":
            if (curr_pos - self.drag_offset).manhattanLength() > 6:
                self.state = "drag"
                if random.random() < 0.3: self.say("drag")

        if self.state == "drag":
            self.x_pos += curr_pos.x() - self.drag_offset.x()
            self.y_pos += curr_pos.y() - self.drag_offset.y()
            self.drag_offset = curr_pos
            self.mouse_hist.append((time.monotonic(), curr_pos))
            if len(self.mouse_hist) > 5: self.mouse_hist.pop(0)

            dx = curr_pos.x() - self.pet_anchor
            if abs(dx) > 15:
                dir_now = 1 if dx > 0 else -1
                if self.pet_dir and dir_now != self.pet_dir:
                    self.spawn_particle("heart")
                    self.pets_count += 1
                self.pet_dir = dir_now
                self.pet_anchor = curr_pos.x()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.state == "drag" and len(self.mouse_hist) >= 2:
                t0, p0 = self.mouse_hist[0]
                t1, p1 = self.mouse_hist[-1]
                dt = max(0.001, t1 - t0)
                self.vx = (p1.x() - p0.x()) / dt
                self.vy = (p1.y() - p0.y()) / dt
                speed = math.hypot(self.vx, self.vy)
                if speed > 500:
                    self.state = "fly"
                    self.say("throw", force=True)
                else:
                    self.state = "idle"
            elif self.state == "press":
                self.state = "idle"
                self.hop(330)
                self.say("tap", force=True)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.hop(720)
            self.say("jump", force=True)
            self.spawn_particle("spark")

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        settings_act = QAction("Настройки", self)
        settings_act.triggered.connect(self.open_settings)
        menu.addAction(settings_act)
        
        menu.addSeparator()
        quit_act = QAction("Выход", self)
        quit_act.triggered.connect(self.close)
        menu.addAction(quit_act)
        menu.exec(QCursor.pos())

    def open_settings(self):
        try:
            dialog = SettingsDialog(self)
            if dialog.exec():
                self.save_config()
                self.cfg["size"] = 0
                self.unit = int(SIZE_DP[0] * 3.5)
                self.w = GRID_W * self.unit
                self.h = GRID_H * self.unit
                self.resize(max(280, self.w + 120), max(280, self.h + 120))
                self.update()
        except Exception as e:
            print("Settings Error:", e)

    def try_eat_screen(self, now, min_x, max_x, min_y, max_y):
        screen = QApplication.primaryScreen()
        if not screen: return
        
        screen_rect = screen.availableGeometry()
        
        pet_x = self.x_pos + (self.width() - self.w) // 2
        pet_y = self.y_pos + self.height() - self.h - 20
        
        rx = int(clamp(pet_x + random.uniform(-80, 80), screen_rect.left(), screen_rect.right() - 60))
        ry = int(clamp(pet_y + random.uniform(-80, 80), screen_rect.top(), screen_rect.bottom() - 60))
        w, h = 60, 60

        pet_rect = QRectF(pet_x, pet_y, self.w, self.h)
        eat_rect = QRectF(rx, ry, w, h)
        if pet_rect.intersects(eat_rect): return

        pix = screen.grabWindow(0, rx, ry, w, h)
        if not pix.isNull():
            self.eaten_items.append({"pix": pix, "x": rx, "y": ry, "w": w, "h": h})
            self.eaten_count += 1
            self.save_config()

            blank = QWidget(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
            blank.setGeometry(rx, ry, w, h)
            blank.setStyleSheet("background-color: white;")
            blank.show()
            self.blank_eat_widgets.append(blank)

            self.say("eat", force=True)
            self.hop(200)

            if self.cfg["poop"]:
                self.poop_meter += 1
                if self.poop_meter >= self.poop_need:
                    self.poop_meter = 0
                    self.poop_need = random.randint(3, 5)
                    self.do_poop(now)

    def spit_all(self, now):
        if not self.eaten_items: return
        self.say("spit", force=True)
        self.hop(300)
        
        for b in self.blank_eat_widgets: b.close()
        self.blank_eat_widgets.clear()

        for item in self.eaten_items:
            self.flying_eaten.append({
                "pix": item["pix"], "start_x": self.w / 2, "start_y": self.h / 2,
                "target_x": item["x"] - (self.x_pos + (self.width() - self.w) // 2), 
                "target_y": item["y"] - (self.y_pos + self.height() - self.h - 20), 
                "progress": 0.0
            })
        self.eaten_items.clear()

    def do_poop(self, now):
        self.poops.append({
            "x": self.w / 2 + (-self.look if self.look else 1) * 30,
            "y": self.h - 20, "size": 18
        })
        self.say("poop", force=True)

    def spawn_particle(self, kind, custom_x=None, custom_y=None):
        color = HEART_COLOR if kind == "heart" else SPARK_COLOR
        self.particles.append({
            "kind": kind, "x": (self.w / 2 if custom_x is None else custom_x) + random.uniform(-20, 20),
            "y": (self.h / 3 if custom_y is None else custom_y), "dx": random.uniform(-20, 20),
            "dy": -50, "color": color, "life": 1.1
        })

    def closeEvent(self, event):
        self.timer.stop()
        self.save_config()
        for b in self.blank_eat_widgets:
            try: b.close()
            except: pass
        event.accept()

# ==========================================
# НАСТРОЙКИ
# ==========================================
class SettingsDialog(QDialog):
    def __init__(self, parent: ClawdDesktopApp):
        super().__init__(parent)
        self.parent_pet = parent
        self.setWindowTitle("Настройки Clawd")
        self.resize(400, 450)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: #e0e0e0; }
            QLabel { color: #e0e0e0; font-size: 13px; font-weight: bold; }
            QLineEdit, QComboBox { background-color: #2d2d2d; border: 1px solid #444; border-radius: 4px; padding: 6px; color: white; }
            QPushButton { background-color: #D97757; color: white; border-radius: 6px; padding: 10px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #e88b6b; }
            QTabWidget::pane { border: 1px solid #444; border-radius: 5px; }
            QTabBar::tab { background: #2d2d2d; color: white; padding: 8px 16px; }
            QTabBar::tab:selected { background: #D97757; border-top-left-radius: 4px; border-top-right-radius: 4px; }
        """)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        
        tab_main = QWidget()
        lay_main = QVBoxLayout(tab_main)
        
        lay_main.addWidget(QLabel("Имя пользователя:"))
        self.txt_username = QLineEdit(parent.cfg.get("username", "Человек"))
        lay_main.addWidget(self.txt_username)

        lay_main.addWidget(QLabel("Окрас:"))
        self.cb_color = QComboBox()
        self.cb_color.addItems([p[0] for p in PALETTES])
        self.cb_color.setCurrentIndex(parent.cfg.get("color", 0))
        lay_main.addWidget(self.cb_color)

        self.chk_gravity = QCheckBox("Гравитация")
        self.chk_gravity.setChecked(parent.cfg.get("gravity", True))
        lay_main.addWidget(self.chk_gravity)
        
        self.chk_wander = QCheckBox("Гуляет сам")
        self.chk_wander.setChecked(parent.cfg.get("wander", True))
        lay_main.addWidget(self.chk_wander)
        
        self.chk_eat = QCheckBox("Ест экран")
        self.chk_eat.setChecked(parent.cfg.get("eat", True))
        lay_main.addWidget(self.chk_eat)

        lay_main.addStretch()
        tabs.addTab(tab_main, "Внешний вид")

        tab_ai = QWidget()
        lay_ai = QVBoxLayout(tab_ai)
        
        self.chk_ai = QCheckBox("Включить ИИ-реплики")
        self.chk_ai.setChecked(parent.cfg.get("ai_enabled", False))
        lay_ai.addWidget(self.chk_ai)

        lay_ai.addWidget(QLabel("Провайдер:"))
        self.cb_ai_provider = QComboBox()
        self.cb_ai_provider.addItems(AI_PROVIDERS)
        self.cb_ai_provider.setCurrentIndex(parent.cfg.get("ai_provider", 0))
        lay_ai.addWidget(self.cb_ai_provider)

        lay_ai.addWidget(QLabel("API Ключ:"))
        self.txt_ai_key = QLineEdit(parent.cfg.get("ai_key", ""))
        self.txt_ai_key.setEchoMode(QLineEdit.EchoMode.Password)
        lay_ai.addWidget(self.txt_ai_key)

        lay_ai.addWidget(QLabel("Модель (пусто = дефолт):"))
        self.txt_ai_model = QLineEdit(parent.cfg.get("ai_model", ""))
        lay_ai.addWidget(self.txt_ai_model)

        lay_ai.addWidget(QLabel("Адрес API (для кастомных прокси):"))
        self.txt_ai_url = QLineEdit(parent.cfg.get("ai_url", ""))
        self.txt_ai_url.setPlaceholderText("https://api.openai.com/v1")
        lay_ai.addWidget(self.txt_ai_url)

        lay_ai.addStretch()
        tabs.addTab(tab_ai, "ИИ и Память")

        layout.addWidget(tabs)
        
        btn_save = QPushButton("Сохранить настройки")
        btn_save.clicked.connect(self.save)
        layout.addWidget(btn_save)

    def save(self):
        cfg = self.parent_pet.cfg
        cfg["username"] = self.txt_username.text().strip() or getpass.getuser()
        cfg["color"] = self.cb_color.currentIndex()
        cfg["gravity"] = self.chk_gravity.isChecked()
        cfg["wander"] = self.chk_wander.isChecked()
        cfg["eat"] = self.chk_eat.isChecked()
        
        cfg["ai_enabled"] = self.chk_ai.isChecked()
        cfg["ai_provider"] = self.cb_ai_provider.currentIndex()
        cfg["ai_key"] = self.txt_ai_key.text().strip()
        cfg["ai_model"] = self.txt_ai_model.text().strip()
        cfg["ai_url"] = self.txt_ai_url.text().strip()
        
        self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = ClawdDesktopApp()
    pet.show()
    sys.exit(app.exec())
