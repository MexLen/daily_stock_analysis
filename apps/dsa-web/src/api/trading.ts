import apiClient from './index';
import { toCamelCase } from './utils';

// ============ Type Definitions ============

export interface Account {
  totalBalance: number;
  cashBalance: number;
  marketValue: number;
  profitLoss: number;
  profitLossPct: number;
}

export interface Position {
  id: number;
  stockCode: string;
  stockName: string | null;
  quantity: number;
  avgCost: number;
  currentPrice: number | null;
  marketValue: number | null;
  profitLoss: number | null;
  profitLossPct: number | null;
  holdingDays: number;
  createdAt: string | null;
  updatedAt: string | null;
}

export interface Order {
  id: number;
  stockCode: string;
  stockName: string | null;
  orderType: string;
  quantity: number;
  price: number | null;
  amount: number;
  status: string;
  filledQuantity: number;
  filledPrice: number | null;
  filledAmount: number | null;
  commission: number;
  stampDuty: number;
  transferFee: number;
  totalFee: number;
  errorMessage: string | null;
  createdAt: string | null;
  updatedAt: string | null;
}

export interface PlaceOrderRequest {
  stockCode: string;
  orderType: 'buy' | 'sell';
  quantity: number;
  price?: number;
}

export interface PlaceOrderResponse {
  orderId: number;
  status: string;
  message: string;
}

export interface AccountResponse {
  account: Account;
}

export interface PositionsResponse {
  positions: Position[];
  total: number;
}

export interface OrdersResponse {
  orders: Order[];
  total: number;
}

export interface StopLoss {
  id: number;
  stockCode: string;
  stockName: string | null;
  takeProfitPrice: number | null;
  takeProfitPct: number | null;
  stopLossPrice: number | null;
  stopLossPct: number | null;
  isActive: boolean;
  triggeredType: string | null;
  triggeredAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
}

export interface SetStopLossRequest {
  stockCode: string;
  takeProfitPrice?: number;
  takeProfitPct?: number;
  stopLossPrice?: number;
  stopLossPct?: number;
}

export interface SetStopLossResponse {
  success: boolean;
  message: string;
  stopLoss: StopLoss | null;
}

export interface StopLossResponse {
  stopLoss: StopLoss | null;
}

export interface StopLossListResponse {
  stopLosses: StopLoss[];
  total: number;
}

export interface DeleteStopLossResponse {
  success: boolean;
  message: string;
}

export interface AccountHistory {
  id: number;
  totalBalance: number;
  cashBalance: number;
  marketValue: number;
  profitLoss: number;
  profitLossPct: number;
  dailyReturnPct: number;
  cumulativeReturnPct: number;
  recordDate: string;
  createdAt: string | null;
}

export interface AccountHistoryResponse {
  histories: AccountHistory[];
  total: number;
}

export interface PerformanceMetrics {
  totalReturnPct: number;
  annualizedReturnPct: number;
  maxDrawdownPct: number;
  winRatePct: number;
  totalTrades: number;
  profitableTrades: number;
  averageHoldingDays: number;
}

export interface PerformanceMetricsResponse {
  metrics: PerformanceMetrics;
}

// ============ API ============

export const tradingApi = {
  /**
   * Get account information
   */
  getAccount: async (): Promise<Account> => {
    const response = await apiClient.get<Record<string, unknown>>(
      '/api/v1/trading/account',
    );
    const data = toCamelCase<AccountResponse>(response.data);
    return data.account;
  },

  /**
   * Get positions list
   */
  getPositions: async (): Promise<Position[]> => {
    const response = await apiClient.get<Record<string, unknown>>(
      '/api/v1/trading/positions',
    );
    const data = toCamelCase<PositionsResponse>(response.data);
    return data.positions;
  },

  /**
   * Get orders list
   */
  getOrders: async (limit: number = 50): Promise<Order[]> => {
    const response = await apiClient.get<Record<string, unknown>>(
      '/api/v1/trading/orders',
      { params: { limit } },
    );
    const data = toCamelCase<OrdersResponse>(response.data);
    return data.orders;
  },

  /**
   * Place order
   */
  placeOrder: async (request: PlaceOrderRequest): Promise<PlaceOrderResponse> => {
    const requestData: Record<string, unknown> = {
      stock_code: request.stockCode,
      order_type: request.orderType,
      quantity: request.quantity,
    };
    if (request.price !== undefined) {
      requestData.price = request.price;
    }

    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/trading/order',
      requestData,
    );
    return toCamelCase<PlaceOrderResponse>(response.data);
  },

  /**
   * Set stop loss / take profit
   */
  setStopLoss: async (request: SetStopLossRequest): Promise<SetStopLossResponse> => {
    const requestData: Record<string, unknown> = {
      stock_code: request.stockCode,
    };
    if (request.takeProfitPrice !== undefined) {
      requestData.take_profit_price = request.takeProfitPrice;
    }
    if (request.takeProfitPct !== undefined) {
      requestData.take_profit_pct = request.takeProfitPct;
    }
    if (request.stopLossPrice !== undefined) {
      requestData.stop_loss_price = request.stopLossPrice;
    }
    if (request.stopLossPct !== undefined) {
      requestData.stop_loss_pct = request.stopLossPct;
    }

    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/trading/stop-loss',
      requestData,
    );
    return toCamelCase<SetStopLossResponse>(response.data);
  },

  /**
   * Get stop loss / take profit for a stock
   */
  getStopLoss: async (stockCode: string): Promise<StopLoss | null> => {
    const response = await apiClient.get<Record<string, unknown>>(
      `/api/v1/trading/stop-loss/${stockCode}`,
    );
    const data = toCamelCase<StopLossResponse>(response.data);
    return data.stopLoss;
  },

  /**
   * Get all stop loss / take profit settings
   */
  getAllStopLoss: async (): Promise<StopLoss[]> => {
    const response = await apiClient.get<Record<string, unknown>>(
      '/api/v1/trading/stop-loss',
    );
    const data = toCamelCase<StopLossListResponse>(response.data);
    return data.stopLosses;
  },

  /**
   * Delete stop loss / take profit
   */
  deleteStopLoss: async (stockCode: string): Promise<DeleteStopLossResponse> => {
    const response = await apiClient.delete<Record<string, unknown>>(
      `/api/v1/trading/stop-loss/${stockCode}`,
    );
    return toCamelCase<DeleteStopLossResponse>(response.data);
  },

  /**
   * Get account history for return rate curve
   */
  getAccountHistory: async (days: number = 30): Promise<AccountHistory[]> => {
    const response = await apiClient.get<Record<string, unknown>>(
      '/api/v1/trading/account-history',
      { params: { days } },
    );
    const data = toCamelCase<AccountHistoryResponse>(response.data);
    return data.histories;
  },

  /**
   * Get performance metrics
   */
  getPerformanceMetrics: async (): Promise<PerformanceMetrics> => {
    const response = await apiClient.get<Record<string, unknown>>(
      '/api/v1/trading/performance-metrics',
    );
    const data = toCamelCase<PerformanceMetricsResponse>(response.data);
    return data.metrics;
  },
};
