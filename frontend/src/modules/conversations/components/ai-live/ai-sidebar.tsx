import { Loader2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { useAuthStore } from "@/store/auth-store";
import type { AIStateResponse, SuggestReplyResponse } from "@/types/ai-live";
import { AIStatusControls } from "@/modules/conversations/components/ai-live/ai-status-controls";
import { InsightsPanel } from "@/modules/conversations/components/ai-live/insights-panel";
import { SuggestedReplies } from "@/modules/conversations/components/ai-live/suggested-replies";

type AISidebarProps = {
  conversationId: string | null;
  onSelectSuggestedReply: (text: string) => void;
};

function friendlyError(err: unknown, fallback: string): string {
  if (!err) return fallback;
  const e = err as { status?: number; message?: string };
  if (e.status === 404) return "AI not available for this conversation";
  if (e.status === 403) return "You don't have permission for AI features";
  if (e.status === 401) return "Session expired. Please refresh.";
  if (e.status && e.status >= 500) return "AI service temporarily unavailable";
  if (e.message && e.message !== "Failed to fetch") return e.message;
  return fallback;
}

export function AISidebar({ conversationId, onSelectSuggestedReply }: AISidebarProps) {
  const { accessToken, refreshSession } = useAuthStore();
  const activeRef = useRef(true);
  const [tokenReady, setTokenReady] = useState(false);

  const [aiState, setAiState] = useState<AIStateResponse | null>(null);
  const [suggestedReplies, setSuggestedReplies] = useState<SuggestReplyResponse | null>(null);
  const [updatingField, setUpdatingField] = useState<string | null>(null);

  const [loadingState, setLoadingState] = useState(false);
  const [loadingReplies, setLoadingReplies] = useState(false);

  const [errorState, setErrorState] = useState<string | null>(null);
  const [errorReplies, setErrorReplies] = useState<string | null>(null);

  useEffect(() => {
    activeRef.current = true;
    if (accessToken) setTokenReady(true);
    return () => { activeRef.current = false; };
  }, [accessToken]);

  const fetchWithRetry = useCallback(async function fetchWithRetry<T>(
    fetcher: (token: string) => Promise<T>,
    setData: (data: T) => void,
    setLoading: (v: boolean) => void,
    setError: (v: string | null) => void,
    errorMsg: string,
    retried = false
  ) {
    if (!accessToken) {
      setLoading(false);
      setError("Authentication not available");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetcher(accessToken);
      if (activeRef.current) setData(data);
    } catch (err: unknown) {
      const apiErr = err as { status?: number; message?: string };
      if (apiErr?.status === 401 && !retried) {
        try {
          await refreshSession();
          return fetchWithRetry(fetcher, setData, setLoading, setError, errorMsg, true);
        } catch {
          if (activeRef.current) setError("Session refresh failed. Please log in again.");
          return;
        }
      }
      if (activeRef.current) setError(friendlyError(err, errorMsg));
    } finally {
      if (activeRef.current) setLoading(false);
    }
  }, [accessToken, refreshSession]);

  const loadState = useCallback(() => {
    if (!conversationId) return;
    if (!accessToken) {
      setLoadingState(false);
      setErrorState("Authentication not available");
      return;
    }
    fetchWithRetry(
      (t) => import("@/services/ai-live.service").then((m) => m.getAIState(t, conversationId)),
      setAiState,
      setLoadingState, setErrorState, "Failed to load AI state"
    );
  }, [conversationId, accessToken, fetchWithRetry]);

  const loadSuggestedReplies = useCallback(() => {
    if (!conversationId) return;
    if (!accessToken) {
      setLoadingReplies(false);
      setErrorReplies("Authentication not available");
      return;
    }
    fetchWithRetry(
      (t) => import("@/services/ai-live.service").then((m) => m.getSuggestedReplies(t, conversationId)),
      setSuggestedReplies,
      setLoadingReplies, setErrorReplies, "Failed to load suggestions"
    );
  }, [conversationId, accessToken, fetchWithRetry]);

  useEffect(() => {
    if (conversationId && tokenReady) {
      loadState();
      loadSuggestedReplies();
    } else {
      setAiState(null);
      setSuggestedReplies(null);
      setErrorState(null);
      setErrorReplies(null);
    }
  }, [conversationId, tokenReady, loadState, loadSuggestedReplies]);

  async function handleToggleAI(enabled: boolean) {
    if (!accessToken || !conversationId) return;
    setUpdatingField("ai_enabled");
    try {
      const data = await import("@/services/ai-live.service").then((m) =>
        m.toggleAI(accessToken, conversationId, enabled)
      );
      if (activeRef.current) setAiState(data);
    } catch {
      setErrorState("Failed to update AI state");
    } finally {
      setUpdatingField(null);
    }
  }

  async function handleToggleAutoReply(enabled: boolean) {
    if (!accessToken || !conversationId) return;
    setUpdatingField("auto_reply_enabled");
    try {
      const data = await import("@/services/ai-live.service").then((m) =>
        m.toggleAutoReply(accessToken, conversationId, enabled)
      );
      if (activeRef.current) setAiState(data);
    } catch {
      setErrorState("Failed to update auto-reply state");
    } finally {
      setUpdatingField(null);
    }
  }

  async function handleRequestHandoff() {
    if (!accessToken || !conversationId) return;
    try {
      await import("@/services/ai-live.service").then((m) =>
        m.requestHandoff(accessToken, conversationId)
      );
      loadState();
    } catch {
      setErrorState("Failed to request handoff");
    }
  }

  if (!conversationId) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-lg border bg-card p-6 text-center text-xs text-muted-foreground shadow-sm">
        <Loader2 className="h-5 w-5 animate-spin opacity-30" />
        Select a conversation to see AI insights
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <AIStatusControls
        aiEnabled={aiState?.ai_enabled ?? true}
        autoReplyEnabled={aiState?.auto_reply_enabled ?? false}
        escalationRequired={aiState?.escalation_required ?? false}
        isLoading={loadingState && !aiState}
        onToggleAI={handleToggleAI}
        onToggleAutoReply={handleToggleAutoReply}
        onRequestHandoff={handleRequestHandoff}
        updatingField={updatingField}
      />

      <InsightsPanel
        state={aiState ? {
          ai_enabled: aiState.ai_enabled,
          auto_reply_enabled: aiState.auto_reply_enabled,
          escalation_required: aiState.escalation_required,
          last_detected_intent: aiState.last_detected_intent,
          sentiment: aiState.sentiment,
          urgency_score: aiState.urgency_score,
          lead_temperature: aiState.lead_temperature,
          ai_last_response: aiState.ai_last_response,
          ai_confidence: aiState.ai_confidence,
        } : null}
        isLoading={loadingState && !aiState}
        error={errorState}
      />

      <SuggestedReplies
        replies={suggestedReplies?.suggestions ?? []}
        isLoading={loadingReplies}
        error={errorReplies}
        onSelect={onSelectSuggestedReply}
      />
    </div>
  );
}
