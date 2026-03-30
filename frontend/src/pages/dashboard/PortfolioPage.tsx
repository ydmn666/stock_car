import { EmptyStatePanel } from "../../components/dashboard/EmptyStatePanel";

export function PortfolioPage() {
  return <EmptyStatePanel title="个人投资模块即将接入" description="这里会承接你的买入卖出记录、持仓成本、累计投入、浮动盈亏、收益曲线与组合表现。当前先保留页面位置，后续直接接数据库和真实接口。" />;
}
