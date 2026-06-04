"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";

import { ApiError } from "@/services/api-client";
import * as pipelineService from "@/services/pipeline.service";
import { useAuthStore } from "@/store/auth-store";
import type {
  PipelineAlerts,
  PipelineBoard,
  PipelineDashboard,
  PipelineFunnel,
  PipelineItem,
  PipelineItemCreate,
  PipelineItemUpdate,
  PipelineMetrics,
  PipelineRecommendations,
  PipelineStageInfo
} from "@/types/pipeline";

type State = {
  isLoading: boolean;
  isMutating: boolean;
  error: string | null;
  board: PipelineBoard | null;
  stages: PipelineStageInfo[];
  metrics: PipelineMetrics | null;
  funnel: PipelineFunnel | null;
  alerts: PipelineAlerts | null;
  recommendations: PipelineRecommendations | null;
  dashboard: PipelineDashboard | null;
  filters: { search: string; is_open: boolean | null };
  refreshAll: () => Promise<void>;
  refreshBoard: () => Promise<void>;
  createDeal: (payload: PipelineItemCreate) => Promise<PipelineItem | null>;
  updateDeal: (
    id: string,
    payload: PipelineItemUpdate
  ) => Promise<PipelineItem | null>;
  moveStage: (
    id: string,
    targetStage: string,
    extras?: { probability?: number; notes?: string; won_reason?: string; lost_reason?: string }
  ) => Promise<PipelineItem | null>;
  deleteDeal: (id: string) => Promise<boolean>;
  setSearch: (q: string) => void;
  setOpenFilter: (v: boolean | null) => void;
};

const PipelineStoreContext = createContext<State | null>(null);

