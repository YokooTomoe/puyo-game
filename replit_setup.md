# Replitでオンライン実行する方法

## 手順

1. **Replitアカウント作成**
   - https://replit.com にアクセス
   - アカウントを作成

2. **新しいReplを作成**
   - 「Create Repl」をクリック
   - 「Python」を選択
   - 名前を「puyo-game」に設定

3. **ファイルをアップロード**
   - `main.py`をアップロード
   - `requirements.txt`をアップロード
   - 画像ファイル（red.png, blue.png, green.png, yellow.png, ojama.png）をアップロード

4. **依存関係をインストール**
   - Shellタブで以下を実行：
   ```bash
   pip install pygame
   ```

5. **実行**
   - `main.py`を選択
   - 「Run」ボタンをクリック

6. **公開**
   - 右上の「Share」をクリック
   - 公開URLが生成される

## 注意点
- Replitでは音声が制限される場合があります
- パフォーマンスがローカル実行より劣る場合があります