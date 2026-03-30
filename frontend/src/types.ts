export type StockRecord = Record<string, string | number | null>;

export interface StockOption {
  code: string;
  name: string;
}

export interface NewsResponse {
  records: StockRecord[];
  is_fallback: boolean;
}

export interface ForecastResponse {
  records: StockRecord[];
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
