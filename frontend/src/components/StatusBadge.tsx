import type { BudgetStatus, TransactionType } from "../types/api";

export function BudgetStatusBadge({ status }: { status: BudgetStatus }) {
  const map: Record<BudgetStatus, { cls: string; label: string }> = {
    under: { cls: "badge-good", label: "Under" },
    approaching: { cls: "badge-warning", label: "Approaching" },
    over: { cls: "badge-critical", label: "Over" },
  };
  const { cls, label } = map[status];
  return <span className={`badge ${cls}`}>{label}</span>;
}

export function TransactionTypeBadge({ type }: { type: TransactionType }) {
  return (
    <span className={`badge ${type === "income" ? "badge-income" : "badge-expense"}`}>
      {type === "income" ? "Income" : "Expense"}
    </span>
  );
}
