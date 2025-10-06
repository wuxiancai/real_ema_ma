#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web监控界面
提供交易系统的Web监控功能
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, render_template, jsonify, request
import pandas as pd

from config import config
from binance_futures_client import BinanceFuturesClient
from trade_recorder import TradeRecorder
from real_trading_executor import RealTradingExecutor
from position_manager import PositionManager


class WebMonitor:
    """Web监控类"""
    
    def __init__(self):
        """初始化Web监控"""
        self.app = Flask(__name__)
        self.logger = logging.getLogger('WebMonitor')
        
        # 初始化组件
        self.client = BinanceFuturesClient()
        self.trade_recorder = TradeRecorder()
        self.executor = RealTradingExecutor()
        self.position_manager = PositionManager(self.client)
        
        # 系统启动时间
        self.system_start_time = datetime.now()
        
        # 设置路由
        self._setup_routes()
    
    def _setup_routes(self):
        """设置Flask路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            return render_template('index.html')
        
        @self.app.route('/api/config')
        def get_config():
            """获取系统配置参数"""
            try:
                config_data = {
                    'trading_config': {
                        'symbol': config.SYMBOL,
                        'position_size': config.POSITION_SIZE_PERCENT,
                        'leverage': config.LEVERAGE,
                        'commission_rate': config.COMMISSION_RATE,
                        'timeframe': config.TIMEFRAME
                    },
                    'indicator_config': {
                        'ema_period': config.EMA_PERIOD,
                        'ma_period': config.MA_PERIOD
                    },
                    'system_config': {
                        'test_mode': config.TEST_MODE,
                        'paper_trading': config.PAPER_TRADING,
                        'check_interval': config.CHECK_INTERVAL
                    }
                }
                return jsonify({'success': True, 'data': config_data})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/trades')
        def get_trades():
            """获取交易记录"""
            try:
                limit = request.args.get('limit', 50, type=int)
                trades = self.trade_recorder.get_recent_trades(limit)
                return jsonify({'success': True, 'data': trades})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/positions')
        def get_positions():
            """获取持仓信息"""
            try:
                positions = self.executor.get_current_positions()
                return jsonify({'success': True, 'data': positions})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/fund_flows')
        def get_fund_flows():
            """获取资金流水"""
            try:
                limit = request.args.get('limit', 50, type=int)
                fund_flows = self.trade_recorder.get_recent_fund_flows(limit)
                return jsonify({'success': True, 'data': fund_flows})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/statistics')
        def get_statistics():
            """获取统计信息"""
            try:
                stats = self._calculate_statistics()
                return jsonify({'success': True, 'data': stats})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/balance')
        def get_balance():
            """获取账户余额"""
            try:
                balance = self.executor.get_account_balance()
                return jsonify({'success': True, 'data': balance})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/account_info')
        def get_account_info():
            """获取完整账户信息"""
            try:
                account_info = self.client.get_account_info()
                return jsonify({'success': True, 'data': account_info})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/order_history')
        def get_order_history():
            """获取订单历史"""
            try:
                symbol = request.args.get('symbol', config.SYMBOL)
                limit = request.args.get('limit', 100, type=int)
                orders = self.client.get_order_history(symbol, limit)
                return jsonify({'success': True, 'data': orders})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/trade_history')
        def get_trade_history():
            """获取交易历史"""
            try:
                symbol = request.args.get('symbol', config.SYMBOL)
                limit = request.args.get('limit', 100, type=int)
                trades = self.client.get_trade_history(symbol, limit)
                return jsonify({'success': True, 'data': trades})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/current_price')
        def get_current_price():
            """获取当前价格"""
            try:
                symbol = request.args.get('symbol', config.SYMBOL)
                price = self.client.get_current_price(symbol)
                return jsonify({'success': True, 'data': {'symbol': symbol, 'price': price}})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/klines')
        def get_klines():
            """获取K线数据"""
            try:
                symbol = request.args.get('symbol', config.SYMBOL)
                interval = request.args.get('interval', config.TIMEFRAME)
                limit = request.args.get('limit', 100, type=int)
                klines = self.client.get_klines(symbol, interval, limit)
                
                # 确保数据按时间排序，最新的在最后
                klines = klines.sort_values('timestamp')
                
                # 转换DataFrame为字典列表
                klines_data = klines.to_dict('records')
                # 转换时间戳为字符串
                for item in klines_data:
                    item['timestamp'] = item['timestamp'].isoformat()
                return jsonify({'success': True, 'data': klines_data})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/test_connectivity')
        def test_connectivity():
            """测试API连接"""
            try:
                is_connected = self.client.test_connectivity()
                return jsonify({'success': True, 'data': {'connected': is_connected}})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """计算统计信息"""
        try:
            # 获取交易统计
            executor_stats = self.executor.get_statistics()
            
            # 计算收益相关数据
            total_pnl = 0.0
            total_commission = 0.0
            total_trades = 0
            winning_trades = 0
            
            # 从数据库获取交易记录
            conn = sqlite3.connect(config.DATABASE_PATH)
            cursor = conn.cursor()
            
            # 获取所有已完成的交易
            cursor.execute('''
                SELECT pnl, commission FROM trades 
                WHERE action = 'CLOSE' AND pnl IS NOT NULL
            ''')
            
            closed_trades = cursor.fetchall()
            for pnl, commission in closed_trades:
                if pnl is not None:
                    total_pnl += pnl
                    total_commission += commission or 0
                    total_trades += 1
                    if pnl > 0:
                        winning_trades += 1
            
            # 计算净收益（扣除手续费）
            net_pnl = total_pnl - total_commission
            
            # 计算胜率
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # 计算收益率（基于初始资金）
            initial_balance = 1000.0  # 假设初始资金，实际应从配置或数据库获取
            roi_percentage = (net_pnl / initial_balance * 100) if initial_balance > 0 else 0
            
            # 计算运行时间
            runtime = datetime.now() - self.system_start_time
            runtime_hours = runtime.total_seconds() / 3600
            
            conn.close()
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 4),
                'total_commission': round(total_commission, 4),
                'net_pnl': round(net_pnl, 4),
                'roi_percentage': round(roi_percentage, 2),
                'current_positions': len(self.executor.local_positions),
                'runtime_hours': round(runtime_hours, 2),
                'system_start_time': self.system_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'test_mode': config.TEST_MODE
            }
            
        except Exception as e:
            self.logger.error(f"计算统计信息失败: {e}")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_commission': 0,
                'net_pnl': 0,
                'roi_percentage': 0,
                'current_positions': 0,
                'runtime_hours': 0,
                'system_start_time': self.system_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'test_mode': config.TEST_MODE
            }
    
    def run(self, host='127.0.0.1', port=8888, debug=False):
        """运行Web服务器"""
        print(f"Web监控界面启动: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def main():
    """主函数"""
    monitor = WebMonitor()
    monitor.run(host='0.0.0.0', port=8888, debug=True)


if __name__ == "__main__":
    main()