#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易历史和资金流水记录模块
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from binance_futures_client import BinanceFuturesClient
from config import config


class TradeRecorder:
    """交易记录器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化交易记录器
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path or config.DATABASE_PATH
        self.logger = logging.getLogger('TradeRecorder')
        self.client = BinanceFuturesClient()
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建交易记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        action TEXT NOT NULL,
                        quantity REAL NOT NULL,
                        price REAL NOT NULL,
                        amount REAL NOT NULL,
                        commission REAL NOT NULL,
                        pnl REAL DEFAULT 0,
                        leverage INTEGER NOT NULL,
                        order_id TEXT,
                        trade_id TEXT,
                        is_maker BOOLEAN DEFAULT 0,
                        test_mode BOOLEAN DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建资金流水表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fund_flows (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        type TEXT NOT NULL,
                        asset TEXT NOT NULL,
                        amount REAL NOT NULL,
                        balance REAL NOT NULL,
                        description TEXT,
                        trade_id INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (trade_id) REFERENCES trades (id)
                    )
                ''')
                
                # 创建持仓快照表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS position_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        size REAL NOT NULL,
                        entry_price REAL NOT NULL,
                        mark_price REAL NOT NULL,
                        pnl REAL NOT NULL,
                        margin REAL NOT NULL,
                        leverage INTEGER NOT NULL,
                        percentage REAL NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建账户余额快照表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS balance_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        asset TEXT NOT NULL,
                        balance REAL NOT NULL,
                        available REAL NOT NULL,
                        margin REAL NOT NULL,
                        unrealized_pnl REAL NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建交易统计表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trading_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL UNIQUE,
                        total_trades INTEGER DEFAULT 0,
                        winning_trades INTEGER DEFAULT 0,
                        losing_trades INTEGER DEFAULT 0,
                        total_pnl REAL DEFAULT 0,
                        total_commission REAL DEFAULT 0,
                        total_volume REAL DEFAULT 0,
                        max_drawdown REAL DEFAULT 0,
                        win_rate REAL DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                self.logger.info("数据库初始化完成")
                
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    def record_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        记录交易
        
        Args:
            trade_data: 交易数据
            
        Returns:
            交易记录ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO trades (
                        timestamp, symbol, side, action, quantity, price, amount,
                        commission, pnl, leverage, order_id, trade_id, is_maker, test_mode
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_data.get('timestamp', datetime.now().isoformat()),
                    trade_data.get('symbol', config.SYMBOL),
                    trade_data.get('side'),
                    trade_data.get('action'),
                    trade_data.get('quantity', 0),
                    trade_data.get('price', 0),
                    trade_data.get('amount', 0),
                    trade_data.get('commission', 0),
                    trade_data.get('pnl', 0),
                    trade_data.get('leverage', config.LEVERAGE),
                    trade_data.get('order_id'),
                    trade_data.get('trade_id'),
                    trade_data.get('is_maker', False),
                    trade_data.get('test_mode', config.TEST_MODE)
                ))
                
                trade_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"交易记录已保存: ID={trade_id}, {trade_data.get('action')} {trade_data.get('side')}")
                return trade_id
                
        except Exception as e:
            self.logger.error(f"记录交易失败: {e}")
            return 0
    
    def record_fund_flow(self, flow_data: Dict[str, Any], trade_id: int = None):
        """
        记录资金流水
        
        Args:
            flow_data: 资金流水数据
            trade_id: 关联的交易ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO fund_flows (
                        timestamp, type, asset, amount, balance, description, trade_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    flow_data.get('timestamp', datetime.now().isoformat()),
                    flow_data.get('type'),
                    flow_data.get('asset', 'USDT'),
                    flow_data.get('amount', 0),
                    flow_data.get('balance', 0),
                    flow_data.get('description', ''),
                    trade_id
                ))
                
                conn.commit()
                self.logger.debug(f"资金流水已记录: {flow_data.get('type')} {flow_data.get('amount')}")
                
        except Exception as e:
            self.logger.error(f"记录资金流水失败: {e}")
    
    def save_position_snapshot(self, positions: List[Dict]):
        """
        保存持仓快照
        
        Args:
            positions: 持仓列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                timestamp = datetime.now().isoformat()
                
                for pos in positions:
                    cursor.execute('''
                        INSERT INTO position_snapshots (
                            timestamp, symbol, side, size, entry_price, mark_price,
                            pnl, margin, leverage, percentage
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        timestamp,
                        pos.get('symbol'),
                        pos.get('side'),
                        pos.get('size', 0),
                        pos.get('entry_price', 0),
                        pos.get('mark_price', 0),
                        pos.get('pnl', 0),
                        pos.get('margin', 0),
                        pos.get('leverage', 0),
                        pos.get('percentage', 0)
                    ))
                
                conn.commit()
                self.logger.debug(f"持仓快照已保存: {len(positions)} 个持仓")
                
        except Exception as e:
            self.logger.error(f"保存持仓快照失败: {e}")
    
    def save_balance_snapshot(self, balance_data: Dict):
        """
        保存账户余额快照
        
        Args:
            balance_data: 余额数据
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                timestamp = datetime.now().isoformat()
                
                for asset, data in balance_data.items():
                    cursor.execute('''
                        INSERT INTO balance_snapshots (
                            timestamp, asset, balance, available, margin, unrealized_pnl
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        timestamp,
                        asset,
                        data.get('balance', 0),
                        data.get('available', 0),
                        data.get('margin', 0),
                        data.get('unrealized_pnl', 0)
                    ))
                
                conn.commit()
                self.logger.debug("账户余额快照已保存")
                
        except Exception as e:
            self.logger.error(f"保存余额快照失败: {e}")
    
    def update_daily_stats(self, date: str = None):
        """
        更新每日统计
        
        Args:
            date: 日期 (YYYY-MM-DD)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 计算当日统计
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(pnl) as total_pnl,
                        SUM(commission) as total_commission,
                        SUM(amount) as total_volume
                    FROM trades 
                    WHERE DATE(timestamp) = ? AND action = 'CLOSE'
                ''', (date,))
                
                stats = cursor.fetchone()
                
                if stats and stats[0] > 0:
                    total_trades, winning_trades, losing_trades, total_pnl, total_commission, total_volume = stats
                    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                    
                    # 插入或更新统计
                    cursor.execute('''
                        INSERT OR REPLACE INTO trading_stats (
                            date, total_trades, winning_trades, losing_trades,
                            total_pnl, total_commission, total_volume, win_rate
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        date, total_trades, winning_trades, losing_trades,
                        total_pnl or 0, total_commission or 0, total_volume or 0, win_rate
                    ))
                    
                    conn.commit()
                    self.logger.info(f"每日统计已更新: {date}")
                
        except Exception as e:
            self.logger.error(f"更新每日统计失败: {e}")
    
    def get_trade_history(self, days: int = 30, limit: int = 100) -> List[Dict]:
        """
        获取交易历史
        
        Args:
            days: 查询天数
            limit: 限制数量
            
        Returns:
            交易历史列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor.execute('''
                    SELECT * FROM trades 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (start_date, limit))
                
                columns = [desc[0] for desc in cursor.description]
                trades = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return trades
                
        except Exception as e:
            self.logger.error(f"获取交易历史失败: {e}")
            return []
    
    def get_fund_flows(self, days: int = 30, limit: int = 100) -> List[Dict]:
        """
        获取资金流水
        
        Args:
            days: 查询天数
            limit: 限制数量
            
        Returns:
            资金流水列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor.execute('''
                    SELECT * FROM fund_flows 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (start_date, limit))
                
                columns = [desc[0] for desc in cursor.description]
                flows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return flows
                
        except Exception as e:
            self.logger.error(f"获取资金流水失败: {e}")
            return []

    def get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """
        获取最近的交易记录
        
        Args:
            limit: 限制数量
            
        Returns:
            交易记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM trades 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                trades = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return trades
                
        except Exception as e:
            self.logger.error(f"获取最近交易记录失败: {e}")
            return []

    def get_recent_fund_flows(self, limit: int = 50) -> List[Dict]:
        """
        获取最近的资金流水
        
        Args:
            limit: 限制数量
            
        Returns:
            资金流水列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM fund_flows 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                flows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return flows
                
        except Exception as e:
            self.logger.error(f"获取最近资金流水失败: {e}")
            return []
    
    def get_trading_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        获取交易统计
        
        Args:
            days: 查询天数
            
        Returns:
            交易统计
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
                cursor.execute('''
                    SELECT 
                        SUM(total_trades) as total_trades,
                        SUM(winning_trades) as winning_trades,
                        SUM(losing_trades) as losing_trades,
                        SUM(total_pnl) as total_pnl,
                        SUM(total_commission) as total_commission,
                        SUM(total_volume) as total_volume,
                        AVG(win_rate) as avg_win_rate
                    FROM trading_stats 
                    WHERE date >= ?
                ''', (start_date,))
                
                stats = cursor.fetchone()
                
                if stats:
                    return {
                        'total_trades': stats[0] or 0,
                        'winning_trades': stats[1] or 0,
                        'losing_trades': stats[2] or 0,
                        'total_pnl': stats[3] or 0,
                        'total_commission': stats[4] or 0,
                        'total_volume': stats[5] or 0,
                        'avg_win_rate': stats[6] or 0,
                        'period_days': days
                    }
                else:
                    return {
                        'total_trades': 0,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'total_pnl': 0,
                        'total_commission': 0,
                        'total_volume': 0,
                        'avg_win_rate': 0,
                        'period_days': days
                    }
                
        except Exception as e:
            self.logger.error(f"获取交易统计失败: {e}")
            return {}
    
    def sync_trades_from_api(self, days: int = 7) -> int:
        """
        从API同步交易记录
        
        Args:
            days: 同步天数
            
        Returns:
            同步的交易数量
        """
        if config.TEST_MODE:
            return 0
        
        try:
            # 获取API交易历史
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            api_trades = self.client.get_trade_history(config.SYMBOL, start_time=start_time)
            
            synced_count = 0
            
            for trade in api_trades:
                # 检查是否已存在
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT id FROM trades WHERE trade_id = ?', (trade['id'],))
                    
                    if not cursor.fetchone():
                        # 记录新交易
                        trade_data = {
                            'timestamp': datetime.fromtimestamp(trade['time'] / 1000).isoformat(),
                            'symbol': trade['symbol'],
                            'side': trade['side'],
                            'action': 'SYNC',
                            'quantity': float(trade['qty']),
                            'price': float(trade['price']),
                            'amount': float(trade['quoteQty']),
                            'commission': float(trade['commission']),
                            'trade_id': trade['id'],
                            'is_maker': trade['isMaker'],
                            'test_mode': False
                        }
                        
                        self.record_trade(trade_data)
                        synced_count += 1
            
            self.logger.info(f"从API同步了 {synced_count} 条交易记录")
            return synced_count
            
        except Exception as e:
            self.logger.error(f"从API同步交易记录失败: {e}")
            return 0
    
    def export_data(self, filename: str = None, format: str = 'json') -> str:
        """
        导出数据
        
        Args:
            filename: 文件名
            format: 格式 ('json', 'csv')
            
        Returns:
            导出的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"trading_data_export_{timestamp}.{format}"
        
        try:
            # 获取所有数据
            trades = self.get_trade_history(days=365, limit=10000)
            fund_flows = self.get_fund_flows(days=365, limit=10000)
            stats = self.get_trading_stats(days=365)
            
            export_data = {
                'export_time': datetime.now().isoformat(),
                'trades': trades,
                'fund_flows': fund_flows,
                'statistics': stats
            }
            
            if format == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            elif format == 'csv':
                # 导出为多个CSV文件
                base_name = filename.replace('.csv', '')
                
                if trades:
                    trades_df = pd.DataFrame(trades)
                    trades_df.to_csv(f"{base_name}_trades.csv", index=False, encoding='utf-8')
                
                if fund_flows:
                    flows_df = pd.DataFrame(fund_flows)
                    flows_df.to_csv(f"{base_name}_fund_flows.csv", index=False, encoding='utf-8')
            
            self.logger.info(f"数据导出完成: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"数据导出失败: {e}")
            return ""