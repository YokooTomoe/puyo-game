import pygame
import sys
import random
import json
import os
import math
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

# 定数
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BOARD_WIDTH = 6
BOARD_HEIGHT = 12
CELL_SIZE = 40
BOARD_X = 50
BOARD_Y = 50

# 色定義
class PuyoColor(Enum):
    EMPTY = 0
    RED = 1
    BLUE = 2
    GREEN = 3
    YELLOW = 4
    OJAMA = 5  # おじゃまぷよ

# 色のRGB値（フォールバック用）
COLORS = {
    PuyoColor.EMPTY: (0, 0, 0),
    PuyoColor.RED: (255, 0, 0),
    PuyoColor.BLUE: (0, 0, 255),
    PuyoColor.GREEN: (0, 255, 0),
    PuyoColor.YELLOW: (255, 255, 0),
    PuyoColor.OJAMA: (180, 180, 180)  # グレー
}

# スコアランキング機能のデータ構造
@dataclass
class ScoreEntry:
    """個別のスコア記録を表現するクラス"""
    score: int
    player_name: str
    date_time: datetime
    chain_count: int
    level_reached: int
    play_time: int  # 秒単位
    
    def to_dict(self) -> dict:
        """JSON保存用の辞書変換"""
        return {
            'score': self.score,
            'player_name': self.player_name,
            'date_time': self.date_time.isoformat(),
            'chain_count': self.chain_count,
            'level_reached': self.level_reached,
            'play_time': self.play_time
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScoreEntry':
        """辞書からオブジェクト復元"""
        return cls(
            score=data['score'],
            player_name=data['player_name'],
            date_time=datetime.fromisoformat(data['date_time']),
            chain_count=data['chain_count'],
            level_reached=data['level_reached'],
            play_time=data['play_time']
        )

@dataclass
class PlayerStatistics:
    """プレイヤー統計情報を管理するクラス"""
    player_name: str
    total_games: int = 0
    total_score: int = 0
    best_score: int = 0
    best_chain: int = 0
    total_play_time: int = 0
    average_score: float = 0.0
    games_this_session: int = 0
    first_play: Optional[datetime] = None
    last_play: Optional[datetime] = None
    
    def update_stats(self, score: int, chain_count: int, play_time: int):
        """統計を更新"""
        self.total_games += 1
        self.games_this_session += 1
        self.total_score += score
        self.total_play_time += play_time
        
        if score > self.best_score:
            self.best_score = score
        if chain_count > self.best_chain:
            self.best_chain = chain_count
            
        self.calculate_average()
        self.last_play = datetime.now()
        
        if self.first_play is None:
            self.first_play = datetime.now()
    
    def calculate_average(self):
        """平均スコアを計算"""
        if self.total_games > 0:
            self.average_score = self.total_score / self.total_games
        else:
            self.average_score = 0.0
    
    def to_dict(self) -> dict:
        """JSON保存用の辞書変換"""
        return {
            'player_name': self.player_name,
            'total_games': self.total_games,
            'total_score': self.total_score,
            'best_score': self.best_score,
            'best_chain': self.best_chain,
            'total_play_time': self.total_play_time,
            'average_score': self.average_score,
            'games_this_session': self.games_this_session,
            'first_play': self.first_play.isoformat() if self.first_play else None,
            'last_play': self.last_play.isoformat() if self.last_play else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerStatistics':
        """辞書からオブジェクト復元"""
        stats = cls(
            player_name=data['player_name'],
            total_games=data.get('total_games', 0),
            total_score=data.get('total_score', 0),
            best_score=data.get('best_score', 0),
            best_chain=data.get('best_chain', 0),
            total_play_time=data.get('total_play_time', 0),
            average_score=data.get('average_score', 0.0),
            games_this_session=data.get('games_this_session', 0)
        )
        
        if data.get('first_play'):
            stats.first_play = datetime.fromisoformat(data['first_play'])
        if data.get('last_play'):
            stats.last_play = datetime.fromisoformat(data['last_play'])
            
        return stats

# 色別パーティクル設定
PARTICLE_COLORS = {
    PuyoColor.RED: {
        'base_color': (255, 100, 100),
        'variants': [(255, 150, 100), (255, 200, 150)],  # 炎効果
        'gravity': 0.15,  # 軽い（炎は上昇気流）
    },
    PuyoColor.BLUE: {
        'base_color': (100, 150, 255),
        'variants': [(150, 200, 255), (200, 220, 255)],  # 水滴効果
        'gravity': 0.25,  # 重い（水は重力に従う）
    },
    PuyoColor.GREEN: {
        'base_color': (100, 255, 100),
        'variants': [(150, 255, 150), (200, 255, 200)],  # 葉っぱ効果
        'gravity': 0.1,   # 軽い（葉っぱは舞い散る）
    },
    PuyoColor.YELLOW: {
        'base_color': (255, 255, 100),
        'variants': [(255, 255, 150), (255, 255, 200)],  # 星効果
        'gravity': 0.05,  # 最軽量（星は輝く）
    }
}

# スコアランキング機能のデータ構造
@dataclass
class ScoreEntry:
    """個別のスコア記録を表現するクラス"""
    score: int
    player_name: str
    date_time: datetime
    chain_count: int
    level_reached: int
    play_time: int  # 秒単位
    
    def to_dict(self) -> dict:
        """JSON保存用の辞書変換"""
        return {
            'score': self.score,
            'player_name': self.player_name,
            'date_time': self.date_time.isoformat(),
            'chain_count': self.chain_count,
            'level_reached': self.level_reached,
            'play_time': self.play_time
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScoreEntry':
        """辞書からオブジェクト復元"""
        return cls(
            score=data['score'],
            player_name=data['player_name'],
            date_time=datetime.fromisoformat(data['date_time']),
            chain_count=data['chain_count'],
            level_reached=data['level_reached'],
            play_time=data['play_time']
        )
    
    def __lt__(self, other):
        """ソート用の比較演算子（スコア降順、同スコアなら日時昇順）"""
        if self.score != other.score:
            return self.score > other.score  # スコア降順
        return self.date_time < other.date_time  # 日時昇順

class RankingManager:
    """トップ10ランキングの管理クラス"""
    def __init__(self, max_entries: int = 10):
        self.rankings: List[ScoreEntry] = []
        self.max_entries = max_entries
    
    def add_score(self, score_entry: ScoreEntry) -> int:
        """新しいスコアを追加し、順位を返す（0-based、-1は圏外）"""
        self.rankings.append(score_entry)
        self.rankings.sort()  # ScoreEntry.__lt__でソート
        
        # 最大数を超えた場合は削除
        if len(self.rankings) > self.max_entries:
            self.rankings = self.rankings[:self.max_entries]
        
        # 順位を返す（追加されたエントリが残っている場合）
        try:
            return self.rankings.index(score_entry)
        except ValueError:
            return -1  # 圏外
    
    def is_high_score(self, score: int) -> bool:
        """ハイスコア判定"""
        if len(self.rankings) < self.max_entries:
            return True  # まだ枠がある
        return score > self.rankings[-1].score  # 最下位より高い
    
    def get_ranking(self) -> List[ScoreEntry]:
        """ランキング取得（スコア順）"""
        return self.rankings.copy()
    
    def get_player_best(self, player_name: str) -> Optional[ScoreEntry]:
        """特定プレイヤーの最高記録"""
        player_entries = [entry for entry in self.rankings if entry.player_name == player_name]
        return player_entries[0] if player_entries else None
    
    def filter_by_player(self, player_name: str) -> List[ScoreEntry]:
        """プレイヤー別記録フィルタ"""
        return [entry for entry in self.rankings if entry.player_name == player_name]

class PlayerInputDialog:
    """プレイヤー名入力ダイアログクラス"""
    def __init__(self, screen, font, small_font):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.input_text = ""
        self.max_length = 10
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        
    def show_dialog(self, score: int) -> str:
        """プレイヤー名入力ダイアログを表示し、入力された名前を返す"""
        self.input_text = ""
        self.active = True
        self.cursor_visible = True
        self.cursor_timer = 0
        
        clock = pygame.time.Clock()
        
        while self.active:
            dt = clock.tick(60)
            self.cursor_timer += dt
            
            # カーソル点滅
            if self.cursor_timer >= 500:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if self.handle_input(event):
                        break
            
            self.draw_dialog(score)
            pygame.display.flip()
        
        # 空白の場合はデフォルト名
        return self.input_text.strip() if self.input_text.strip() else "名無し"
    
    def handle_input(self, event) -> bool:
        """キーボード入力処理。Trueを返すとダイアログ終了"""
        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            # Enterキーで確定
            self.active = False
            return True
        elif event.key == pygame.K_ESCAPE:
            # Escapeキーでキャンセル（デフォルト名使用）
            self.input_text = ""
            self.active = False
            return True
        elif event.key == pygame.K_BACKSPACE:
            # バックスペースで文字削除
            if self.input_text:
                self.input_text = self.input_text[:-1]
        else:
            # 文字入力
            if len(self.input_text) < self.max_length:
                char = self.get_char_from_event(event)
                if char:
                    self.input_text += char
        
        return False
    
    def get_char_from_event(self, event) -> str:
        """キーイベントから文字を取得"""
        # 基本的な英数字と記号
        if event.unicode and event.unicode.isprintable():
            # 不適切な文字をフィルタリング
            forbidden_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
            if event.unicode not in forbidden_chars:
                return event.unicode
        return ""
    
    def draw_dialog(self, score: int):
        """ダイアログを描画"""
        # 背景を暗くする
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # ダイアログボックス
        dialog_width = 400
        dialog_height = 200
        dialog_x = (WINDOW_WIDTH - dialog_width) // 2
        dialog_y = (WINDOW_HEIGHT - dialog_height) // 2
        
        # ダイアログ背景
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, (60, 60, 60), dialog_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), dialog_rect, 3)
        
        # タイトル
        title_text = self.font.render("ハイスコア達成！", True, (255, 255, 0))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, dialog_y + 30))
        self.screen.blit(title_text, title_rect)
        
        # スコア表示
        score_text = self.small_font.render(f"スコア: {score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, dialog_y + 60))
        self.screen.blit(score_text, score_rect)
        
        # 入力案内
        prompt_text = self.small_font.render("プレイヤー名を入力してください:", True, (255, 255, 255))
        prompt_rect = prompt_text.get_rect(center=(WINDOW_WIDTH // 2, dialog_y + 90))
        self.screen.blit(prompt_text, prompt_rect)
        
        # 入力ボックス
        input_box_width = 300
        input_box_height = 30
        input_box_x = (WINDOW_WIDTH - input_box_width) // 2
        input_box_y = dialog_y + 110
        
        input_box_rect = pygame.Rect(input_box_x, input_box_y, input_box_width, input_box_height)
        pygame.draw.rect(self.screen, (255, 255, 255), input_box_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), input_box_rect, 2)
        
        # 入力テキスト
        if self.input_text or not self.cursor_visible:
            text_surface = self.small_font.render(self.input_text, True, (0, 0, 0))
            text_x = input_box_x + 5
            text_y = input_box_y + (input_box_height - text_surface.get_height()) // 2
            self.screen.blit(text_surface, (text_x, text_y))
        
        # カーソル
        if self.cursor_visible:
            cursor_x = input_box_x + 5 + (self.small_font.size(self.input_text)[0] if self.input_text else 0)
            cursor_y = input_box_y + 5
            pygame.draw.line(self.screen, (0, 0, 0), 
                           (cursor_x, cursor_y), (cursor_x, cursor_y + 20), 2)
        
        # 操作案内
        help_text = self.small_font.render("Enter: 確定  Escape: キャンセル", True, (200, 200, 200))
        help_rect = help_text.get_rect(center=(WINDOW_WIDTH // 2, dialog_y + 160))
        self.screen.blit(help_text, help_rect)

class RankingDisplay:
    """ランキング表示画面クラス"""
    def __init__(self, screen, font, small_font, big_font):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.big_font = big_font
        self.active = False
        self.scroll_position = 0
        
    def show_ranking(self, ranking_manager: 'RankingManager'):
        """ランキング画面を表示"""
        self.active = True
        self.scroll_position = 0
        
        clock = pygame.time.Clock()
        
        while self.active:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if self.handle_input(event):
                        break
            
            self.draw_ranking_screen(ranking_manager)
            pygame.display.flip()
    
    def handle_input(self, event) -> bool:
        """キーボード入力処理。Trueを返すと画面終了"""
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_r:
            # EscapeキーまたはRキーで戻る
            self.active = False
            return True
        elif event.key == pygame.K_UP:
            # 上スクロール
            self.scroll_position = max(0, self.scroll_position - 1)
        elif event.key == pygame.K_DOWN:
            # 下スクロール
            self.scroll_position = min(9, self.scroll_position + 1)  # 最大10エントリ
        
        return False
    
    def draw_ranking_screen(self, ranking_manager: 'RankingManager'):
        """ランキング画面を描画"""
        # 背景
        self.screen.fill((30, 30, 50))
        
        # タイトル
        title_text = self.big_font.render("ランキング", True, (255, 255, 0))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 50))
        self.screen.blit(title_text, title_rect)
        
        # ランキングデータを取得
        rankings = ranking_manager.get_ranking()
        
        if not rankings:
            # ランキングが空の場合
            no_data_text = self.font.render("まだ記録がありません", True, (255, 255, 255))
            no_data_rect = no_data_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(no_data_text, no_data_rect)
        else:
            # ヘッダー
            header_y = 120
            self.draw_header(header_y)
            
            # ランキングエントリ
            start_y = 160
            entry_height = 35
            
            for i, entry in enumerate(rankings):
                if i < self.scroll_position:
                    continue
                if i >= self.scroll_position + 10:  # 画面に10個まで表示
                    break
                
                y_pos = start_y + (i - self.scroll_position) * entry_height
                self.draw_entry(entry, i + 1, y_pos)
        
        # 操作案内
        self.draw_controls()
    
    def draw_header(self, y_pos: int):
        """ヘッダーを描画"""
        # ヘッダー背景
        header_rect = pygame.Rect(50, y_pos - 5, WINDOW_WIDTH - 100, 30)
        pygame.draw.rect(self.screen, (60, 60, 80), header_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), header_rect, 2)
        
        # ヘッダーテキスト
        rank_text = self.small_font.render("順位", True, (255, 255, 255))
        name_text = self.small_font.render("プレイヤー名", True, (255, 255, 255))
        score_text = self.small_font.render("スコア", True, (255, 255, 255))
        chain_text = self.small_font.render("最大連鎖", True, (255, 255, 255))
        date_text = self.small_font.render("達成日時", True, (255, 255, 255))
        
        self.screen.blit(rank_text, (70, y_pos))
        self.screen.blit(name_text, (150, y_pos))
        self.screen.blit(score_text, (300, y_pos))
        self.screen.blit(chain_text, (400, y_pos))
        self.screen.blit(date_text, (520, y_pos))
    
    def draw_entry(self, entry: ScoreEntry, rank: int, y_pos: int):
        """個別エントリを描画"""
        # 背景色（順位に応じて）
        if rank == 1:
            bg_color = (80, 60, 20)  # 金色っぽい
        elif rank == 2:
            bg_color = (60, 60, 60)  # 銀色っぽい
        elif rank == 3:
            bg_color = (60, 40, 20)  # 銅色っぽい
        else:
            bg_color = (40, 40, 50)  # 通常
        
        # エントリ背景
        entry_rect = pygame.Rect(50, y_pos - 2, WINDOW_WIDTH - 100, 30)
        pygame.draw.rect(self.screen, bg_color, entry_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), entry_rect, 1)
        
        # テキスト色（順位に応じて）
        if rank == 1:
            text_color = (255, 215, 0)  # 金色
        elif rank == 2:
            text_color = (192, 192, 192)  # 銀色
        elif rank == 3:
            text_color = (205, 127, 50)  # 銅色
        else:
            text_color = (255, 255, 255)  # 白色
        
        # 順位
        rank_text = self.small_font.render(f"{rank}", True, text_color)
        self.screen.blit(rank_text, (80, y_pos))
        
        # プレイヤー名（長い場合は省略）
        player_name = entry.player_name
        if len(player_name) > 8:
            player_name = player_name[:7] + "..."
        name_text = self.small_font.render(player_name, True, text_color)
        self.screen.blit(name_text, (150, y_pos))
        
        # スコア
        score_text = self.small_font.render(f"{entry.score:,}", True, text_color)
        self.screen.blit(score_text, (300, y_pos))
        
        # 最大連鎖
        chain_text = self.small_font.render(f"{entry.chain_count}", True, text_color)
        self.screen.blit(chain_text, (430, y_pos))
        
        # 達成日時
        date_str = entry.date_time.strftime("%m/%d %H:%M")
        date_text = self.small_font.render(date_str, True, text_color)
        self.screen.blit(date_text, (520, y_pos))
    
    def draw_controls(self):
        """操作案内を描画"""
        controls = [
            "操作方法:",
            "↑↓: スクロール",
            "Escape/R: 戻る"
        ]
        
        y_offset = WINDOW_HEIGHT - 80
        for control in controls:
            text = self.small_font.render(control, True, (200, 200, 200))
            self.screen.blit(text, (50, y_offset))
            y_offset += 25

