"""
PyInstallerを使ってexeファイルを作成するスクリプト
"""

import subprocess
import sys
import os

def build_executable():
    """実行可能ファイルを作成"""
    try:
        # PyInstallerがインストールされているかチェック
        subprocess.run([sys.executable, "-c", "import PyInstaller"], check=True)
    except subprocess.CalledProcessError:
        print("PyInstallerをインストールしています...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # PyInstallerでexeファイルを作成
    cmd = [
        "pyinstaller",
        "--onefile",  # 単一のexeファイルを作成
        "--windowed",  # コンソールウィンドウを表示しない
        "--name", "PuyoGame",  # 実行ファイル名
        "--add-data", "*.png;.",  # 画像ファイルを含める
        "main.py"
    ]
    
    print("実行可能ファイルを作成中...")
    subprocess.run(cmd, check=True)
    print("完了！dist/PuyoGame.exe が作成されました。")

if __name__ == "__main__":
    build_executable()