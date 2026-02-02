# AI 財務助手 (AI Finance Assistant)

🤖 一個智能的個人財務管理助手，提供投資分析、風險評估與自動化報告功能。

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 功能特點

### 📊 市場追蹤
- 即時追蹤美股與台股指數
- 自訂追蹤清單
- 市場摘要儀表板

### 📈 技術分析
- RSI、MACD、布林通道等技術指標
- AI 投資建議（買入/賣出/持有）
- K 線圖視覺化

### 💼 投資組合管理
- 持股新增/刪除/修改
- 損益追蹤與報酬率計算
- 交易記錄

### ⚠️ 風險分析
- 波動率（年化標準差）
- Beta 值（相對市場波動）
- 夏普比率（風險調整後報酬）
- 最大回撤
- 分散度評估

### ⏰ 自動化報告
- 每日 18:00 自動生成市場報告
- 投資組合損益追蹤

## 🚀 快速開始

### 環境需求
- Python 3.11+
- Conda (建議)

### 安裝步驟

```bash
# 1. 克隆倉庫
git clone https://github.com/YOUR_USERNAME/ai-finance-assistant.git
cd ai-finance-assistant

# 2. 建立虛擬環境
conda create -n ai-finance python=3.11 -y
conda activate ai-finance

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 啟動應用
python app.py
```

### 訪問應用
開啟瀏覽器訪問：http://localhost:5000

## 📁 專案結構

```
ai-finance-assistant/
├── app.py                    # Flask 主程式
├── config.py                 # 設定檔
├── requirements.txt          # 依賴套件
├── models/
│   └── portfolio.py          # 資料庫模型
├── services/
│   ├── stock_service.py      # 股票資料服務
│   ├── analysis_service.py   # 技術分析服務
│   ├── ai_advisor.py         # AI 建議服務
│   ├── risk_service.py       # 風險分析服務
│   └── scheduler_service.py  # 排程服務
├── templates/
│   ├── index.html            # 首頁儀表板
│   ├── analysis.html         # 技術分析頁
│   ├── portfolio.html        # 投資組合頁
│   └── risk.html             # 風險分析頁
└── static/css/
    └── style.css             # 樣式檔
```

## 📖 使用說明

### 股票代碼格式
| 市場 | 格式 | 範例 |
|------|------|------|
| 美股 | 直接輸入代碼 | AAPL, NVDA, TSLA |
| 台股 | 代碼.TW | 2330.TW, 0050.TW |

### API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/stock/<symbol>` | GET | 取得股票資訊 |
| `/api/analysis/<symbol>` | GET | 取得技術分析 |
| `/api/portfolio` | GET/POST | 投資組合 CRUD |
| `/api/watchlist` | GET/POST | 追蹤清單 CRUD |
| `/api/risk` | GET | 投組風險分析 |
| `/api/risk/<symbol>` | GET | 單一股票風險 |

## 🔧 技術棧

- **後端**: Flask, Flask-APScheduler
- **資料來源**: yfinance (免費 Yahoo Finance API)
- **資料庫**: SQLite
- **前端**: HTML, CSS, JavaScript, Plotly.js
- **數據分析**: Pandas, NumPy

## ⚠️ 免責聲明

本系統僅供學習與參考用途，不構成任何投資建議。投資有風險，請自行評估。

## 📄 授權

MIT License
