interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onOffsetChange: (offset: number) => void;
}

export function Pagination({ total, limit, offset, onOffsetChange }: PaginationProps) {
  const page = Math.floor(offset / limit) + 1;
  const pageCount = Math.max(1, Math.ceil(total / limit));
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);

  return (
    <div className="pagination">
      <span>
        {from}–{to} of {total}
      </span>
      <div className="pagination-controls">
        <button
          type="button"
          className="btn btn-sm"
          disabled={offset === 0}
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
        >
          Previous
        </button>
        <span>
          Page {page} of {pageCount}
        </span>
        <button
          type="button"
          className="btn btn-sm"
          disabled={offset + limit >= total}
          onClick={() => onOffsetChange(offset + limit)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
