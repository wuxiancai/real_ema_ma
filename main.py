#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实交易系统主程序
基于EMA-MA交叉策略的自动化交易系统
"""

import time
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from config import config
from binance_futures_client import BinanceFuturesClient
from real_trading_executor import RealTradingExecutor
from position_manager import PositionManager
from trade_recorder import TradeRecorder
from indicators import TechnicalIndicators


class RealTradingSystem:
    """真实交易系统主类"""
    
    def __init__(self):
        """初始化交易系统"""
        self.logger = self._setup_logger()
        self.running = False
        
        # 初始化各个组件
        self.client = BinanceFuturesClient()
        self.executor = RealTradingExecutor()
        self.position_manager = PositionManager(self.client)
        self.trade_recorder = TradeRecorder()
        
        # 交易参数
        self.symbol = config.SYMBOL
        self.timeframe = config.TIMEFRAME
        self.ema_period = config.EMA_PERIOD
        self.ma_period = config.MA_PERIOD
        self.check_interval = config.CHECK_INTERVAL
        
        # 系统状态
        self.last_check_time = datetime.now()
        self.last_data_update = datetime.now()
        self.system_start_time = datetime.now()
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("真实交易系统初始化完成")
    
    def _setup_logger(self) -> logging.Logger:
        """
        设置日志记录器
        
        Returns:
            日志记录器
        """
        logger = logging.getLogger('RealTradingSystem')
        logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # 创建文件处理器
        handler = logging.FileHandler('real_trading_system.log', encoding='utf-8')
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
    
    def _signal_handler(self, signum, frame):
        """
        信号处理器
        
        Args:
            signum: 信号编号
            frame: 当前栈帧
        """
        self.logger.info(f"收到信号 {signum}，正在安全关闭系统...")
        self.stop()
    
    def initialize(self) -> bool:
        """
        初始化系统
        
        Returns:
            初始化是否成功
        """
        try:
            self.logger.info("开始初始化交易系统...")
            
            # 初始化交易执行器
            if not self.executor.initialize_trading():
                self.logger.error("交易执行器初始化失败")
                return False
            
            # 同步持仓
            self.position_manager.sync_positions_from_api()
            
            # 同步历史交易（可选）
            if not config.TEST_MODE:
                self.trade_recorder.sync_trades_from_api(days=1)
            
            self.logger.info("交易系统初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"系统初始化失败: {e}")
            return False
    
    def get_market_data(self, limit: int = 100) -> pd.DataFrame:
        """
        获取市场数据
        
        Args:
            limit: 数据条数
            
        Returns:
            市场数据DataFrame
        """
        try:
            klines = self.client.get_klines(self.symbol, self.timeframe, limit=limit)
            
            # 检查是否为DataFrame且不为空
            if isinstance(klines, pd.DataFrame):
                if klines.empty:
                    self.logger.error("获取市场数据失败：数据为空")
                    return pd.DataFrame()
                
                # 确保数据按时间排序，最新的在最后
                klines = klines.sort_values('timestamp')
                return klines
            
            # 如果返回的是列表格式，转换为DataFrame
            if not klines or len(klines) == 0:
                self.logger.error("获取市场数据失败：无数据")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignore'
            ])
            
            # 数据类型转换
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            # 转换时间戳
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # 确保数据按时间排序，最新的在最后
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取市场数据失败: {e}")
            return pd.DataFrame()
    
    def is_kline_closed(self, df: pd.DataFrame) -> bool:
        """
        检查最新K线是否已收盘
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            True如果K线已收盘，False如果仍在进行中
        """
        if df.empty:
            return False
        
        try:
            # 获取最新K线的时间戳
            latest_timestamp = df.index[-1]
            
            # 确保时间戳是datetime对象
            if not isinstance(latest_timestamp, pd.Timestamp):
                latest_timestamp = pd.to_datetime(latest_timestamp)
            
            current_time = datetime.now()
            
            # 计算15分钟K线的收盘时间
            # 15分钟K线在每个15分钟整点收盘（如：15:00, 15:15, 15:30, 15:45）
            minutes = latest_timestamp.minute
            expected_close_minute = ((minutes // 15) + 1) * 15
            
            if expected_close_minute >= 60:
                expected_close_time = latest_timestamp.replace(
                    hour=latest_timestamp.hour + 1, 
                    minute=expected_close_minute - 60, 
                    second=0, 
                    microsecond=0
                )
            else:
                expected_close_time = latest_timestamp.replace(
                    minute=expected_close_minute, 
                    second=0, 
                    microsecond=0
                )
            
            # 如果当前时间已经超过预期收盘时间，说明K线已收盘
            return current_time >= expected_close_time
            
        except Exception as e:
            self.logger.error(f"检查K线收盘状态失败: {e}")
            return False
    
    def analyze_market(self, df: pd.DataFrame) -> Dict:
        """
        分析市场数据
        
        Args:
            df: 市场数据
            
        Returns:
            分析结果
        """
        try:
            # 检查K线是否已收盘，只有收盘后才进行分析
            if not self.is_kline_closed(df):
                self.logger.debug("当前K线尚未收盘，跳过分析")
                return {}
            
            # 计算技术指标
            df_with_indicators = TechnicalIndicators.calculate_indicators(
                df, self.ema_period, self.ma_period
            )
            
            # 获取最新信号
            latest_signals = TechnicalIndicators.get_latest_signals(df_with_indicators)
            
            # 获取市场状态
            market_condition = TechnicalIndicators.get_market_condition(df_with_indicators)
            
            # 计算支撑阻力位
            support_resistance = TechnicalIndicators.calculate_support_resistance(df)
            
            # 计算波动率
            volatility = TechnicalIndicators.calculate_volatility(df)
            
            return {
                'signals': latest_signals,
                'market_condition': market_condition,
                'support_resistance': support_resistance,
                'volatility': volatility,
                'data_length': len(df_with_indicators),
                'kline_closed': True  # 标记K线已收盘
            }
            
        except Exception as e:
            self.logger.error(f"市场分析失败: {e}")
            return {}
    
    def execute_trading_logic(self, analysis: Dict):
        """
        执行交易逻辑
        
        Args:
            analysis: 市场分析结果
        """
        try:
            signals = analysis.get('signals', {})
            
            current_price = signals.get('close', 0)
            current_time = datetime.now()
            
            # 获取当前持仓
            current_positions = self.position_manager.get_current_positions()
            
            # 根据技术指标生成交易信号
            action = None
            
            # 使用完整的入场条件检查
            # 检查做多条件
            if TechnicalIndicators.check_entry_conditions(signals, 'LONG'):
                # 先平空仓，再开多仓
                if any(pos.side == 'SHORT' for pos in self.executor.local_positions):
                    action = 'CLOSE_SHORT_OPEN_LONG'
                else:
                    action = 'BUY'
                self.logger.info(f"满足做多条件 - EMA金叉MA: EMA={signals.get('ema', 0):.2f}, MA={signals.get('ma', 0):.2f}, "
                               f"价格={current_price:.2f}, EMA斜率={signals.get('ema_slope', 0):.4f}")
            
            # 检查做空条件
            elif TechnicalIndicators.check_entry_conditions(signals, 'SHORT'):
                # 先平多仓，再开空仓
                if any(pos.side == 'LONG' for pos in self.executor.local_positions):
                    action = 'CLOSE_LONG_OPEN_SHORT'
                else:
                    action = 'SELL'
                self.logger.info(f"满足做空条件 - EMA死叉MA: EMA={signals.get('ema', 0):.2f}, MA={signals.get('ma', 0):.2f}, "
                               f"价格={current_price:.2f}, EMA斜率={signals.get('ema_slope', 0):.4f}")
            
            # 记录当前信号状态（用于调试）
            if signals.get('golden_cross', False) or signals.get('death_cross', False):
                self.logger.info(f"信号状态 - 金叉:{signals.get('golden_cross', False)}, "
                               f"死叉:{signals.get('death_cross', False)}, "
                               f"价格>EMA:{signals.get('price_above_ema', False)}, "
                               f"价格>MA:{signals.get('price_above_ma', False)}, "
                               f"EMA>MA:{signals.get('ema_above_ma', False)}, "
                               f"EMA斜率:{signals.get('ema_slope', 0):.4f}")
            
            # 执行交易信号
            if action == 'BUY':
                # 开多仓
                self._open_long_position(current_price, current_time)
                    
            elif action == 'SELL':
                # 开空仓
                self._open_short_position(current_price, current_time)
            
            elif action == 'CLOSE_SHORT_OPEN_LONG':
                # 先平空仓，再开多仓
                self._close_all_positions(current_price, current_time)
                self._open_long_position(current_price, current_time)
            
            elif action == 'CLOSE_LONG_OPEN_SHORT':
                # 先平多仓，再开空仓
                self._close_all_positions(current_price, current_time)
                self._open_short_position(current_price, current_time)
            
        except Exception as e:
            self.logger.error(f"执行交易逻辑失败: {e}")
    
    def _open_long_position(self, current_price: float, current_time: datetime):
        """开多仓"""
        try:
            # 检查是否可以开仓
            account_info = self.client.get_account_info()
            account_balance = float(account_info.get('totalWalletBalance', 0))
            
            if self.position_manager.can_open_new_position(account_balance):
                # 计算仓位大小
                position_size = account_balance * config.POSITION_SIZE_PERCENT
                
                # 开多仓
                result = self.executor.open_position(
                    'LONG', 
                    current_price, 
                    current_time
                )
                
                if result:
                    self.logger.info(f"开多仓成功: 价格={current_price}, 仓位={position_size}")
                    
                    # 记录交易
                    self.trade_recorder.record_trade({
                        'action': 'OPEN',
                        'side': 'LONG',
                        'symbol': self.symbol,
                        'price': current_price,
                        'quantity': position_size / current_price,
                        'amount': position_size,
                        'timestamp': current_time.isoformat(),
                        'commission': position_size * config.COMMISSION_RATE
                    })
            else:
                self.logger.warning("无法开多仓：不满足开仓条件")
        except Exception as e:
            self.logger.error(f"开多仓失败: {e}")
    
    def _open_short_position(self, current_price: float, current_time: datetime):
        """开空仓"""
        try:
            # 检查是否可以开仓
            account_info = self.client.get_account_info()
            account_balance = float(account_info.get('totalWalletBalance', 0))
            
            if self.position_manager.can_open_new_position(account_balance):
                # 计算仓位大小
                position_size = account_balance * config.POSITION_SIZE_PERCENT
                
                # 开空仓
                result = self.executor.open_position(
                    'SHORT', 
                    current_price, 
                    current_time
                )
                
                if result:
                    self.logger.info(f"开空仓成功: 价格={current_price}, 仓位={position_size}")
                    
                    # 记录交易
                    self.trade_recorder.record_trade({
                        'action': 'OPEN',
                        'side': 'SHORT',
                        'symbol': self.symbol,
                        'price': current_price,
                        'quantity': position_size / current_price,
                        'amount': position_size,
                        'timestamp': current_time.isoformat(),
                        'commission': position_size * config.COMMISSION_RATE
                    })
            else:
                self.logger.warning("无法开空仓：不满足开仓条件")
        except Exception as e:
            self.logger.error(f"开空仓失败: {e}")
    
    def _close_all_positions(self, current_price: float, current_time: datetime):
        """平掉所有仓位"""
        try:
            # 平掉所有仓位
            for i in range(len(self.executor.local_positions)):
                pnl = self.executor.close_position(i, current_price, current_time)
                
                # 记录资金流水
                self.trade_recorder.record_transaction({
                    'type': 'CLOSE_POSITION',
                    'symbol': self.symbol,
                    'price': current_price,
                    'pnl': pnl,
                    'timestamp': current_time.isoformat(),
                    'commission': abs(pnl) * config.COMMISSION_RATE if pnl else 0
                })
                
                self.logger.info(f"平仓完成: 价格={current_price}, 盈亏={pnl:.2f}")
        except Exception as e:
            self.logger.error(f"平仓失败: {e}")
    
    def save_snapshots(self):
        """保存快照数据"""
        try:
            # 保存持仓快照
            positions = self.position_manager.get_current_positions()
            if positions:
                self.trade_recorder.save_position_snapshot(positions)
            
            # 保存余额快照
            balance = self.executor.get_account_balance()
            if balance:
                self.trade_recorder.save_balance_snapshot(balance)
            
        except Exception as e:
            self.logger.error(f"保存快照失败: {e}")
    
    def print_status(self):
        """打印系统状态"""
        try:
            # 获取统计信息
            stats = self.executor.get_statistics()
            position_summary = self.position_manager.get_position_summary()
            basic_metrics = self.position_manager.get_basic_metrics()
            
            self.logger.info("=" * 60)
            self.logger.info("系统状态报告")
            self.logger.info("=" * 60)
            self.logger.info(f"运行时间: {datetime.now() - self.system_start_time}")
            self.logger.info(f"测试模式: {config.TEST_MODE}")
            self.logger.info(f"交易对: {self.symbol}")
            self.logger.info(f"当前持仓: {position_summary['total_positions']}")
            self.logger.info(f"总交易次数: {stats['total_trades']}")
            self.logger.info(f"胜率: {stats['win_rate']:.1f}%")
            self.logger.info(f"总手续费: {stats['total_commission']:.4f} USDT")
            self.logger.info(f"每日盈亏: {stats['daily_pnl']:.2f} USDT")
            self.logger.info(f"持仓集中度: {basic_metrics['position_concentration']:.2f}")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"打印状态失败: {e}")
    
    def run(self):
        """运行交易系统"""
        if not self.initialize():
            self.logger.error("系统初始化失败，退出")
            return
        
        self.running = True
        self.logger.info("交易系统开始运行...")
        
        last_status_time = datetime.now()
        last_snapshot_time = datetime.now()
        
        try:
            while self.running:
                current_time = datetime.now()
                
                # 获取市场数据
                market_data = self.get_market_data()
                if market_data.empty:
                    self.logger.warning("无法获取市场数据，等待下次检查")
                    time.sleep(self.check_interval)
                    continue
                
                # 分析市场（只在K线收盘后进行）
                analysis = self.analyze_market(market_data)
                if analysis and analysis.get('kline_closed', False):
                    # 执行交易逻辑
                    self.execute_trading_logic(analysis)
                else:
                    self.logger.debug("K线尚未收盘，等待收盘后进行交易分析")
                
                # 定期保存快照（每5分钟）
                if current_time - last_snapshot_time > timedelta(minutes=5):
                    self.save_snapshots()
                    self.trade_recorder.update_daily_stats()
                    last_snapshot_time = current_time
                
                # 定期打印状态（每30分钟）
                if current_time - last_status_time > timedelta(minutes=30):
                    self.print_status()
                    last_status_time = current_time
                
                # 等待下次检查
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在停止...")
        except Exception as e:
            self.logger.error(f"系统运行异常: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止交易系统"""
        self.running = False
        
        try:
            # 保存最终状态
            self.save_snapshots()
            self.trade_recorder.update_daily_stats()
            
            # 保存交易日志
            self.executor.save_trading_log()
            
            # 打印最终统计
            self.print_status()
            
            self.logger.info("交易系统已安全停止")
            
        except Exception as e:
            self.logger.error(f"停止系统时发生错误: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("真实交易系统 - EMA/MA交叉策略")
    print("=" * 60)
    print(f"交易对: {config.SYMBOL}")
    print(f"时间框架: {config.TIMEFRAME}")
    print(f"EMA周期: {config.EMA_PERIOD}")
    print(f"MA周期: {config.MA_PERIOD}")
    print(f"仓位大小: {config.POSITION_SIZE_PERCENT * 100}% 余额")
    print(f"杠杆倍数: {config.LEVERAGE}x")
    print(f"测试模式: {config.TEST_MODE}")
    print("=" * 60)
    
    # 确认启动
    if not config.TEST_MODE:
        confirm = input("这是真实交易模式，确认启动？(yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消启动")
            return
    
    # 创建并运行交易系统
    trading_system = RealTradingSystem()
    trading_system.run()


if __name__ == "__main__":
    main()