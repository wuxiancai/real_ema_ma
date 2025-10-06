// 主要的JavaScript功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initializePage();
    
    // 设置定时刷新
    setInterval(loadAllData, 5000); // 每5秒刷新一次
    
    // 绑定刷新按钮事件
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadAllData);
    }
});

/**
 * 初始化页面
 */
function initializePage() {
    console.log('初始化交易系统监控面板');
    loadAllData();
}

/**
 * 加载所有数据
 */
function loadAllData() {
    loadConfig();
    loadStatistics();
    loadPositions();
    loadTrades();
    loadFundFlows();
    loadCurrentPrice();
    loadOrderHistory();
    loadTradeHistory();
    loadKlines();
    loadConnectivity();
}

/**
 * 渲染错误信息
 */
function renderError(containerId, error) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <div class="error-message">错误: ${error}</div>
            </div>
        `;
    }
}

/**
 * 加载系统配置
 */
function loadConfig() {
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderConfig(data.data);
            } else {
                renderError('config-container', data.error || '加载配置失败');
            }
        })
        .catch(error => {
            console.error('加载配置失败:', error);
            renderError('config-container', error.message);
        });
}

/**
 * 加载统计数据
 */
function loadStatistics() {
    fetch('/api/statistics')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderStatistics(data.data);
            } else {
                renderError('stats-container', data.error || '加载统计数据失败');
            }
        })
        .catch(error => {
            console.error('加载统计数据失败:', error);
            renderError('stats-container', error.message);
        });
}

/**
 * 加载持仓信息
 */
function loadPositions() {
    fetch('/api/positions')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderPositions(data.data);
            } else {
                renderError('positions-container', data.error || '加载持仓失败');
            }
        })
        .catch(error => {
            console.error('加载持仓失败:', error);
            renderError('positions-container', error.message);
        });
}

/**
 * 加载交易记录
 */
function loadTrades() {
    fetch('/api/trades')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderTrades(data.data);
            } else {
                renderError('trades-container', data.error || '加载交易记录失败');
            }
        })
        .catch(error => {
            console.error('加载交易记录失败:', error);
            renderError('trades-container', error.message);
        });
}

/**
 * 加载资金流水
 */
function loadFundFlows() {
    fetch('/api/fund_flows')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderFundFlows(data.data);
            } else {
                renderError('fund-flows-container', data.error || '加载资金流水失败');
            }
        })
        .catch(error => {
            console.error('加载资金流水失败:', error);
            renderError('fund-flows-container', error.message);
        });
}

/**
 * 加载当前价格
 */
function loadCurrentPrice() {
    fetch('/api/current_price')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderCurrentPrice(data.data);
            } else {
                renderError('current-price-container', data.error || '加载价格失败');
            }
        })
        .catch(error => {
            console.error('加载价格失败:', error);
            renderError('current-price-container', error.message);
        });
}

/**
 * 加载订单历史
 */
function loadOrderHistory() {
    fetch('/api/order_history')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderOrderHistory(data.data);
            } else {
                renderError('order-history-container', data.error || '加载订单历史失败');
            }
        })
        .catch(error => {
            console.error('加载订单历史失败:', error);
            renderError('order-history-container', error.message);
        });
}

/**
 * 加载交易历史
 */
function loadTradeHistory() {
    fetch('/api/trade_history')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderTradeHistory(data.data);
            } else {
                renderError('trade-history-container', data.error || '加载交易历史失败');
            }
        })
        .catch(error => {
            console.error('加载交易历史失败:', error);
            renderError('trade-history-container', error.message);
        });
}

/**
 * 加载K线数据
 */
function loadKlines() {
    fetch('/api/klines')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderKlines(data.data);
            } else {
                renderError('klines-container', data.error || '加载K线数据失败');
            }
        })
        .catch(error => {
            console.error('加载K线数据失败:', error);
            renderError('klines-container', error.message);
        });
}

/**
 * 加载API连接状态
 */
function loadConnectivity() {
    fetch('/api/test_connectivity')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderConnectivity(data);  // 传递完整的data对象，而不是data.data
            } else {
                renderError('connectivity-container', data.error || '连接测试失败');
            }
        })
        .catch(error => {
            console.error('连接测试失败:', error);
            renderError('connectivity-container', error.message);
        });
}

/**
 * 渲染系统配置
 */
function renderConfig(config) {
    const container = document.getElementById('config-container');
    if (!container) return;
    
    // 从嵌套的配置对象中提取数据
    const tradingConfig = config.trading_config || {};
    const systemConfig = config.system_config || {};
    const indicatorConfig = config.indicator_config || {};
    
    container.innerHTML = `
        <div class="config-grid">
            <div class="config-section">
                <h3>交易配置</h3>
                <div class="config-items">
                    <div class="config-item">
                        <span class="config-label">交易对:</span>
                        <span class="config-value">${tradingConfig.symbol || 'N/A'}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">杠杆倍数:</span>
                        <span class="config-value">${tradingConfig.leverage || 'N/A'}x</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">仓位大小:</span>
                        <span class="config-value">${((tradingConfig.position_size_percent || 0) * 100).toFixed(1)}% 余额</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">手续费率:</span>
                        <span class="config-value">${((tradingConfig.commission_rate || 0) * 100).toFixed(3)}%</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">时间周期:</span>
                        <span class="config-value">${tradingConfig.timeframe || 'N/A'}</span>
                    </div>
                </div>
            </div>
            
            <div class="config-section">
                <h3>系统配置</h3>
                <div class="config-items">
                    <div class="config-item">
                        <span class="config-label">测试模式:</span>
                        <span class="config-value ${systemConfig.test_mode ? 'status-warning' : 'status-success'}">
                            ${systemConfig.test_mode ? '是' : '否'}
                        </span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">模拟交易:</span>
                        <span class="config-value ${systemConfig.paper_trading ? 'status-warning' : 'status-success'}">
                            ${systemConfig.paper_trading ? '是' : '否'}
                        </span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">检查间隔:</span>
                        <span class="config-value">${systemConfig.check_interval || 'N/A'}秒</span>
                    </div>
                </div>
            </div>
            
            <div class="config-section">
                <h3>技术指标</h3>
                <div class="config-items">
                    <div class="config-item">
                        <span class="config-label">EMA周期:</span>
                        <span class="config-value">${indicatorConfig.ema_period || 'N/A'}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">MA周期:</span>
                        <span class="config-value">${indicatorConfig.ma_period || 'N/A'}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">时间框架:</span>
                        <span class="config-value">${indicatorConfig.timeframe || 'N/A'}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * 渲染统计数据
 */
