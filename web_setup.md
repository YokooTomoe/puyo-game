# ブラウザでゲームを実行する方法

## Pygbagを使用してWebAssembly版を作成

### 1. Pygbagのインストール
```bash
pip install pygbag
```

### 2. main.pyを修正
ブラウザ対応のため、以下の修正が必要です：

1. **非同期対応**：メインループを非同期にする
2. **ファイルパス修正**：相対パスを使用
3. **フォント修正**：システムフォントの代わりにデフォルトフォントを使用

### 3. 修正版main.pyの作成
```python
import asyncio
import pygame
# ... 他のimport

class PuyoGame:
    def __init__(self):
        # フォント設定を修正
        try:
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
            self.big_font = pygame.font.Font(None, 72)
        except:
            self.font = pygame.font.SysFont(None, 36)
            self.small_font = pygame.font.SysFont(None, 24)
            self.big_font = pygame.font.SysFont(None, 72)
    
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
            
            # ゲーム更新処理
            if not self.game_over:
                self.fall_timer += dt
                if self.fall_timer >= self.fall_speed:
                    self.move_puyo_down()
                    self.fall_timer = 0
            
            self.particle_system.update()
            self.update_ojama_timer(dt)
            
            # 描画
            self.draw()
            pygame.display.flip()
            
            # 非同期処理のため必要
            await asyncio.sleep(0)
        
        pygame.quit()

async def main():
    game = PuyoGame()
    await game.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Webビルド実行
```bash
pygbag main.py
```

### 5. GitHub Pagesで公開
1. `dist/`フォルダの内容をGitHubリポジトリにコミット
2. GitHub Settings → Pages → Source を「GitHub Actions」に設定
3. 自動的にWebサイトが生成される

## 注意点
- 日本語フォントが制限される場合があります
- ファイル保存機能が制限される場合があります
- パフォーマンスがネイティブ版より劣る場合があります