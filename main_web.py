import asyncio
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

# 簡略化されたパーティクルシステム（Web版用）
class SimpleParticle:
    def __init__(self, x, y, color, velocity_x, velocity_y):
        self.x = x
        self.y = y
        self.color = color
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.life = 1.0
        self.size = random.randint(2, 5)
    
    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += 0.2  # 重力
        self.life -= 0.02
    
    def is_alive(self):
        return self.life > 0 and self.y < WINDOW_HEIGHT + 50
    
    def draw(self, screen):
        if self.life > 0:
            alpha = max(0, min(255, int(self.life * 255)))
            color_with_alpha = (*self.color[:3], alpha)
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

class SimpleParticleSystem:
    def __init__(self):
        self.particles = []
        self.max_particles = 100  # Web版では制限
    
    def emit_particles(self, x, y, color, count=5, chain_level=1):
        for _ in range(min(count, 10)):  # 最大10個に制限
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.0, 4.0)
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed - 2.0
            
            particle = SimpleParticle(x, y, COLORS[color], velocity_x, velocity_y)
            self.particles.append(particle)
            
            if len(self.particles) >= self.max_particles:
                break
    
    def update(self):
        alive_particles = []
        for particle in self.particles:
            particle.update()
            if particle.is_alive():
                alive_particles.append(particle)
        self.particles = alive_particles
    
    def draw(self, screen):
        for particle in self.particles:
            particle.draw(screen)

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
        self.next_puyo = self.create_new_puyo()
        self.puyo_x = BOARD_WIDTH // 2 - 1
        self.puyo_y = 0
        self.puyo_rotation = 0
        
        # 落下タイマー
        self.fall_timer = 0
        self.fall_speed = 500
        self.base_fall_speed = 500
        
        # レベルシステム
        self.level = 1
        self.lines_cleared = 0
        
        # スコアシステム
        self.score = 0
        
        # Web版用フォント設定
        try:
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
            self.big_font = pygame.font.Font(None, 72)
        except:
            self.font = pygame.font.SysFont(None, 36)
            self.small_font = pygame.font.SysFont(None, 24)
            self.big_font = pygame.font.SysFont(None, 72)
        
        # ゲーム状態
        self.game_over = False
        
        # 簡略化されたシステム
        self.particle_system = SimpleParticleSystem()
        self.high_score = 0
        self.game_start_time = datetime.now()
        self.max_chain_count = 0
    
    def create_new_puyo(self):
        """新しいぷよペアを作成"""
        colors = [PuyoColor.RED, PuyoColor.BLUE, PuyoColor.GREEN, PuyoColor.YELLOW]
        return [random.choice(colors), random.choice(colors)]
    
    def get_puyo_positions(self):
        """現在のぷよペアの位置を取得"""
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
    
    async def run(self):
        """非同期メインループ"""
        running = True
        while running:
            dt = self.clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_input(event.key)
            
            # ぷよの自動落下
            if not self.game_over:
                self.fall_timer += dt
                if self.fall_timer >= self.fall_speed:
                    self.move_puyo_down()
                    self.fall_timer = 0
            
            # パーティクルシステム更新
            self.particle_system.update()
            
            # 描画
            self.draw()
            pygame.display.flip()
            
            # 非同期処理のため必要
            await asyncio.sleep(0)
        
        pygame.quit()
    
    def handle_input(self, key):
        """キー入力処理"""
        if self.game_over:
            if key == pygame.K_r:
                self.reset_game()
        else:
            if key == pygame.K_LEFT:
                self.move_puyo(-1, 0)
            elif key == pygame.K_RIGHT:
                self.move_puyo(1, 0)
            elif key == pygame.K_DOWN:
                self.move_puyo_down()
            elif key == pygame.K_SPACE:
                self.rotate_puyo()
            elif key == pygame.K_q:
                self.end_game()
    
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
            self.place_puyo()
            self.apply_gravity()
            self.check_chains()
            
            if self.check_game_over():
                self.game_over = True
                if self.score > self.high_score:
                    self.high_score = self.score
                return
            
            self.current_puyo = self.next_puyo
            self.next_puyo = self.create_new_puyo()
            self.puyo_x = BOARD_WIDTH // 2 - 1
            self.puyo_y = 0
            self.puyo_rotation = 0
    
    def is_valid_position(self, x, y, rotation=None):
        """位置が有効かチェック"""
        if rotation is None:
            rotation = self.puyo_rotation
            
        rotation_offsets = [
            (0, -1), (1, 0), (0, 1), (-1, 0)
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
        """ぷよを回転"""
        new_rotation = (self.puyo_rotation + 1) % 4
        
        if self.is_valid_position(self.puyo_x, self.puyo_y, new_rotation):
            self.puyo_rotation = new_rotation
        else:
            # 壁キック
            for offset in [1, -1]:
                if self.is_valid_position(self.puyo_x + offset, self.puyo_y, new_rotation):
                    self.puyo_x += offset
                    self.puyo_rotation = new_rotation
                    break
    
    def check_chains(self):
        """連鎖チェック"""
        chains_found = True
        chain_count = 0
        total_score = 0
        
        while chains_found:
            chains_found = False
            to_remove = set()
            
            for y in range(BOARD_HEIGHT):
                for x in range(BOARD_WIDTH):
                    if self.board[y][x] != PuyoColor.EMPTY:
                        connected = self.find_connected_puyos(x, y, self.board[y][x])
                        if len(connected) >= 4:
                            new_connected = [pos for pos in connected if pos not in to_remove]
                            if new_connected:
                                to_remove.update(new_connected)
                                chains_found = True
            
            if to_remove:
                chain_count += 1
                chain_bonus = chain_count * 50
                puyo_score = len(to_remove) * 10
                round_score = puyo_score + chain_bonus
                total_score += round_score
                
                # パーティクル生成
                for x, y in to_remove:
                    pixel_x = BOARD_X + x * CELL_SIZE + CELL_SIZE // 2
                    pixel_y = BOARD_Y + y * CELL_SIZE + CELL_SIZE // 2
                    puyo_color = self.board[y][x]
                    self.particle_system.emit_particles(pixel_x, pixel_y, puyo_color, 5, chain_count)
                
                # ぷよを削除
                for x, y in to_remove:
                    self.board[y][x] = PuyoColor.EMPTY
                
                self.apply_gravity()
        
        self.score += total_score
        
        if chain_count > 0:
            self.lines_cleared += chain_count
            self.max_chain_count = max(self.max_chain_count, chain_count)
            self.update_level()
        
        return chain_count
    
    def find_connected_puyos(self, start_x, start_y, color):
        """つながったぷよを探す"""
        if color == PuyoColor.EMPTY:
            return []
        
        visited = set()
        stack = [(start_x, start_y)]
        connected = []
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
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                    stack.append((nx, ny))
        
        return connected
    
    def update_level(self):
        """レベルアップ"""
        new_level = (self.lines_cleared // 10) + 1
        
        if new_level > self.level:
            self.level = new_level
            self.fall_speed = max(50, self.base_fall_speed - (self.level - 1) * 80)
    
    def apply_gravity(self):
        """重力適用"""
        for x in range(BOARD_WIDTH):
            column = []
            for y in range(BOARD_HEIGHT):
                if self.board[y][x] != PuyoColor.EMPTY:
                    column.append(self.board[y][x])
            
            for y in range(BOARD_HEIGHT):
                self.board[y][x] = PuyoColor.EMPTY
            
            for i, puyo in enumerate(reversed(column)):
                self.board[BOARD_HEIGHT - 1 - i][x] = puyo
    
    def check_game_over(self):
        """ゲームオーバー判定"""
        start_x = BOARD_WIDTH // 2 - 1
        start_y = 1
        
        for rotation in range(4):
            if self.is_valid_position(start_x, start_y, rotation):
                return False
        
        return True
    
    def end_game(self):
        """ゲーム終了"""
        if not self.game_over:
            self.game_over = True
            if self.score > self.high_score:
                self.high_score = self.score
    
    def reset_game(self):
        """ゲームリセット"""
        self.board = [[PuyoColor.EMPTY for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_puyo = self.create_new_puyo()
        self.next_puyo = self.create_new_puyo()
        self.puyo_x = BOARD_WIDTH // 2 - 1
        self.puyo_y = 0
        self.puyo_rotation = 0
        self.score = 0
        self.game_over = False
        self.fall_timer = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = self.base_fall_speed
        self.game_start_time = datetime.now()
        self.max_chain_count = 0
    
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
                
                if self.board[y][x] == PuyoColor.EMPTY:
                    pygame.draw.rect(self.screen, (0, 0, 0), rect)
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)
                else:
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
            pygame.draw.rect(self.screen, COLORS[self.current_puyo[0]], rect1)
            pygame.draw.rect(self.screen, (255, 255, 255), rect1, 2)
            
            # 副ぷよ
            rect2 = pygame.Rect(
                BOARD_X + sub_pos[0] * CELL_SIZE,
                BOARD_Y + sub_pos[1] * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(self.screen, COLORS[self.current_puyo[1]], rect2)
            pygame.draw.rect(self.screen, (255, 255, 255), rect2, 2)
        
        # パーティクル描画
        self.particle_system.draw(self.screen)
        
        # UI描画
        self.draw_ui()
        
        # ゲームオーバー表示
        if self.game_over:
            self.draw_game_over()
    
    def draw_ui(self):
        """UI描画"""
        # スコア表示
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (BOARD_X + BOARD_WIDTH * CELL_SIZE + 20, BOARD_Y))
        
        # レベル表示
        level_text = self.font.render(f"Level: {self.level}", True, (255, 255, 255))
        self.screen.blit(level_text, (BOARD_X + BOARD_WIDTH * CELL_SIZE + 20, BOARD_Y + 35))
        
        # ハイスコア表示
        high_score_text = self.small_font.render(f"High: {self.high_score}", True, (255, 255, 0))
        self.screen.blit(high_score_text, (BOARD_X + BOARD_WIDTH * CELL_SIZE + 20, BOARD_Y + 70))
        
        # 次のぷよ表示
        next_text = self.small_font.render("Next:", True, (255, 255, 255))
        self.screen.blit(next_text, (BOARD_X + BOARD_WIDTH * CELL_SIZE + 20, BOARD_Y + 100))
        
        if self.next_puyo:
            next_x = BOARD_X + BOARD_WIDTH * CELL_SIZE + 30
            next_y = BOARD_Y + 130
            
            # 主ぷよ（上）
            rect1 = pygame.Rect(next_x, next_y, CELL_SIZE - 10, CELL_SIZE - 10)
            pygame.draw.rect(self.screen, COLORS[self.next_puyo[0]], rect1)
            pygame.draw.rect(self.screen, (255, 255, 255), rect1, 2)
            
            # 副ぷよ（下）
            rect2 = pygame.Rect(next_x, next_y + CELL_SIZE - 5, CELL_SIZE - 10, CELL_SIZE - 10)
            pygame.draw.rect(self.screen, COLORS[self.next_puyo[1]], rect2)
            pygame.draw.rect(self.screen, (255, 255, 255), rect2, 2)
        
        # 操作説明
        instructions = [
            "Controls:",
            "Arrow Keys: Move",
            "Space: Rotate",
            "Q: End Game"
        ]
        
        y_offset = BOARD_Y + 220
        for instruction in instructions:
            text = self.small_font.render(instruction, True, (200, 200, 200))
            self.screen.blit(text, (BOARD_X + BOARD_WIDTH * CELL_SIZE + 20, y_offset))
            y_offset += 25
    
    def draw_game_over(self):
        """ゲームオーバー画面"""
        # 半透明背景
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # ゲームオーバーテキスト
        game_over_text = self.big_font.render("GAME OVER", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(game_over_text, text_rect)
        
        # 最終スコア
        final_score_text = self.font.render(f"Final Score: {self.score}", True, (255, 255, 255))
        score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(final_score_text, score_rect)
        
        # リスタート案内
        restart_text = self.small_font.render("Press R to Restart", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(restart_text, restart_rect)

async def main():
    game = PuyoGame()
    await game.run()

if __name__ == "__main__":
    asyncio.run(main())