class Particle:
    """個別パーティクルクラス"""
    def __init__(self, x, y, puyo_color, velocity_x, velocity_y, chain_level=1):
        self.x = x
        self.y = y
        self.puyo_color = puyo_color
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.life = 1.0  # 寿命（1.0→0.0）
        self.chain_level = chain_level
        self.time = 0  # 時間カウンター（虹色エフェクト用）
        
        # 基本サイズ（連鎖レベルで調整）
        base_size = random.randint(2, 6)
        if chain_level >= 3:
            self.size = int(base_size * 1.2)  # 3連鎖以上でサイズアップ
        else:
            self.size = base_size
        
        # 5連鎖以上で虹色パーティクルの可能性
        self.is_rainbow = chain_level >= 5 and random.random() < 0.2
        
        # 色別設定を適用
        if self.is_rainbow:
            self.color = (255, 255, 255)  # 初期色（後で変化）
            self.gravity = 0.05  # 虹色は軽い
        elif puyo_color in PARTICLE_COLORS:
            config = PARTICLE_COLORS[puyo_color]
            self.gravity = config['gravity']
            # ランダムに基本色または変種色を選択
            colors = [config['base_color']] + config['variants']
            self.color = random.choice(colors)
        else:
            self.gravity = 0.2
            self.color = COLORS.get(puyo_color, (255, 255, 255))
        
    def update(self):
        """パーティクルの状態を更新"""
        self.time += 1  # 時間カウンター更新
        
        # 虹色パーティクルの色更新
        if self.is_rainbow:
            self.color = self.get_rainbow_color()
            # 虹色は特別な動き（キラキラ）
            self.velocity_x += random.uniform(-0.2, 0.2)
            self.velocity_y += random.uniform(-0.2, 0.2)
        else:
            # 色別特殊効果
            if self.puyo_color == PuyoColor.RED:
                # 赤：上昇気流効果（炎）
                self.velocity_y -= 0.1  # 上向きの力
                self.velocity_x += random.uniform(-0.2, 0.2)  # 揺らぎ
            elif self.puyo_color == PuyoColor.BLUE:
                # 青：重い水滴効果
                pass  # 通常の重力のみ
            elif self.puyo_color == PuyoColor.GREEN:
                # 緑：葉っぱの舞い散り効果
                self.velocity_x += random.uniform(-0.3, 0.3)  # 横風
            elif self.puyo_color == PuyoColor.YELLOW:
                # 黄：星の輝き効果（ランダム移動）
                self.velocity_x += random.uniform(-0.1, 0.1)
                self.velocity_y += random.uniform(-0.1, 0.1)
            elif self.puyo_color == PuyoColor.OJAMA:
                # おじゃま：バウンド効果
                if random.random() < 0.1:
                    self.velocity_x = -self.velocity_x * 0.8
                self.velocity_y += 0.3  # 重い
        
        # 位置更新
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 重力適用
        self.velocity_y += self.gravity
        
        # 寿命減少
        self.life -= 0.02  # 約50フレームで消滅
        
    def is_alive(self):
        """生存判定"""
        return self.life > 0 and self.y < WINDOW_HEIGHT + 50
        
    def get_alpha(self):
        """透明度計算（寿命に基づく）"""
        return max(0, min(255, int(self.life * 255)))
    
    def get_rainbow_color(self):
        """虹色の計算（時間に基づく）"""
        # HSVからRGBへの簡易変換
        hue = (self.time * 5) % 360  # 色相を時間で変化
        saturation = 1.0
        value = 1.0
        
        # 簡易HSV→RGB変換
        c = value * saturation
        x = c * (1 - abs((hue / 60) % 2 - 1))
        m = value - c
        
        if 0 <= hue < 60:
            r, g, b = c, x, 0
        elif 60 <= hue < 120:
            r, g, b = x, c, 0
        elif 120 <= hue < 180:
            r, g, b = 0, c, x
        elif 180 <= hue < 240:
            r, g, b = 0, x, c
        elif 240 <= hue < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

