#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标计算模块
与模拟系统保持一致的指标计算逻辑
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """
        计算指数移动平均线 (EMA)
        
        Args:
            data: 价格数据序列
            period: 计算周期
            
        Returns:
            EMA序列
        """
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_ma(data: pd.Series, period: int) -> pd.Series:
        """
        计算简单移动平均线 (MA)
        
        Args:
            data: 价格数据序列
            period: 计算周期
            
        Returns:
            MA序列
        """
        return data.rolling(window=period).mean()
    
    @staticmethod
    def detect_crossover(fast_line: pd.Series, slow_line: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """
        检测金叉和死叉
        
        Args:
            fast_line: 快线数据
            slow_line: 慢线数据
            
        Returns:
            (金叉信号, 死叉信号)
        """
        # 计算快线与慢线的差值
        diff = fast_line - slow_line
        prev_diff = diff.shift(1)
        
        # 金叉：快线从下方穿越慢线（差值从负变正）
        golden_cross = (prev_diff <= 0) & (diff > 0)
        
        # 死叉：快线从上方穿越慢线（差值从正变负）
        death_cross = (prev_diff >= 0) & (diff < 0)
        
        return golden_cross, death_cross
    
    @staticmethod
    def calculate_indicators(df: pd.DataFrame, ema_period: int = 20, ma_period: int = 35) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            df: 包含OHLCV数据的DataFrame
            ema_period: EMA周期
            ma_period: MA周期
            
        Returns:
            包含所有指标的DataFrame
        """
        result_df = df.copy()
        
        # 计算EMA和MA
        result_df['ema'] = TechnicalIndicators.calculate_ema(df['close'], ema_period)
        result_df['ma'] = TechnicalIndicators.calculate_ma(df['close'], ma_period)
        
        # 检测交叉信号
        golden_cross, death_cross = TechnicalIndicators.detect_crossover(
            result_df['ema'], result_df['ma']
        )
        
        result_df['golden_cross'] = golden_cross
        result_df['death_cross'] = death_cross
        
        # 计算价格与指标的关系
        result_df['price_above_ema'] = df['close'] > result_df['ema']
        result_df['price_above_ma'] = df['close'] > result_df['ma']
        result_df['ema_above_ma'] = result_df['ema'] > result_df['ma']
        
        # 计算指标斜率（趋势方向）
        result_df['ema_slope'] = result_df['ema'].diff()
        result_df['ma_slope'] = result_df['ma'].diff()
        
        # 计算价格动量
        result_df['price_momentum'] = df['close'].pct_change()
        
        return result_df
    
    @staticmethod
    def get_latest_signals(df: pd.DataFrame) -> Dict[str, any]:
        """
        获取最新的交易信号
        
        Args:
            df: 包含指标的DataFrame
            
        Returns:
            最新信号字典
        """
        if len(df) == 0:
            return {}
        
        latest = df.iloc[-1]
        
        return {
            'timestamp': latest.name if hasattr(latest, 'name') else None,
            'close': latest['close'],
            'ema': latest['ema'],
            'ma': latest['ma'],
            'golden_cross': latest['golden_cross'],
            'death_cross': latest['death_cross'],
            'price_above_ema': latest['price_above_ema'],
            'price_above_ma': latest['price_above_ma'],
            'ema_above_ma': latest['ema_above_ma'],
            'ema_slope': latest['ema_slope'],
            'ma_slope': latest['ma_slope'],
            'price_momentum': latest['price_momentum']
        }
    
    @staticmethod
    def check_entry_conditions(signals: Dict[str, any], side: str) -> bool:
        """
        检查入场条件
        
        Args:
            signals: 信号字典
            side: 交易方向 ('LONG' 或 'SHORT')
            
        Returns:
            是否满足入场条件
        """
        if not signals:
            return False
        
        if side == 'LONG':
            # 做多条件：金叉 + 价格在EMA上方 + EMA在MA上方 + EMA上升趋势
            return (
                signals.get('golden_cross', False) and
                signals.get('price_above_ema', False) and
                signals.get('ema_above_ma', False) and
                signals.get('ema_slope', 0) > 0
            )
        
        elif side == 'SHORT':
            # 做空条件：死叉 + 价格在EMA下方 + EMA在MA下方 + EMA下降趋势
            return (
                signals.get('death_cross', False) and
                not signals.get('price_above_ema', True) and
                not signals.get('ema_above_ma', True) and
                signals.get('ema_slope', 0) < 0
            )
        
        return False
    
    @staticmethod
    def check_exit_conditions(signals: Dict[str, any], position_side: str) -> bool:
        """
        检查出场条件
        
        Args:
            signals: 信号字典
            position_side: 持仓方向 ('LONG' 或 'SHORT')
            
        Returns:
            是否满足出场条件
        """
        if not signals:
            return False
        
        if position_side == 'LONG':
            # 多头出场条件：死叉 或 价格跌破EMA
            return (
                signals.get('death_cross', False) or
                not signals.get('price_above_ema', True)
            )
        
        elif position_side == 'SHORT':
            # 空头出场条件：金叉 或 价格突破EMA
            return (
                signals.get('golden_cross', False) or
                signals.get('price_above_ema', False)
            )
        
        return False
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """
        计算支撑阻力位
        
        Args:
            df: 价格数据
            window: 计算窗口
            
        Returns:
            支撑阻力位字典
        """
        if len(df) < window:
            return {'support': 0, 'resistance': 0}
        
        recent_data = df.tail(window)
        
        support = recent_data['low'].min()
        resistance = recent_data['high'].max()
        
        return {
            'support': support,
            'resistance': resistance,
            'range': resistance - support
        }
    
    @staticmethod
    def calculate_volatility(df: pd.DataFrame, window: int = 20) -> float:
        """
        计算价格波动率
        
        Args:
            df: 价格数据
            window: 计算窗口
            
        Returns:
            波动率
        """
        if len(df) < window:
            return 0.0
        
        returns = df['close'].pct_change().dropna()
        volatility = returns.tail(window).std() * np.sqrt(24)  # 日化波动率
        
        return volatility
    
    @staticmethod
    def get_market_condition(df: pd.DataFrame) -> str:
        """
        判断市场状态
        
        Args:
            df: 包含指标的DataFrame
            
        Returns:
            市场状态 ('BULLISH', 'BEARISH', 'SIDEWAYS')
        """
        if len(df) < 10:
            return 'UNKNOWN'
        
        recent_data = df.tail(10)
        
        # 计算EMA和MA的平均斜率
        ema_trend = recent_data['ema_slope'].mean()
        ma_trend = recent_data['ma_slope'].mean()
        
        # 计算价格相对于指标的位置
        price_above_ema_ratio = recent_data['price_above_ema'].sum() / len(recent_data)
        ema_above_ma_ratio = recent_data['ema_above_ma'].sum() / len(recent_data)
        
        # 判断市场状态
        if ema_trend > 0 and ma_trend > 0 and price_above_ema_ratio > 0.6 and ema_above_ma_ratio > 0.6:
            return 'BULLISH'
        elif ema_trend < 0 and ma_trend < 0 and price_above_ema_ratio < 0.4 and ema_above_ma_ratio < 0.4:
            return 'BEARISH'
        else:
            return 'SIDEWAYS'