"""
定期排程服務
"""
from datetime import datetime
from typing import Dict, List
from config import Config
from services.stock_service import StockService
from services.ai_advisor import AIAdvisor
from models.portfolio import get_db, Portfolio, Watchlist


class SchedulerService:
    """定期排程服務"""
    
    @staticmethod
    def generate_daily_report() -> Dict:
        """
        生成每日市場報告
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'type': 'daily',
            'market_summary': {},
            'watchlist_updates': [],
            'portfolio_summary': {},
        }
        
        # 市場摘要
        report['market_summary'] = StockService.get_market_summary()
        
        # 追蹤清單更新
        db = get_db()
        watchlist = Watchlist(db)
        watched_symbols = [item['symbol'] for item in watchlist.get_all()]
        
        if watched_symbols:
            for symbol in watched_symbols:
                try:
                    info = StockService.get_stock_info(symbol)
                    if 'error' not in info:
                        previous = info.get('previous_close', 0)
                        current = info.get('current_price', 0)
                        if previous > 0:
                            change_pct = ((current - previous) / previous) * 100
                        else:
                            change_pct = 0
                        
                        report['watchlist_updates'].append({
                            'symbol': symbol,
                            'name': info.get('name', symbol),
                            'price': current,
                            'change_pct': round(change_pct, 2),
                        })
                except Exception as e:
                    print(f"Error fetching {symbol}: {e}")
        
        # 投資組合摘要
        portfolio = Portfolio(db)
        holdings = portfolio.get_all_holdings()
        
        total_cost = 0
        total_value = 0
        
        for holding in holdings:
            symbol = holding['symbol']
            shares = holding['shares']
            avg_cost = holding['avg_cost']
            
            try:
                info = StockService.get_stock_info(symbol)
                current_price = info.get('current_price', avg_cost)
                
                cost = shares * avg_cost
                value = shares * current_price
                
                total_cost += cost
                total_value += value
            except:
                total_cost += shares * avg_cost
                total_value += shares * avg_cost
        
        if total_cost > 0:
            total_return_pct = ((total_value - total_cost) / total_cost) * 100
        else:
            total_return_pct = 0
        
        report['portfolio_summary'] = {
            'total_cost': round(total_cost, 2),
            'total_value': round(total_value, 2),
            'total_return': round(total_value - total_cost, 2),
            'total_return_pct': round(total_return_pct, 2),
            'holdings_count': len(holdings),
        }
        
        # 儲存報告
        cursor = db.conn.cursor()
        import json
        cursor.execute('''
            INSERT INTO reports (report_type, content) VALUES (?, ?)
        ''', ('daily', json.dumps(report, ensure_ascii=False)))
        db.conn.commit()
        
        return report
    
    @staticmethod
    def generate_investment_recommendations() -> List[Dict]:
        """
        生成投資建議
        """
        db = get_db()
        
        # 從追蹤清單和持股中取得股票
        watchlist = Watchlist(db)
        portfolio = Portfolio(db)
        
        watched = [item['symbol'] for item in watchlist.get_all()]
        held = [item['symbol'] for item in portfolio.get_all_holdings()]
        
        # 合併並去重
        all_symbols = list(set(watched + held))
        
        # 如果沒有任何股票，使用預設清單
        if not all_symbols:
            all_symbols = Config.DEFAULT_US_STOCKS[:3] + Config.DEFAULT_TW_STOCKS[:2]
        
        recommendations = AIAdvisor.get_portfolio_recommendations(all_symbols)
        return recommendations
    
    @staticmethod
    def check_price_alerts() -> List[Dict]:
        """
        檢查價格警報（未來擴充用）
        """
        # TODO: 實作價格警報功能
        return []


# 測試用
if __name__ == '__main__':
    scheduler = SchedulerService()
    
    print("=== 生成每日報告 ===")
    report = scheduler.generate_daily_report()
    
    print(f"\n市場摘要:")
    for name, data in report['market_summary'].items():
        if 'error' not in data:
            print(f"  {name}: {data['price']} ({data['change_pct']:+.2f}%)")
    
    print(f"\n投資組合摘要:")
    summary = report['portfolio_summary']
    print(f"  總成本: ${summary['total_cost']:,.2f}")
    print(f"  總市值: ${summary['total_value']:,.2f}")
    print(f"  總報酬: ${summary['total_return']:,.2f} ({summary['total_return_pct']:+.2f}%)")
