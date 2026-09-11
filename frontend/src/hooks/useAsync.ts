import { useEffect, useState } from "react";
import { ApiError } from "../api/client";

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Runs `fn` on mount and whenever `deps` change, tracking loading/error state.
 * Ignores results from stale (superseded) calls.
 */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): AsyncState<T> & {
  reload: () => void;
} {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: true,
    error: null,
  });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    fn()
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null });
      })
      .catch((err) => {
        if (!cancelled) {
          setState({
            data: null,
            loading: false,
            error: err instanceof ApiError ? err.detail : "Something went wrong.",
          });
        }
      });
    return () => {
      cancelled = true;
    };
    // deps is caller-controlled; fn is expected to close over deps' values.
  }, [...deps, tick]);

  return { ...state, reload: () => setTick((t) => t + 1) };
}
