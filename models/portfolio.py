"""
投資組合資料模型
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from config import Config


class Database:
    """資料庫管理"""
    
    def __init__(self):
        # 確保目錄存在
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
        self.conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        """初始化資料表"""
        cursor = self.conn.cursor()
        
        # 投資組合持股表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                name TEXT,
                shares REAL NOT NULL,
                avg_cost REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 交易記錄表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                type TEXT NOT NULL,  -- BUY, SELL
                shares REAL NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                note TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 追蹤清單表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 報告歷史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def close(self):
        self.conn.close()


class Portfolio:
    """投資組合管理"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def add_holding(self, symbol: str, name: str, shares: float, avg_cost: float, currency: str = 'USD') -> int:
        """新增持股"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO holdings (symbol, name, shares, avg_cost, currency)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol.upper(), name, shares, avg_cost, currency))
        self.db.conn.commit()
        return cursor.lastrowid
    
    def update_holding(self, holding_id: int, shares: float = None, avg_cost: float = None) -> bool:
        """更新持股"""
        cursor = self.db.conn.cursor()
        updates = []
        values = []
        
        if shares is not None:
            updates.append('shares = ?')
            values.append(shares)
        if avg_cost is not None:
            updates.append('avg_cost = ?')
            values.append(avg_cost)
        
        if not updates:
            return False
        
        updates.append('updated_at = ?')
        values.append(datetime.now())
        values.append(holding_id)
        
        cursor.execute(f'''
            UPDATE holdings SET {', '.join(updates)} WHERE id = ?
        ''', values)
        self.db.conn.commit()
        return cursor.rowcount > 0
    
    def delete_holding(self, holding_id: int) -> bool:
        """刪除持股"""
        cursor = self.db.conn.cursor()
        cursor.execute('DELETE FROM holdings WHERE id = ?', (holding_id,))
        self.db.conn.commit()
        return cursor.rowcount > 0
    
    def get_all_holdings(self) -> List[Dict]:
        """取得所有持股"""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM holdings ORDER BY symbol')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_holding_by_symbol(self, symbol: str) -> Optional[Dict]:
        """依股票代碼取得持股"""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM holdings WHERE symbol = ?', (symbol.upper(),))
        row = cursor.fetchone()
        return dict(row) if row else None


class Watchlist:
    """追蹤清單管理"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def add_symbol(self, symbol: str, name: str = None) -> bool:
        """新增追蹤股票"""
        cursor = self.db.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO watchlist (symbol, name) VALUES (?, ?)
            ''', (symbol.upper(), name))
            self.db.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_symbol(self, symbol: str) -> bool:
        """移除追蹤股票"""
        cursor = self.db.conn.cursor()
        cursor.execute('DELETE FROM watchlist WHERE symbol = ?', (symbol.upper(),))
        self.db.conn.commit()
        return cursor.rowcount > 0
    
    def get_all(self) -> List[Dict]:
        """取得所有追蹤股票"""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM watchlist ORDER BY symbol')
        return [dict(row) for row in cursor.fetchall()]


class TransactionLog:
    """交易記錄"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def add_transaction(self, symbol: str, trans_type: str, shares: float, 
                       price: float, currency: str = 'USD', note: str = None) -> int:
        """新增交易記錄"""
        total = shares * price
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (symbol, type, shares, price, total, currency, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (symbol.upper(), trans_type.upper(), shares, price, total, currency, note))
        self.db.conn.commit()
        return cursor.lastrowid
    
    def get_transactions(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """取得交易記錄"""
        cursor = self.db.conn.cursor()
        if symbol:
            cursor.execute('''
                SELECT * FROM transactions WHERE symbol = ? 
                ORDER BY transaction_date DESC LIMIT ?
            ''', (symbol.upper(), limit))
        else:
            cursor.execute('''
                SELECT * FROM transactions ORDER BY transaction_date DESC LIMIT ?
            ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]


# 全域資料庫實例
_db = None

def get_db() -> Database:
    """取得資料庫實例"""
    global _db
    if _db is None:
        _db = Database()
    return _db
