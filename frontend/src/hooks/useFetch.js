import { useCallback, useEffect, useRef, useState } from "react";
import { errorMessage } from "../services/api";

/**
 * Loads data when the component mounts or `deps` change.
 * refreshMs: optional polling interval (silent refresh, no loading flicker).
 */
export function useFetch(fetcher, deps = [], { refreshMs } = {}) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      setData(await fetcherRef.current());
      setError(null);
    } catch (e) {
      if (!silent) setError(errorMessage(e));
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    if (!refreshMs) return undefined;
    const id = setInterval(() => load(true), refreshMs);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, refreshMs]);

  return { data, error, loading, reload: () => load() };
}
