"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  Bot,
  MessageSquare,
  Plus,
  Search,
  Send,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { t } from "@/lib/i18n";
import { DataTable } from "@/components/data-table/data-table";
import { EmptyState } from "@/components/feedback/empty-state";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusPill } from "@/components/ui/status-pill";
import { Card, CardContent } from "@/components/ui/card";
import { ApiError } from "@/services/api-client";
import {
  getConversationDetail,
  getTypingState,
  listConversations,
  processMessage,
} from "@/modules/conversations/services/conversations-api";
import { AISidebar } from "@/modules/conversations/components/ai-live/ai-sidebar";
import { useAuthStore } from "@/store/auth-store";
import type {
  ConversationDetail,
  ConversationStatus,
  ConversationSummary,
  MessageSummary,
} from "@/types/conversation";

const W = t.conversations.workspace;
const statuses: Array<ConversationStatus | "all"> = ["all", "open", "pending", "closed"];

const statusLabel: Record<string, string> = {
  open: t.conversations.status.open,
  pending: t.conversations.status.pending,
  closed: t.conversations.status.closed,
};

const canalIcon: Record<string, string> = {
  manual: "👤",
  whatsapp: "💬",
  instagram: "📸",
  facebook: "👍",
  web: "🌐",
};

function MessageBubble({ message }: { message: MessageSummary }) {
  const isAgent = message.role === "agent";
  const isSystem = message.role === "system";
  const isAi = isAgent && message.sender_name === "AI Asistente";
  return (
    <div className={`flex ${isAgent ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isSystem
            ? "bg-muted text-muted-foreground italic"
            : isAi
              ? "bg-indigo-50 text-indigo-900 border border-indigo-200 rounded-bl-sm"
              : isAgent
                ? "bg-primary text-primary-foreground rounded-br-sm"
                : "bg-secondary text-secondary-foreground rounded-bl-sm"
        }`}
      >
        {message.sender_name && !isSystem ? (
          <p className={`mb-1 flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide ${
            isAi ? "text-indigo-500" : "opacity-70"
          }`}>
            {isAi ? <Bot className="h-3 w-3" /> : null}
            {message.sender_name}
          </p>
        ) : null}
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        <p className={`mt-1 text-right text-[10px] ${isAi ? "text-indigo-400" : "opacity-60"}`}>
          {new Date(message.created_at).toLocaleString("es-PE", {
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}

function AiTypingBubble() {
  return (
    <div className="flex justify-start mb-3">
      <div className="max-w-[80%] rounded-2xl rounded-bl-sm px-4 py-3 text-sm bg-indigo-50 text-indigo-400 border border-indigo-200">
        <p className="mb-1 flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-indigo-500">
          <Bot className="h-3 w-3" />
          AI Asistente
        </p>
        <p className="flex items-center gap-1">
          <span className="animate-pulse">●</span>
          <span className="animate-pulse animation-delay-200">●</span>
          <span className="animate-pulse animation-delay-400">●</span>
        </p>
      </div>
    </div>
  );
}

export function ConversationsWorkspace() {
  const { accessToken, refreshSession } = useAuthStore();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [selected, setSelected] = useState<ConversationDetail | null>(null);
  const [search, setSearch] = useState("");
  const [estado, setEstado] = useState<ConversationStatus | "all">("all");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [newMessage, setNewMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isAiTyping, setIsAiTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const limit = 10;
  const activeRef = useRef(true);

  const loadConversations = useCallback(async (retried = false) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listConversations({
        accessToken: accessToken!,
        search: search || undefined,
        estado,
        limit,
        offset,
      });
      if (!activeRef.current) return;
      setConversations(response.items);
      setTotal(response.total);
    } catch (err) {
      if (!activeRef.current) return;
      if (!retried && err instanceof ApiError && err.status === 401) {
        try {
          await refreshSession();
        } catch {
          setError(W.errorLoad);
          setConversations([]);
          setTotal(0);
          return;
        }
        return loadConversations(true);
      }
      setError(W.errorLoad);
      setConversations([]);
      setTotal(0);
    } finally {
      if (activeRef.current) setIsLoading(false);
    }
  }, [accessToken, estado, offset, search, refreshSession]);

  useEffect(() => {
    if (!accessToken) return;
    activeRef.current = true;
    loadConversations();
    return () => { activeRef.current = false; };
  }, [accessToken, estado, offset, search, refreshKey, loadConversations]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [selected?.messages, isAiTyping]);

  useEffect(() => {
    if (!isAiTyping || !accessToken || !selected) {
      if (typingPollRef.current) {
        clearInterval(typingPollRef.current);
        typingPollRef.current = null;
      }
      return;
    }
    const poll = async () => {
      if (!accessToken || !selected) return;
      try {
        const state = await getTypingState(accessToken, selected.id);
        if (!state.is_typing) {
          setIsAiTyping(false);
          if (typingPollRef.current) {
            clearInterval(typingPollRef.current);
            typingPollRef.current = null;
          }
        }
      } catch {
        // ignore polling errors
      }
    };
    typingPollRef.current = setInterval(poll, 800);
    return () => {
      if (typingPollRef.current) {
        clearInterval(typingPollRef.current);
        typingPollRef.current = null;
      }
    };
  }, [isAiTyping, accessToken, selected]);

  async function openConversation(conv: ConversationSummary) {
    if (!accessToken) return;
    try {
      const detail = await getConversationDetail(accessToken, conv.id);
      setSelected(detail);
    } catch {
      setError(W.errorLoad);
    }
  }

  async function handleSend() {
    const content = newMessage.trim();
    if (!content || !accessToken || !selected || isSending) return;

    const tempId = `optimistic-${Date.now()}`;
    const optimisticMsg: MessageSummary = {
      id: tempId,
      empresa_id: selected.empresa_id,
      conversation_id: selected.id,
      role: "client",
      content,
      sender_name: "Tú",
      extra_data: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setSelected((prev) => {
      if (!prev) return prev;
      return { ...prev, messages: [...prev.messages, optimisticMsg] };
    });
    setNewMessage("");
    setIsSending(true);
    setIsAiTyping(true);

    try {
      const result = await processMessage(accessToken, selected.id, {
        content,
        role: "client",
        sender_name: "Tú",
      });

      setSelected((prev) => {
        if (!prev) return prev;
        const filtered = prev.messages.filter((m) => m.id !== tempId);
        const updated = [result.message];
        if (result.ai_reply) {
          updated.push(result.ai_reply);
        }
        return { ...prev, messages: [...filtered, ...updated] };
      });

      if (!result.typing.is_typing) {
        setIsAiTyping(false);
      }
      setRefreshKey((k) => k + 1);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        try { await refreshSession(); } catch { /* ignore */ }
      }
      setSelected((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          messages: prev.messages.map((m) =>
            m.id === tempId ? { ...m, content: `${content} ${W.sendError}` } : m
          ),
        };
      });
    } finally {
      setIsSending(false);
    }
  }

  function closeDetail() {
    setSelected(null);
  }

  const tableRows = conversations.map((conv) => ({
    conversation: (
      <button
        type="button"
        className="text-left"
        onClick={() => openConversation(conv)}
      >
        <span className="block font-medium text-foreground">
          {conv.asunto ?? W.noSubject}
        </span>
        <span className="text-xs text-muted-foreground">
          {canalIcon[conv.canal] ?? canalIcon.manual} {conv.canal}
        </span>
      </button>
    ),
    status: (
      <StatusPill
        tone={
          conv.estado === "open"
            ? "success"
            : conv.estado === "pending"
              ? "warning"
              : "neutral"
        }
        size="sm"
        dot
      >
        {statusLabel[conv.estado] ?? conv.estado}
      </StatusPill>
    ),
    updated: (
      <span className="text-sm text-muted-foreground">
        {new Date(conv.updated_at).toLocaleDateString("es-PE")}
      </span>
    ),
  }));

  const gridCols = selected
    ? "xl:grid-cols-[minmax(0,1fr)_480px_280px]"
    : "xl:grid-cols-[minmax(0,1fr)_480px]";

  function handleSelectSuggestedReply(text: string) {
    setNewMessage(text);
  }

  return (
    <>
      <div className={`grid gap-6 ${gridCols}`}>
        <div className="grid gap-5">
          <Card>
            <CardContent className="p-4">
              <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_200px_auto]">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <input
                    className="h-10 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm shadow-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder={W.searchPlaceholder}
                    value={search}
                    onChange={(event) => {
                      setSearch(event.target.value);
                      setOffset(0);
                    }}
                  />
                </div>
                <select
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm shadow-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={estado}
                  onChange={(event) => {
                    setEstado(event.target.value as ConversationStatus | "all");
                    setOffset(0);
                  }}
                >
                  {statuses.map((s) => (
                    <option key={s} value={s}>
                      {s === "all" ? W.allStatuses : statusLabel[s]}
                    </option>
                  ))}
                </select>
                <Button type="button" variant="outline">
                  <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
                  {W.filters}
                </Button>
              </div>
            </CardContent>
          </Card>

          {error ? (
            <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          ) : null}

          <DashboardSection
            title={W.title}
            description={`${total} ${total === 1 ? W.conversationLabel : W.conversationsLabel}`}
          >
            <div className="hidden lg:block">
              <DataTable
                columns={[
                  { key: "conversation", header: W.tableHeaderConversation },
                  { key: "status", header: W.tableHeaderStatus },
                  { key: "updated", header: W.tableHeaderUpdated },
                ]}
                rows={tableRows}
                isLoading={isLoading}
                emptyTitle={W.emptyTitle}
                emptyDescription={W.emptyDesc}
              />
            </div>

            <div className="grid gap-3 lg:hidden">
              {isLoading ? (
                Array.from({ length: 4 }).map((_, index) => <Skeleton key={index} className="h-28 w-full" />)
              ) : conversations.length ? (
                <AnimatePresence>
                  {conversations.map((conv) => (
                    <motion.button
                      key={conv.id}
                      type="button"
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 8 }}
                      className="rounded-lg border bg-card p-4 text-left shadow-sm"
                      onClick={() => openConversation(conv)}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-medium">{conv.asunto ?? W.noSubject}</p>
                          <p className="mt-1 text-sm text-muted-foreground">
                            {canalIcon[conv.canal] ?? canalIcon.manual} {conv.canal}
                          </p>
                        </div>
                        <span>
                          <StatusPill
                            tone={
                              conv.estado === "open"
                                ? "success"
                                : conv.estado === "pending"
                                  ? "warning"
                                  : "neutral"
                            }
                            size="sm"
                            dot
                          >
                            {statusLabel[conv.estado] ?? conv.estado}
                          </StatusPill>
                        </span>
                      </div>
                    </motion.button>
                  ))}
                </AnimatePresence>
              ) : (
                <EmptyState
                  icon={MessageSquare}
                  title={W.emptyTitle}
                  description={W.emptyDesc}
                />
              )}
            </div>

            <div className="flex items-center justify-between pt-2 text-sm text-muted-foreground">
              <span>
                {total > 0
                  ? W.paginationShowing
                      .replace("{start}", String(offset + 1))
                      .replace("{end}", String(offset + conversations.length))
                      .replace("{total}", String(total))
                  : W.paginationNone}
              </span>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={offset === 0}
                  onClick={() => setOffset((current) => Math.max(0, current - limit))}
                >
                  {W.previous}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={offset + limit >= total}
                  onClick={() => setOffset((current) => current + limit)}
                >
                  {W.next}
                </Button>
              </div>
            </div>
          </DashboardSection>
        </div>

        {/* Conversation Detail Panel */}
        {selected ? (
          <Card className="flex flex-col overflow-hidden">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div>
                <h3 className="text-sm font-semibold tracking-tight text-foreground">
                  {selected.asunto ?? W.noSubject}
                </h3>
                <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span>{canalIcon[selected.canal] ?? canalIcon.manual}</span>
                  <span>{selected.canal}</span>
                  <span>—</span>
                  <StatusPill
                    tone={
                      selected.estado === "open"
                        ? "success"
                        : selected.estado === "pending"
                          ? "warning"
                          : "neutral"
                    }
                    size="sm"
                    dot
                  >
                    {statusLabel[selected.estado] ?? selected.estado}
                  </StatusPill>
                </p>
              </div>
              <Button type="button" variant="ghost" size="icon" onClick={closeDetail} aria-label="Cerrar conversaci&oacute;n">
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {selected.messages.length === 0 ? (
                <EmptyState
                  icon={MessageSquare}
                  title={W.noMessages}
                  description={W.noMessagesDesc}
                />
              ) : (
                <AnimatePresence>
                  {selected.messages.map((msg) => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      <MessageBubble message={msg} />
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
              {isAiTyping ? <AiTypingBubble /> : null}
              <div ref={messagesEndRef} />
            </div>

            {selected.estado !== "closed" ? (
              <div className="border-t border-border p-3">
                <div className="flex gap-2">
                  <input
                    className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder={W.messagePlaceholder}
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                  />
                  <Button
                    type="button"
                    size="icon"
                    disabled={!newMessage.trim() || isSending}
                    onClick={handleSend}
                    aria-label="Enviar mensaje"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ) : (
              <div className="border-t border-border p-3 text-center text-sm text-muted-foreground">
                {W.closedChat}
              </div>
            )}
          </Card>
        ) : (
          <div className="flex items-center justify-center rounded-xl border border-dashed border-border bg-card p-12">
            <EmptyState
              icon={MessageSquare}
              title={W.selectChat}
              description={W.selectChatDesc}
            />
          </div>
        )}

        {/* AI Sidebar */}
        {selected && (
          <div className="hidden xl:block">
            <AISidebar
              conversationId={selected.id}
              onSelectSuggestedReply={handleSelectSuggestedReply}
            />
          </div>
        )}
      </div>
    </>
  );
}
