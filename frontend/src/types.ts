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

export type StockOption = Instrument;
export type StockRecord = PriceBar;
