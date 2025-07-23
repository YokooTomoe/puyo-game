// ぷよぷよゲーム - JavaScript版
class PuyoGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // ゲーム定数
        this.BOARD_WIDTH = 6;
        this.BOARD_HEIGHT = 12;
        this.CELL_SIZE = 40;
        this.BOARD_X = 50;
        this.BOARD_Y = 50;
        
        // 色定義（フォールバック用）
        this.COLORS = {
            0: '#000000', // EMPTY
            1: '#FF0000', // RED
            2: '#0000FF', // BLUE
            3: '#00FF00', // GREEN
            4: '#FFFF00', // YELLOW
            5: '#B4B4B4'  // OJAMA (グレー)
        };
        
        // 画像読み込み
        this.images = {};
        this.imagesLoaded = 0;
        this.totalImages = 5; // おじゃまぷよ画像を追加
        this.loadImages();
        
        // ゲーム状態
        this.board = Array(this.BOARD_HEIGHT).fill().map(() => Array(this.BOARD_WIDTH).fill(0));
        this.currentPuyo = this.createNewPuyo();
        this.nextPuyo = this.createNewPuyo();
        this.puyoX = Math.floor(this.BOARD_WIDTH / 2) - 1;
        this.puyoY = 0;
        this.puyoRotation = 0;
        
        this.score = 0;
        this.level = 1;
        this.gameOver = false;
        this.fallTimer = 0;
        this.fallSpeed = 500;
        
        // おじゃまぷよシステム
        this.ojamaTimer = 0;
        this.ojamaInterval = 30000; // 30秒
        this.ojamaCount = 0;
        this.fallingOjamas = []; // 落下中のおじゃまぷよ
        
        // パーティクル
        this.particles = [];
        
        this.setupControls();
    }
    
    loadImages() {
        const imageFiles = {
            1: 'red.png',
            2: 'blue.png',
            3: 'green.png',
            4: 'yellow.png',
            5: 'ojama.png'
        };
        
        for (let [color, filename] of Object.entries(imageFiles)) {
            const img = new Image();
            img.onload = () => {
                this.imagesLoaded++;
                if (this.imagesLoaded === this.totalImages) {
                    this.gameLoop(); // 全画像読み込み完了後にゲーム開始
                }
            };
            img.onerror = () => {
                console.log(`画像 ${filename} の読み込みに失敗しました`);
                this.imagesLoaded++;
                if (this.imagesLoaded === this.totalImages) {
                    this.gameLoop(); // エラーでもゲーム開始
                }
            };
            img.src = filename;
            this.images[color] = img;
        }
    }
    
    createNewPuyo() {
        const colors = [1, 2, 3, 4]; // RED, BLUE, GREEN, YELLOW
        return [
            colors[Math.floor(Math.random() * colors.length)],
            colors[Math.floor(Math.random() * colors.length)]
        ];
    }
    
    setupControls() {
        document.addEventListener('keydown', (e) => {
            // ゲーム用のキーの場合、デフォルト動作を無効化
            const gameKeys = ['ArrowLeft', 'ArrowRight', 'ArrowDown', 'ArrowUp', ' ', 'q', 'Q', 'r', 'R'];
            if (gameKeys.includes(e.key)) {
                e.preventDefault(); // スクロールなどのデフォルト動作を無効化
            }
            
            if (this.gameOver) {
                if (e.key === 'r' || e.key === 'R') {
                    this.resetGame();
                }
                return;
            }
            
            switch(e.key) {
                case 'ArrowLeft':
                    this.movePuyo(-1, 0);
                    break;
                case 'ArrowRight':
                    this.movePuyo(1, 0);
                    break;
                case 'ArrowDown':
                    this.movePuyoDown();
                    break;
                case ' ':
                    this.rotatePuyo();
                    break;
                case 'q':
                case 'Q':
                    this.endGame();
                    break;
            }
        });
        
        // キーアップイベントでも無効化（念のため）
        document.addEventListener('keyup', (e) => {
            const gameKeys = ['ArrowLeft', 'ArrowRight', 'ArrowDown', 'ArrowUp', ' '];
            if (gameKeys.includes(e.key)) {
                e.preventDefault();
            }
        });
    }
    
    getPuyoPositions() {
        const rotationOffsets = [
            [0, -1], // 上
            [1, 0],  // 右
            [0, 1],  // 下
            [-1, 0]  // 左
        ];
        
        const mainPos = [this.puyoX, this.puyoY];
        const [offsetX, offsetY] = rotationOffsets[this.puyoRotation];
        const subPos = [this.puyoX + offsetX, this.puyoY + offsetY];
        
        return [mainPos, subPos];
    }
    
    isValidPosition(x, y, rotation = null) {
        if (rotation === null) rotation = this.puyoRotation;
        
        const rotationOffsets = [[0, -1], [1, 0], [0, 1], [-1, 0]];
        
        // 主ぷよチェック
        if (x < 0 || x >= this.BOARD_WIDTH || y < 0 || y >= this.BOARD_HEIGHT) return false;
        if (this.board[y][x] !== 0) return false;
        
        // 副ぷよチェック
        const [offsetX, offsetY] = rotationOffsets[rotation];
        const subX = x + offsetX;
        const subY = y + offsetY;
        
        if (subX < 0 || subX >= this.BOARD_WIDTH || subY < 0 || subY >= this.BOARD_HEIGHT) return false;
        if (this.board[subY][subX] !== 0) return false;
        
        return true;
    }
    
    movePuyo(dx, dy) {
        const newX = this.puyoX + dx;
        const newY = this.puyoY + dy;
        
        if (this.isValidPosition(newX, newY)) {
            this.puyoX = newX;
            this.puyoY = newY;
            return true;
        }
        return false;
    }
    
    movePuyoDown() {
        if (!this.movePuyo(0, 1)) {
            this.placePuyo();
            this.applyGravity();
            this.checkChains();
            
            if (this.checkGameOver()) {
                this.gameOver = true;
                return;
            }
            
            this.currentPuyo = this.nextPuyo;
            this.nextPuyo = this.createNewPuyo();
            this.puyoX = Math.floor(this.BOARD_WIDTH / 2) - 1;
            this.puyoY = 0;
            this.puyoRotation = 0;
        }
    }
    
    rotatePuyo() {
        const newRotation = (this.puyoRotation + 1) % 4;
        
        // まず現在位置で回転を試す
        if (this.isValidPosition(this.puyoX, this.puyoY, newRotation)) {
            this.puyoRotation = newRotation;
            return;
        }
        
        // 壁キック：回転状態に応じた優先順位でオフセットを試す
        const kickOffsets = this.getWallKickOffsets(this.puyoRotation, newRotation);
        
        for (let [offsetX, offsetY] of kickOffsets) {
            const newX = this.puyoX + offsetX;
            const newY = this.puyoY + offsetY;
            
            if (this.isValidPosition(newX, newY, newRotation)) {
                this.puyoX = newX;
                this.puyoY = newY;
                this.puyoRotation = newRotation;
                return;
            }
        }
        
        // どうしても回転できない場合は何もしない
    }
    
    getWallKickOffsets(fromRotation, toRotation) {
        // 回転方向に応じた壁キックオフセット
        // より自然な回転を実現するため、回転状態別に優先順位を設定
        
        const baseOffsets = [
            [1, 0],   // 右に1マス
            [-1, 0],  // 左に1マス
            [0, -1],  // 上に1マス
            [2, 0],   // 右に2マス
            [-2, 0],  // 左に2マス
            [1, -1],  // 右上に1マス
            [-1, -1], // 左上に1マス
            [0, 1],   // 下に1マス
            [1, 1],   // 右下に1マス
            [-1, 1]   // 左下に1マス
        ];
        
        // 特定の回転パターンで優先順位を調整
        if (fromRotation === 0 && toRotation === 1) { // 上→右
            return [[-1, 0], [-2, 0], [0, -1], [-1, -1], ...baseOffsets];
        } else if (fromRotation === 1 && toRotation === 2) { // 右→下
            return [[0, -1], [1, 0], [2, 0], [1, -1], ...baseOffsets];
        } else if (fromRotation === 2 && toRotation === 3) { // 下→左
            return [[1, 0], [2, 0], [0, -1], [1, -1], ...baseOffsets];
        } else if (fromRotation === 3 && toRotation === 0) { // 左→上
            return [[-1, 0], [-2, 0], [0, -1], [-1, -1], ...baseOffsets];
        }
        
        return baseOffsets;
    }
    
    drawFallingOjamas() {
        // 落下中のおじゃまぷよを描画
        this.fallingOjamas.forEach(ojama => {
            const cellX = this.BOARD_X + ojama.x * this.CELL_SIZE;
            const cellY = ojama.pixelY;
            
            // おじゃまぷよ画像または特別描画
            if (this.images[5] && this.images[5].complete) {
                this.ctx.drawImage(this.images[5], cellX, cellY, this.CELL_SIZE, this.CELL_SIZE);
            } else {
                this.drawOjamaPuyo(cellX, cellY);
            }
            
            // 落下エフェクト（影）- 着地予定地に薄い影を表示
            if (ojama.targetRow >= 0 && ojama.targetRow < this.BOARD_HEIGHT) {
                this.ctx.globalAlpha = 0.2;
                this.ctx.fillStyle = '#666666';
                const shadowY = this.BOARD_Y + ojama.targetRow * this.CELL_SIZE;
                
                // 影を楕円形にして、より自然に
                this.ctx.beginPath();
                this.ctx.ellipse(
                    cellX + this.CELL_SIZE / 2, 
                    shadowY + this.CELL_SIZE - 5, 
                    this.CELL_SIZE / 3, 
                    this.CELL_SIZE / 6, 
                    0, 0, Math.PI * 2
                );
                this.ctx.fill();
                this.ctx.globalAlpha = 1.0;
            }
        });
    }
    
    placePuyo() {
        const [mainPos, subPos] = this.getPuyoPositions();
        this.board[mainPos[1]][mainPos[0]] = this.currentPuyo[0];
        this.board[subPos[1]][subPos[0]] = this.currentPuyo[1];
    }
    
    applyGravity() {
        for (let x = 0; x < this.BOARD_WIDTH; x++) {
            const column = [];
            for (let y = 0; y < this.BOARD_HEIGHT; y++) {
                if (this.board[y][x] !== 0) {
                    column.push(this.board[y][x]);
                }
            }
            
            for (let y = 0; y < this.BOARD_HEIGHT; y++) {
                this.board[y][x] = 0;
            }
            
            for (let i = 0; i < column.length; i++) {
                this.board[this.BOARD_HEIGHT - 1 - i][x] = column[column.length - 1 - i];
            }
        }
    }
    
    checkChains() {
        let chainsFound = true;
        let chainCount = 0;
        let totalScore = 0;
        
        while (chainsFound) {
            chainsFound = false;
            const toRemove = new Set();
            
            for (let y = 0; y < this.BOARD_HEIGHT; y++) {
                for (let x = 0; x < this.BOARD_WIDTH; x++) {
                    if (this.board[y][x] !== 0) {
                        const connected = this.findConnectedPuyos(x, y, this.board[y][x]);
                        if (connected.length >= 4) {
                            connected.forEach(pos => toRemove.add(`${pos[0]},${pos[1]}`));
                            chainsFound = true;
                        }
                    }
                }
            }
            
            if (toRemove.size > 0) {
                chainCount++;
                const chainBonus = chainCount * 50;
                const puyoScore = toRemove.size * 10;
                totalScore += puyoScore + chainBonus;
                
                // おじゃまぷよも消去（隣接するものを探す）
                const ojamaToRemove = new Set();
                toRemove.forEach(posStr => {
                    const [x, y] = posStr.split(',').map(Number);
                    // 隣接する4方向をチェック
                    const directions = [[0, 1], [0, -1], [1, 0], [-1, 0]];
                    directions.forEach(([dx, dy]) => {
                        const nx = x + dx;
                        const ny = y + dy;
                        if (nx >= 0 && nx < this.BOARD_WIDTH && ny >= 0 && ny < this.BOARD_HEIGHT) {
                            if (this.board[ny][nx] === 5) { // おじゃまぷよ
                                ojamaToRemove.add(`${nx},${ny}`);
                            }
                        }
                    });
                });
                
                // パーティクル生成（通常ぷよ）
                toRemove.forEach(posStr => {
                    const [x, y] = posStr.split(',').map(Number);
                    this.createParticles(
                        this.BOARD_X + x * this.CELL_SIZE + this.CELL_SIZE / 2,
                        this.BOARD_Y + y * this.CELL_SIZE + this.CELL_SIZE / 2,
                        this.board[y][x],
                        chainCount
                    );
                    this.board[y][x] = 0;
                });
                
                // パーティクル生成（おじゃまぷよ）
                ojamaToRemove.forEach(posStr => {
                    const [x, y] = posStr.split(',').map(Number);
                    this.createParticles(
                        this.BOARD_X + x * this.CELL_SIZE + this.CELL_SIZE / 2,
                        this.BOARD_Y + y * this.CELL_SIZE + this.CELL_SIZE / 2,
                        5,
                        1
                    );
                    this.board[y][x] = 0;
                });
                
                this.applyGravity();
            }
        }
        
        this.score += totalScore;
        return chainCount;
    }
    
    findConnectedPuyos(startX, startY, color) {
        if (color === 0 || color === 5) return []; // 空またはおじゃまぷよは連鎖しない
        
        const visited = new Set();
        const stack = [[startX, startY]];
        const connected = [];
        const directions = [[0, 1], [0, -1], [1, 0], [-1, 0]];
        
        while (stack.length > 0) {
            const [x, y] = stack.pop();
            const key = `${x},${y}`;
            
            if (visited.has(key)) continue;
            if (x < 0 || x >= this.BOARD_WIDTH || y < 0 || y >= this.BOARD_HEIGHT) continue;
            if (this.board[y][x] !== color) continue;
            
            visited.add(key);
            connected.push([x, y]);
            
            directions.forEach(([dx, dy]) => {
                const nx = x + dx;
                const ny = y + dy;
                const nkey = `${nx},${ny}`;
                if (!visited.has(nkey)) {
                    stack.push([nx, ny]);
                }
            });
        }
        
        return connected;
    }
    
    createParticles(x, y, color, chainLevel = 1) {
        // 連鎖レベルに応じてパーティクル数を調整
        const baseCount = 8;
        const actualCount = chainLevel >= 2 ? Math.min(baseCount * 1.5, 20) : baseCount;
        
        for (let i = 0; i < actualCount; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 4 + 2;
            
            // 色別の特殊設定
            const particleConfig = this.getParticleConfig(color, chainLevel);
            
            this.particles.push({
                x: x,
                y: y,
                vx: Math.cos(angle) * speed + particleConfig.windX,
                vy: Math.sin(angle) * speed - 2 + particleConfig.initialVY,
                life: 1.0,
                color: particleConfig.color,
                size: Math.random() * 3 + 2,
                gravity: particleConfig.gravity,
                shape: particleConfig.shape,
                time: 0,
                isRainbow: chainLevel >= 5 && Math.random() < 0.2
            });
        }
    }
    
    getParticleConfig(color, chainLevel) {
        const configs = {
            1: { // RED - 炎効果
                color: '#FF6464',
                gravity: 0.15,
                windX: Math.random() * 0.4 - 0.2,
                initialVY: -0.1,
                shape: 'flame'
            },
            2: { // BLUE - 水滴効果
                color: '#6496FF',
                gravity: 0.25,
                windX: 0,
                initialVY: 0,
                shape: 'drop'
            },
            3: { // GREEN - 葉っぱ効果
                color: '#64FF64',
                gravity: 0.1,
                windX: Math.random() * 0.6 - 0.3,
                initialVY: 0,
                shape: 'leaf'
            },
            4: { // YELLOW - 星効果
                color: '#FFFF64',
                gravity: 0.05,
                windX: Math.random() * 0.2 - 0.1,
                initialVY: Math.random() * 0.2 - 0.1,
                shape: 'star'
            },
            5: { // OJAMA
                color: '#B4B4B4',
                gravity: 0.3,
                windX: 0,
                initialVY: 0,
                shape: 'circle'
            }
        };
        
        return configs[color] || configs[1];
    }
    
    updateParticles() {
        this.particles = this.particles.filter(particle => {
            particle.time += 1;
            
            // 虹色パーティクルの色更新
            if (particle.isRainbow) {
                particle.color = this.getRainbowColor(particle.time);
                // 虹色は特別な動き
                particle.vx += (Math.random() - 0.5) * 0.4;
                particle.vy += (Math.random() - 0.5) * 0.4;
            } else {
                // 色別特殊効果
                switch(particle.shape) {
                    case 'flame': // 赤：上昇気流
                        particle.vy -= 0.1;
                        particle.vx += (Math.random() - 0.5) * 0.4;
                        break;
                    case 'leaf': // 緑：横風
                        particle.vx += (Math.random() - 0.5) * 0.6;
                        break;
                    case 'star': // 黄：ランダム移動
                        particle.vx += (Math.random() - 0.5) * 0.2;
                        particle.vy += (Math.random() - 0.5) * 0.2;
                        break;
                }
            }
            
            // 位置更新
            particle.x += particle.vx;
            particle.y += particle.vy;
            particle.vy += particle.gravity;
            
            // 寿命減少
            particle.life -= 0.02;
            
            return particle.life > 0 && particle.y < 700;
        });
    }
    
    getRainbowColor(time) {
        const hue = (time * 5) % 360;
        return `hsl(${hue}, 100%, 60%)`;
    }
    
    drawParticleShape(particle) {
        const x = particle.x;
        const y = particle.y;
        const size = particle.size;
        
        this.ctx.fillStyle = particle.color;
        
        switch(particle.shape) {
            case 'flame': // 炎：縦長の楕円
                const flameHeight = size * 2;
                const flameWidth = Math.max(1, size / 2);
                const offsetX = (Math.random() - 0.5) * 2;
                const offsetY = (Math.random() - 0.5) * 4;
                
                this.ctx.beginPath();
                this.ctx.ellipse(x + offsetX, y + offsetY, flameWidth, flameHeight, 0, 0, Math.PI * 2);
                this.ctx.fill();
                break;
                
            case 'drop': // 水滴：涙型
                // メイン部分（楕円）
                this.ctx.beginPath();
                this.ctx.ellipse(x, y, size/2, size, 0, 0, Math.PI * 2);
                this.ctx.fill();
                // 上部の小さな円
                this.ctx.beginPath();
                this.ctx.arc(x, y - size, Math.max(1, size/3), 0, Math.PI * 2);
                this.ctx.fill();
                break;
                
            case 'leaf': // 葉っぱ：楕円 + 線
                this.ctx.beginPath();
                this.ctx.ellipse(x, y, size, size/2, 0, 0, Math.PI * 2);
                this.ctx.fill();
                // 葉脈
                this.ctx.strokeStyle = particle.color;
                this.ctx.lineWidth = 1;
                this.ctx.beginPath();
                this.ctx.moveTo(x - size, y);
                this.ctx.lineTo(x + size, y);
                this.ctx.stroke();
                break;
                
            case 'star': // 星：十字形
                const starSize = size;
                // 縦線
                this.ctx.fillRect(x - 1, y - starSize, 2, starSize * 2);
                // 横線
                this.ctx.fillRect(x - starSize, y - 1, starSize * 2, 2);
                // 中心の円
                this.ctx.beginPath();
                this.ctx.arc(x, y, Math.max(1, starSize/3), 0, Math.PI * 2);
                this.ctx.fill();
                break;
                
            default: // デフォルト：円形
                this.ctx.beginPath();
                this.ctx.arc(x, y, size, 0, Math.PI * 2);
                this.ctx.fill();
                break;
        }
    }
    
    checkGameOver() {
        const startX = Math.floor(this.BOARD_WIDTH / 2) - 1;
        const startY = 1;
        
        for (let rotation = 0; rotation < 4; rotation++) {
            if (this.isValidPosition(startX, startY, rotation)) {
                return false;
            }
        }
        return true;
    }
    
    endGame() {
        if (!this.gameOver) {
            this.gameOver = true;
        }
    }
    
    dropOjamaPuyos() {
        // レベルに応じておじゃまぷよの数を決定
        this.ojamaCount += this.level;
        
        // 各列にランダムにおじゃまぷよを落下開始
        const columns = Array.from({length: this.BOARD_WIDTH}, (_, i) => i);
        this.shuffleArray(columns);
        
        for (let i = 0; i < Math.min(this.ojamaCount, this.BOARD_WIDTH); i++) {
            const col = columns[i];
            
            // 画面上部から落下開始
            this.fallingOjamas.push({
                x: col,
                y: -2, // 画面上部から開始
                pixelY: this.BOARD_Y - 3 * this.CELL_SIZE, // 実際の描画位置（より上から）
                fallSpeed: 2, // 落下速度を少し遅く（ピクセル/フレーム）
                targetRow: this.findTargetRow(col) // 着地予定行
            });
        }
        
        this.ojamaCount -= Math.min(this.ojamaCount, this.BOARD_WIDTH);
    }
    
    findTargetRow(col) {
        // 指定された列で着地する行を見つける
        for (let row = 0; row < this.BOARD_HEIGHT; row++) {
            if (this.board[row][col] === 0) {
                return row;
            }
        }
        return this.BOARD_HEIGHT - 1; // 列が満杯の場合は最上段
    }
    
    updateFallingOjamas() {
        // 落下中のおじゃまぷよを更新
        this.fallingOjamas = this.fallingOjamas.filter(ojama => {
            // 落下
            ojama.pixelY += ojama.fallSpeed;
            
            // 着地位置を再計算（他のぷよが変化している可能性があるため）
            ojama.targetRow = this.findTargetRow(ojama.x);
            
            // 着地判定（少し余裕を持たせる）
            const targetPixelY = this.BOARD_Y + ojama.targetRow * this.CELL_SIZE;
            if (ojama.pixelY >= targetPixelY - 5) { // 5ピクセルの余裕
                // 着地：ボードに配置
                if (ojama.targetRow >= 0 && ojama.targetRow < this.BOARD_HEIGHT) {
                    // 既に何かが配置されていないかチェック
                    if (this.board[ojama.targetRow][ojama.x] === 0) {
                        this.board[ojama.targetRow][ojama.x] = 5;
                        
                        // 着地エフェクト
                        this.createParticles(
                            this.BOARD_X + ojama.x * this.CELL_SIZE + this.CELL_SIZE / 2,
                            this.BOARD_Y + ojama.targetRow * this.CELL_SIZE + this.CELL_SIZE / 2,
                            5,
                            1
                        );
                        
                        // 少し遅延してから重力適用（視覚的に自然にするため）
                        setTimeout(() => {
                            this.applyGravity();
                        }, 100);
                    }
                }
                
                return false; // 配列から削除
            }
            
            // 画面下部を超えた場合も削除
            if (ojama.pixelY > this.BOARD_Y + this.BOARD_HEIGHT * this.CELL_SIZE + 50) {
                return false;
            }
            
            return true; // 継続して落下
        });
    }
    
    shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }
    
    drawOjamaPuyo(x, y) {
        // 灰色の円
        this.ctx.fillStyle = '#969696';
        this.ctx.beginPath();
        this.ctx.arc(x + this.CELL_SIZE/2, y + this.CELL_SIZE/2, this.CELL_SIZE/2 - 2, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 赤い目
        const eyeRadius = this.CELL_SIZE / 12;
        const eyeOffset = this.CELL_SIZE / 6;
        const centerX = x + this.CELL_SIZE/2;
        const centerY = y + this.CELL_SIZE/2;
        
        // 左目
        this.ctx.fillStyle = '#FF0000';
        this.ctx.beginPath();
        this.ctx.arc(centerX - eyeOffset, centerY - eyeOffset, eyeRadius, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 右目
        this.ctx.beginPath();
        this.ctx.arc(centerX + eyeOffset, centerY - eyeOffset, eyeRadius, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 白い光沢
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.beginPath();
        this.ctx.arc(centerX - eyeOffset, centerY - eyeOffset - 1, eyeRadius/3, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.beginPath();
        this.ctx.arc(centerX + eyeOffset, centerY - eyeOffset - 1, eyeRadius/3, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 白い牙
        this.ctx.fillStyle = '#FFFFFF';
        const teethWidth = this.CELL_SIZE / 6;
        const teethHeight = this.CELL_SIZE / 10;
        const teethY = centerY + eyeOffset/2;
        
        // 左の牙
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - teethWidth, teethY);
        this.ctx.lineTo(centerX - teethWidth/2, teethY + teethHeight);
        this.ctx.lineTo(centerX, teethY);
        this.ctx.fill();
        
        // 右の牙
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, teethY);
        this.ctx.lineTo(centerX + teethWidth/2, teethY + teethHeight);
        this.ctx.lineTo(centerX + teethWidth, teethY);
        this.ctx.fill();
    }
    
    resetGame() {
        this.board = Array(this.BOARD_HEIGHT).fill().map(() => Array(this.BOARD_WIDTH).fill(0));
        this.currentPuyo = this.createNewPuyo();
        this.nextPuyo = this.createNewPuyo();
        this.puyoX = Math.floor(this.BOARD_WIDTH / 2) - 1;
        this.puyoY = 0;
        this.puyoRotation = 0;
        this.score = 0;
        this.level = 1;
        this.gameOver = false;
        this.fallTimer = 0;
        this.ojamaTimer = 0;
        this.ojamaCount = 0;
        this.fallingOjamas = [];
        this.particles = [];
    }
    
    draw() {
        // 背景クリア
        this.ctx.fillStyle = '#323232';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // ボード描画
        for (let y = 0; y < this.BOARD_HEIGHT; y++) {
            for (let x = 0; x < this.BOARD_WIDTH; x++) {
                const cellX = this.BOARD_X + x * this.CELL_SIZE;
                const cellY = this.BOARD_Y + y * this.CELL_SIZE;
                
                if (this.board[y][x] === 0) {
                    this.ctx.fillStyle = '#000000';
                    this.ctx.fillRect(cellX, cellY, this.CELL_SIZE, this.CELL_SIZE);
                    this.ctx.strokeStyle = '#FFFFFF';
                    this.ctx.strokeRect(cellX, cellY, this.CELL_SIZE, this.CELL_SIZE);
                } else {
                    // 画像があれば画像を使用、なければ色で描画
                    const color = this.board[y][x];
                    if (this.images[color] && this.images[color].complete) {
                        this.ctx.drawImage(this.images[color], cellX, cellY, this.CELL_SIZE, this.CELL_SIZE);
                    } else if (color === 5) {
                        // おじゃまぷよの特別描画
                        this.drawOjamaPuyo(cellX, cellY);
                    } else {
                        this.ctx.fillStyle = this.COLORS[color];
                        this.ctx.fillRect(cellX, cellY, this.CELL_SIZE, this.CELL_SIZE);
                        this.ctx.strokeStyle = '#FFFFFF';
                        this.ctx.lineWidth = 2;
                        this.ctx.strokeRect(cellX, cellY, this.CELL_SIZE, this.CELL_SIZE);
                    }
                }
            }
        }
        
        // 現在のぷよ描画
        if (this.currentPuyo && !this.gameOver) {
            const [mainPos, subPos] = this.getPuyoPositions();
            
            // 主ぷよ
            const mainX = this.BOARD_X + mainPos[0] * this.CELL_SIZE;
            const mainY = this.BOARD_Y + mainPos[1] * this.CELL_SIZE;
            const mainColor = this.currentPuyo[0];
            if (this.images[mainColor] && this.images[mainColor].complete) {
                this.ctx.drawImage(this.images[mainColor], mainX, mainY, this.CELL_SIZE, this.CELL_SIZE);
            } else {
                this.ctx.fillStyle = this.COLORS[mainColor];
                this.ctx.fillRect(mainX, mainY, this.CELL_SIZE, this.CELL_SIZE);
                this.ctx.strokeStyle = '#FFFFFF';
                this.ctx.lineWidth = 2;
                this.ctx.strokeRect(mainX, mainY, this.CELL_SIZE, this.CELL_SIZE);
            }
            
            // 副ぷよ
            const subX = this.BOARD_X + subPos[0] * this.CELL_SIZE;
            const subY = this.BOARD_Y + subPos[1] * this.CELL_SIZE;
            const subColor = this.currentPuyo[1];
            if (this.images[subColor] && this.images[subColor].complete) {
                this.ctx.drawImage(this.images[subColor], subX, subY, this.CELL_SIZE, this.CELL_SIZE);
            } else {
                this.ctx.fillStyle = this.COLORS[subColor];
                this.ctx.fillRect(subX, subY, this.CELL_SIZE, this.CELL_SIZE);
                this.ctx.strokeStyle = '#FFFFFF';
                this.ctx.lineWidth = 2;
                this.ctx.strokeRect(subX, subY, this.CELL_SIZE, this.CELL_SIZE);
            }
        }
        
        // パーティクル描画
        this.particles.forEach(particle => {
            this.ctx.globalAlpha = particle.life;
            this.drawParticleShape(particle);
        });
        this.ctx.globalAlpha = 1.0;
        
        // 落下中のおじゃまぷよ描画
        this.drawFallingOjamas();
        
        // UI描画
        this.drawUI();
        
        // ゲームオーバー表示
        if (this.gameOver) {
            this.drawGameOver();
        }
    }
    
    drawUI() {
        const uiX = this.BOARD_X + this.BOARD_WIDTH * this.CELL_SIZE + 20;
        
        // スコア
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = '24px Arial';
        this.ctx.fillText(`Score: ${this.score}`, uiX, this.BOARD_Y + 30);
        
        // レベル
        this.ctx.fillText(`Level: ${this.level}`, uiX, this.BOARD_Y + 60);
        
        // 次のぷよ
        this.ctx.font = '18px Arial';
        this.ctx.fillText('Next:', uiX, this.BOARD_Y + 100);
        
        if (this.nextPuyo) {
            const nextX = uiX + 10;
            const nextY = this.BOARD_Y + 120;
            
            // 主ぷよ（上）
            const nextColor1 = this.nextPuyo[0];
            if (this.images[nextColor1] && this.images[nextColor1].complete) {
                this.ctx.drawImage(this.images[nextColor1], nextX, nextY, 30, 30);
            } else {
                this.ctx.fillStyle = this.COLORS[nextColor1];
                this.ctx.fillRect(nextX, nextY, 30, 30);
                this.ctx.strokeStyle = '#FFFFFF';
                this.ctx.strokeRect(nextX, nextY, 30, 30);
            }
            
            // 副ぷよ（下）
            const nextColor2 = this.nextPuyo[1];
            if (this.images[nextColor2] && this.images[nextColor2].complete) {
                this.ctx.drawImage(this.images[nextColor2], nextX, nextY + 35, 30, 30);
            } else {
                this.ctx.fillStyle = this.COLORS[nextColor2];
                this.ctx.fillRect(nextX, nextY + 35, 30, 30);
                this.ctx.strokeStyle = '#FFFFFF';
                this.ctx.strokeRect(nextX, nextY + 35, 30, 30);
            }
        }
        
        // 操作説明
        this.ctx.font = '14px Arial';
        this.ctx.fillStyle = '#CCCCCC';
        const instructions = [
            'Controls:',
            '← →: Move',
            '↓: Drop',
            'Space: Rotate',
            'Q: End Game'
        ];
        
        instructions.forEach((text, i) => {
            this.ctx.fillText(text, uiX, this.BOARD_Y + 200 + i * 20);
        });
    }
    
    drawGameOver() {
        // 半透明背景
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // ゲームオーバーテキスト
        this.ctx.fillStyle = '#FF0000';
        this.ctx.font = '48px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('GAME OVER', this.canvas.width / 2, this.canvas.height / 2 - 50);
        
        // 最終スコア
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = '24px Arial';
        this.ctx.fillText(`Final Score: ${this.score}`, this.canvas.width / 2, this.canvas.height / 2);
        
        // リスタート案内
        this.ctx.font = '18px Arial';
        this.ctx.fillText('Press R to Restart', this.canvas.width / 2, this.canvas.height / 2 + 50);
        
        this.ctx.textAlign = 'left';
    }
    
    gameLoop() {
        const now = Date.now();
        
        if (!this.gameOver) {
            this.fallTimer += 16; // 約60FPS
            if (this.fallTimer >= this.fallSpeed) {
                this.movePuyoDown();
                this.fallTimer = 0;
            }
            
            // おじゃまぷよタイマー
            this.ojamaTimer += 16;
            if (this.ojamaTimer >= this.ojamaInterval) {
                this.dropOjamaPuyos();
                this.ojamaTimer = 0;
            }
        }
        
        this.updateParticles();
        this.updateFallingOjamas();
        this.draw();
        
        requestAnimationFrame(() => this.gameLoop());
    }
}

// ゲーム開始
window.addEventListener('load', () => {
    const loading = document.getElementById('loading');
    const canvas = document.getElementById('gameCanvas');
    
    setTimeout(() => {
        loading.style.display = 'none';
        canvas.style.display = 'block';
        
        // キャンバスをフォーカス可能にして、キーイベントを確実に受け取る
        canvas.tabIndex = 0;
        canvas.focus();
        
        new PuyoGame();
    }, 1000);
});