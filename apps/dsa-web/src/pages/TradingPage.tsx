import type React from 'react';
import { useState, useEffect } from 'react';
import { Card, Badge } from '../components/common';
import { tradingApi, type Account, type Position, type Order, type StopLoss, type AccountHistory, type PerformanceMetrics } from '../api/trading';

/**
 * Simulated Trading Page
 * Paper trading functionality with real-time data
 */
const TradingPage: React.FC = () => {
  const [account, setAccount] = useState<Account | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [stockCode, setStockCode] = useState('');
  const [quantity, setQuantity] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  // Stop loss / take profit states
  const [stopLosses, setStopLosses] = useState<Record<string, StopLoss>>({});
  const [showStopLossModal, setShowStopLossModal] = useState(false);
  const [selectedStockCode, setSelectedStockCode] = useState('');
  const [takeProfitPrice, setTakeProfitPrice] = useState('');
  const [takeProfitPct, setTakeProfitPct] = useState('');
  const [stopLossPrice, setStopLossPrice] = useState('');
  const [stopLossPct, setStopLossPct] = useState('');
  const [savingStopLoss, setSavingStopLoss] = useState(false);

  // Performance metrics and history states
  const [accountHistory, setAccountHistory] = useState<AccountHistory[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [accountData, positionsData, ordersData, stopLossData, historyData, metricsData] = await Promise.all([
        tradingApi.getAccount(),
        tradingApi.getPositions(),
        tradingApi.getOrders(),
        tradingApi.getAllStopLoss(),
        tradingApi.getAccountHistory(30),
        tradingApi.getPerformanceMetrics(),
      ]);
      setAccount(accountData);
      setPositions(positionsData);
      setOrders(ordersData);
      setAccountHistory(historyData);
      setPerformanceMetrics(metricsData);
      
      // Convert stop loss array to object for easy lookup
      const stopLossMap: Record<string, StopLoss> = {};
      stopLossData.forEach((sl) => {
        stopLossMap[sl.stockCode] = sl;
      });
      setStopLosses(stopLossMap);
    } catch (error) {
      console.error('Failed to load data:', error);
      showMessage('error', '加载数据失败');
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleBuy = async () => {
    if (!stockCode.trim() || !quantity.trim()) {
      showMessage('error', '请输入股票代码和数量');
      return;
    }

    const qty = parseInt(quantity, 10);
    if (isNaN(qty) || qty <= 0) {
      showMessage('error', '请输入有效的数量');
      return;
    }

    setLoading(true);
    try {
      const result = await tradingApi.placeOrder({
        stockCode: stockCode.trim().toUpperCase(),
        orderType: 'buy',
        quantity: qty,
      });

      if (result.status === 'filled') {
        showMessage('success', result.message);
        setStockCode('');
        setQuantity('');
        await loadData();
      } else {
        showMessage('error', result.message);
      }
    } catch (error: any) {
      console.error('Buy failed:', error);
      showMessage('error', error.response?.data?.detail?.message || '买入失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSell = async () => {
    if (!stockCode.trim() || !quantity.trim()) {
      showMessage('error', '请输入股票代码和数量');
      return;
    }

    const qty = parseInt(quantity, 10);
    if (isNaN(qty) || qty <= 0) {
      showMessage('error', '请输入有效的数量');
      return;
    }

    setLoading(true);
    try {
      const result = await tradingApi.placeOrder({
        stockCode: stockCode.trim().toUpperCase(),
        orderType: 'sell',
        quantity: qty,
      });

      if (result.status === 'filled') {
        showMessage('success', result.message);
        setStockCode('');
        setQuantity('');
        await loadData();
      } else {
        showMessage('error', result.message);
      }
    } catch (error: any) {
      console.error('Sell failed:', error);
      showMessage('error', error.response?.data?.detail?.message || '卖出失败');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number | string | null | undefined, decimals: number = 2) => {
    if (num === null || num === undefined) return '-';
    const value = typeof num === 'string' ? parseFloat(num) : num;
    if (isNaN(value)) return '-';
    return value.toFixed(decimals);
  };

  const formatPercent = (num: number | string | null | undefined) => {
    if (num === null || num === undefined) return '-';
    const value = typeof num === 'string' ? parseFloat(num) : num;
    if (isNaN(value)) return '-';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const getProfitClass = (num: number | string | null | undefined) => {
    if (num === null || num === undefined) return 'text-muted';
    const value = typeof num === 'string' ? parseFloat(num) : num;
    if (isNaN(value)) return 'text-muted';
    return value >= 0 ? 'text-emerald-400' : 'text-red-400';
  };

  // Stop loss / take profit handlers
  const openStopLossModal = (stockCode: string) => {
    const existingStopLoss = stopLosses[stockCode];
    setSelectedStockCode(stockCode);
    
    if (existingStopLoss) {
      setTakeProfitPrice(existingStopLoss.takeProfitPrice?.toString() || '');
      setTakeProfitPct(existingStopLoss.takeProfitPct?.toString() || '');
      setStopLossPrice(existingStopLoss.stopLossPrice?.toString() || '');
      setStopLossPct(existingStopLoss.stopLossPct?.toString() || '');
    } else {
      setTakeProfitPrice('');
      setTakeProfitPct('');
      setStopLossPrice('');
      setStopLossPct('');
    }
    
    setShowStopLossModal(true);
  };

  const closeStopLossModal = () => {
    setShowStopLossModal(false);
    setSelectedStockCode('');
    setTakeProfitPrice('');
    setTakeProfitPct('');
    setStopLossPrice('');
    setStopLossPct('');
  };

  const handleSaveStopLoss = async () => {
    if (!selectedStockCode) return;

    setSavingStopLoss(true);
    try {
      const request: any = {
        stockCode: selectedStockCode,
      };

      // Only set values that are not empty
      if (takeProfitPrice) {
        request.takeProfitPrice = parseFloat(takeProfitPrice);
      }
      if (takeProfitPct) {
        request.takeProfitPct = parseFloat(takeProfitPct);
      }
      if (stopLossPrice) {
        request.stopLossPrice = parseFloat(stopLossPrice);
      }
      if (stopLossPct) {
        request.stopLossPct = parseFloat(stopLossPct);
      }

      // If all fields are empty, delete the stop loss
      if (!takeProfitPrice && !takeProfitPct && !stopLossPrice && !stopLossPct) {
        await tradingApi.deleteStopLoss(selectedStockCode);
        showMessage('success', '已删除止盈止损设置');
      } else {
        await tradingApi.setStopLoss(request);
        showMessage('success', '止盈止损设置已保存');
      }

      await loadData();
      closeStopLossModal();
    } catch (error: any) {
      console.error('Failed to save stop loss:', error);
      showMessage('error', error.response?.data?.detail?.message || '保存失败');
    } finally {
      setSavingStopLoss(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="flex-shrink-0 px-4 py-3 border-b border-white/5">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-white">模拟交易</h1>
          {account && (
            <div className="flex items-center gap-4 text-sm">
              <div className="text-secondary">
                总资产: <span className="text-cyan font-mono">¥{formatNumber(account.totalBalance)}</span>
              </div>
              <div className="text-secondary">
                可用资金: <span className="text-emerald-400 font-mono">¥{formatNumber(account.cashBalance)}</span>
              </div>
              <div className={getProfitClass(account.profitLoss)}>
                盈亏: <span className="font-mono">{formatNumber(account.profitLoss)} ({formatPercent(account.profitLossPct)})</span>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Message */}
      {message && (
        <div className={`px-4 py-2 ${message.type === 'success' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
          {message.text}
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 p-4 overflow-auto">
        <div className="max-w-4xl mx-auto space-y-4">
          {/* Trading Form */}
          <Card variant="gradient" padding="lg">
            <div className="mb-4">
              <span className="label-uppercase">下单交易</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-secondary mb-2">股票代码</label>
                <input
                  type="text"
                  value={stockCode}
                  onChange={(e) => setStockCode(e.target.value.toUpperCase())}
                  placeholder="如 600519、00700、AAPL"
                  className="input-terminal w-full"
                  disabled={loading}
                />
              </div>
              <div>
                <label className="block text-xs text-secondary mb-2">数量</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  placeholder="买入/卖出数量"
                  className="input-terminal w-full"
                  disabled={loading}
                />
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                type="button"
                className="btn-primary flex-1"
                onClick={handleBuy}
                disabled={loading}
              >
                {loading ? '处理中...' : '买入'}
              </button>
              <button
                type="button"
                className="btn-danger flex-1"
                onClick={handleSell}
                disabled={loading}
              >
                {loading ? '处理中...' : '卖出'}
              </button>
            </div>
          </Card>

          {/* Holdings */}
          <Card padding="lg">
            <div className="mb-4 flex items-center justify-between">
              <span className="label-uppercase">持仓</span>
              <Badge variant="default">{positions.length} 只股票</Badge>
            </div>
            {positions.length === 0 ? (
              <div className="text-center py-8 text-muted">暂无持仓</div>
            ) : (
              <div className="space-y-2">
                {positions.map((pos) => {
                  const stopLoss = stopLosses[pos.stockCode];
                  return (
                    <div
                      key={pos.id}
                      className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
                    >
                      <div>
                        <div className="font-medium text-white">{pos.stockCode}</div>
                        <div className="text-xs text-secondary">{pos.stockName || '-'}</div>
                        <div className="text-xs text-secondary mt-1">
                          持仓 <span className="text-white">{pos.holdingDays || 0}</span> 天
                        </div>
                        {stopLoss && stopLoss.isActive && (
                          <div className="mt-1 flex items-center gap-2">
                            {stopLoss.takeProfitPrice && (
                              <span className="text-xs text-emerald-400">
                                止盈: ¥{formatNumber(stopLoss.takeProfitPrice)}
                              </span>
                            )}
                            {stopLoss.stopLossPrice && (
                              <span className="text-xs text-red-400">
                                止损: ¥{formatNumber(stopLoss.stopLossPrice)}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-white">{pos.quantity} 股</div>
                        <div className="text-xs text-secondary">
                          成本 ¥{formatNumber(pos.avgCost)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-white">¥{formatNumber(pos.marketValue)}</div>
                        <div className={`text-xs ${getProfitClass(pos.profitLossPct)}`}>
                          {formatPercent(pos.profitLossPct)}
                        </div>
                      </div>
                      <button
                        type="button"
                        className="px-3 py-1 text-xs bg-white/10 hover:bg-white/20 text-white rounded transition-colors"
                        onClick={() => openStopLossModal(pos.stockCode)}
                      >
                        {stopLoss ? '编辑' : '止盈止损'}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Orders */}
          <Card padding="lg">
            <div className="mb-4 flex items-center justify-between">
              <span className="label-uppercase">委托记录</span>
              <Badge variant="default">{orders.length} 条记录</Badge>
            </div>
            {orders.length === 0 ? (
              <div className="text-center py-8 text-muted">暂无委托记录</div>
            ) : (
              <div className="space-y-2">
                {orders.map((order) => (
                  <div
                    key={order.id}
                    className="p-3 bg-white/5 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-medium text-white">{order.stockCode}</div>
                        <div className="text-xs text-secondary">{order.stockName || '-'}</div>
                      </div>
                      <div className="text-right">
                        <div className={`text-sm ${order.orderType === 'buy' ? 'text-emerald-400' : 'text-red-400'}`}>
                          {order.orderType === 'buy' ? '买入' : '卖出'}
                        </div>
                        <div className="text-xs text-secondary">
                          {order.quantity} 股 @ ¥{formatNumber(order.filledPrice)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-white">¥{formatNumber(order.filledAmount)}</div>
                        <div className="text-xs text-secondary">
                          {order.status === 'filled' ? '已成交' : order.status}
                        </div>
                      </div>
                    </div>
                    {order.totalFee > 0 && (
                      <div className="mt-2 pt-2 border-t border-white/10 text-xs text-secondary grid grid-cols-2 gap-2">
                        <div>佣金: ¥{formatNumber(order.commission)}</div>
                        <div>印花税: ¥{formatNumber(order.stampDuty)}</div>
                        <div>过户费: ¥{formatNumber(order.transferFee)}</div>
                        <div className="text-white">手续费: ¥{formatNumber(order.totalFee)}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Performance Metrics */}
          {performanceMetrics && accountHistory.length > 0 && (
            <Card padding="lg">
              <div className="mb-4">
                <span className="label-uppercase">绩效指标</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white/5 p-3 rounded-lg">
                  <div className="text-xs text-secondary mb-1">总收益率</div>
                  <div className={`text-lg font-mono ${getProfitClass(performanceMetrics.totalReturnPct)}`}>
                    {formatPercent(performanceMetrics.totalReturnPct)}
                  </div>
                </div>
                <div className="bg-white/5 p-3 rounded-lg">
                  <div className="text-xs text-secondary mb-1">年化收益率</div>
                  <div className={`text-lg font-mono ${getProfitClass(performanceMetrics.annualizedReturnPct)}`}>
                    {formatPercent(performanceMetrics.annualizedReturnPct)}
                  </div>
                </div>
                <div className="bg-white/5 p-3 rounded-lg">
                  <div className="text-xs text-secondary mb-1">最大回撤</div>
                  <div className="text-lg font-mono text-red-400">
                    {formatPercent(performanceMetrics.maxDrawdownPct)}
                  </div>
                </div>
                <div className="bg-white/5 p-3 rounded-lg">
                  <div className="text-xs text-secondary mb-1">胜率</div>
                  <div className="text-lg font-mono text-cyan">
                    {formatPercent(performanceMetrics.winRatePct)}
                  </div>
                </div>
                <div className="bg-white/5 p-3 rounded-lg">
                  <div className="text-xs text-secondary mb-1">总交易次数</div>
                  <div className="text-lg font-mono text-white">
                    {performanceMetrics.totalTrades}
                  </div>
                </div>
                <div className="bg-white/5 p-3 rounded-lg">
                  <div className="text-xs text-secondary mb-1">盈利交易</div>
                  <div className="text-lg font-mono text-emerald-400">
                    {performanceMetrics.profitableTrades}
                  </div>
                </div>
                <div className="bg-white/5 p-3 rounded-lg col-span-2">
                  <div className="text-xs text-secondary mb-1">平均持仓天数</div>
                  <div className="text-lg font-mono text-white">
                    {performanceMetrics.averageHoldingDays.toFixed(1)} 天
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Account History - Return Rate Curve */}
          {accountHistory.length > 0 && (
            <Card padding="lg">
              <div className="mb-4 flex items-center justify-between">
                <span className="label-uppercase">收益率曲线</span>
                <Badge variant="default">{accountHistory.length} 天记录</Badge>
              </div>
              <div className="bg-white/5 p-4 rounded-lg">
                <div className="flex items-end justify-between h-32 gap-1">
                  {accountHistory.map((history) => {
                    const height = Math.max(5, Math.min(100, 50 + history.cumulativeReturnPct * 2));
                    const isPositive = history.cumulativeReturnPct >= 0;
                    return (
                      <div
                        key={history.id}
                        className="flex-1 flex flex-col items-center gap-1"
                        title={`${history.recordDate}: ${formatPercent(history.cumulativeReturnPct)}`}
                      >
                        <div
                          className="w-full rounded-sm transition-all"
                          style={{
                            height: `${height}%`,
                            backgroundColor: isPositive ? 'rgba(52, 211, 153, 0.7)' : 'rgba(248, 113, 113, 0.7)',
                          }}
                        />
                      </div>
                    );
                  })}
                </div>
                <div className="mt-3 flex justify-between text-xs text-secondary">
                  <span>{accountHistory[0]?.recordDate}</span>
                  <span>累计收益率</span>
                  <span>{accountHistory[accountHistory.length - 1]?.recordDate}</span>
                </div>
              </div>
            </Card>
          )}
        </div>
      </main>

      {/* Stop Loss / Take Profit Modal */}
      {showStopLossModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1a2e] rounded-lg p-6 w-full max-w-md border border-white/10">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-white">
                止盈止损设置 - {selectedStockCode}
              </h3>
              <p className="text-xs text-secondary mt-1">
                设置止盈止损后，系统将自动监控并触发交易
              </p>
            </div>

            <div className="space-y-4">
              {/* Take Profit */}
              <div>
                <label className="block text-xs text-secondary mb-2">止盈价格</label>
                <input
                  type="number"
                  value={takeProfitPrice}
                  onChange={(e) => setTakeProfitPrice(e.target.value)}
                  placeholder="如 100.50"
                  className="input-terminal w-full"
                />
              </div>
              <div>
                <label className="block text-xs text-secondary mb-2">止盈百分比 (%)</label>
                <input
                  type="number"
                  value={takeProfitPct}
                  onChange={(e) => setTakeProfitPct(e.target.value)}
                  placeholder="如 10"
                  className="input-terminal w-full"
                />
              </div>

              {/* Stop Loss */}
              <div>
                <label className="block text-xs text-secondary mb-2">止损价格</label>
                <input
                  type="number"
                  value={stopLossPrice}
                  onChange={(e) => setStopLossPrice(e.target.value)}
                  placeholder="如 90.00"
                  className="input-terminal w-full"
                />
              </div>
              <div>
                <label className="block text-xs text-secondary mb-2">止损百分比 (%)</label>
                <input
                  type="number"
                  value={stopLossPct}
                  onChange={(e) => setStopLossPct(e.target.value)}
                  placeholder="如 5"
                  className="input-terminal w-full"
                />
              </div>
            </div>

            <div className="mt-6 flex gap-2">
              <button
                type="button"
                className="btn-secondary flex-1"
                onClick={closeStopLossModal}
                disabled={savingStopLoss}
              >
                取消
              </button>
              <button
                type="button"
                className="btn-primary flex-1"
                onClick={handleSaveStopLoss}
                disabled={savingStopLoss}
              >
                {savingStopLoss ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingPage;
