# -*- coding: utf-8 -*-
"""Paper trading endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_database_manager
from api.v1.schemas.trading import (
    Account,
    AccountHistory,
    AccountHistoryResponse,
    AccountResponse,
    DeleteStopLossResponse,
    Order,
    OrdersResponse,
    PerformanceMetrics,
    PerformanceMetricsResponse,
    PlaceOrderRequest,
    PlaceOrderResponse,
    Position,
    PositionsResponse,
    SetStopLossRequest,
    SetStopLossResponse,
    StopLoss,
    StopLossListResponse,
    StopLossResponse,
)
from api.v1.schemas.common import ErrorResponse
from src.services.trading_service import TradingService
from src.storage import DatabaseManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/account",
    response_model=AccountResponse,
    responses={
        200: {"description": "账户信息"},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="获取账户信息",
    description="获取模拟交易账户的总资产、可用资金、持仓市值和盈亏信息",
)
def get_account(
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> AccountResponse:
    """
    获取模拟交易账户信息
    
    Returns:
        AccountResponse: 账户信息
    """
    try:
        service = TradingService(db_manager)
        account_data = service.get_account()
        return AccountResponse(account=Account(**account_data))
    except Exception as exc:
        logger.error(f"获取账户信息失败: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"获取账户信息失败: {str(exc)}"},
        )


@router.get(
    "/positions",
    response_model=PositionsResponse,
    responses={
        200: {"description": "持仓列表"},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="获取持仓列表",
    description="获取当前所有持仓信息",
)
def get_positions(
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> PositionsResponse:
    """
    获取持仓列表
    
    Returns:
        PositionsResponse: 持仓列表
    """
    try:
        service = TradingService(db_manager)
        positions_data = service.get_positions()
        positions = [Position(**pos) for pos in positions_data]
        return PositionsResponse(positions=positions, total=len(positions))
    except Exception as exc:
        logger.error(f"获取持仓列表失败: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"获取持仓列表失败: {str(exc)}"},
        )


@router.get(
    "/orders",
    response_model=OrdersResponse,
    responses={
        200: {"description": "委托记录"},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="获取委托记录",
    description="获取委托记录列表",
)
def get_orders(
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> OrdersResponse:
    """
    获取委托记录
    
    Args:
        limit: 返回数量限制
        
    Returns:
        OrdersResponse: 委托记录列表
    """
    try:
        service = TradingService(db_manager)
        orders_data = service.get_orders(limit=limit)
        orders = [Order(**order) for order in orders_data]
        return OrdersResponse(orders=orders, total=len(orders))
    except Exception as exc:
        logger.error(f"获取委托记录失败: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"获取委托记录失败: {str(exc)}"},
        )


@router.post(
    "/order",
    response_model=PlaceOrderResponse,
    responses={
        200: {"description": "下单成功"},
        400: {"description": "参数错误", "model": ErrorResponse},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="下单",
    description="提交买入或卖出订单",
)
def place_order(
    request: PlaceOrderRequest,
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> PlaceOrderResponse:
    """
    下单
    
    Args:
        request: 下单请求
        
    Returns:
        PlaceOrderResponse: 下单结果
    """
    try:
        service = TradingService(db_manager)
        result = service.place_order(
            stock_code=request.stock_code,
            order_type=request.order_type,
            quantity=request.quantity,
            price=float(request.price) if request.price else None,
        )
        return PlaceOrderResponse(**result)
    except Exception as exc:
        logger.error(f"下单失败: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"下单失败: {str(exc)}"},
        )


@router.post(
    "/stop-loss",
    response_model=SetStopLossResponse,
    responses={
        200: {"description": "设置成功"},
        400: {"description": "参数错误", "model": ErrorResponse},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="设置止盈止损",
    description="为持仓设置止盈止损条件",
)
def set_stop_loss(
    request: SetStopLossRequest,
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> SetStopLossResponse:
    """
    设置止盈止损
    
    Args:
        request: 设置请求
        
    Returns:
        SetStopLossResponse: 设置结果
    """
    try:
        service = TradingService(db_manager)
        result = service.set_stop_loss(
            stock_code=request.stock_code,
            take_profit_price=float(request.take_profit_price) if request.take_profit_price else None,
            take_profit_pct=float(request.take_profit_pct) if request.take_profit_pct else None,
            stop_loss_price=float(request.stop_loss_price) if request.stop_loss_price else None,
            stop_loss_pct=float(request.stop_loss_pct) if request.stop_loss_pct else None,
        )
        
        if result.get("success"):
            stop_loss_data = result.get("stop_loss")
            stop_loss = StopLoss(**stop_loss_data) if stop_loss_data else None
            return SetStopLossResponse(success=True, message=result.get("message", "设置成功"), stop_loss=stop_loss)
        else:
            return SetStopLossResponse(success=False, message=result.get("message", "设置失败"), stop_loss=None)
    except Exception as exc:
        logger.error(f"设置止盈止损失败: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"设置止盈止损失败: {str(exc)}"},
        )


@router.get(
    "/stop-loss/{stock_code}",
    response_model=StopLossResponse,
    responses={
        200: {"description": "获取成功"},
        404: {"description": "未找到"},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="获取止盈止损",
    description="获取指定股票的止盈止损设置",
)
def get_stop_loss(
    stock_code: str,
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> StopLossResponse:
    """
    获取止盈止损
    
    Args:
        stock_code: 股票代码
        
    Returns:
        StopLossResponse: 止盈止损设置
    """
    try:
        service = TradingService(db_manager)
        stop_loss_data = service.get_stop_loss(stock_code)
        stop_loss = StopLoss(**stop_loss_data) if stop_loss_data else None
        return StopLossResponse(stop_loss=stop_loss)
    except Exception as exc:
        logger.error(f"获取止盈止损失败: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"获取止盈止损失败: {str(exc)}"},
        )


@router.get(
    "/stop-loss",
    response_model=StopLossListResponse,
    responses={
        200: {"description": "获取成功"},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="获取所有止盈止损",
    description="获取所有止盈止损设置",
)
def get_all_stop_loss(
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> StopLossListResponse:
    """
    获取所有止盈止损
    
    Returns:
        StopLossListResponse: 止盈止损列表
    """
    try:
        service = TradingService(db_manager)
        stop_losses_data = service.get_all_stop_loss()
        stop_losses = [StopLoss(**sl) for sl in stop_losses_data]
        return StopLossListResponse(stop_losses=stop_losses, total=len(stop_losses))
    except Exception as exc:
        logger.error(f"获取止盈止损列表失败: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"获取止盈止损列表失败: {str(exc)}"},
        )


@router.delete(
    "/stop-loss/{stock_code}",
    response_model=DeleteStopLossResponse,
    responses={
        200: {"description": "删除成功"},
        404: {"description": "未找到"},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="删除止盈止损",
    description="删除指定股票的止盈止损设置",
)
def delete_stop_loss(
    stock_code: str,
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> DeleteStopLossResponse:
    """
    删除止盈止损
    
    Args:
        stock_code: 股票代码
        
    Returns:
        DeleteStopLossResponse: 删除结果
    """
    try:
        service = TradingService(db_manager)
        result = service.delete_stop_loss(stock_code)
        return DeleteStopLossResponse(**result)
    except Exception as exc:
        logger.error(f"删除止盈止损失败: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"删除止盈止损失败: {str(exc)}"},
        )

@router.get(
    "/account-history",
    response_model=AccountHistoryResponse,
    responses={
        200: {"description": "获取成功"},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="获取账户历史记录",
    description="获取账户历史记录，用于绘制收益率曲线",
)
def get_account_history(
    days: int = Query(30, ge=1, le=365, description="返回天数限制"),
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> AccountHistoryResponse:
    """
    获取账户历史记录
    
    Args:
        days: 返回天数限制
        
    Returns:
        AccountHistoryResponse: 账户历史记录列表
    """
    try:
        service = TradingService(db_manager)
        histories_data = service.get_account_history(days=days)
        histories = [AccountHistory(**h) for h in histories_data]
        return AccountHistoryResponse(histories=histories, total=len(histories))
    except Exception as exc:
        logger.error(f"获取账户历史记录失败: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"获取账户历史记录失败: {str(exc)}"},
        )

@router.get(
    "/performance-metrics",
    response_model=PerformanceMetricsResponse,
    responses={
        200: {"description": "获取成功"},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="获取绩效指标",
    description="获取账户绩效指标，包括总收益率、年化收益率、最大回撤、胜率等",
)
def get_performance_metrics(
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> PerformanceMetricsResponse:
    """
    获取绩效指标
    
    Returns:
        PerformanceMetricsResponse: 绩效指标
    """
    try:
        service = TradingService(db_manager)
        metrics_data = service.get_performance_metrics()
        metrics = PerformanceMetrics(**metrics_data)
        return PerformanceMetricsResponse(metrics=metrics)
    except Exception as exc:
        logger.error(f"获取绩效指标失败: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"获取绩效指标失败: {str(exc)}"},
        )
