"""
AI 財務助手 - Flask 主應用程式
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_apscheduler import APScheduler
from datetime import datetime
import json

from config import Config
from models.portfolio import get_db, Portfolio, Watchlist, TransactionLog
from services.stock_service import StockService
from services.analysis_service import AnalysisService
from services.ai_advisor import AIAdvisor
from services.scheduler_service import SchedulerService
from services.risk_service import RiskAnalysisService


# 初始化 Flask 應用
app = Flask(__name__)
app.config.from_object(Config)

# 初始化排程器
scheduler = APScheduler()
scheduler.init_app(app)


# ==================== 排程任務 ====================

@scheduler.task('cron', id='daily_report', hour=18, minute=0)
def scheduled_daily_report():
    """每日 18:00 生成報告"""
    with app.app_context():
        print(f"[{datetime.now()}] 執行每日報告...")
        SchedulerService.generate_daily_report()


# ==================== 頁面路由 ====================

@app.route('/')
def index():
    """首頁儀表板"""
    # 市場摘要
    market_summary = StockService.get_market_summary()
    
    # 投資組合
    db = get_db()
    portfolio = Portfolio(db)
    holdings = portfolio.get_all_holdings()
    
    # 計算持股現值
    portfolio_data = []
    total_cost = 0
    total_value = 0
    
    for holding in holdings:
        symbol = holding['symbol']
        shares = holding['shares']
        avg_cost = holding['avg_cost']
        
        try:
            info = StockService.get_stock_info(symbol)
            current_price = info.get('current_price', avg_cost)
        except:
            current_price = avg_cost
        
        cost = shares * avg_cost
        value = shares * current_price
        profit = value - cost
        profit_pct = (profit / cost * 100) if cost > 0 else 0
        
        portfolio_data.append({
            'id': holding['id'],
            'symbol': symbol,
            'name': holding.get('name', symbol),
            'shares': shares,
            'avg_cost': avg_cost,
            'current_price': current_price,
            'cost': cost,
            'value': value,
            'profit': profit,
            'profit_pct': profit_pct,
            'currency': holding.get('currency', 'USD'),
        })
        
        total_cost += cost
        total_value += value
    
    total_profit = total_value - total_cost
    total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
    
    return render_template('index.html',
                         market_summary=market_summary,
                         portfolio=portfolio_data,
                         total_cost=total_cost,
                         total_value=total_value,
                         total_profit=total_profit,
                         total_profit_pct=total_profit_pct,
                         now=datetime.now())


@app.route('/analysis')
def analysis():
    """分析頁面"""
    symbol = request.args.get('symbol', 'AAPL')
    
    # 取得建議
    recommendation = AIAdvisor.get_recommendation(symbol)
    
    # 取得歷史資料用於圖表
    df = StockService.get_historical_data(symbol, period='6mo')
    
    chart_data = []
    if not df.empty:
        for _, row in df.iterrows():
            chart_data.append({
                'date': row['Date'].strftime('%Y-%m-%d') if hasattr(row['Date'], 'strftime') else str(row['Date'])[:10],
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume']),
            })
    
    # 追蹤清單用於選擇
    db = get_db()
    watchlist = Watchlist(db)
    watched = watchlist.get_all()
    
    return render_template('analysis.html',
                         symbol=symbol,
                         recommendation=recommendation,
                         chart_data=json.dumps(chart_data),
                         watchlist=watched,
                         default_stocks=Config.DEFAULT_US_STOCKS + Config.DEFAULT_TW_STOCKS)


@app.route('/portfolio')
def portfolio_page():
    """投資組合管理頁面"""
    db = get_db()
    portfolio = Portfolio(db)
    holdings = portfolio.get_all_holdings()
    
    transactions = TransactionLog(db)
    recent_transactions = transactions.get_transactions(limit=20)
    
    return render_template('portfolio.html',
                         holdings=holdings,
                         transactions=recent_transactions)


@app.route('/risk')
def risk_page():
    """風險分析頁面"""
    db = get_db()
    portfolio = Portfolio(db)
    holdings = portfolio.get_all_holdings()
    
    # 計算投資組合風險
    risk_analysis = RiskAnalysisService.analyze_portfolio_risk(holdings)
    
    return render_template('risk.html',
                         risk_analysis=risk_analysis,
                         holdings=holdings)


# ==================== API 路由 ====================

@app.route('/api/stock/<symbol>')
def api_stock_info(symbol):
    """取得股票資訊 API"""
    info = StockService.get_stock_info(symbol)
    return jsonify(info)


@app.route('/api/analysis/<symbol>')
def api_analysis(symbol):
    """取得技術分析 API"""
    recommendation = AIAdvisor.get_recommendation(symbol)
    return jsonify(recommendation)


@app.route('/api/market')
def api_market():
    """取得市場摘要 API"""
    summary = StockService.get_market_summary()
    return jsonify(summary)


@app.route('/api/portfolio', methods=['GET'])
def api_portfolio_list():
    """取得投資組合 API"""
    db = get_db()
    portfolio = Portfolio(db)
    holdings = portfolio.get_all_holdings()
    return jsonify(holdings)


@app.route('/api/portfolio', methods=['POST'])
def api_portfolio_add():
    """新增持股 API"""
    data = request.json
    db = get_db()
    portfolio = Portfolio(db)
    
    # 取得股票名稱
    info = StockService.get_stock_info(data['symbol'])
    name = info.get('name', data['symbol'])
    
    holding_id = portfolio.add_holding(
        symbol=data['symbol'],
        name=name,
        shares=float(data['shares']),
        avg_cost=float(data['avg_cost']),
        currency=data.get('currency', 'USD')
    )
    
    # 記錄交易
    transactions = TransactionLog(db)
    transactions.add_transaction(
        symbol=data['symbol'],
        trans_type='BUY',
        shares=float(data['shares']),
        price=float(data['avg_cost']),
        currency=data.get('currency', 'USD')
    )
    
    return jsonify({'success': True, 'id': holding_id})


@app.route('/api/portfolio/<int:holding_id>', methods=['DELETE'])
def api_portfolio_delete(holding_id):
    """刪除持股 API"""
    db = get_db()
    portfolio = Portfolio(db)
    success = portfolio.delete_holding(holding_id)
    return jsonify({'success': success})


@app.route('/api/watchlist', methods=['GET'])
def api_watchlist_list():
    """取得追蹤清單 API"""
    db = get_db()
    watchlist = Watchlist(db)
    items = watchlist.get_all()
    return jsonify(items)


@app.route('/api/watchlist', methods=['POST'])
def api_watchlist_add():
    """新增追蹤 API"""
    data = request.json
    db = get_db()
    watchlist = Watchlist(db)
    
    info = StockService.get_stock_info(data['symbol'])
    name = info.get('name', data['symbol'])
    
    success = watchlist.add_symbol(data['symbol'], name)
    return jsonify({'success': success})


@app.route('/api/watchlist/<symbol>', methods=['DELETE'])
def api_watchlist_remove(symbol):
    """移除追蹤 API"""
    db = get_db()
    watchlist = Watchlist(db)
    success = watchlist.remove_symbol(symbol)
    return jsonify({'success': success})


@app.route('/api/report/generate')
def api_generate_report():
    """手動生成報告 API"""
    report = SchedulerService.generate_daily_report()
    return jsonify(report)


@app.route('/api/recommendations')
def api_recommendations():
    """取得所有建議 API"""
    recommendations = SchedulerService.generate_investment_recommendations()
    return jsonify(recommendations)


@app.route('/api/risk')
def api_portfolio_risk():
    """取得投資組合風險分析 API"""
    db = get_db()
    portfolio = Portfolio(db)
    holdings = portfolio.get_all_holdings()
    risk_analysis = RiskAnalysisService.analyze_portfolio_risk(holdings)
    return jsonify(risk_analysis)


@app.route('/api/risk/<symbol>')
def api_stock_risk(symbol):
    """取得單一股票風險分析 API"""
    volatility = RiskAnalysisService.calculate_volatility(symbol)
    beta = RiskAnalysisService.calculate_beta(symbol)
    sharpe = RiskAnalysisService.calculate_sharpe_ratio(symbol)
    return jsonify({
        'symbol': symbol,
        'volatility': volatility,
        'beta': beta,
        'sharpe': sharpe,
    })


# ==================== 啟動應用 ====================

if __name__ == '__main__':
    # 啟動排程器
    scheduler.start()
    
    print("=" * 50)
    print("🤖 AI 財務助手啟動中...")
    print("=" * 50)
    print(f"📊 預設追蹤美股: {Config.DEFAULT_US_STOCKS}")
    print(f"📊 預設追蹤台股: {Config.DEFAULT_TW_STOCKS}")
    print("=" * 50)
    print("🌐 請在瀏覽器開啟: http://localhost:5000")
    print("=" * 50)
    
    # 開發模式運行
    app.run(debug=True, host='0.0.0.0', port=5000)