class RankingManager:
    """トップ10ランキングの管理クラス"""
    def __init__(self):
        self.rankings: List[ScoreEntry] = []
        self.max_entries = 10
    
    def add_score(self, score_entry: ScoreEntry) -> int:
        """新しいスコアを追加し、順位を返す"""
        # スコア順（降順）で挿入位置を見つける
        insert_position = 0
        for i, entry in enumerate(self.rankings):
            if score_entry.score > entry.score:
                insert_position = i
                break
            elif score_entry.score == entry.score:
                # 同じスコアの場合は達成日時の早い順
                if score_entry.date_time < entry.date_time:
                    insert_position = i
                    break
            insert_position = i + 1
        
        # 挿入
        self.rankings.insert(insert_position, score_entry)
        
        # トップ10に制限
        if len(self.rankings) > self.max_entries:
            self.rankings = self.rankings[:self.max_entries]
        
        # 順位を返す（1から始まる）
        return insert_position + 1 if insert_position < self.max_entries else -1
    
    def is_high_score(self, score: int) -> bool:
        """ハイスコア判定"""
        if len(self.rankings) < self.max_entries:
            return True
        return score > self.rankings[-1].score
    
    def get_ranking(self) -> List[ScoreEntry]:
        """ランキング取得（スコア順）"""
        return self.rankings.copy()
    
    def get_player_best(self, player_name: str) -> Optional[ScoreEntry]:
        """特定プレイヤーの最高記録"""
        player_entries = [entry for entry in self.rankings if entry.player_name == player_name]
        return player_entries[0] if player_entries else None
    
    def filter_by_player(self, player_name: str) -> List[ScoreEntry]:
        """プレイヤー別記録フィルタ"""
        return [entry for entry in self.rankings if entry.player_name == player_name]
    
    def clear_ranking(self):
        """ランキングをクリア"""
        self.rankings.clear()
    
    def remove_entry(self, index: int) -> bool:
        """特定の記録を削除"""
        if 0 <= index < len(self.rankings):
            self.rankings.pop(index)
            return True
        return False

