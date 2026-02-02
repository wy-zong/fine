"""
AI 財務助手 - 設定檔
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """應用程式設定"""
    
    # Flask 設定
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 資料庫設定
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/finance.db')
    
    # 排程設定
    SCHEDULER_API_ENABLED = True
    
    # 預設追蹤的股票
    DEFAULT_US_STOCKS = ['AAPL', 'TSLA', 'NVDA', 'GOOGL', 'MSFT']
    DEFAULT_TW_STOCKS = ['2330.TW', '2317.TW', '2454.TW', '2308.TW', '0050.TW']  # 台積電、鴻海、聯發科、台達電、0050
    
    # 技術分析參數
    RSI_PERIOD = 14
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    MA_SHORT = 20
    MA_LONG = 60