export function PipelineStoreProvider({ children }: { children: ReactNode }) {
  const { accessToken, refreshSession } = useAuthStore();
  const [board, setBoard] = useState<PipelineBoard | null>(null);
  const [stages, setStages] = useState<PipelineStageInfo[]>([]);
  const [metrics, setMetrics] = useState<PipelineMetrics | null>(null);
  const [funnel, setFunnel] = useState<PipelineFunnel | null>(null);
  const [alerts, setAlerts] = useState<PipelineAlerts | null>(null);
  const [recommendations, setRecommendations] =
    useState<PipelineRecommendations | null>(null);
  const [dashboard, setDashboard] = useState<PipelineDashboard | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<{ search: string; is_open: boolean | null }>({
    search: "",
    is_open: true
  });

  const runWithAuth = useCallback(
    async <T,>(fn: (token: string) => Promise<T>): Promise<T | null> => {
      if (!accessToken) return null;
      try {
        return await fn(accessToken);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          try {
            await refreshSession();
          } catch {
            return null;
          }
        }
        if (err instanceof ApiError) {
          setError(err.message);
        } else if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("Error desconocido");
        }
        return null;
      }
    },
    [accessToken, refreshSession]
  );

  const loadStages = useCallback(async () => {
    const s = await runWithAuth(pipelineService.fetchStages);
    if (s) setStages(s);
  }, [runWithAuth]);

  const loadBoard = useCallback(async () => {
    if (!accessToken) return;
    const data = await runWithAuth((t) =>
      pipelineService.fetchBoard(t, {
        is_open: filters.is_open ?? undefined,
        search: filters.search || undefined
      })
    );
    if (data) setBoard(data);
  }, [accessToken, runWithAuth, filters.is_open, filters.search]);

  const loadAux = useCallback(async () => {
    if (!accessToken) return;
    const [m, f, a, r, d] = await Promise.all([
      runWithAuth(pipelineService.fetchMetrics),
      runWithAuth(pipelineService.fetchFunnel),
      runWithAuth(pipelineService.fetchAlerts),
      runWithAuth(pipelineService.fetchRecommendations),
      runWithAuth(pipelineService.fetchDashboard)
    ]);
    if (m) setMetrics(m);
    if (f) setFunnel(f);
    if (a) setAlerts(a);
    if (r) setRecommendations(r);
    if (d) setDashboard(d);
  }, [accessToken, runWithAuth]);

  const refreshAll = useCallback(async () => {
    if (!accessToken) return;
    setIsLoading(true);
    setError(null);
    await loadStages();
    await Promise.all([loadBoard(), loadAux()]);
    setIsLoading(false);
  }, [accessToken, loadBoard, loadAux, loadStages]);

  const refreshBoard = useCallback(async () => {
    await loadBoard();
  }, [loadBoard]);

  useEffect(() => {
    if (!accessToken) {
      setBoard(null);
      setMetrics(null);
      setFunnel(null);
      setAlerts(null);
      setRecommendations(null);
      setDashboard(null);
      setStages([]);
      return;
    }
    void refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken) return;
    void loadBoard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.is_open, filters.search]);

  const createDeal = useCallback(
    async (payload: PipelineItemCreate) => {
      setIsMutating(true);
      const result = await runWithAuth((t) => pipelineService.createDeal(t, payload));
      setIsMutating(false);
      if (result) {
        await loadBoard();
        await loadAux();
      }
      return result;
    },
    [runWithAuth, loadBoard, loadAux]
  );

  const updateDeal = useCallback(
    async (id: string, payload: PipelineItemUpdate) => {
      setIsMutating(true);
      const result = await runWithAuth((t) =>
        pipelineService.updateDeal(t, id, payload)
      );
      setIsMutating(false);
      if (result) {
        await loadBoard();
      }
      return result;
    },
    [runWithAuth, loadBoard]
  );

  const moveStage = useCallback(
    async (
      id: string,
      targetStage: string,
      extras?: { probability?: number; notes?: string; won_reason?: string; lost_reason?: string }
    ) => {
      setIsMutating(true);
      const result = await runWithAuth((t) =>
        pipelineService.moveDealStage(t, id, {
          target_stage: targetStage as never,
          probability: extras?.probability,
          notes: extras?.notes,
          won_reason: extras?.won_reason,
          lost_reason: extras?.lost_reason
        })
      );
      setIsMutating(false);
      if (result) {
        await loadBoard();
        await loadAux();
      }
      return result;
    },
    [runWithAuth, loadBoard, loadAux]
  );

  const deleteDeal = useCallback(
    async (id: string) => {
      setIsMutating(true);
      const ok = await runWithAuth((t) => pipelineService.deleteDeal(t, id));
      setIsMutating(false);
      if (ok !== null) {
        await loadBoard();
        await loadAux();
        return true;
      }
      return false;
    },
    [runWithAuth, loadBoard, loadAux]
  );

  const setSearch = useCallback((q: string) => {
    setFilters((f) => ({ ...f, search: q }));
  }, []);
  const setOpenFilter = useCallback((v: boolean | null) => {
    setFilters((f) => ({ ...f, is_open: v }));
  }, []);

  const value = useMemo<State>(
    () => ({
      isLoading,
      isMutating,
      error,
      board,
      stages,
      metrics,
      funnel,
      alerts,
      recommendations,
      dashboard,
      filters,
      refreshAll,
      refreshBoard,
      createDeal,
      updateDeal,
      moveStage,
      deleteDeal,
      setSearch,
      setOpenFilter
    }),
    [
      isLoading,
      isMutating,
      error,
      board,
      stages,
      metrics,
      funnel,
      alerts,
      recommendations,
      dashboard,
      filters,
      refreshAll,
      refreshBoard,
      createDeal,
      updateDeal,
      moveStage,
      deleteDeal,
      setSearch,
      setOpenFilter
    ]
  );

  return (
    <PipelineStoreContext.Provider value={value}>
      {children}
    </PipelineStoreContext.Provider>
  );
}

export function usePipelineStore() {
  const ctx = useContext(PipelineStoreContext);
  if (!ctx) {
    throw new Error("usePipelineStore must be used inside PipelineStoreProvider");
  }
  return ctx;
}