class DataPersistence:
    """ランキングデータの保存・読み込み管理クラス"""
    def __init__(self):
        self.ranking_file = "ranking.json"
        self.stats_file = "statistics.json"
        self.backup_dir = "backups"
    
    def save_ranking(self, rankings: List[ScoreEntry]):
        """ランキングデータ保存"""
        try:
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "rankings": [entry.to_dict() for entry in rankings]
            }
            
            # バックアップ作成
            self.create_backup()
            
            # メインファイルに保存
            with open(self.ranking_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"ランキングデータの保存に失敗しました: {e}")
    
    def load_ranking(self) -> List[ScoreEntry]:
        """ランキングデータ読み込み"""
        try:
            if not os.path.exists(self.ranking_file):
                return []
            
            with open(self.ranking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            rankings = []
            for entry_data in data.get('rankings', []):
                try:
                    rankings.append(ScoreEntry.from_dict(entry_data))
                except Exception as e:
                    print(f"スコアエントリの読み込みに失敗: {e}")
                    continue
            
            return rankings
            
        except Exception as e:
            print(f"ランキングデータの読み込みに失敗しました: {e}")
            # バックアップから復元を試みる
            return self.restore_from_backup()
    
    def save_statistics(self, stats_dict: dict):
        """統計データ保存"""
        try:
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "players": {name: stats.to_dict() for name, stats in stats_dict.items()},
                "global_stats": self.calculate_global_stats(stats_dict)
            }
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"統計データの保存に失敗しました: {e}")
    
    def load_statistics(self) -> dict:
        """統計データ読み込み"""
        try:
            if not os.path.exists(self.stats_file):
                return {}
            
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stats_dict = {}
            for name, stats_data in data.get('players', {}).items():
                try:
                    stats_dict[name] = PlayerStatistics.from_dict(stats_data)
                except Exception as e:
                    print(f"プレイヤー統計の読み込みに失敗: {e}")
                    continue
            
            return stats_dict
            
        except Exception as e:
            print(f"統計データの読み込みに失敗しました: {e}")
            return {}
    
    def create_backup(self):
        """バックアップ作成"""
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
            
            if os.path.exists(self.ranking_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(self.backup_dir, f"ranking_backup_{timestamp}.json")
                
                import shutil
                shutil.copy2(self.ranking_file, backup_file)
                
                # 古いバックアップを削除（最新5個まで保持）
                self.cleanup_old_backups()
                
        except Exception as e:
            print(f"バックアップの作成に失敗しました: {e}")
    
    def restore_from_backup(self) -> List[ScoreEntry]:
        """最新のバックアップから復元"""
        try:
            if not os.path.exists(self.backup_dir):
                return []
            
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith("ranking_backup_")]
            if not backup_files:
                return []
            
            # 最新のバックアップファイルを選択
            latest_backup = max(backup_files)
            backup_path = os.path.join(self.backup_dir, latest_backup)
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            rankings = []
            for entry_data in data.get('rankings', []):
                try:
                    rankings.append(ScoreEntry.from_dict(entry_data))
                except Exception:
                    continue
            
            print(f"バックアップから復元しました: {latest_backup}")
            return rankings
            
        except Exception as e:
            print(f"バックアップからの復元に失敗しました: {e}")
            return []
    
    def cleanup_old_backups(self):
        """古いバックアップファイルを削除"""
        try:
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith("ranking_backup_")]
            backup_files.sort(reverse=True)  # 新しい順
            
            # 5個を超える古いバックアップを削除
            for old_backup in backup_files[5:]:
                os.remove(os.path.join(self.backup_dir, old_backup))
                
        except Exception as e:
            print(f"古いバックアップの削除に失敗しました: {e}")
    
    def calculate_global_stats(self, stats_dict: dict) -> dict:
        """グローバル統計を計算"""
        if not stats_dict:
            return {
                "total_games_played": 0,
                "unique_players": 0,
                "highest_score_ever": 0,
                "longest_chain_ever": 0
            }
        
        total_games = sum(stats.total_games for stats in stats_dict.values())
        highest_score = max((stats.best_score for stats in stats_dict.values()), default=0)
        longest_chain = max((stats.best_chain for stats in stats_dict.values()), default=0)
        
        return {
            "total_games_played": total_games,
            "unique_players": len(stats_dict),
            "highest_score_ever": highest_score,
            "longest_chain_ever": longest_chain
        }

