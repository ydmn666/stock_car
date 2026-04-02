export type Market = "CN";

export interface Instrument {
  id: string;
  market: Market;
  symbol: string;
  full_symbol: string;
  asset_type: "stock";
  display_name: string;
  exchange?: string | null;
  currency?: string | null;
}

export interface PriceBar {
  instrument_id: string;
  market: Market;
  symbol: string;
  trade_date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  turnover: number | null;
  amplitude: number | null;
  pct_change: number | null;
  price_change: number | null;
  turnover_rate: number | null;
  adjusted: "none" | "qfq" | "hfq";
  currency: string;
  source: string;
  source_symbol?: string | null;
  is_fallback?: boolean;
}

export interface NewsItem {
  id: string;
  instrument_id: string;
  market: Market;
  symbol: string;
  title: string;
  summary?: string | null;
  content?: string | null;
  source: string;
  publisher?: string | null;
  url?: string | null;
  published_at: string;
  language?: string | null;
  matched_by: "ticker" | "symbol" | "name" | "keyword";
  is_fallback?: boolean;
}

export interface ForecastPoint {
  ds: string;
  yhat: number | null;
  yhat_upper: number | null;
  yhat_lower: number | null;
}

export interface PriceHistoryResponse {
  instrument: Instrument;
  records: PriceBar[];
  meta: {
    provider: string;
    fallback_used: boolean;
    requested_market: Market;
    requested_symbol: string;
    currency?: string | null;
    adjusted?: string | null;
  };
}

export interface NewsResponse {
  instrument: Instrument;
  records: NewsItem[];
  meta: {
    provider: string;
    fallback_used: boolean;
  };
}

export interface ForecastResponse {
  records: ForecastPoint[];
}

export interface AgentResponse {
  content: string;
  actions: Array<Record<string, string>>;
}

export interface ChatResponse {
  content: string;
}

export interface HistoryItem {
  id: number;
  stock_name: string;
  stock_code: string;
  visit_time_str: string;
}

export interface PortfolioSummary {
  total_buy_amount: number;
  total_sell_amount: number;
  total_fees: number;
  net_invested: number;
  cash_returned: number;
  realized_pnl: number;
  holding_cost: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number | null;
  position_count: number;
  transaction_count: number;
}

export interface PortfolioPosition {
  symbol: string;
  stock_name: string;
  quantity: number;
  avg_cost: number;
  cost_basis: number;
  latest_price: number | null;
  market_value: number | null;
  unrealized_pnl: number | null;
  unrealized_pnl_pct: number | null;
}

export interface PortfolioTransaction {
  id: number;
  username: string;
  symbol: string;
  stock_name: string;
  trade_type: "buy" | "sell";
  trade_date: string;
  price: number;
  quantity: number;
  fee: number;
  amount: number;
  note?: string | null;
}

export interface PortfolioPerformancePoint {
  date: string;
  net_invested: number;
  cash_returned: number;
  holding_cost: number;
  market_value: number;
  realized_pnl: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number | null;
}

export interface PortfolioAllocationItem {
  symbol: string;
  stock_name: string;
  market_value: number | null;
  weight_pct: number | null;
  unrealized_pnl: number | null;
}

export interface PortfolioPerformanceResponse {
  curve: PortfolioPerformancePoint[];
  allocation: PortfolioAllocationItem[];
  stats: {
    latest_market_value: number;
    latest_cash_returned: number;
    latest_realized_pnl: number;
    latest_unrealized_pnl: number;
    latest_unrealized_pnl_pct: number | null;
    max_market_value: number;
    min_market_value: number;
  };
}

export type StockOption = Instrument;
export type StockRecord = PriceBar;
