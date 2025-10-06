# 真实交易系统 - EMA/MA交叉策略

基于币安合约API的自动化交易系统，使用EMA和MA交叉策略进行交易。

## 功能特性

- **自动交易**: 基于EMA/MA交叉信号自动开仓平仓
- **风险控制**: 止损止盈、最大持仓数量、每日亏损限制
- **持仓管理**: 实时同步API持仓，本地持仓跟踪
- **交易记录**: 完整的交易历史和资金流水记录
- **数据库存储**: SQLite数据库存储所有交易数据
- **测试模式**: 支持模拟交易和真实交易模式

## 文件结构

```
real_ema_ma/
├── main.py                    # 主程序入口
├── config.py                  # 配置文件
├── binance_futures_client.py  # 币安合约API客户端
├── real_trading_executor.py   # 真实交易执行器
├── position_manager.py        # 持仓管理和风险控制
├── trade_recorder.py          # 交易历史和资金流水记录
├── indicators.py              # 技术指标计算
├── requirements.txt           # Python依赖
├── start.sh                   # 启动脚本
└── README.md                  # 说明文档
```

## 安装和配置

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 2. 配置API密钥

编辑 `config.py` 文件，设置您的币安合约API密钥：

```python
API_KEY = "your_api_key_here"
SECRET_KEY = "your_secret_key_here"
```

### 3. 调整交易参数

在 `config.py` 中调整以下参数：

- `SYMBOL`: 交易对（默认: BTCUSDT）
- `POSITION_SIZE`: 仓位大小（默认: 100 USDT）
- `LEVERAGE`: 杠杆倍数（默认: 10）
- `EMA_PERIOD`: EMA周期（默认: 20）
- `MA_PERIOD`: MA周期（默认: 35）
- `STOP_LOSS_PERCENT`: 止损百分比（默认: 0.02）
- `TAKE_PROFIT_PERCENT`: 止盈百分比（默认: 0.04）

## 使用方法

### 启动系统

```bash
# 使用启动脚本
./start.sh

# 或直接运行Python
python3 main.py
```

### 测试模式

首次使用建议开启测试模式：

```python
# 在config.py中设置
TEST_MODE = True
PAPER_TRADING = True
```

### 真实交易模式

确认策略有效后，可切换到真实交易：

```python
# 在config.py中设置
TEST_MODE = False
PAPER_TRADING = False
```

## 交易策略

### 开仓条件

**做多条件**:
- EMA金叉MA
- 价格在EMA上方
- EMA在MA上方
- EMA呈上升趋势

**做空条件**:
- EMA死叉MA
- 价格在EMA下方
- EMA在MA下方
- EMA呈下降趋势

### 平仓条件

**多头平仓**:
- EMA死叉MA
- 价格跌破EMA

**空头平仓**:
- EMA金叉MA
- 价格突破EMA

### 风险控制

- **止损**: 亏损达到设定百分比自动平仓
- **止盈**: 盈利达到设定百分比自动平仓
- **最大持仓**: 限制同时持有的仓位数量
- **每日亏损限制**: 达到每日最大亏损后停止交易

## 数据记录

系统会自动记录以下数据：

- **交易记录**: 所有开仓平仓操作
- **资金流水**: 每笔交易的资金变动
- **持仓快照**: 定期保存持仓状态
- **余额快照**: 定期保存账户余额
- **交易统计**: 每日交易统计数据

## 监控和日志

- **日志文件**: `real_trading_system.log`
- **交易日志**: 自动生成的交易记录文件
- **数据库**: `real_trading.db` (SQLite数据库)

## 安全提示

1. **API权限**: 确保API密钥只有合约交易权限，不要开启提现权限
2. **资金管理**: 建议只投入可承受损失的资金
3. **测试先行**: 在真实交易前充分测试策略
4. **监控系统**: 定期检查系统运行状态和交易结果
5. **备份数据**: 定期备份交易数据和配置文件

## 故障排除

### 常见问题

1. **API连接失败**
   - 检查网络连接
   - 验证API密钥是否正确
   - 确认API权限设置

2. **交易失败**
   - 检查账户余额是否充足
   - 验证交易对是否正确
   - 确认杠杆设置是否合理

3. **数据获取失败**
   - 检查币安API服务状态
   - 验证交易对和时间框架参数

### 日志分析

查看日志文件了解系统运行状态：

```bash
tail -f real_trading_system.log
```

## 免责声明

本交易系统仅供学习和研究使用。加密货币交易存在高风险，可能导致资金损失。使用本系统进行真实交易的所有风险由用户自行承担。

## 技术支持

如有问题，请检查：
1. 日志文件中的错误信息
2. 配置参数是否正确
3. API密钥权限设置
4. 网络连接状态