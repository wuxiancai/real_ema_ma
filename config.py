#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实交易系统配置文件
包含API密钥、交易参数等配置信息
"""

import os
from typing import Dict, Any

class TradingConfig:
    """交易配置类"""
    
    def __init__(self):
        """初始化配置"""
        # 币安合约API配置
        self.BINANCE_API_KEY = "yHEbiLZVNTpX81Vc6UYPJpIsPFa6P461R1OVHHq7JcLs60B4GPcVSEq7Chw8OCGG"
        self.BINANCE_SECRET_KEY = "gwbbkf4uCPTJbMH6M3QZFJ4qtkqqzasg28vVZb20nkWwe7kDCZsSRSMjidHCb3Th"
        self.BINANCE_BASE_URL = "https://fapi.binance.com"  # 合约API基础URL
        
        # 交易参数配置
        self.SYMBOL = "BTCUSDT"  # 交易对
        self.POSITION_SIZE_PERCENT = 0.50  # 开仓金额百分比（50%）
        self.LEVERAGE = 20  # 杠杆倍数
        self.COMMISSION_RATE = 0.0005  # 手续费率 0.05%
        
        # 技术指标参数
        self.EMA_PERIOD = 2  # EMA周期
        self.MA_PERIOD = 4  # MA周期
        self.TIMEFRAME = "15m"  # 时间周期
        
        # 系统参数
        self.CHECK_INTERVAL = 60  # 检查间隔（秒）
        self.LOG_LEVEL = "INFO"  # 日志级别
        self.DATABASE_PATH = "real_trading.db"  # 数据库路径
        
        # 测试模式配置
        self.TEST_MODE = True  # 测试模式开关，True时不执行真实交易
        self.PAPER_TRADING = True  # 模拟交易模式
        
    def get_config_dict(self) -> Dict[str, Any]:
        """
        获取配置字典
        
        Returns:
            配置字典
        """
        return {
            'api_config': {
                'api_key': self.BINANCE_API_KEY,
                'secret_key': self.BINANCE_SECRET_KEY,
                'base_url': self.BINANCE_BASE_URL
            },
            'trading_config': {
                'symbol': self.SYMBOL,
                'position_size': self.POSITION_SIZE_PERCENT,
                'leverage': self.LEVERAGE,
                'commission_rate': self.COMMISSION_RATE
            },
            'indicator_config': {
                'ema_period': self.EMA_PERIOD,
                'ma_period': self.MA_PERIOD,
                'timeframe': self.TIMEFRAME
            },

            'system_config': {
                'check_interval': self.CHECK_INTERVAL,
                'log_level': self.LOG_LEVEL,
                'database_path': self.DATABASE_PATH,
                'test_mode': self.TEST_MODE,
                'paper_trading': self.PAPER_TRADING
            }
        }
    
    def validate_config(self) -> bool:
        """
        验证配置有效性
        
        Returns:
            配置是否有效
        """
        # 检查必要的API密钥
        if not self.BINANCE_API_KEY or not self.BINANCE_SECRET_KEY:
            print("错误：缺少币安API密钥配置")
            return False
            
        # 检查交易参数
        if self.POSITION_SIZE_PERCENT <= 0:
            print("错误：仓位大小必须大于0")
            return False
            
        if self.LEVERAGE <= 0 or self.LEVERAGE > 125:
            print("错误：杠杆倍数必须在1-125之间")
            return False
            
        return True

# 全局配置实例
config = TradingConfig()