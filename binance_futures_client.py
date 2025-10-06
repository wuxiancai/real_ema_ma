#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安合约API客户端
实现与币安合约API的交互功能
"""

import hashlib
import hmac
import time
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from config import config


class BinanceFuturesClient:
    """币安合约API客户端类"""
    
    def __init__(self, api_key: str = None, secret_key: str = None, base_url: str = None):
        """
        初始化币安合约客户端
        
        Args:
            api_key: API密钥
            secret_key: 密钥
            base_url: API基础URL
        """
        self.api_key = api_key or config.BINANCE_API_KEY
        self.secret_key = secret_key or config.BINANCE_SECRET_KEY
        self.base_url = base_url or config.BINANCE_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        })
        
        # 配置代理
        proxies = {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890'
        }
        self.session.proxies.update(proxies)
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        生成API签名
        
        Args:
            params: 请求参数
            
        Returns:
            签名字符串
        """
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """
        发送API请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: 请求参数
            signed: 是否需要签名
            
        Returns:
            API响应数据
        """
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应内容: {e.response.text}")
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            账户信息
        """
        return self._make_request('GET', '/fapi/v2/account', signed=True)
    
    def get_balance(self) -> Dict[str, float]:
        """
        获取账户余额
        
        Returns:
            余额信息字典
        """
        account_info = self.get_account_info()
        balance_info = {}
        
        for asset in account_info.get('assets', []):
            if float(asset['walletBalance']) > 0:
                balance_info[asset['asset']] = {
                    'balance': float(asset['walletBalance']),
                    'available': float(asset['availableBalance']),
                    'margin': float(asset['initialMargin'])
                }
        
        return balance_info
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        获取当前持仓
        
        Returns:
            持仓列表
        """
        positions = self._make_request('GET', '/fapi/v2/positionRisk', signed=True)
        active_positions = []
        
        for pos in positions:
            if float(pos['positionAmt']) != 0:
                active_positions.append({
                    'symbol': pos['symbol'],
                    'side': 'LONG' if float(pos['positionAmt']) > 0 else 'SHORT',
                    'size': abs(float(pos['positionAmt'])),
                    'entry_price': float(pos['entryPrice']),
                    'mark_price': float(pos['markPrice']),
                    'pnl': float(pos['unRealizedProfit']),
                    'percentage': float(pos['percentage']),
                    'leverage': int(pos['leverage'])
                })
        
        return active_positions
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: 时间间隔
            limit: 数据条数
            
        Returns:
            K线数据DataFrame
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        klines = self._make_request('GET', '/fapi/v1/klines', params)
        
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'count', 'taker_buy_volume',
            'taker_buy_quote_volume', 'ignore'
        ])
        
        # 转换数据类型
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    def get_current_price(self, symbol: str) -> float:
        """
        获取当前价格
        
        Args:
            symbol: 交易对
            
        Returns:
            当前价格
        """
        params = {'symbol': symbol}
        ticker = self._make_request('GET', '/fapi/v1/ticker/price', params)
        return float(ticker['price'])
    
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                   price: float = None, time_in_force: str = 'GTC') -> Dict[str, Any]:
        """
        下单
        
        Args:
            symbol: 交易对
            side: 买卖方向 ('BUY' 或 'SELL')
            order_type: 订单类型 ('MARKET' 或 'LIMIT')
            quantity: 数量
            price: 价格（限价单需要）
            time_in_force: 时效性
            
        Returns:
            订单信息
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'timeInForce': time_in_force
        }
        
        if order_type == 'LIMIT' and price is not None:
            params['price'] = price
        
        return self._make_request('POST', '/fapi/v1/order', params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        取消订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            取消结果
        """
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        
        return self._make_request('DELETE', '/fapi/v1/order', params, signed=True)
    
    def get_order_history(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """
        获取订单历史
        
        Args:
            symbol: 交易对
            limit: 数据条数
            
        Returns:
            订单历史列表
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        return self._make_request('GET', '/fapi/v1/allOrders', params, signed=True)
    
    def get_trade_history(self, symbol: str, limit: int = 500, start_time: int = None) -> List[Dict[str, Any]]:
        """
        获取交易历史
        
        Args:
            symbol: 交易对
            limit: 数据条数
            start_time: 开始时间戳（毫秒）
            
        Returns:
            交易历史列表
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        
        return self._make_request('GET', '/fapi/v1/userTrades', params, signed=True)
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        设置杠杆倍数
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数
            
        Returns:
            设置结果
        """
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        
        return self._make_request('POST', '/fapi/v1/leverage', params, signed=True)
    
    def set_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """
        设置保证金模式
        
        Args:
            symbol: 交易对
            margin_type: 保证金模式 ('ISOLATED' 或 'CROSSED')
            
        Returns:
            设置结果
        """
        params = {
            'symbol': symbol,
            'marginType': margin_type
        }
        
        return self._make_request('POST', '/fapi/v1/marginType', params, signed=True)
    
    def test_connectivity(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否正常
        """
        try:
            self._make_request('GET', '/fapi/v1/ping')
            return True
        except Exception as e:
            print(f"API连接测试失败: {e}")
            return False