function renderStatistics(stats) {
    const container = document.getElementById('stats-container');
    if (!container) return;
    
    container.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">总盈亏</div>
                <div class="stat-value ${stats.total_pnl >= 0 ? 'positive' : 'negative'}">
                    ${stats.total_pnl ? stats.total_pnl.toFixed(2) : '0.00'} USDT
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-label">胜率</div>
                <div class="stat-value">${stats.win_rate ? (stats.win_rate * 100).toFixed(1) : '0.0'}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">总交易次数</div>
                <div class="stat-value">${stats.total_trades || 0}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">ROI</div>
                <div class="stat-value ${stats.roi >= 0 ? 'positive' : 'negative'}">
                    ${stats.roi ? (stats.roi * 100).toFixed(2) : '0.00'}%
                </div>
            </div>
        </div>
    `;
}

/**
 * 渲染持仓信息
 */
function renderPositions(positions) {
    const container = document.getElementById('positions-container');
    if (!container) return;
    
    if (!positions || positions.length === 0) {
        container.innerHTML = '<div class="no-data">暂无持仓</div>';
        return;
    }
    
    let html = '<div class="positions-table"><table><thead><tr>';
    html += '<th>交易对</th><th>方向</th><th>数量</th><th>入场价</th><th>标记价</th><th>盈亏</th>';
    html += '</tr></thead><tbody>';
    
    positions.forEach(position => {
        html += `
            <tr>
                <td>${position.symbol || 'N/A'}</td>
                <td class="${position.side === 'LONG' ? 'long' : 'short'}">${position.side || 'N/A'}</td>
                <td>${position.size || '0'}</td>
                <td>${position.entry_price || '0'}</td>
                <td>${position.mark_price || '0'}</td>
                <td class="${position.pnl >= 0 ? 'positive' : 'negative'}">
                    ${position.pnl ? position.pnl.toFixed(2) : '0.00'}
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

/**
 * 渲染交易记录
 */
function renderTrades(trades) {
    const container = document.getElementById('trades-container');
    if (!container) return;
    
    if (!trades || trades.length === 0) {
        container.innerHTML = '<div class="no-data">暂无交易记录</div>';
        return;
    }
    
    let html = '<div class="trades-table"><table><thead><tr>';
    html += '<th>时间</th><th>交易对</th><th>方向</th><th>数量</th><th>价格</th><th>盈亏</th>';
    html += '</tr></thead><tbody>';
    
    trades.slice(0, 10).forEach(trade => {
        html += `
            <tr>
                <td>${new Date(trade.timestamp).toLocaleString()}</td>
                <td>${trade.symbol || 'N/A'}</td>
                <td class="${trade.side === 'BUY' ? 'long' : 'short'}">${trade.side || 'N/A'}</td>
                <td>${trade.quantity || '0'}</td>
                <td>${trade.price || '0'}</td>
                <td class="${trade.pnl >= 0 ? 'positive' : 'negative'}">
                    ${trade.pnl ? trade.pnl.toFixed(2) : '0.00'}
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

/**
 * 渲染资金流水
 */
function renderFundFlows(flows) {
    const container = document.getElementById('fund-flows-container');
    if (!container) return;
    
    if (!flows || flows.length === 0) {
        container.innerHTML = '<div class="no-data">暂无资金流水</div>';
        return;
    }
    
    // 获取今天的日期（只比较年月日）
    const today = new Date();
    const todayDateString = today.toDateString();
    
    // 过滤出今天的资金流水
    const todayFlows = flows.filter(flow => {
        if (!flow.timestamp) return false;
        const flowDate = new Date(flow.timestamp);
        return flowDate.toDateString() === todayDateString;
    });
    
    // 如果今天没有资金流水，显示提示信息
    if (todayFlows.length === 0) {
        container.innerHTML = '<div class="no-data">今日暂无资金流水</div>';
        return;
    }
    
    // 按时间戳降序排序（最新的在前面）
    const sortedFlows = todayFlows.sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime();
        const timeB = new Date(b.timestamp).getTime();
        return timeB - timeA; // 降序排序
    });
    
    let html = '<div class="flows-table"><table><thead><tr>';
    html += '<th>时间</th><th>类型</th><th>资产</th><th>金额</th><th>余额</th><th>描述</th>';
    html += '</tr></thead><tbody>';
    
    // 只显示前5条记录
    sortedFlows.slice(0, 5).forEach(flow => {
        const amount = parseFloat(flow.amount || 0);
        const balance = parseFloat(flow.balance || 0);
        
        html += `
            <tr>
                <td>${flow.timestamp ? new Date(flow.timestamp).toLocaleString('zh-CN') : 'N/A'}</td>
                <td><span class="flow-type">${flow.type || 'N/A'}</span></td>
                <td>${flow.asset || 'USDT'}</td>
                <td class="${amount >= 0 ? 'positive' : 'negative'}">
                    ${amount >= 0 ? '+' : ''}${amount.toFixed(2)}
                </td>
                <td>${balance.toFixed(2)}</td>
                <td class="flow-description">${flow.description || '-'}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

/**
 * 渲染当前价格
 */
function renderCurrentPrice(priceData) {
    const container = document.getElementById('current-price-container');
    if (!container) return;
    
    if (!priceData) {
        container.innerHTML = '<div class="no-data">暂无价格数据</div>';
        return;
    }
    
    container.innerHTML = `
        <div class="price-display">
            <div class="price-value">${priceData.price || 'N/A'}</div>
            <div class="price-symbol">${priceData.symbol || 'N/A'}</div>
        </div>
    `;
}

/**
 * 渲染订单历史
 */
function renderOrderHistory(orders) {
    const container = document.getElementById('order-history-container');
    if (!container) return;
    
    if (!orders || orders.length === 0) {
        container.innerHTML = '<div class="no-data">暂无订单历史</div>';
        return;
    }
    
    let html = '<div class="orders-table"><table><thead><tr>';
    html += '<th>时间</th><th>交易对</th><th>类型</th><th>方向</th><th>数量</th><th>价格</th><th>状态</th>';
    html += '</tr></thead><tbody>';
    
    orders.slice(0, 10).forEach(order => {
        html += `
            <tr>
                <td>${new Date(order.time).toLocaleString()}</td>
                <td>${order.symbol || 'N/A'}</td>
                <td>${order.type || 'N/A'}</td>
                <td class="${order.side === 'BUY' ? 'long' : 'short'}">${order.side || 'N/A'}</td>
                <td>${order.origQty || '0'}</td>
                <td>${order.price || '0'}</td>
                <td class="status-${order.status ? order.status.toLowerCase() : 'unknown'}">${order.status || 'N/A'}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

/**
 * 渲染交易历史
 */
function renderTradeHistory(trades) {
    const container = document.getElementById('trade-history-container');
    if (!container) return;
    
    if (!trades || trades.length === 0) {
        container.innerHTML = '<div class="no-data">暂无交易历史</div>';
        return;
    }
    
    let html = '<div class="trade-history-table"><table><thead><tr>';
    html += '<th>时间</th><th>交易对</th><th>方向</th><th>数量</th><th>价格</th><th>手续费</th>';
    html += '</tr></thead><tbody>';
    
    trades.slice(0, 10).forEach(trade => {
        html += `
            <tr>
                <td>${new Date(trade.time).toLocaleString()}</td>
                <td>${trade.symbol || 'N/A'}</td>
                <td class="${trade.isBuyer ? 'long' : 'short'}">${trade.isBuyer ? 'BUY' : 'SELL'}</td>
                <td>${trade.qty || '0'}</td>
                <td>${trade.price || '0'}</td>
                <td>${trade.commission || '0'} ${trade.commissionAsset || ''}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

/**
 * 渲染K线数据
 */
function renderKlines(klines) {
    const container = document.getElementById('klines-container');
    if (!container) return;
    
    if (!klines || klines.length === 0) {
        container.innerHTML = '<div class="no-data">暂无K线数据</div>';
        return;
    }
    
    let html = '<div class="klines-table"><table><thead><tr>';
    html += '<th>时间</th><th>开盘价</th><th>最高价</th><th>最低价</th><th>收盘价</th><th>成交量</th>';
    html += '</tr></thead><tbody>';
    
    // 对K线数据按时间戳降序排序（最新的在前面），并只取前5条
    const sortedKlines = klines.sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime();
        const timeB = new Date(b.timestamp).getTime();
        return timeB - timeA; // 降序排序
    });
    
    sortedKlines.slice(0, 5).forEach(kline => {
        // 处理时间戳，确保正确解析并转换为北京时间（UTC+8）
        let timestamp;
        if (kline.timestamp) {
            const date = new Date(kline.timestamp);
            // 转换为北京时间（UTC+8）
            const beijingTime = new Date(date.getTime() + (8 * 60 * 60 * 1000));
            timestamp = beijingTime.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'Asia/Shanghai'
            });
        } else {
            timestamp = 'Invalid Date';
        }
        
        html += `
            <tr>
                <td>${timestamp}</td>
                <td>${parseFloat(kline.open || 0).toFixed(2)}</td>
                <td>${parseFloat(kline.high || 0).toFixed(2)}</td>
                <td>${parseFloat(kline.low || 0).toFixed(2)}</td>
                <td>${parseFloat(kline.close || 0).toFixed(2)}</td>
                <td>${parseFloat(kline.volume || 0).toFixed(3)}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

/**
 * 渲染API连接状态
 */
function renderConnectivity(connectivity) {
    const container = document.getElementById('connectivity-container');
    if (!container) return;
    
    // 检查API响应的数据结构
    const isConnected = connectivity && connectivity.success && connectivity.data && connectivity.data.connected;
    
    container.innerHTML = `
        <div class="connectivity-status">
            <div class="status-indicator ${isConnected ? 'status-success' : 'status-error'}"></div>
            <div class="status-text">
                ${isConnected ? 'API连接正常' : 'API连接失败'}
            </div>
            ${connectivity && connectivity.data && connectivity.data.serverTime ? 
                `<div class="server-time">服务器时间: ${new Date(connectivity.data.serverTime).toLocaleString('zh-CN')}</div>` : 
                ''
            }
        </div>
    `;
}