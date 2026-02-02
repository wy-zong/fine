"""
技術分析服務 - 計算各種技術指標
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from config import Config


class AnalysisService:
    """技術分析服務"""
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = None) -> pd.Series:
        """
        計算 RSI (Relative Strength Index)
        
        Args:
            df: 包含 'Close' 欄位的 DataFrame
            period: RSI 週期
        
        Returns:
            RSI 序列
        """
        period = period or Config.RSI_PERIOD
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        計算 MACD (Moving Average Convergence Divergence)
        
        Returns:
            (MACD線, 信號線, 柱狀圖)
        """
        ema_fast = df['Close'].ewm(span=Config.MACD_FAST, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=Config.MACD_SLOW, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=Config.MACD_SIGNAL, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_moving_averages(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        計算移動平均線
        
        Returns:
            移動平均線字典
        """
        return {
            f'MA{Config.MA_SHORT}': df['Close'].rolling(window=Config.MA_SHORT).mean(),
            f'MA{Config.MA_LONG}': df['Close'].rolling(window=Config.MA_LONG).mean(),
            'MA5': df['Close'].rolling(window=5).mean(),
            'MA10': df['Close'].rolling(window=10).mean(),
        }
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        計算布林通道
        
        Returns:
            (上軌, 中軌, 下軌)
        """
        middle = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    @staticmethod
    def get_technical_summary(df: pd.DataFrame) -> Dict:
        """
        取得完整技術分析摘要
        
        Args:
            df: 股票歷史資料
        
        Returns:
            技術分析摘要
        """
        if df.empty or len(df) < Config.MA_LONG:
            return {'error': '資料不足，無法進行分析'}
        
        # 計算各項指標
        rsi = AnalysisService.calculate_rsi(df)
        macd_line, signal_line, histogram = AnalysisService.calculate_macd(df)
        mas = AnalysisService.calculate_moving_averages(df)
        bb_upper, bb_middle, bb_lower = AnalysisService.calculate_bollinger_bands(df)
        
        # 取得最新值
        latest_close = df['Close'].iloc[-1]
        latest_rsi = rsi.iloc[-1]
        latest_macd = macd_line.iloc[-1]
        latest_signal = signal_line.iloc[-1]
        latest_histogram = histogram.iloc[-1]
        
        # 判斷趨勢
        ma_short = mas[f'MA{Config.MA_SHORT}'].iloc[-1]
        ma_long = mas[f'MA{Config.MA_LONG}'].iloc[-1]
        
        trend = 'neutral'
        if ma_short > ma_long and latest_close > ma_short:
            trend = 'bullish'
        elif ma_short < ma_long and latest_close < ma_short:
            trend = 'bearish'
        
        # RSI 狀態
        rsi_status = 'neutral'
        if latest_rsi > 70:
            rsi_status = 'overbought'
        elif latest_rsi < 30:
            rsi_status = 'oversold'
        
        # MACD 狀態
        macd_status = 'bullish' if latest_macd > latest_signal else 'bearish'
        
        return {
            'close': round(latest_close, 2),
            'rsi': round(latest_rsi, 2),
            'rsi_status': rsi_status,
            'macd': round(latest_macd, 4),
            'macd_signal': round(latest_signal, 4),
            'macd_histogram': round(latest_histogram, 4),
            'macd_status': macd_status,
            'ma_short': round(ma_short, 2),
            'ma_long': round(ma_long, 2),
            'trend': trend,
            'bb_upper': round(bb_upper.iloc[-1], 2),
            'bb_middle': round(bb_middle.iloc[-1], 2),
            'bb_lower': round(bb_lower.iloc[-1], 2),
        }


# 測試用
if __name__ == '__main__':
    from stock_service import StockService
    
    # 取得歷史資料
    df = StockService.get_historical_data('AAPL', period='6mo')
    
    # 技術分析
    analysis = AnalysisService()
    summary = analysis.get_technical_summary(df)
    print("=== AAPL 技術分析 ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
