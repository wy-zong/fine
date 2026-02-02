"""
投資組合風險分析服務
計算波動率、Beta、夏普比率、分散度等風險指標
"""
import numpy as np
import pandas as pd
from typing import Dict, List
from services.stock_service import StockService


class RiskAnalysisService:
    """投資組合風險分析服務"""
    
    RISK_FREE_RATE = 0.05  # 無風險利率假設 5%（年化）
    MARKET_INDEX = '^GSPC'  # S&P 500 作為市場基準
    
    @staticmethod
    def calculate_volatility(symbol: str, period: str = '1y') -> Dict:
        """
        計算單一股票的波動率
        
        Args:
            symbol: 股票代碼
            period: 計算期間
        
        Returns:
            波動率資訊
        """
        df = StockService.get_historical_data(symbol, period=period)
        if df.empty or len(df) < 20:
            return {'symbol': symbol, 'error': '資料不足'}
        
        # 計算日報酬率
        returns = df['Close'].pct_change().dropna()
        
        # 日波動率（標準差）
        daily_volatility = returns.std()
        
        # 年化波動率（假設一年 252 個交易日）
        annual_volatility = daily_volatility * np.sqrt(252)
        
        # 計算最大回撤
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()
        
        return {
            'symbol': symbol,
            'daily_volatility': round(daily_volatility * 100, 2),
            'annual_volatility': round(annual_volatility * 100, 2),
            'max_drawdown': round(max_drawdown * 100, 2),
            'avg_daily_return': round(returns.mean() * 100, 4),
            'data_points': len(returns),
        }
    
    @staticmethod
    def calculate_beta(symbol: str, period: str = '1y') -> Dict:
        """
        計算股票相對於市場的 Beta 值
        
        Args:
            symbol: 股票代碼
            period: 計算期間
        
        Returns:
            Beta 值資訊
        """
        # 取得股票資料
        stock_df = StockService.get_historical_data(symbol, period=period)
        market_df = StockService.get_historical_data(RiskAnalysisService.MARKET_INDEX, period=period)
        
        if stock_df.empty or market_df.empty:
            return {'symbol': symbol, 'error': '無法取得資料'}
        
        # 計算報酬率
        stock_returns = stock_df['Close'].pct_change().dropna()
        market_returns = market_df['Close'].pct_change().dropna()
        
        # 對齊日期
        min_len = min(len(stock_returns), len(market_returns))
        stock_returns = stock_returns.iloc[-min_len:]
        market_returns = market_returns.iloc[-min_len:]
        
        if len(stock_returns) < 20:
            return {'symbol': symbol, 'error': '資料點不足'}
        
        # 計算協方差和市場變異數
        covariance = np.cov(stock_returns, market_returns)[0][1]
        market_variance = np.var(market_returns)
        
        # Beta = Cov(stock, market) / Var(market)
        beta = covariance / market_variance if market_variance != 0 else 0
        
        # 計算相關係數
        correlation = np.corrcoef(stock_returns, market_returns)[0][1]
        
        return {
            'symbol': symbol,
            'beta': round(beta, 2),
            'correlation': round(correlation, 2),
            'interpretation': RiskAnalysisService._interpret_beta(beta),
        }
    
    @staticmethod
    def _interpret_beta(beta: float) -> str:
        """解釋 Beta 值意義"""
        if beta > 1.5:
            return '高風險：波動遠大於市場'
        elif beta > 1.0:
            return '較高風險：波動略大於市場'
        elif beta > 0.8:
            return '中等風險：與市場波動接近'
        elif beta > 0.5:
            return '較低風險：波動小於市場'
        else:
            return '防禦型：波動遠小於市場'
    
    @staticmethod
    def calculate_sharpe_ratio(symbol: str, period: str = '1y') -> Dict:
        """
        計算夏普比率 (風險調整後報酬)
        
        Sharpe Ratio = (Return - Risk Free Rate) / Volatility
        """
        df = StockService.get_historical_data(symbol, period=period)
        if df.empty or len(df) < 20:
            return {'symbol': symbol, 'error': '資料不足'}
        
        returns = df['Close'].pct_change().dropna()
        
        # 年化報酬率
        annual_return = returns.mean() * 252
        
        # 年化波動率
        annual_volatility = returns.std() * np.sqrt(252)
        
        # 夏普比率
        sharpe = (annual_return - RiskAnalysisService.RISK_FREE_RATE) / annual_volatility if annual_volatility != 0 else 0
        
        return {
            'symbol': symbol,
            'sharpe_ratio': round(sharpe, 2),
            'annual_return': round(annual_return * 100, 2),
            'annual_volatility': round(annual_volatility * 100, 2),
            'interpretation': RiskAnalysisService._interpret_sharpe(sharpe),
        }
    
    @staticmethod
    def _interpret_sharpe(sharpe: float) -> str:
        """解釋夏普比率"""
        if sharpe > 2:
            return '優秀：極佳的風險調整報酬'
        elif sharpe > 1:
            return '良好：優於無風險投資'
        elif sharpe > 0:
            return '普通：正報酬但風險調整後一般'
        else:
            return '差：風險調整後為負報酬'
    
    @staticmethod
    def analyze_portfolio_risk(holdings: List[Dict]) -> Dict:
        """
        分析整體投資組合風險
        
        Args:
            holdings: 持股列表 [{'symbol': str, 'shares': float, 'avg_cost': float}, ...]
        
        Returns:
            投資組合風險分析結果
        """
        if not holdings:
            return {'error': '無持股資料'}
        
        # 計算各持股現值和權重
        portfolio_value = 0
        stock_data = []
        
        for holding in holdings:
            symbol = holding['symbol']
            shares = holding['shares']
            
            try:
                info = StockService.get_stock_info(symbol)
                current_price = info.get('current_price', holding['avg_cost'])
                value = shares * current_price
                
                stock_data.append({
                    'symbol': symbol,
                    'value': value,
                    'shares': shares,
                    'price': current_price,
                })
                portfolio_value += value
            except:
                continue
        
        if portfolio_value == 0:
            return {'error': '無法計算投組價值'}
        
        # 計算各股權重
        for stock in stock_data:
            stock['weight'] = stock['value'] / portfolio_value
        
        # 計算各股風險指標
        risk_metrics = []
        total_weighted_volatility = 0
        total_weighted_beta = 0
        
        for stock in stock_data:
            symbol = stock['symbol']
            weight = stock['weight']
            
            vol_data = RiskAnalysisService.calculate_volatility(symbol)
            beta_data = RiskAnalysisService.calculate_beta(symbol)
            sharpe_data = RiskAnalysisService.calculate_sharpe_ratio(symbol)
            
            volatility = vol_data.get('annual_volatility', 0)
            beta = beta_data.get('beta', 1)
            sharpe = sharpe_data.get('sharpe_ratio', 0)
            max_dd = vol_data.get('max_drawdown', 0)
            
            total_weighted_volatility += weight * volatility
            total_weighted_beta += weight * beta
            
            risk_metrics.append({
                'symbol': symbol,
                'weight': round(weight * 100, 1),
                'volatility': volatility,
                'beta': beta,
                'sharpe': sharpe,
                'max_drawdown': max_dd,
            })
        
        # 計算分散度 (使用 Herfindahl Index)
        hhi = sum(stock['weight'] ** 2 for stock in stock_data)
        diversification_score = round((1 - hhi) * 100, 1)  # 越高越分散
        
        # 評估整體風險等級
        portfolio_beta = round(total_weighted_beta, 2)
        portfolio_volatility = round(total_weighted_volatility, 2)
        
        if portfolio_beta > 1.3 or portfolio_volatility > 30:
            risk_level = '高風險'
            risk_color = 'danger'
        elif portfolio_beta > 0.9 or portfolio_volatility > 20:
            risk_level = '中等風險'
            risk_color = 'warning'
        else:
            risk_level = '低風險'
            risk_color = 'success'
        
        return {
            'portfolio_value': round(portfolio_value, 2),
            'holdings_count': len(stock_data),
            'portfolio_beta': portfolio_beta,
            'portfolio_volatility': portfolio_volatility,
            'diversification_score': diversification_score,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'stock_risks': risk_metrics,
            'recommendations': RiskAnalysisService._generate_risk_recommendations(
                portfolio_beta, portfolio_volatility, diversification_score, risk_metrics
            ),
        }
    
    @staticmethod
    def _generate_risk_recommendations(beta: float, volatility: float, 
                                       diversification: float, stocks: List[Dict]) -> List[str]:
        """生成風險管理建議"""
        recommendations = []
        
        if diversification < 50:
            recommendations.append('⚠️ 投資組合過度集中，建議增加持股數量以分散風險')
        
        if beta > 1.3:
            recommendations.append('⚡ 投組 Beta 值偏高，市場下跌時可能遭受較大損失')
        
        if volatility > 30:
            recommendations.append('📉 年化波動率超過 30%，屬於高波動組合')
        
        # 檢查單一股票權重
        high_weight_stocks = [s for s in stocks if s['weight'] > 30]
        if high_weight_stocks:
            symbols = ', '.join(s['symbol'] for s in high_weight_stocks)
            recommendations.append(f'🎯 {symbols} 佔比過高（>30%），建議降低單一標的權重')
        
        # 檢查高風險股票
        high_beta_stocks = [s for s in stocks if s['beta'] > 1.5]
        if high_beta_stocks:
            symbols = ', '.join(s['symbol'] for s in high_beta_stocks)
            recommendations.append(f'🔥 {symbols} 為高 Beta 股票，波動較大')
        
        if not recommendations:
            recommendations.append('✅ 投資組合風險控制良好')
        
        return recommendations


# 測試用
if __name__ == '__main__':
    service = RiskAnalysisService()
    
    print("=== NVDA 風險分析 ===")
    vol = service.calculate_volatility('NVDA')
    print(f"年化波動率: {vol['annual_volatility']}%")
    print(f"最大回撤: {vol['max_drawdown']}%")
    
    beta = service.calculate_beta('NVDA')
    print(f"Beta: {beta['beta']} ({beta['interpretation']})")
    
    sharpe = service.calculate_sharpe_ratio('NVDA')
    print(f"夏普比率: {sharpe['sharpe_ratio']} ({sharpe['interpretation']})")
