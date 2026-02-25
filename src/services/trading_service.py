# -*- coding: utf-8 -*-
"""
===================================
模拟交易服务层
===================================

职责：
1. 封装模拟交易业务逻辑
2. 处理买入/卖出订单
3. 管理持仓和账户信息
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from src.storage import DatabaseManager, TradingPosition, TradingOrder, TradingAccount, TradingStopLoss, TradingAccountHistory
from src.services.stock_service import StockService

logger = logging.getLogger(__name__)


class TradingService:
    """
    模拟交易服务
    
    封装模拟交易的业务逻辑，包括下单、持仓管理、账户管理等
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化模拟交易服务
        
        Args:
            db_manager: 数据库管理器（可选，默认使用单例）
        """
        self.db = db_manager or DatabaseManager.get_instance()
        self.stock_service = StockService()
        
        # A股手续费配置
        self.commission_rate = 0.0003  # 佣金率：万分之3
        self.commission_min = 5.0  # 佣金最低：5元
        self.stamp_duty_rate = 0.001  # 印花税率：千分之一（仅卖出）
        self.transfer_fee_rate = 0.0001  # 过户费率：万分之一（仅沪市）
    
    def _calculate_fees(
        self,
        stock_code: str,
        order_type: str,
        amount: float
    ) -> Dict[str, float]:
        """
        计算交易手续费
        
        Args:
            stock_code: 股票代码
            order_type: 订单类型 (buy/sell)
            amount: 交易金额
            
        Returns:
            手续费字典
        """
        # 计算佣金
        commission = amount * self.commission_rate
        commission = max(commission, self.commission_min)  # 最低5元
        
        # 计算印花税（仅卖出）
        stamp_duty = 0.0
        if order_type == "sell":
            stamp_duty = amount * self.stamp_duty_rate
        
        # 计算过户费（仅沪市：6开头）
        transfer_fee = 0.0
        if stock_code.startswith("6"):
            transfer_fee = amount * self.transfer_fee_rate
        
        # 总手续费
        total_fee = commission + stamp_duty + transfer_fee
        
        return {
            "commission": commission,
            "stamp_duty": stamp_duty,
            "transfer_fee": transfer_fee,
            "total_fee": total_fee,
        }
    
    def _get_or_create_account(self, session: Session) -> TradingAccount:
        """
        获取或创建账户
        
        Args:
            session: 数据库会话
            
        Returns:
            TradingAccount: 账户对象
        """
        account = session.execute(
            select(TradingAccount).order_by(TradingAccount.id.desc())
        ).scalar_one_or_none()
        
        if account is None:
            account = TradingAccount(
                total_balance=1000000.0,
                cash_balance=1000000.0,
                market_value=0.0,
                profit_loss=0.0,
                profit_loss_pct=0.0,
            )
            session.add(account)
            session.flush()
        
        return account
    
    def _update_account(self, session: Session, account: TradingAccount) -> None:
        """
        更新账户信息
        
        Args:
            session: 数据库会话
            account: 账户对象
        """
        # 计算持仓市值
        positions = session.execute(
            select(TradingPosition)
        ).scalars().all()
        
        market_value = sum(p.market_value or 0.0 for p in positions)
        account.market_value = market_value
        account.total_balance = account.cash_balance + market_value
        
        # 计算盈亏
        initial_balance = 1000000.0
        account.profit_loss = account.total_balance - initial_balance
        account.profit_loss_pct = (account.profit_loss / initial_balance * 100) if initial_balance > 0 else 0.0
        
        account.updated_at = datetime.now()
    
    def _update_position_price(self, session: Session, position: TradingPosition) -> None:
        """
        更新持仓的当前价格和盈亏
        
        Args:
            session: 数据库会话
            position: 持仓对象
        """
        quote = self.stock_service.get_realtime_quote(position.stock_code)
        
        if quote and quote.get("current_price"):
            current_price = float(quote["current_price"])
            position.current_price = current_price
            position.market_value = position.quantity * current_price
            position.profit_loss = (current_price - position.avg_cost) * position.quantity
            position.profit_loss_pct = ((current_price - position.avg_cost) / position.avg_cost * 100) if position.avg_cost > 0 else 0.0
            position.updated_at = datetime.now()
    
    def get_account(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            账户信息字典
        """
        with self.db.get_session() as session:
            account = self._get_or_create_account(session)
            self._update_account(session, session.merge(account))
            session.commit()
            
            return {
                "total_balance": float(account.total_balance),
                "cash_balance": float(account.cash_balance),
                "market_value": float(account.market_value),
                "profit_loss": float(account.profit_loss),
                "profit_loss_pct": float(account.profit_loss_pct),
            }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        获取持仓列表
        
        Returns:
            持仓列表
        """
        with self.db.get_session() as session:
            positions = session.execute(
                select(TradingPosition)
            ).scalars().all()
            
            result = []
            for pos in positions:
                self._update_position_price(session, pos)
                result.append({
                    "id": pos.id,
                    "stock_code": pos.stock_code,
                    "stock_name": pos.stock_name,
                    "quantity": pos.quantity,
                    "avg_cost": float(pos.avg_cost),
                    "current_price": float(pos.current_price) if pos.current_price else None,
                    "market_value": float(pos.market_value) if pos.market_value else None,
                    "profit_loss": float(pos.profit_loss) if pos.profit_loss else None,
                    "profit_loss_pct": float(pos.profit_loss_pct) if pos.profit_loss_pct else None,
                    "created_at": pos.created_at.isoformat() if pos.created_at else None,
                    "updated_at": pos.updated_at.isoformat() if pos.updated_at else None,
                })
            
            session.commit()
            return result
    
    def get_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取委托记录
        
        Args:
            limit: 返回数量限制
            
        Returns:
            委托记录列表
        """
        with self.db.get_session() as session:
            orders = session.execute(
                select(TradingOrder)
                .order_by(TradingOrder.created_at.desc())
                .limit(limit)
            ).scalars().all()
            
            return [
                {
                    "id": order.id,
                    "stock_code": order.stock_code,
                    "stock_name": order.stock_name,
                    "order_type": order.order_type,
                    "quantity": order.quantity,
                    "price": float(order.price) if order.price else None,
                    "amount": float(order.amount),
                    "status": order.status,
                    "filled_quantity": order.filled_quantity,
                    "filled_price": float(order.filled_price) if order.filled_price else None,
                    "filled_amount": float(order.filled_amount) if order.filled_amount else None,
                    "commission": float(order.commission) if order.commission else 0.0,
                    "stamp_duty": float(order.stamp_duty) if order.stamp_duty else 0.0,
                    "transfer_fee": float(order.transfer_fee) if order.transfer_fee else 0.0,
                    "total_fee": float(order.total_fee) if order.total_fee else 0.0,
                    "error_message": order.error_message,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                }
                for order in orders
            ]
    
    def place_order(
        self,
        stock_code: str,
        order_type: str,
        quantity: int,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        下单
        
        Args:
            stock_code: 股票代码
            order_type: 订单类型 (buy/sell)
            quantity: 数量
            price: 委托价格（市价为 None）
            
        Returns:
            下单结果
        """
        with self.db.get_session() as session:
            # 获取实时行情
            quote = self.stock_service.get_realtime_quote(stock_code)
            
            if quote is None or not quote.get("current_price"):
                return {
                    "order_id": 0,
                    "status": "failed",
                    "message": f"无法获取股票 {stock_code} 的实时行情"
                }
            
            current_price = float(quote["current_price"])
            stock_name = quote.get("stock_name", f"股票{stock_code}")
            
            # 使用市价或委托价
            execution_price = price if price is not None else current_price
            amount = execution_price * quantity
            
            # 获取账户
            account = self._get_or_create_account(session)
            
            # 验证订单
            if order_type == "buy":
                if account.cash_balance < amount:
                    return {
                        "order_id": 0,
                        "status": "failed",
                        "message": f"可用资金不足，需要 ¥{amount:.2f}，当前 ¥{account.cash_balance:.2f}"
                    }
            elif order_type == "sell":
                position = session.execute(
                    select(TradingPosition).where(TradingPosition.stock_code == stock_code)
                ).scalar_one_or_none()
                
                if position is None or position.quantity < quantity:
                    return {
                        "order_id": 0,
                        "status": "failed",
                        "message": f"持仓不足，需要 {quantity} 股，当前 {position.quantity if position else 0} 股"
                    }
            else:
                return {
                    "order_id": 0,
                    "status": "failed",
                    "message": f"无效的订单类型: {order_type}"
                }
            
            # 计算手续费
            fees = self._calculate_fees(stock_code, order_type, amount)
            
            # 创建订单
            order = TradingOrder(
                stock_code=stock_code,
                stock_name=stock_name,
                order_type=order_type,
                quantity=quantity,
                price=price,
                amount=amount,
                status="filled",
                filled_quantity=quantity,
                filled_price=execution_price,
                filled_amount=amount,
                commission=fees["commission"],
                stamp_duty=fees["stamp_duty"],
                transfer_fee=fees["transfer_fee"],
                total_fee=fees["total_fee"],
            )
            session.add(order)
            session.flush()
            
            # 执行订单
            if order_type == "buy":
                # 计算总成本（包含手续费）
                total_cost = amount + fees["total_fee"]
                
                # 扣除资金（包含手续费）
                account.cash_balance -= total_cost
                
                # 更新或创建持仓
                position = session.execute(
                    select(TradingPosition).where(TradingPosition.stock_code == stock_code)
                ).scalar_one_or_none()
                
                if position is None:
                    # 新建持仓，平均成本包含手续费
                    avg_cost_with_fee = total_cost / quantity
                    position = TradingPosition(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        quantity=quantity,
                        avg_cost=avg_cost_with_fee,
                        current_price=current_price,
                        market_value=quantity * current_price,
                        profit_loss=0.0,
                        profit_loss_pct=0.0,
                    )
                    session.add(position)
                else:
                    # 计算新的平均成本（包含手续费）
                    total_cost_existing = position.avg_cost * position.quantity
                    new_total_cost = total_cost_existing + total_cost
                    total_quantity = position.quantity + quantity
                    position.avg_cost = new_total_cost / total_quantity
                    position.quantity = total_quantity
                    self._update_position_price(session, position)
                
            elif order_type == "sell":
                # 计算实际到账金额（扣除手续费）
                actual_amount = amount - fees["total_fee"]
                
                # 增加资金（扣除手续费后）
                account.cash_balance += actual_amount
                
                # 更新持仓
                position = session.execute(
                    select(TradingPosition).where(TradingPosition.stock_code == stock_code)
                ).scalar_one_or_none()
                
                if position:
                    position.quantity -= quantity
                    if position.quantity == 0:
                        session.delete(position)
                    else:
                        self._update_position_price(session, position)
            
            # 更新账户
            self._update_account(session, account)
            
            session.commit()
            
            return {
                "order_id": order.id,
                "status": "filled",
                "message": f"{order_type == 'buy' and '买入' or '卖出'}成功，成交价 ¥{execution_price:.2f}"
            }
    
    def set_stop_loss(
        self,
        stock_code: str,
        take_profit_price: Optional[float] = None,
        take_profit_pct: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        stop_loss_pct: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        设置止盈止损
        
        Args:
            stock_code: 股票代码
            take_profit_price: 止盈价格
            take_profit_pct: 止盈百分比（相对于成本价）
            stop_loss_price: 止损价格
            stop_loss_pct: 止损百分比（相对于成本价）
            
        Returns:
            设置结果
        """
        with self.db.get_session() as session:
            # 检查持仓是否存在
            position = session.execute(
                select(TradingPosition).where(TradingPosition.stock_code == stock_code)
            ).scalar_one_or_none()
            
            if position is None:
                return {
                    "success": False,
                    "message": f"股票 {stock_code} 没有持仓，无法设置止盈止损"
                }
            
            # 获取股票名称
            stock_name = position.stock_name
            
            # 计算止盈止损价格
            if take_profit_pct is not None:
                take_profit_price = position.avg_cost * (1 + take_profit_pct / 100)
            
            if stop_loss_pct is not None:
                stop_loss_price = position.avg_cost * (1 - stop_loss_pct / 100)
            
            # 检查是否已有设置
            stop_loss = session.execute(
                select(TradingStopLoss).where(TradingStopLoss.stock_code == stock_code)
            ).scalar_one_or_none()
            
            if stop_loss is None:
                # 创建新的止盈止损设置
                stop_loss = TradingStopLoss(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    take_profit_price=take_profit_price,
                    take_profit_pct=take_profit_pct,
                    stop_loss_price=stop_loss_price,
                    stop_loss_pct=stop_loss_pct,
                    is_active=True,
                    triggered_type="not_triggered",
                    position_id=position.id,
                )
                session.add(stop_loss)
            else:
                # 更新现有设置
                stop_loss.stock_name = stock_name
                stop_loss.take_profit_price = take_profit_price
                stop_loss.take_profit_pct = take_profit_pct
                stop_loss.stop_loss_price = stop_loss_price
                stop_loss.stop_loss_pct = stop_loss_pct
                stop_loss.is_active = True
                stop_loss.triggered_type = "not_triggered"
                stop_loss.triggered_at = None
                stop_loss.position_id = position.id
                stop_loss.updated_at = datetime.now()
            
            session.commit()
            
            return {
                "success": True,
                "message": "止盈止损设置成功",
                "stop_loss": {
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "take_profit_price": float(take_profit_price) if take_profit_price else None,
                    "take_profit_pct": take_profit_pct,
                    "stop_loss_price": float(stop_loss_price) if stop_loss_price else None,
                    "stop_loss_pct": stop_loss_pct,
                }
            }
    
    def get_stop_loss(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取止盈止损设置
        
        Args:
            stock_code: 股票代码
            
        Returns:
            止盈止损设置
        """
        with self.db.get_session() as session:
            stop_loss = session.execute(
                select(TradingStopLoss).where(TradingStopLoss.stock_code == stock_code)
            ).scalar_one_or_none()
            
            if stop_loss is None:
                return None
            
            return {
                "id": stop_loss.id,
                "stock_code": stop_loss.stock_code,
                "stock_name": stop_loss.stock_name,
                "take_profit_price": float(stop_loss.take_profit_price) if stop_loss.take_profit_price else None,
                "take_profit_pct": float(stop_loss.take_profit_pct) if stop_loss.take_profit_pct else None,
                "stop_loss_price": float(stop_loss.stop_loss_price) if stop_loss.stop_loss_price else None,
                "stop_loss_pct": float(stop_loss.stop_loss_pct) if stop_loss.stop_loss_pct else None,
                "is_active": stop_loss.is_active,
                "triggered_type": stop_loss.triggered_type,
                "triggered_at": stop_loss.triggered_at.isoformat() if stop_loss.triggered_at else None,
                "created_at": stop_loss.created_at.isoformat() if stop_loss.created_at else None,
                "updated_at": stop_loss.updated_at.isoformat() if stop_loss.updated_at else None,
            }
    
    def get_all_stop_loss(self) -> List[Dict[str, Any]]:
        """
        获取所有止盈止损设置
        
        Returns:
            止盈止损设置列表
        """
        with self.db.get_session() as session:
            stop_losses = session.execute(
                select(TradingStopLoss).where(TradingStopLoss.is_active == True)
            ).scalars().all()
            
            return [
                {
                    "id": sl.id,
                    "stock_code": sl.stock_code,
                    "stock_name": sl.stock_name,
                    "take_profit_price": float(sl.take_profit_price) if sl.take_profit_price else None,
                    "take_profit_pct": float(sl.take_profit_pct) if sl.take_profit_pct else None,
                    "stop_loss_price": float(sl.stop_loss_price) if sl.stop_loss_price else None,
                    "stop_loss_pct": float(sl.stop_loss_pct) if sl.stop_loss_pct else None,
                    "is_active": sl.is_active,
                    "triggered_type": sl.triggered_type,
                    "triggered_at": sl.triggered_at.isoformat() if sl.triggered_at else None,
                    "created_at": sl.created_at.isoformat() if sl.created_at else None,
                    "updated_at": sl.updated_at.isoformat() if sl.updated_at else None,
                }
                for sl in stop_losses
            ]
    
    def check_and_trigger_stop_loss(self) -> List[Dict[str, Any]]:
        """
        检查并触发止盈止损
        
        Returns:
            触发的止盈止损列表
        """
        triggered = []
        
        with self.db.get_session() as session:
            # 获取所有激活的止盈止损设置
            stop_losses = session.execute(
                select(TradingStopLoss).where(TradingStopLoss.is_active == True)
            ).scalars().all()
            
            for sl in stop_losses:
                # 获取持仓
                position = session.execute(
                    select(TradingPosition).where(TradingPosition.stock_code == sl.stock_code)
                ).scalar_one_or_none()
                
                if position is None:
                    # 持仓不存在，停用止盈止损
                    sl.is_active = False
                    continue
                
                # 获取实时行情
                quote = self.stock_service.get_realtime_quote(sl.stock_code)
                
                if quote is None or not quote.get("current_price"):
                    continue
                
                current_price = float(quote["current_price"])
                trigger_type = None
                
                # 检查止盈
                if sl.take_profit_price and current_price >= sl.take_profit_price:
                    trigger_type = "take_profit"
                    logger.info(
                        f"触发止盈: {sl.stock_code}, "
                        f"当前价 ¥{current_price:.2f} >= 止盈价 ¥{sl.take_profit_price:.2f}"
                    )
                
                # 检查止损
                elif sl.stop_loss_price and current_price <= sl.stop_loss_price:
                    trigger_type = "stop_loss"
                    logger.info(
                        f"触发止损: {sl.stock_code}, "
                        f"当前价 ¥{current_price:.2f} <= 止损价 ¥{sl.stop_loss_price:.2f}"
                    )
                
                # 触发卖出
                if trigger_type:
                    # 执行卖出
                    result = self.place_order(
                        stock_code=sl.stock_code,
                        order_type="sell",
                        quantity=position.quantity,
                        price=current_price,
                    )
                    
                    if result.get("status") == "filled":
                        # 更新止盈止损状态
                        sl.is_active = False
                        sl.triggered_type = trigger_type
                        sl.triggered_at = datetime.now()
                        sl.updated_at = datetime.now()
                        
                        triggered.append({
                            "stock_code": sl.stock_code,
                            "stock_name": sl.stock_name,
                            "trigger_type": trigger_type,
                            "trigger_price": current_price,
                            "quantity": position.quantity,
                            "order_id": result.get("order_id"),
                        })
            
            session.commit()
        
        return triggered
    
    def delete_stop_loss(self, stock_code: str) -> Dict[str, Any]:
        """
        删除止盈止损设置
        
        Args:
            stock_code: 股票代码
            
        Returns:
            删除结果
        """
        with self.db.get_session() as session:
            stop_loss = session.execute(
                select(TradingStopLoss).where(TradingStopLoss.stock_code == stock_code)
            ).scalar_one_or_none()
            
            if stop_loss is None:
                return {
                    "success": False,
                    "message": f"股票 {stock_code} 没有止盈止损设置"
                }
            
            session.delete(stop_loss)
            session.commit()
            
            return {
                "success": True,
                "message": "止盈止损设置已删除"
            }
    
    def _calculate_holding_days(self, position: TradingPosition) -> int:
        """
        计算持仓天数
        
        Args:
            position: 持仓对象
            
        Returns:
            持仓天数
        """
        if position.created_at is None:
            return 0
        
        created_date = position.created_at.date()
        current_date = datetime.now().date()
        holding_days = (current_date - created_date).days
        return max(0, holding_days)
    
    def get_positions_with_holding_days(self) -> List[Dict[str, Any]]:
        """
        获取持仓列表（包含持仓天数）
        
        Returns:
            持仓列表（包含持仓天数）
        """
        with self.db.get_session() as session:
            positions = session.execute(
                select(TradingPosition)
            ).scalars().all()
            
            result = []
            for pos in positions:
                self._update_position_price(session, pos)
                holding_days = self._calculate_holding_days(pos)
                result.append({
                    "id": pos.id,
                    "stock_code": pos.stock_code,
                    "stock_name": pos.stock_name,
                    "quantity": pos.quantity,
                    "avg_cost": float(pos.avg_cost),
                    "current_price": float(pos.current_price) if pos.current_price else None,
                    "market_value": float(pos.market_value) if pos.market_value else None,
                    "profit_loss": float(pos.profit_loss) if pos.profit_loss else None,
                    "profit_loss_pct": float(pos.profit_loss_pct) if pos.profit_loss_pct else None,
                    "holding_days": holding_days,
                    "created_at": pos.created_at.isoformat() if pos.created_at else None,
                    "updated_at": pos.updated_at.isoformat() if pos.updated_at else None,
                })
            
            session.commit()
            return result
    
    def record_account_history(self) -> Dict[str, Any]:
        """
        记录账户历史快照
        
        Returns:
            记录结果
        """
        with self.db.get_session() as session:
            # 获取当前账户信息
            account = self._get_or_create_account(session)
            self._update_account(session, account)
            
            # 获取当前日期
            current_date = datetime.now().date()
            
            # 检查今日是否已有记录
            existing_history = session.execute(
                select(TradingAccountHistory).where(TradingAccountHistory.record_date == current_date)
            ).scalar_one_or_none()
            
            # 获取前一交易日的记录
            previous_history = session.execute(
                select(TradingAccountHistory)
                .where(TradingAccountHistory.record_date < current_date)
                .order_by(TradingAccountHistory.record_date.desc())
                .limit(1)
            ).scalar_one_or_none()
            
            # 计算日收益率
            daily_return_pct = 0.0
            if previous_history:
                if previous_history.total_balance > 0:
                    daily_return_pct = ((account.total_balance - previous_history.total_balance) / previous_history.total_balance) * 100
            
            # 计算累计收益率（相对于初始资金）
            initial_balance = 1000000.0
            cumulative_return_pct = ((account.total_balance - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0.0
            
            if existing_history is None:
                # 创建新记录
                history = TradingAccountHistory(
                    total_balance=float(account.total_balance),
                    cash_balance=float(account.cash_balance),
                    market_value=float(account.market_value),
                    profit_loss=float(account.profit_loss),
                    profit_loss_pct=float(account.profit_loss_pct),
                    daily_return_pct=daily_return_pct,
                    cumulative_return_pct=cumulative_return_pct,
                    record_date=current_date,
                )
                session.add(history)
            else:
                # 更新现有记录
                existing_history.total_balance = float(account.total_balance)
                existing_history.cash_balance = float(account.cash_balance)
                existing_history.market_value = float(account.market_value)
                existing_history.profit_loss = float(account.profit_loss)
                existing_history.profit_loss_pct = float(account.profit_loss_pct)
                existing_history.daily_return_pct = daily_return_pct
                existing_history.cumulative_return_pct = cumulative_return_pct
            
            session.commit()
            
            return {
                "success": True,
                "message": "账户历史记录已更新",
                "record_date": current_date.isoformat(),
                "total_balance": float(account.total_balance),
                "daily_return_pct": daily_return_pct,
                "cumulative_return_pct": cumulative_return_pct,
            }
    
    def get_account_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取账户历史记录（用于收益率曲线）
        
        Args:
            days: 返回天数限制
            
        Returns:
            账户历史记录列表
        """
        with self.db.get_session() as session:
            # 计算起始日期
            start_date = (datetime.now() - timedelta(days=days)).date()
            
            # 查询历史记录
            histories = session.execute(
                select(TradingAccountHistory)
                .where(TradingAccountHistory.record_date >= start_date)
                .order_by(TradingAccountHistory.record_date.asc())
            ).scalars().all()
            
            return [
                {
                    "id": h.id,
                    "total_balance": float(h.total_balance),
                    "cash_balance": float(h.cash_balance),
                    "market_value": float(h.market_value),
                    "profit_loss": float(h.profit_loss),
                    "profit_loss_pct": float(h.profit_loss_pct),
                    "daily_return_pct": float(h.daily_return_pct) if h.daily_return_pct else 0.0,
                    "cumulative_return_pct": float(h.cumulative_return_pct) if h.cumulative_return_pct else 0.0,
                    "record_date": h.record_date.isoformat(),
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in histories
            ]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取绩效指标
        
        Returns:
            绩效指标字典
        """
        with self.db.get_session() as session:
            # 获取所有历史记录
            histories = session.execute(
                select(TradingAccountHistory)
                .order_by(TradingAccountHistory.record_date.asc())
            ).scalars().all()
            
            if len(histories) < 2:
                return {
                    "total_return_pct": 0.0,
                    "annualized_return_pct": 0.0,
                    "max_drawdown_pct": 0.0,
                    "win_rate_pct": 0.0,
                    "total_trades": 0,
                    "profitable_trades": 0,
                    "average_holding_days": 0.0,
                }
            
            # 计算总收益率
            initial_balance = histories[0].total_balance
            current_balance = histories[-1].total_balance
            total_return_pct = ((current_balance - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0.0
            
            # 计算年化收益率
            days_count = len(histories)
            annualized_return_pct = 0.0
            if days_count > 0 and initial_balance > 0:
                annualized_return_pct = ((current_balance / initial_balance) ** (365.0 / days_count) - 1) * 100
            
            # 计算最大回撤
            max_balance = initial_balance
            max_drawdown = 0.0
            for h in histories:
                if h.total_balance > max_balance:
                    max_balance = h.total_balance
                drawdown = (max_balance - h.total_balance) / max_balance * 100 if max_balance > 0 else 0.0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # 获取交易统计
            orders = session.execute(
                select(TradingOrder).where(TradingOrder.status == "filled")
            ).scalars().all()
            
            total_trades = len(orders)
            
            # 计算盈利交易数（简化版：卖出订单的盈亏）
            profitable_trades = 0
            total_holding_days = 0
            position_count = 0
            
            positions = session.execute(
                select(TradingPosition)
            ).scalars().all()
            
            for pos in positions:
                holding_days = self._calculate_holding_days(pos)
                total_holding_days += holding_days
                position_count += 1
                if pos.profit_loss and pos.profit_loss > 0:
                    profitable_trades += 1
            
            # 计算胜率
            win_rate_pct = (profitable_trades / position_count * 100) if position_count > 0 else 0.0
            
            # 计算平均持仓天数
            average_holding_days = (total_holding_days / position_count) if position_count > 0 else 0.0
            
            return {
                "total_return_pct": total_return_pct,
                "annualized_return_pct": annualized_return_pct,
                "max_drawdown_pct": max_drawdown,
                "win_rate_pct": win_rate_pct,
                "total_trades": total_trades,
                "profitable_trades": profitable_trades,
                "average_holding_days": average_holding_days,
            }
