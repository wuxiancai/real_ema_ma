#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓管理模块
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from binance_futures_client import BinanceFuturesClient
from config import config


class PositionManager:
    """持仓管理器"""
    
    def __init__(self, client: BinanceFuturesClient):
        """
        初始化持仓管理器
        
        Args:
            client: Binance客户端
        """
        self.client = client
        self.logger = logging.getLogger('PositionManager')
        
        # 持仓跟踪
        self.positions: List[Dict] = []
        self.position_history: List[Dict] = []
        
        # 同步间隔
        self.last_sync_time = datetime.now()
        self.sync_interval = timedelta(minutes=1)
    
    def sync_positions_from_api(self) -> bool:
        """
        从API同步持仓信息
        
        Returns:
            同步是否成功
        """
        try:
            if config.TEST_MODE:
                return True
            
            api_positions = self.client.get_positions()
            self.positions = []
            
            for pos in api_positions:
                if pos['symbol'] == config.SYMBOL and float(pos['size']) > 0:
                    position_info = {
                        'symbol': pos['symbol'],
                        'side': pos['side'],
                        'size': float(pos['size']),
                        'entry_price': float(pos['entry_price']),
                        'mark_price': float(pos['mark_price']),
                        'pnl': float(pos['pnl']),
                        'percentage': float(pos['percentage']),
                        'margin': float(pos['margin']),
                        'leverage': int(pos['leverage']),
                        'last_update': datetime.now()
                    }
                    self.positions.append(position_info)
            
            self.last_sync_time = datetime.now()
            self.logger.info(f"持仓同步完成，当前持仓数量: {len(self.positions)}")
            return True
            
        except Exception as e:
            self.logger.error(f"持仓同步失败: {e}")
            return False
    
    def should_sync_positions(self) -> bool:
        """
        是否应该同步持仓
        
        Returns:
            是否需要同步
        """
        return datetime.now() - self.last_sync_time > self.sync_interval
    
    def get_current_positions(self) -> List[Dict]:
        """
        获取当前持仓
        
        Returns:
            持仓列表
        """
        if self.should_sync_positions():
            self.sync_positions_from_api()
        
        return self.positions.copy()
    
    def get_position_count(self) -> int:
        """
        获取持仓数量
        
        Returns:
            持仓数量
        """
        return len(self.get_current_positions())
    
    def get_total_margin(self) -> float:
        """
        获取总保证金
        
        Returns:
            总保证金
        """
        positions = self.get_current_positions()
        return sum(pos['margin'] for pos in positions)
    
    def get_total_pnl(self) -> float:
        """
        获取总未实现盈亏
        
        Returns:
            总未实现盈亏
        """
        positions = self.get_current_positions()
        return sum(pos['pnl'] for pos in positions)
    
    def can_open_new_position(self, account_balance: float) -> bool:
        """
        检查是否可以开新仓位
        
        Args:
            account_balance: 账户余额
            
        Returns:
            是否可以开仓
        """
        current_positions = self.get_position_count()
        
        # 简单检查账户余额
        required_margin = account_balance * config.POSITION_SIZE_PERCENT / config.LEVERAGE
        if account_balance < required_margin * 2:  # 保留2倍保证金
            self.logger.warning(f"账户余额不足，当前: {account_balance}, 需要: {required_margin * 2}")
            return False
        
        return True
    
    def get_position_summary(self) -> Dict[str, Any]:
        """
        获取持仓摘要
        
        Returns:
            持仓摘要
        """
        positions = self.get_current_positions()
        
        if not positions:
            return {
                'total_positions': 0,
                'total_margin': 0.0,
                'total_pnl': 0.0,
                'long_positions': 0,
                'short_positions': 0,
                'avg_leverage': 0
            }
        
        long_positions = [p for p in positions if p['side'] == 'LONG']
        short_positions = [p for p in positions if p['side'] == 'SHORT']
        
        return {
            'total_positions': len(positions),
            'total_margin': self.get_total_margin(),
            'total_pnl': self.get_total_pnl(),
            'long_positions': len(long_positions),
            'short_positions': len(short_positions),
            'avg_leverage': sum(p['leverage'] for p in positions) / len(positions),
            'positions_detail': positions
        }
    
    def update_position_history(self, action: str, position_data: Dict):
        """
        更新持仓历史
        
        Args:
            action: 操作类型 ('OPEN', 'CLOSE', 'UPDATE')
            position_data: 持仓数据
        """
        history_record = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'position_data': position_data.copy()
        }
        
        self.position_history.append(history_record)
        
        # 保持历史记录在合理范围内
        if len(self.position_history) > 1000:
            self.position_history = self.position_history[-500:]
    
    def get_basic_metrics(self) -> Dict[str, Any]:
        """
        获取基本指标（移除风险控制相关指标）
        
        Returns:
            基本指标
        """
        positions = self.get_current_positions()
        
        # 计算持仓集中度
        total_margin = self.get_total_margin()
        position_concentration = total_margin / (total_margin * config.POSITION_SIZE_PERCENT) if total_margin > 0 else 0
        
        # 计算杠杆使用率
        avg_leverage = sum(p['leverage'] for p in positions) / len(positions) if positions else 0
        leverage_utilization = avg_leverage / config.LEVERAGE if config.LEVERAGE > 0 else 0
        
        return {
            'position_concentration': position_concentration,
            'leverage_utilization': leverage_utilization,
            'total_positions': len(positions),
            'total_margin_used': total_margin,
            'unrealized_pnl': self.get_total_pnl()
        }