class ParticleSystem:
    """パーティクルシステム管理クラス"""
    def __init__(self):
        self.particles = []
        self.max_particles = 500  # 最大パーティクル数
        
    def emit_particles(self, x, y, puyo_color, count=8, chain_level=1):
        """パーティクルを生成"""
        # 連鎖レベルに応じてパーティクル数調整
        if chain_level >= 2:
            actual_count = min(int(count * 1.5), 25)  # 2連鎖以上で1.5倍
        else:
            actual_count = count
        
        for _ in range(actual_count):
            # ランダムな方向と速度
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.0, 6.0)
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed - 2.0  # 上向きに初期バイアス
            
            # パーティクル生成（連鎖レベルを渡す）
            particle = Particle(x, y, puyo_color, velocity_x, velocity_y, chain_level)
            self.particles.append(particle)
            
            # 最大数制限
            if len(self.particles) >= self.max_particles:
                break
                
    def update(self):
        """全パーティクルの更新"""
        # 生きているパーティクルのみ更新
        alive_particles = []
        for particle in self.particles:
            particle.update()
            if particle.is_alive():
                alive_particles.append(particle)
        
        self.particles = alive_particles
        
    def draw(self, screen):
        """全パーティクルの描画"""
        for particle in self.particles:
            alpha = particle.get_alpha()
            if alpha > 0:
                self.draw_particle_shape(screen, particle)
    
    def draw_particle_shape(self, screen, particle):
        """パーティクルの形状別描画"""
        x, y = int(particle.x), int(particle.y)
        size = particle.size
        color = particle.color
        
        if particle.puyo_color == PuyoColor.RED:
            # 炎：縦長の楕円 + 揺らぎ
            flame_height = size * 2
            flame_width = max(1, size // 2)
            # 揺らぎ効果
            offset_x = random.randint(-1, 1)
            offset_y = random.randint(-2, 0)
            pygame.draw.ellipse(screen, color, 
                              (x - flame_width + offset_x, y - flame_height + offset_y, 
                               flame_width * 2, flame_height))
                               
        elif particle.puyo_color == PuyoColor.BLUE:
            # 水滴：涙型（楕円 + 小さな円）
            # メイン部分（楕円）
            pygame.draw.ellipse(screen, color, (x - size//2, y - size, size, size * 2))
            # 上部の小さな円（涙の先端）
            pygame.draw.circle(screen, color, (x, y - size), max(1, size//3))
            
        elif particle.puyo_color == PuyoColor.GREEN:
            # 葉っぱ：小さな楕円を回転
            leaf_width = size
            leaf_height = size // 2
            # 簡易的な葉っぱ形状
            pygame.draw.ellipse(screen, color, (x - leaf_width//2, y - leaf_height//2, 
                                              leaf_width, leaf_height))
            # 葉脈（線）
            pygame.draw.line(screen, color, (x - leaf_width//2, y), (x + leaf_width//2, y), 1)
            
        elif particle.puyo_color == PuyoColor.YELLOW:
            # 星：十字形
            star_size = size
            # 縦線
            pygame.draw.line(screen, color, (x, y - star_size), (x, y + star_size), 2)
            # 横線
            pygame.draw.line(screen, color, (x - star_size, y), (x + star_size, y), 2)
            # 中心の円
            pygame.draw.circle(screen, color, (x, y), max(1, star_size//3))
            
        elif particle.puyo_color == PuyoColor.OJAMA:
            # おじゃま：添付画像風の小さなバージョン
            # 灰色の円
            pygame.draw.circle(screen, (150, 150, 150), (x, y), size)
            
            # 赤い目（サイズに応じて調整）
            eye_size = max(1, size // 3)
            eye_offset = max(1, size // 3)
            
            # 左目
            pygame.draw.circle(screen, (255, 0, 0), 
                             (x - eye_offset, y - eye_offset), 
                             eye_size)
            # 右目
            pygame.draw.circle(screen, (255, 0, 0), 
                             (x + eye_offset, y - eye_offset), 
                             eye_size)
            
            # 牙（簡易版）
            if size > 3:
                pygame.draw.polygon(screen, (255, 255, 255), [
                    (x - size//2, y + eye_offset//2),
                    (x, y + size//2),
                    (x + size//2, y + eye_offset//2)
                ])
            
        else:
            # デフォルト：円形（バックアップ）
            pygame.draw.circle(screen, color, (x, y), size)

class PuyoGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("ぷよぷよゲーム")
        self.clock = pygame.time.Clock()
        
        # ゲームボード初期化
        self.board = [[PuyoColor.EMPTY for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        
        # 現在のぷよペア
        self.current_puyo = self.create_new_puyo()
        self.next_puyo = self.create_new_puyo()  # 次のぷよ
        self.puyo_x = BOARD_WIDTH // 2 - 1
        self.puyo_y = 0
        self.puyo_rotation = 0  # 0:上, 1:右, 2:下, 3:左
        
        # 落下タイマー
        self.fall_timer = 0
        self.fall_speed = 500  # ミリ秒
        self.base_fall_speed = 500  # 基本落下速度
        
        # レベルシステム
        self.level = 1
        self.lines_cleared = 0  # 消去したライン数（連鎖回数）
        
        # おじゃまぷよシステム
        self.ojama_timer = 0
        self.ojama_interval = 30000  # 30秒ごとにおじゃまぷよ
        self.ojama_count = 0  # 次に落とすおじゃまぷよの数
        
        # スコアシステム
        self.score = 0
        # 日本語対応フォント
        try:
            self.font = pygame.font.Font("C:/Windows/Fonts/msgothic.ttc", 36)
            self.small_font = pygame.font.Font("C:/Windows/Fonts/msgothic.ttc", 24)
            self.big_font = pygame.font.Font("C:/Windows/Fonts/msgothic.ttc", 72)
        except:
            # フォントが見つからない場合はシステムデフォルト
            self.font = pygame.font.SysFont("msgothic", 36)
            self.small_font = pygame.font.SysFont("msgothic", 24)
            self.big_font = pygame.font.SysFont("msgothic", 72)
        
        # ゲーム状態
        self.game_over = False
        
        # ぷよ画像を読み込み
        self.puyo_images = self.load_puyo_images()
        
        # ハイスコアシステム
        self.high_score = self.load_high_score()
        
        # パーティクルシステム
        self.particle_system = ParticleSystem()
        
        # ランキングシステム
        self.ranking_manager = RankingManager()
        self.player_input_dialog = PlayerInputDialog(self.screen, self.font, self.small_font)
        self.ranking_display = RankingDisplay(self.screen, self.font, self.small_font, self.big_font)
        self.game_start_time = datetime.now()
        self.max_chain_count = 0  # 最大連鎖数を記録
        
    def load_puyo_images(self):
        """ぷよ画像を読み込み"""
        images = {}
        try:
            images[PuyoColor.RED] = pygame.image.load("red.png")
            images[PuyoColor.BLUE] = pygame.image.load("blue.png")
            images[PuyoColor.GREEN] = pygame.image.load("green.png")
            images[PuyoColor.YELLOW] = pygame.image.load("yellow.png")
            
            # おじゃまぷよ画像を読み込み
            try:
                images[PuyoColor.OJAMA] = pygame.image.load("ojama.png")
            except:
                print("おじゃまぷよ画像の読み込みに失敗しました")
            
            # 画像をセルサイズにリサイズ
            for color in images:
                images[color] = pygame.transform.scale(images[color], (CELL_SIZE, CELL_SIZE))
                
        except pygame.error as e:
            print(f"画像の読み込みに失敗しました: {e}")
            return None
            
        return images
    
    def load_high_score(self):
        """ハイスコアを読み込み"""
        try:
            if os.path.exists("highscore.json"):
                with open("highscore.json", "r") as f:
                    data = json.load(f)
                    return data.get("high_score", 0)
        except (json.JSONDecodeError, IOError):
            pass
        return 0
    
    def save_high_score(self):
        """ハイスコアを保存"""
        try:
            data = {"high_score": self.high_score}
            with open("highscore.json", "w") as f:
                json.dump(data, f)
        except IOError:
            print("ハイスコアの保存に失敗しました")
    
    def create_new_puyo(self):
        """新しいぷよペアを作成"""
        colors = [PuyoColor.RED, PuyoColor.BLUE, PuyoColor.GREEN, PuyoColor.YELLOW]
        return [random.choice(colors), random.choice(colors)]
    
    def get_puyo_positions(self):
        """現在のぷよペアの位置を取得"""
        # 回転に応じた副ぷよの相対位置
        rotation_offsets = [
            (0, -1),  # 0: 上
            (1, 0),   # 1: 右
            (0, 1),   # 2: 下
            (-1, 0)   # 3: 左
        ]
        
        main_pos = (self.puyo_x, self.puyo_y)
        offset_x, offset_y = rotation_offsets[self.puyo_rotation]
        sub_pos = (self.puyo_x + offset_x, self.puyo_y + offset_y)
        
        return main_pos, sub_pos
    
    def run(self):
        """メインゲームループ"""
        running = True
        while running:
            dt = self.clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_input(event.key)
            
            # ぷよの自動落下（ゲームオーバー時は停止）
            if not self.game_over:
                self.fall_timer += dt
                if self.fall_timer >= self.fall_speed:
                    self.move_puyo_down()
                    self.fall_timer = 0
            
            # パーティクルシステム更新
            self.particle_system.update()
            
            # おじゃまぷよタイマー更新
            self.update_ojama_timer(dt)
            
            # 描画
            self.draw()
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()
    
    def handle_input(self, key):
        """キー入力処理"""
        if self.game_over:
            # ゲームオーバー時はRキーでリスタート、Qキーで終了
            if key == pygame.K_r:
                self.reset_game()
            elif key == pygame.K_l:  # Lキーでランキング表示
                self.ranking_display.show_ranking(self.ranking_manager)
            elif key == pygame.K_q:
                pygame.quit()
                sys.exit()
        else:
            # 通常のゲーム操作
            if key == pygame.K_LEFT:
                self.move_puyo(-1, 0)
            elif key == pygame.K_RIGHT:
                self.move_puyo(1, 0)
            elif key == pygame.K_DOWN:
                self.move_puyo_down()
            elif key == pygame.K_SPACE:
                self.rotate_puyo()
            elif key == pygame.K_q:  # Qキーでゲーム終了
                self.end_game()
            elif key == pygame.K_l:  # Lキーでランキング表示
                self.ranking_display.show_ranking(self.ranking_manager)
            elif key == pygame.K_t:  # テスト用：虹色パーティクル生成
                # 画面中央に虹色パーティクル生成
                center_x = BOARD_X + (BOARD_WIDTH * CELL_SIZE) // 2
                center_y = BOARD_Y + (BOARD_HEIGHT * CELL_SIZE) // 2
                self.particle_system.emit_particles(center_x, center_y, PuyoColor.RED, 10, 5)
    
    def move_puyo(self, dx, dy):
        """ぷよを移動"""
        new_x = self.puyo_x + dx
        new_y = self.puyo_y + dy
        
        if self.is_valid_position(new_x, new_y):
            self.puyo_x = new_x
            self.puyo_y = new_y
            return True
        return False
    
    def move_puyo_down(self):
        """ぷよを下に移動"""
        if not self.move_puyo(0, 1):
            # 着地したらボードに配置
            self.place_puyo()
            # 着地後に重力を適用（個別のぷよが独立して落下）
            self.apply_gravity()
            self.check_chains()
            
            # ゲームオーバーチェック
            if self.check_game_over():
                self.game_over = True
                
                # ランキング記録処理
                self.record_score()
                
                # ハイスコア更新チェック
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
                return
            
            # 次のぷよを現在のぷよにして、新しい次のぷよを生成
            self.current_puyo = self.next_puyo
            self.next_puyo = self.create_new_puyo()
            self.puyo_x = BOARD_WIDTH // 2 - 1
            self.puyo_y = 0
            self.puyo_rotation = 0
    
    def is_valid_position(self, x, y, rotation=None):
        """位置が有効かチェック"""
        if rotation is None:
            rotation = self.puyo_rotation
            
        # 回転に応じた副ぷよの相対位置
        rotation_offsets = [
            (0, -1),  # 0: 上
            (1, 0),   # 1: 右
            (0, 1),   # 2: 下
            (-1, 0)   # 3: 左
        ]
        
        # 主ぷよの位置チェック
        if x < 0 or x >= BOARD_WIDTH or y < 0 or y >= BOARD_HEIGHT:
            return False
        if self.board[y][x] != PuyoColor.EMPTY:
            return False
        
        # 副ぷよの位置チェック
        offset_x, offset_y = rotation_offsets[rotation]
        sub_x, sub_y = x + offset_x, y + offset_y
        
        if sub_x < 0 or sub_x >= BOARD_WIDTH or sub_y < 0 or sub_y >= BOARD_HEIGHT:
            return False
        if self.board[sub_y][sub_x] != PuyoColor.EMPTY:
            return False
        
        return True
    
    def place_puyo(self):
        """ぷよをボードに配置"""
        main_pos, sub_pos = self.get_puyo_positions()
        self.board[main_pos[1]][main_pos[0]] = self.current_puyo[0]
        self.board[sub_pos[1]][sub_pos[0]] = self.current_puyo[1]
    
    def rotate_puyo(self):
        """ぷよを回転（4方向回転）- 壁キック機能付き"""
        new_rotation = (self.puyo_rotation + 1) % 4
        
        # 回転後の位置が有効かチェック
        if self.is_valid_position(self.puyo_x, self.puyo_y, new_rotation):
            # 通常回転
            self.puyo_rotation = new_rotation
        else:
            # 壁キック処理（左右に1マスずらして回転を試みる）
            kick_offsets = [1, -1, 2, -2]  # 右、左、右2マス、左2マス
            for offset in kick_offsets:
                if self.is_valid_position(self.puyo_x + offset, self.puyo_y, new_rotation):
                    self.puyo_x += offset
                    self.puyo_rotation = new_rotation
                    break
    
    def check_chains(self):
        """連鎖チェック - 4つ以上つながったぷよを消去"""
        chains_found = True
        chain_count = 0
        total_score = 0
        
        while chains_found:
            chains_found = False
            to_remove = set()
            groups = []  # 消去されるグループを記録
            
            # 各セルから連結チェック
            for y in range(BOARD_HEIGHT):
                for x in range(BOARD_WIDTH):
                    if self.board[y][x] != PuyoColor.EMPTY:
                        connected = self.find_connected_puyos(x, y, self.board[y][x])
                        if len(connected) >= 4:
                            # 既に処理済みのぷよは除外
                            new_connected = [pos for pos in connected if pos not in to_remove]
                            if new_connected:
                                to_remove.update(new_connected)
                                groups.append(new_connected)
                                chains_found = True
            
            # 連結したぷよを消去してスコア計算
            if to_remove:
                chain_count += 1
                
                # スコア計算（連鎖数とぷよ数に応じて）
                chain_bonus = chain_count * 50  # 連鎖ボーナス
                puyo_score = len(to_remove) * 10  # ぷよ1個につき10点
                round_score = puyo_score + chain_bonus
                total_score += round_score
                
                # おじゃまぷよも消去（隣接するものを探す）
                ojama_to_remove = set()
                for x, y in to_remove:
                    # 隣接する4方向をチェック
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < BOARD_WIDTH and 0 <= ny < BOARD_HEIGHT and 
                            self.board[ny][nx] == PuyoColor.OJAMA):
                            ojama_to_remove.add((nx, ny))
                
                # フェードアウトアニメーションとパーティクル生成を同時に行う
                self.animate_puyo_removal(to_remove, ojama_to_remove, chain_count)
                
                # 重力適用（ぷよを下に落とす）
                self.apply_gravity()
                
                # 少し待機（連鎖の視覚効果）
                pygame.time.wait(300)
                self.draw()
                pygame.display.flip()
        
        # 総スコアを加算
        self.score += total_score
        
        # 連鎖があった場合、レベルアップをチェック
        if chain_count > 0:
            self.lines_cleared += chain_count
            self.update_level()
            # 最大連鎖数を記録
            self.max_chain_count = max(self.max_chain_count, chain_count)
        
        return chain_count
    
    def find_connected_puyos(self, start_x, start_y, color):
        """指定した色のつながったぷよを探す（深度優先探索）"""
        if color == PuyoColor.EMPTY:
            return []
        
        visited = set()
        stack = [(start_x, start_y)]
        connected = []
        
        # 4方向（上下左右）
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        while stack:
            x, y = stack.pop()
            
            if (x, y) in visited:
                continue
            
            if (x < 0 or x >= BOARD_WIDTH or y < 0 or y >= BOARD_HEIGHT or
                self.board[y][x] != color):
                continue
            
            visited.add((x, y))
            connected.append((x, y))
            
            # 隣接セルをスタックに追加
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                    stack.append((nx, ny))
        
        return connected
    
    def update_level(self):
        """レベルアップをチェックして落下速度を調整"""
        # 10連鎖ごとにレベルアップ
        new_level = (self.lines_cleared // 10) + 1
        
        if new_level > self.level:
            self.level = new_level
            # レベルが上がるごとに落下速度を速くする
            # レベル1: 500ms, レベル2: 400ms, レベル3: 320ms...
            self.fall_speed = max(50, self.base_fall_speed - (self.level - 1) * 80)
    
    def apply_gravity(self):
        """重力を適用してぷよを下に落とす"""
        for x in range(BOARD_WIDTH):
            # 各列で空でないぷよを下に詰める
            column = []
            for y in range(BOARD_HEIGHT):
                if self.board[y][x] != PuyoColor.EMPTY:
                    column.append(self.board[y][x])
            
            # 列をクリアして下から詰め直す
            for y in range(BOARD_HEIGHT):
                self.board[y][x] = PuyoColor.EMPTY
            
            # 下から順番に配置
            for i, puyo in enumerate(reversed(column)):
                self.board[BOARD_HEIGHT - 1 - i][x] = puyo
    
    def check_game_over(self):
        """ゲームオーバー判定"""
        # 新しいぷよが配置できるかチェック
        start_x = BOARD_WIDTH // 2 - 1
        start_y = 1  # y=1から開始
        
        # 4つの回転状態すべてで配置可能かチェック
        for rotation in range(4):
            if self.is_valid_position(start_x, start_y, rotation):
                return False  # どれか1つでも配置できればゲーム続行
        
        # どの回転でも配置できない場合のみゲームオーバー
        return True
    
    def update_ojama_timer(self, dt):
        """おじゃまぷよタイマーの更新"""
        self.ojama_timer += dt
        if self.ojama_timer >= self.ojama_interval:
            self.ojama_timer = 0
            # レベルに応じておじゃまぷよの数を決定
            self.ojama_count += self.level
            self.drop_ojama_puyos()
    
    def drop_ojama_puyos(self):
        """おじゃまぷよを落とす"""
        if self.ojama_count <= 0:
            return
            
        # 各列にランダムにおじゃまぷよを配置
        columns = list(range(BOARD_WIDTH))
        random.shuffle(columns)
        
        for i in range(min(self.ojama_count, BOARD_WIDTH)):
            col = columns[i]
            # 列の一番上の空きマスを探す
            for row in range(BOARD_HEIGHT):
                if self.board[row][col] == PuyoColor.EMPTY:
                    self.board[row][col] = PuyoColor.OJAMA
                    # パーティクルエフェクト
                    pixel_x = BOARD_X + col * CELL_SIZE + CELL_SIZE // 2
                    pixel_y = BOARD_Y + row * CELL_SIZE + CELL_SIZE // 2
                    self.particle_system.emit_particles(pixel_x, pixel_y, PuyoColor.OJAMA, 3, 1)
                    break
        
        # 残りのおじゃまぷよを次回に持ち越し
        self.ojama_count -= min(self.ojama_count, BOARD_WIDTH)
        
        # 重力適用
        self.apply_gravity()
        
    def reset_game(self):
        """ゲームリセット"""
        self.board = [[PuyoColor.EMPTY for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_puyo = self.create_new_puyo()
        self.next_puyo = self.create_new_puyo()  # 次のぷよも生成
        self.puyo_x = BOARD_WIDTH // 2 - 1
        self.puyo_y = 0
        self.puyo_rotation = 0
        self.score = 0
        self.game_over = False
        self.fall_timer = 0
        # レベルシステムもリセット
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = self.base_fall_speed
        
        # おじゃまぷよリセット
        self.ojama_timer = 0
        self.ojama_count = 0
        
        # ランキング関連もリセット
        self.game_start_time = datetime.now()
        self.max_chain_count = 0
    
    def end_game(self):
        """ゲームを手動で終了"""
        if not self.game_over:
            self.game_over = True
            
            # ランキング記録処理
            self.record_score()
            
            # ハイスコア更新チェック
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
    
    def draw(self):
        """画面描画"""
        self.screen.fill((50, 50, 50))
        
        # ボード描画
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                rect = pygame.Rect(
                    BOARD_X + x * CELL_SIZE,
                    BOARD_Y + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                
                # 空のセルは黒で塗りつぶし
                if self.board[y][x] == PuyoColor.EMPTY:
                    pygame.draw.rect(self.screen, (0, 0, 0), rect)
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)
                elif self.board[y][x] == PuyoColor.OJAMA:
                    # おじゃまぷよは特別描画（添付画像風）
                    # 灰色の円
                    color = (150, 150, 150)  # 灰色
                    pygame.draw.circle(self.screen, color, 
                                     (rect.centerx, rect.centery), 
                                     CELL_SIZE // 2 - 2)
                    
                    # 赤い目（左）
                    eye_radius = CELL_SIZE // 6
                    eye_offset = CELL_SIZE // 6
                    pygame.draw.circle(self.screen, (255, 0, 0), 
                                     (rect.centerx - eye_offset, rect.centery - eye_offset), 
                                     eye_radius)
                    # 赤い目（右）
                    pygame.draw.circle(self.screen, (255, 0, 0), 
                                     (rect.centerx + eye_offset, rect.centery - eye_offset), 
                                     eye_radius)
                    
                    # 白い光沢（目の中）
                    pygame.draw.circle(self.screen, (255, 255, 255), 
                                     (rect.centerx - eye_offset, rect.centery - eye_offset - 1), 
                                     eye_radius // 3)
                    pygame.draw.circle(self.screen, (255, 255, 255), 
                                     (rect.centerx + eye_offset, rect.centery - eye_offset - 1), 
                                     eye_radius // 3)
                    
                    # 白い牙（三角形）
                    teeth_width = CELL_SIZE // 3
                    teeth_height = CELL_SIZE // 5
                    teeth_y = rect.centery + eye_offset
                    
                    # 左の牙
                    pygame.draw.polygon(self.screen, (255, 255, 255), [
                        (rect.centerx - teeth_width, teeth_y),
                        (rect.centerx - teeth_width//2, teeth_y + teeth_height),
                        (rect.centerx, teeth_y)
                    ])
                    
                    # 中央の牙
                    pygame.draw.polygon(self.screen, (255, 255, 255), [
                        (rect.centerx - teeth_width//2, teeth_y),
                        (rect.centerx, teeth_y + teeth_height),
                        (rect.centerx + teeth_width//2, teeth_y)
                    ])
                    
                    # 右の牙
                    pygame.draw.polygon(self.screen, (255, 255, 255), [
                        (rect.centerx, teeth_y),
                        (rect.centerx + teeth_width//2, teeth_y + teeth_height),
                        (rect.centerx + teeth_width, teeth_y)
                    ])
                else:
                    # 通常ぷよ画像を使用（フォールバック付き）
                    if self.puyo_images and self.board[y][x] in self.puyo_images:
                        self.screen.blit(self.puyo_images[self.board[y][x]], rect)
                    else:
                        # 画像が読み込めない場合は色で描画
                        color = COLORS[self.board[y][x]]
                        pygame.draw.rect(self.screen, color, rect)
                        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
        
        # 現在のぷよ描画
        if self.current_puyo:
            main_pos, sub_pos = self.get_puyo_positions()
            
            # 主ぷよ
            rect1 = pygame.Rect(
                BOARD_X + main_pos[0] * CELL_SIZE,
                BOARD_Y + main_pos[1] * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            if self.puyo_images and self.current_puyo[0] in self.puyo_images:
                self.screen.blit(self.puyo_images[self.current_puyo[0]], rect1)
            else:
                pygame.draw.rect(self.screen, COLORS[self.current_puyo[0]], rect1)
                pygame.draw.rect(self.screen, (255, 255, 255), rect1, 2)
            
            # 副ぷよ
            rect2 = pygame.Rect(
                BOARD_X + sub_pos[0] * CELL_SIZE,
                BOARD_Y + sub_pos[1] * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            if self.puyo_images and self.current_puyo[1] in self.puyo_images:
                self.screen.blit(self.puyo_images[self.current_puyo[1]], rect2)
            else:
                pygame.draw.rect(self.screen, COLORS[self.current_puyo[1]], rect2)
                pygame.draw.rect(self.screen, (255, 255, 255), rect2, 2)
        
        # パーティクル描画
        self.particle_system.draw(self.screen)
        
        # スコア表示
        self.draw_ui()
        
        # ゲームオーバー表示
        if self.game_over:
            self.draw_game_over()
    
    def draw_ui(self):
        """UI要素（スコアなど）を描画"""
        # スコア表示
        score_text = self.font.render(f"スコア: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (BOARD_X + BOARD_WIDTH * CELL_SIZE + 20, BOARD_Y))
        
        # レベル表示
        level_text = self.font.render(f"レベル: {self.level}", True, (255, 255, 255))
        self.screen.blit(level_text, (BOARD_X + BOARD_WIDTH * CELL_SIZE + 20, BOARD_Y + 35))
        
        # ハイスコア表示
        high_score_text = self.small_font.render(f"ハイスコア: {self.high_score}", True, (255, 255, 0))
        self.screen.blit(high_score_text, (BOARD_X + BOARD_WIDTH * CELL_SIZE + 20, BOARD_Y + 70))
        
        # 次のぷよ表示
        self.draw_next_puyo()
        
        # 操作説明
        instructions = [
            "操作方法:",
            "←→: 移動",
            "↓: 高速落下",
            "スペース: 回転",
            "L: ランキング表示",
            "Q: ゲーム終了"
        ]
        
        y_offset = BOARD_Y + 220  # さらに下にずらす
        for instruction in instructions:
            text = self.small_font.render(instruction, True, (200, 200, 200))
            self.screen.blit(text, (BOARD_X + BOARD_WIDTH * CELL_SIZE + 20, y_offset))
            y_offset += 30  # 行間を広げる
    
    def draw_next_puyo(self):
        """次のぷよを表示"""
        # 次のぷよのタイトル
        next_text = self.small_font.render("次のぷよ:", True, (255, 255, 255))
        self.screen.blit(next_text, (BOARD_X + BOARD_WIDTH * CELL_SIZE + 20, BOARD_Y + 100))
        
        # 次のぷよの表示位置
        next_x = BOARD_X + BOARD_WIDTH * CELL_SIZE + 30
        next_y = BOARD_Y + 130
        
        # 次のぷよを縦に表示（主ぷよが上、副ぷよが下）
        if self.next_puyo:
            # 主ぷよ（上）
            rect1 = pygame.Rect(next_x, next_y, CELL_SIZE - 10, CELL_SIZE - 10)
            if self.puyo_images and self.next_puyo[0] in self.puyo_images:
                # 画像をリサイズして表示
                small_image = pygame.transform.scale(self.puyo_images[self.next_puyo[0]], (CELL_SIZE - 10, CELL_SIZE - 10))
                self.screen.blit(small_image, rect1)
            else:
                pygame.draw.rect(self.screen, COLORS[self.next_puyo[0]], rect1)
                pygame.draw.rect(self.screen, (255, 255, 255), rect1, 2)
            
            # 副ぷよ（下）
            rect2 = pygame.Rect(next_x, next_y + CELL_SIZE - 5, CELL_SIZE - 10, CELL_SIZE - 10)
            if self.puyo_images and self.next_puyo[1] in self.puyo_images:
                # 画像をリサイズして表示
                small_image = pygame.transform.scale(self.puyo_images[self.next_puyo[1]], (CELL_SIZE - 10, CELL_SIZE - 10))
                self.screen.blit(small_image, rect2)
            else:
                pygame.draw.rect(self.screen, COLORS[self.next_puyo[1]], rect2)
                pygame.draw.rect(self.screen, (255, 255, 255), rect2, 2)
    
    def animate_puyo_removal(self, to_remove, ojama_to_remove, chain_count):
        """ぷよ消去時のアニメーション効果"""
        # パーティクル生成
        for x, y in to_remove:
            pixel_x = BOARD_X + x * CELL_SIZE + CELL_SIZE // 2
            pixel_y = BOARD_Y + y * CELL_SIZE + CELL_SIZE // 2
            puyo_color = self.board[y][x]
            self.particle_system.emit_particles(pixel_x, pixel_y, puyo_color, 8, chain_count)
        
        # おじゃまぷよのパーティクル生成
        for x, y in ojama_to_remove:
            pixel_x = BOARD_X + x * CELL_SIZE + CELL_SIZE // 2
            pixel_y = BOARD_Y + y * CELL_SIZE + CELL_SIZE // 2
            self.particle_system.emit_particles(pixel_x, pixel_y, PuyoColor.OJAMA, 5, 1)
        
        # ぷよを実際に削除
        for x, y in to_remove:
            self.board[y][x] = PuyoColor.EMPTY
        for x, y in ojama_to_remove:
            self.board[y][x] = PuyoColor.EMPTY

    def record_score(self):
        """ゲーム終了時にスコアをランキングに記録"""
        if self.ranking_manager.is_high_score(self.score):
            # プレイ時間を計算
            play_time = int((datetime.now() - self.game_start_time).total_seconds())
            
            # プレイヤー名入力ダイアログを表示
            player_name = self.player_input_dialog.show_dialog(self.score)
            
            # スコアエントリを作成
            score_entry = ScoreEntry(
                score=self.score,
                player_name=player_name,
                date_time=datetime.now(),
                chain_count=self.max_chain_count,
                level_reached=self.level,
                play_time=play_time
            )
            
            # ランキングに追加
            rank = self.ranking_manager.add_score(score_entry)
            
            # 結果を画面に表示（少し待機）
            self.show_ranking_result(player_name, rank)
    
    def show_ranking_result(self, player_name: str, rank: int):
        """ランキング結果を表示"""
        # 背景を暗くする
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 結果表示
        if rank > 0:
            result_text = self.font.render(f"{player_name}さん", True, (255, 255, 255))
            rank_text = self.font.render(f"{rank}位にランクイン！", True, (255, 255, 0))
        else:
            result_text = self.font.render(f"{player_name}さん", True, (255, 255, 255))
            rank_text = self.font.render("記録されました！", True, (255, 255, 0))
        
        result_rect = result_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        rank_rect = rank_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        
        self.screen.blit(result_text, result_rect)
        self.screen.blit(rank_text, rank_rect)
        
        # 続行案内
        continue_text = self.small_font.render("何かキーを押して続行...", True, (200, 200, 200))
        continue_rect = continue_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
        self.screen.blit(continue_text, continue_rect)
        
        pygame.display.flip()
        
        # キー入力待ち
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    waiting = False
    
    def draw_game_over(self):
        """ゲームオーバー画面を描画"""
        # 半透明の背景
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # ゲームオーバーテキスト
        game_over_text = self.big_font.render("GAME OVER", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(game_over_text, text_rect)
        
        # 最終スコア表示
        final_score_text = self.font.render(f"最終スコア: {self.score}", True, (255, 255, 255))
        score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(final_score_text, score_rect)
        
        # 操作案内
        restart_text = self.small_font.render("Rキーを押してリスタート", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(restart_text, restart_rect)
        
        # ランキング表示案内
        ranking_text = self.small_font.render("Lキーでランキング表示", True, (200, 200, 200))
        ranking_rect = ranking_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80))
        self.screen.blit(ranking_text, ranking_rect)
        
        # 終了案内
        quit_text = self.small_font.render("Qキーでゲーム終了", True, (200, 200, 200))
        quit_rect = quit_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 110))
        self.screen.blit(quit_text, quit_rect)

if __name__ == "__main__":
    game = PuyoGame()
    game.run()