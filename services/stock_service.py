"""
股票資料服務 - 支援台股與美股
使用 yfinance (免費 API)
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import Config


class StockService:
    """股票資料服務"""
    
    @staticmethod
    def get_stock_info(symbol: str) -> Dict:
        """
        取得股票基本資訊
        
        Args:
            symbol: 股票代碼 (美股: AAPL, 台股: 2330.TW)
        
        Returns:
            股票資訊字典
        """
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return {
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', symbol)),
                'currency': info.get('currency', 'USD'),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'previous_close': info.get('previousClose', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
            }
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    @staticmethod
    def get_historical_data(symbol: str, period: str = '3mo', interval: str = '1d') -> pd.DataFrame:
        """
        取得歷史股價資料
        
        Args:
            symbol: 股票代碼
            period: 期間 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 間隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        
        Returns:
            歷史資料 DataFrame
        """
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period=period, interval=interval)
            df.reset_index(inplace=True)
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_multiple_stocks_data(symbols: List[str], period: str = '1d') -> Dict[str, Dict]:
        """
        批次取得多支股票資料
        
        Args:
            symbols: 股票代碼列表
            period: 期間
        
        Returns:
            股票資料字典
        """
        results = {}
        for symbol in symbols:
            info = StockService.get_stock_info(symbol)
            if 'error' not in info:
                results[symbol] = info
        return results
    
    @staticmethod
    def get_market_summary() -> Dict:
        """
        取得市場摘要（主要指數）
        
        Returns:
            市場指數資料
        """
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            '^TWII': '台灣加權指數',
        }
        
        summary = {}
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='2d')
                if len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = current - previous
                    change_pct = (change / previous) * 100
                    summary[name] = {
                        'symbol': symbol,
                        'price': round(current, 2),
                        'change': round(change, 2),
                        'change_pct': round(change_pct, 2),
                    }
            except Exception as e:
                summary[name] = {'symbol': symbol, 'error': str(e)}
        
        return summary


# 測試用
if __name__ == '__main__':
    service = StockService()
    
    # 測試美股
    print("=== 美股測試 ===")
    print(service.get_stock_info('AAPL'))
    
    # 測試台股
    print("\n=== 台股測試 ===")
    print(service.get_stock_info('2330.TW'))
    
    # 市場摘要
    print("\n=== 市場摘要 ===")
    print(service.get_market_summary())
