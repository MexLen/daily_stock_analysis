# -*- coding: utf-8 -*-
"""Paper trading API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class Position(BaseModel):
    """持仓信息"""

    id: int = Field(..., description="持仓 ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    quantity: int = Field(..., description="持仓数量")
    avg_cost: Decimal = Field(..., description="平均成本价")
    current_price: Optional[Decimal] = Field(None, description="当前价格")
    market_value: Optional[Decimal] = Field(None, description="市值")
    profit_loss: Optional[Decimal] = Field(None, description="盈亏金额")
    profit_loss_pct: Optional[Decimal] = Field(None, description="盈亏百分比")
    created_at: datetime = Field(..., description="建仓时间")
    updated_at: datetime = Field(..., description="更新时间")


class Order(BaseModel):
    """委托记录"""

    id: int = Field(..., description="订单 ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    order_type: str = Field(..., description="订单类型: buy/sell")
    quantity: int = Field(..., description="数量")
    price: Optional[Decimal] = Field(None, description="委托价格（市价为 None）")
    amount: Decimal = Field(..., description="金额")
    status: str = Field(..., description="订单状态: pending/filled/cancelled/failed")
    filled_quantity: int = Field(0, description="成交数量")
    filled_price: Optional[Decimal] = Field(None, description="成交价格")
    filled_amount: Optional[Decimal] = Field(None, description="成交金额")
    commission: Decimal = Field(0.0, description="佣金")
    stamp_duty: Decimal = Field(0.0, description="印花税（仅卖出）")
    transfer_fee: Decimal = Field(0.0, description="过户费（仅沪市）")
    total_fee: Decimal = Field(0.0, description="总手续费")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class Account(BaseModel):
    """账户信息"""

    total_balance: Decimal = Field(..., description="总资产")
    cash_balance: Decimal = Field(..., description="可用资金")
    market_value: Decimal = Field(..., description="持仓市值")
    profit_loss: Decimal = Field(..., description="总盈亏")
    profit_loss_pct: Decimal = Field(..., description="总盈亏百分比")


class PlaceOrderRequest(BaseModel):
    """下单请求"""

    stock_code: str = Field(..., description="股票代码")
    order_type: str = Field(..., description="订单类型: buy/sell")
    quantity: int = Field(..., gt=0, description="数量")
    price: Optional[Decimal] = Field(None, description="委托价格（市价为 None）")


class PlaceOrderResponse(BaseModel):
    """下单响应"""

    order_id: int = Field(..., description="订单 ID")
    status: str = Field(..., description="订单状态")
    message: str = Field(..., description="响应消息")


class PositionsResponse(BaseModel):
    """持仓列表响应"""

    positions: List[Position] = Field(default_factory=list, description="持仓列表")
    total: int = Field(..., description="总数量")


class OrdersResponse(BaseModel):
    """委托记录响应"""

    orders: List[Order] = Field(default_factory=list, description="委托记录列表")
    total: int = Field(..., description="总数量")


class AccountResponse(BaseModel):
    """账户信息响应"""

    account: Account = Field(..., description="账户信息")


class StopLoss(BaseModel):
    """止盈止损设置"""

    id: int = Field(..., description="ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    take_profit_price: Optional[Decimal] = Field(None, description="止盈价格")
    take_profit_pct: Optional[Decimal] = Field(None, description="止盈百分比（相对于成本价）")
    stop_loss_price: Optional[Decimal] = Field(None, description="止损价格")
    stop_loss_pct: Optional[Decimal] = Field(None, description="止损百分比（相对于成本价）")
    is_active: bool = Field(..., description="是否激活")
    triggered_type: Optional[str] = Field(None, description="触发类型: take_profit/stop_loss/not_triggered")
    triggered_at: Optional[datetime] = Field(None, description="触发时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class SetStopLossRequest(BaseModel):
    """设置止盈止损请求"""

    stock_code: str = Field(..., description="股票代码")
    take_profit_price: Optional[Decimal] = Field(None, description="止盈价格")
    take_profit_pct: Optional[Decimal] = Field(None, description="止盈百分比（相对于成本价）")
    stop_loss_price: Optional[Decimal] = Field(None, description="止损价格")
    stop_loss_pct: Optional[Decimal] = Field(None, description="止损百分比（相对于成本价）")


class SetStopLossResponse(BaseModel):
    """设置止盈止损响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    stop_loss: Optional[StopLoss] = Field(None, description="止盈止损设置")


class StopLossResponse(BaseModel):
    """止盈止损响应"""

    stop_loss: Optional[StopLoss] = Field(None, description="止盈止损设置")


class StopLossListResponse(BaseModel):
    """止盈止损列表响应"""

    stop_losses: List[StopLoss] = Field(default_factory=list, description="止盈止损列表")
    total: int = Field(..., description="总数量")


class DeleteStopLossResponse(BaseModel):
    """删除止盈止损响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")

class AccountHistory(BaseModel):
    """账户历史记录"""

    id: int = Field(..., description="记录 ID")
    total_balance: Decimal = Field(..., description="总资产")
    cash_balance: Decimal = Field(..., description="可用资金")
    market_value: Decimal = Field(..., description="持仓市值")
    profit_loss: Decimal = Field(..., description="总盈亏")
    profit_loss_pct: Decimal = Field(..., description="总盈亏百分比")
    daily_return_pct: Decimal = Field(..., description="日收益率")
    cumulative_return_pct: Decimal = Field(..., description="累计收益率")
    record_date: datetime = Field(..., description="记录日期")
    created_at: datetime = Field(..., description="创建时间")

class AccountHistoryResponse(BaseModel):
    """账户历史记录响应"""

    histories: List[AccountHistory] = Field(default_factory=list, description="历史记录列表")
    total: int = Field(..., description="总数量")

class PerformanceMetrics(BaseModel):
    """绩效指标"""

    total_return_pct: Decimal = Field(..., description="总收益率")
    annualized_return_pct: Decimal = Field(..., description="年化收益率")
    max_drawdown_pct: Decimal = Field(..., description="最大回撤")
    win_rate_pct: Decimal = Field(..., description="胜率")
    total_trades: int = Field(..., description="总交易次数")
    profitable_trades: int = Field(..., description="盈利交易次数")
    average_holding_days: Decimal = Field(..., description="平均持仓天数")

class PerformanceMetricsResponse(BaseModel):
    """绩效指标响应"""

    metrics: PerformanceMetrics = Field(..., description="绩效指标")
