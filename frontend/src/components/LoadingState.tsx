export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return <div className="loading-state">{label}</div>;
}

export function ErrorState({ message }: { message: string }) {
  return <div className="error-state">{message}</div>;
}

export function EmptyState({ label, colSpan }: { label: string; colSpan: number }) {
  return (
    <tr className="empty-row">
      <td colSpan={colSpan}>{label}</td>
    </tr>
  );
}
