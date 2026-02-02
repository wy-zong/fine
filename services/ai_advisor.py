"""
AI 投資建議服務 - 基於技術分析生成建議
"""
from typing import Dict, List
from services.stock_service import StockService
from services.analysis_service import AnalysisService


class AIAdvisor:
    """AI 投資建議服務"""
    
    RECOMMENDATION_WEIGHTS = {
        'trend': 0.3,
        'rsi': 0.25,
        'macd': 0.25,
        'price_position': 0.2,
    }
    
    @staticmethod
    def get_recommendation(symbol: str) -> Dict:
        """
        取得股票投資建議
        
        Args:
            symbol: 股票代碼
        
        Returns:
            投資建議
        """
        # 取得資料
        info = StockService.get_stock_info(symbol)
        if 'error' in info:
            return {'symbol': symbol, 'error': info['error']}
        
        df = StockService.get_historical_data(symbol, period='6mo')
        if df.empty:
            return {'symbol': symbol, 'error': '無法取得歷史資料'}
        
        # 技術分析
        analysis = AnalysisService.get_technical_summary(df)
        if 'error' in analysis:
            return {'symbol': symbol, 'error': analysis['error']}
        
        # 計算各項分數 (-1 到 1)
        scores = {}
        
        # 趨勢分數
        if analysis['trend'] == 'bullish':
            scores['trend'] = 1.0
        elif analysis['trend'] == 'bearish':
            scores['trend'] = -1.0
        else:
            scores['trend'] = 0.0
        
        # RSI 分數
        rsi = analysis['rsi']
        if rsi < 30:
            scores['rsi'] = 1.0  # 超賣，可能反彈
        elif rsi > 70:
            scores['rsi'] = -1.0  # 超買，可能回檔
        elif rsi < 40:
            scores['rsi'] = 0.5
        elif rsi > 60:
            scores['rsi'] = -0.5
        else:
            scores['rsi'] = 0.0
        
        # MACD 分數
        if analysis['macd_status'] == 'bullish':
            scores['macd'] = 0.8 if analysis['macd_histogram'] > 0 else 0.4
        else:
            scores['macd'] = -0.8 if analysis['macd_histogram'] < 0 else -0.4
        
        # 價格位置分數（相對於布林通道）
        close = analysis['close']
        bb_upper = analysis['bb_upper']
        bb_lower = analysis['bb_lower']
        bb_middle = analysis['bb_middle']
        
        if close < bb_lower:
            scores['price_position'] = 1.0  # 低於下軌，可能超賣
        elif close > bb_upper:
            scores['price_position'] = -1.0  # 高於上軌，可能超買
        elif close < bb_middle:
            scores['price_position'] = 0.3
        else:
            scores['price_position'] = -0.3
        
        # 加權總分
        total_score = sum(
            scores[key] * AIAdvisor.RECOMMENDATION_WEIGHTS[key]
            for key in scores
        )
        
        # 生成建議
        if total_score >= 0.5:
            recommendation = 'BUY'
            recommendation_zh = '買進'
            confidence = min(abs(total_score) * 100, 100)
        elif total_score <= -0.5:
            recommendation = 'SELL'
            recommendation_zh = '賣出'
            confidence = min(abs(total_score) * 100, 100)
        else:
            recommendation = 'HOLD'
            recommendation_zh = '持有'
            confidence = (1 - abs(total_score)) * 100
        
        # 生成理由
        reasons = []
        if analysis['trend'] == 'bullish':
            reasons.append('短期均線在長期均線之上，呈現多頭排列')
        elif analysis['trend'] == 'bearish':
            reasons.append('短期均線在長期均線之下，呈現空頭排列')
        
        if analysis['rsi_status'] == 'oversold':
            reasons.append(f'RSI {analysis["rsi"]:.1f} 處於超賣區，可能出現反彈')
        elif analysis['rsi_status'] == 'overbought':
            reasons.append(f'RSI {analysis["rsi"]:.1f} 處於超買區，注意回檔風險')
        
        if analysis['macd_status'] == 'bullish':
            reasons.append('MACD 呈現黃金交叉，動能轉強')
        else:
            reasons.append('MACD 呈現死亡交叉，動能轉弱')
        
        return {
            'symbol': symbol,
            'name': info.get('name', symbol),
            'current_price': info.get('current_price', 0),
            'currency': info.get('currency', 'USD'),
            'recommendation': recommendation,
            'recommendation_zh': recommendation_zh,
            'confidence': round(confidence, 1),
            'score': round(total_score, 2),
            'technical_analysis': analysis,
            'reasons': reasons,
            'disclaimer': '⚠️ 此建議僅供參考，不構成投資建議。投資有風險，請自行評估。',
        }
    
    @staticmethod
    def get_portfolio_recommendations(symbols: List[str]) -> List[Dict]:
        """
        批次取得多支股票建議
        
        Args:
            symbols: 股票代碼列表
        
        Returns:
            建議列表
        """
        return [AIAdvisor.get_recommendation(symbol) for symbol in symbols]


# 測試用
if __name__ == '__main__':
    advisor = AIAdvisor()
    
    # 測試美股
    print("=== NVDA 投資建議 ===")
    rec = advisor.get_recommendation('NVDA')
    print(f"建議: {rec['recommendation_zh']} ({rec['recommendation']})")
    print(f"信心度: {rec['confidence']}%")
    print(f"理由:")
    for reason in rec.get('reasons', []):
        print(f"  - {reason}")
    print(rec['disclaimer'])
    
    # 測試台股
    print("\n=== 台積電 (2330.TW) 投資建議 ===")
    rec = advisor.get_recommendation('2330.TW')
    print(f"建議: {rec['recommendation_zh']} ({rec['recommendation']})")
    print(f"信心度: {rec['confidence']}%")
