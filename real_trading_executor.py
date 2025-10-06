#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实交易执行器
基于模拟交易系统的逻辑实现真实交易
"""

import os
import json
import glob
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from binance_futures_client import BinanceFuturesClient
from config import config


class RealPosition:
    """真实仓位类"""
    
    def __init__(self, symbol: str, side: str, size: float, entry_price: float, 
                 leverage: int, timestamp: datetime, order_id: str = None):
        """
        初始化真实仓位
        
        Args:
            symbol: 交易对
            side: 方向 ('LONG' 或 'SHORT')
            size: 仓位大小
            entry_price: 开仓价格
            leverage: 杠杆倍数
            timestamp: 开仓时间
            order_id: 订单ID
        """
        self.symbol = symbol
        self.side = side
        self.size = size
        self.entry_price = entry_price
        self.leverage = leverage
        self.timestamp = timestamp
        self.order_id = order_id
        self.margin = size / leverage  # 保证金
        
    def calculate_pnl(self, current_price: float) -> float:
        """
        计算未实现盈亏
        
        Args:
            current_price: 当前价格
            
        Returns:
            未实现盈亏
        """
        if self.side == 'LONG':
            return (current_price - self.entry_price) * self.size / self.entry_price * self.leverage
        else:  # SHORT
            return (self.entry_price - current_price) * self.size / self.entry_price * self.leverage
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'size': self.size,
            'entry_price': self.entry_price,
            'leverage': self.leverage,
            'timestamp': self.timestamp.isoformat(),
            'margin': self.margin,
            'order_id': self.order_id
        }


class RealTradingExecutor:
    """真实交易执行器类"""
    
    def __init__(self):
        """初始化真实交易执行器"""
        self.client = BinanceFuturesClient()
        self.logger = self._setup_logger()
        
        # 交易参数
        self.symbol = config.SYMBOL
        self.position_size_percent = config.POSITION_SIZE_PERCENT  # 改为百分比
        self.leverage = config.LEVERAGE
        self.commission_rate = config.COMMISSION_RATE
        
        # 交易统计
        self.total_commission = 0.0
        self.total_trade_volume = 0.0
        self.daily_pnl = 0.0
        self.trade_history: List[Dict] = []
        
        # 本地仓位跟踪（与API同步）
        self.local_positions: List[RealPosition] = []
        
        # 测试模式
        self.test_mode = config.TEST_MODE
        self.paper_trading = config.PAPER_TRADING
        
        self.logger.info(f"真实交易执行器初始化完成，测试模式: {self.test_mode}")
    
    def _setup_logger(self) -> logging.Logger:
        """
        设置日志记录器
        
        Returns:
            日志记录器
        """
        logger = logging.getLogger('RealTradingExecutor')
        logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # 创建文件处理器
        handler = logging.FileHandler('real_trading.log', encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def initialize_trading(self) -> bool:
        """
        初始化交易环境
        
        Returns:
            初始化是否成功
        """
        try:
            # 测试API连接
            if not self.client.test_connectivity():
                self.logger.error("API连接测试失败")
                return False
            
            # 设置杠杆倍数
            if not self.test_mode:
                try:
                    self.client.set_leverage(self.symbol, self.leverage)
                    self.logger.info(f"杠杆设置成功: {self.leverage}x")
                except Exception as e:
                    self.logger.warning(f"杠杆设置失败（可能已设置）: {e}")
            
            # 同步现有持仓
            self.sync_positions()
            
            # 获取账户信息
            balance_info = self.get_account_balance()
            self.logger.info(f"账户余额: {balance_info}")
            
            self.logger.info("交易环境初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"交易环境初始化失败: {e}")
            return False
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        获取账户余额
        
        Returns:
            余额信息
        """
        if self.test_mode:
            return {'USDT': {'balance': 1000.0, 'available': 1000.0, 'margin': 0.0}}
        
        return self.client.get_balance()
    
    def sync_positions(self):
        """同步API持仓到本地"""
        if self.test_mode:
            return
        
        try:
            api_positions = self.client.get_positions()
            self.local_positions = []
            
            for pos in api_positions:
                if pos['symbol'] == self.symbol:
                    real_pos = RealPosition(
                        symbol=pos['symbol'],
                        side=pos['side'],
                        size=pos['size'],
                        entry_price=pos['entry_price'],
                        leverage=pos['leverage'],
                        timestamp=datetime.now()
                    )
                    self.local_positions.append(real_pos)
            
            self.logger.info(f"同步持仓完成，当前持仓数量: {len(self.local_positions)}")
            
        except Exception as e:
            self.logger.error(f"同步持仓失败: {e}")
    
    def can_open_position(self) -> bool:
        """
        检查是否可以开新仓位
        
        Returns:
            是否可以开仓
        """
        # 检查账户余额
        balance_info = self.get_account_balance()
        usdt_balance = balance_info.get('USDT', {})
        available_balance = usdt_balance.get('available', 0)
        
        if available_balance < 10:  # 最小余额要求
            self.logger.warning(f"账户余额不足: {available_balance} USDT")
            return False
        
        return True
    
    def open_position(self, side: str, price: float, timestamp: datetime) -> bool:
        """
        开仓
        
        Args:
            side: 方向 ('LONG' 或 'SHORT')
            price: 开仓价格
            timestamp: 开仓时间
            
        Returns:
            是否成功开仓
        """
        if not self.can_open_position():
            return False
        
        try:
            # 获取当前账户余额
            balance_info = self.get_account_balance()
            usdt_balance = balance_info.get('USDT', {})
            available_balance = usdt_balance.get('balance', 0)
            
            # 根据百分比计算实际开仓金额
            actual_position_size = available_balance * self.position_size_percent
            
            # 计算订单参数
            quantity = actual_position_size / price  # 计算数量
            order_side = 'BUY' if side == 'LONG' else 'SELL'
            
            # 计算手续费
            actual_trade_amount = actual_position_size * self.leverage
            commission = actual_trade_amount * self.commission_rate
            
            if self.test_mode or self.paper_trading:
                # 模拟交易模式
                order_result = {
                    'orderId': f"TEST_{int(time.time())}",
                    'status': 'FILLED',
                    'executedQty': quantity,
                    'avgPrice': price
                }
                self.logger.info(f"模拟开仓: {side} {quantity:.6f} @ {price:.2f}")
            else:
                # 真实交易模式
                order_result = self.client.place_order(
                    symbol=self.symbol,
                    side=order_side,
                    order_type='MARKET',
                    quantity=quantity
                )
                self.logger.info(f"真实开仓订单已提交: {order_result}")
            
            # 创建本地仓位记录
            position = RealPosition(
                symbol=self.symbol,
                side=side,
                size=actual_position_size,
                entry_price=price,
                leverage=self.leverage,
                timestamp=timestamp,
                order_id=str(order_result['orderId'])
            )
            
            self.local_positions.append(position)
            
            # 更新统计
            self.total_commission += commission
            self.total_trade_volume += actual_trade_amount
            
            # 记录交易历史
            trade_record = {
                'timestamp': timestamp.isoformat(),
                'action': 'OPEN',
                'side': side,
                'price': price,
                'size': actual_position_size,
                'leverage': self.leverage,
                'commission': commission,
                'order_id': order_result['orderId'],
                'test_mode': self.test_mode
            }
            self.trade_history.append(trade_record)
            
            self.logger.info(f"开仓成功: {side} {actual_position_size} USDT @ {price:.2f}, 手续费: {commission:.4f}")
            return True
            
        except Exception as e:
            self.logger.error(f"开仓失败: {e}")
            return False
    
    def close_position(self, position_index: int, price: float, timestamp: datetime) -> float:
        """
        平仓
        
        Args:
            position_index: 仓位索引
            price: 平仓价格
            timestamp: 平仓时间
            
        Returns:
            实现盈亏（扣除手续费后）
        """
        if position_index >= len(self.local_positions):
            return 0.0
        
        position = self.local_positions[position_index]
        
        try:
            # 计算盈亏
            pnl = position.calculate_pnl(price)
            
            # 计算手续费
            base_trade_amount = position.size * position.leverage
            commission = base_trade_amount * self.commission_rate
            net_pnl = pnl - commission
            
            # 计算订单参数
            quantity = position.size / position.entry_price
            order_side = 'SELL' if position.side == 'LONG' else 'BUY'
            
            if self.test_mode or self.paper_trading:
                # 模拟交易模式
                order_result = {
                    'orderId': f"TEST_CLOSE_{int(time.time())}",
                    'status': 'FILLED',
                    'executedQty': quantity,
                    'avgPrice': price
                }
                self.logger.info(f"模拟平仓: {position.side} {quantity:.6f} @ {price:.2f}")
            else:
                # 真实交易模式
                order_result = self.client.place_order(
                    symbol=self.symbol,
                    side=order_side,
                    order_type='MARKET',
                    quantity=quantity
                )
                self.logger.info(f"真实平仓订单已提交: {order_result}")
            
            # 更新统计
            self.total_commission += commission
            self.daily_pnl += net_pnl
            
            # 累加交易额（平仓）- 包含盈亏的资金流水
            actual_trade_amount_with_pnl = base_trade_amount + pnl
            self.total_trade_volume += actual_trade_amount_with_pnl
            
            # 记录交易历史
            trade_record = {
                'timestamp': timestamp.isoformat(),
                'action': 'CLOSE',
                'side': position.side,
                'price': price,
                'size': position.size,
                'pnl': pnl,
                'commission': commission,
                'net_pnl': net_pnl,
                'entry_price': position.entry_price,
                'hold_time': (timestamp - position.timestamp).total_seconds() / 3600,
                'order_id': order_result['orderId'],
                'test_mode': self.test_mode
            }
            self.trade_history.append(trade_record)
            
            self.logger.info(f"平仓成功: {position.side} @ {price:.2f}, 盈亏: {pnl:.2f}, 净盈亏: {net_pnl:.2f}")
            
            # 移除本地仓位
            self.local_positions.pop(position_index)
            
            return net_pnl
            
        except Exception as e:
            self.logger.error(f"平仓失败: {e}")
            return 0.0
    
    def close_all_positions(self, price: float, timestamp: datetime) -> float:
        """
        平掉所有仓位
        
        Args:
            price: 平仓价格
            timestamp: 平仓时间
            
        Returns:
            总盈亏
        """
        total_pnl = 0.0
        positions_to_close = list(range(len(self.local_positions)))
        
        # 从后往前平仓（避免索引变化）
        for i in sorted(positions_to_close, reverse=True):
            pnl = self.close_position(i, price, timestamp)
            total_pnl += pnl
        
        return total_pnl
    

    
    def get_current_positions(self) -> List[Dict]:
        """
        获取当前持仓信息
        
        Returns:
            持仓信息列表
        """
        return [pos.to_dict() for pos in self.local_positions]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取交易统计
        
        Returns:
            统计信息
        """
        # 计算基本统计
        total_trades = len([t for t in self.trade_history if t['action'] == 'CLOSE'])
        winning_trades = len([t for t in self.trade_history if t['action'] == 'CLOSE' and t['net_pnl'] > 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'total_commission': self.total_commission,
            'total_trade_volume': self.total_trade_volume,
            'daily_pnl': self.daily_pnl,
            'current_positions': len(self.local_positions),
            'test_mode': self.test_mode
        }
    
    def save_trading_log(self, filename: str = None):
        """
        保存交易日志，支持日志轮转和目录管理
        
        Args:
            filename: 文件名
        """
        import json
        import os
        import glob
        
        # 确保日志目录存在
        log_dir = "logs/json_snapshots"
        os.makedirs(log_dir, exist_ok=True)
        
        if filename is None:
            filename = f"real_trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 完整文件路径
        filepath = os.path.join(log_dir, filename)
        
        log_data = {
            'config': config.get_config_dict(),
            'statistics': self.get_statistics(),
            'positions': self.get_current_positions(),
            'trade_history': self.trade_history,
            'timestamp': datetime.now().isoformat()
        }
        
        # 检查是否需要保存（避免重复保存相同内容）
        if self._should_save_log(log_data, log_dir):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"交易日志已保存: {filepath}")
            
            # 执行日志轮转
            self._rotate_logs(log_dir)
        else:
            self.logger.debug("日志内容未变化，跳过保存")
    
    def _should_save_log(self, current_data: dict, log_dir: str) -> bool:
        """
        检查是否需要保存日志（避免重复保存相同内容）
        
        Args:
            current_data: 当前日志数据
            log_dir: 日志目录
            
        Returns:
            是否需要保存
        """
        import json
        import glob
        
        # 获取最新的日志文件
        log_files = glob.glob(os.path.join(log_dir, "real_trading_log_*.json"))
        if not log_files:
            return True
        
        latest_file = max(log_files, key=os.path.getctime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                last_data = json.load(f)
            
            # 比较关键数据是否有变化
            current_key_data = {
                'statistics': current_data['statistics'],
                'positions': current_data['positions'],
                'trade_count': len(current_data['trade_history'])
            }
            
            last_key_data = {
                'statistics': last_data['statistics'],
                'positions': last_data['positions'],
                'trade_count': len(last_data['trade_history'])
            }
            
            return current_key_data != last_key_data
            
        except Exception as e:
            self.logger.warning(f"检查日志变化时出错: {e}")
            return True
    
    def _rotate_logs(self, log_dir: str, max_files: int = 20):
        """
        执行日志轮转，保留最新的指定数量文件
        
        Args:
            log_dir: 日志目录
            max_files: 最大保留文件数
        """
        import glob
        
        log_files = glob.glob(os.path.join(log_dir, "real_trading_log_*.json"))
        
        if len(log_files) > max_files:
            # 按创建时间排序，删除最旧的文件
            log_files.sort(key=os.path.getctime)
            files_to_delete = log_files[:-max_files]
            
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    self.logger.info(f"已删除旧日志文件: {file_path}")
                except Exception as e:
                    self.logger.warning(f"删除日志文件失败 {file_path}: {e}")