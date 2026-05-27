import { Brain, Loader2, MessageSquare, ToggleLeft, ToggleRight, UserRound } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

type AIStatusControlsProps = {
  aiEnabled: boolean;
  autoReplyEnabled: boolean;
  escalationRequired: boolean;
  isLoading: boolean;
  onToggleAI: (enabled: boolean) => Promise<void>;
  onToggleAutoReply: (enabled: boolean) => Promise<void>;
  onRequestHandoff: () => Promise<void>;
  updatingField: string | null;
};

export function AIStatusControls({
  aiEnabled,
  autoReplyEnabled,
  escalationRequired,
  isLoading,
  onToggleAI,
  onToggleAutoReply,
  onRequestHandoff,
  updatingField,
}: AIStatusControlsProps) {
  const [togglingAI, setTogglingAI] = useState(false);
  const [togglingAuto, setTogglingAuto] = useState(false);
  const [handingOff, setHandingOff] = useState(false);

  if (isLoading) {
    return (
      <Card className="p-3">
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground mb-2">
          <Loader2 className="h-3 w-3 animate-spin" />
          Loading AI controls...
        </div>
        <div className="space-y-2">
          <div className="h-7 animate-pulse rounded-md bg-muted" />
          <div className="h-7 animate-pulse rounded-md bg-muted" />
        </div>
      </Card>
    );
  }

  const isUpdatingAI = togglingAI || updatingField === "ai_enabled";
  const isUpdatingAuto = togglingAuto || updatingField === "auto_reply_enabled";

  async function handleToggleAI() {
    setTogglingAI(true);
    try {
      await onToggleAI(!aiEnabled);
    } finally {
      setTogglingAI(false);
    }
  }

  async function handleToggleAutoReply() {
    setTogglingAuto(true);
    try {
      await onToggleAutoReply(!autoReplyEnabled);
    } finally {
      setTogglingAuto(false);
    }
  }

  async function handleHandoff() {
    setHandingOff(true);
    try {
      await onRequestHandoff();
    } finally {
      setHandingOff(false);
    }
  }

  return (
    <Card className="p-3">
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground mb-2">
        <Brain className="h-3 w-3" />
        AI Assistant
      </div>
      <div className="space-y-2">
        {/* AI On/Off */}
        <button
          type="button"
          disabled={isUpdatingAI}
          className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-sm hover:bg-secondary disabled:opacity-50"
          onClick={handleToggleAI}
        >
          <span className="text-xs">AI Responses</span>
          <span className={aiEnabled ? "text-emerald-600" : "text-muted-foreground"}>
            {isUpdatingAI ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : aiEnabled ? (
              <ToggleRight className="h-4 w-4" />
            ) : (
              <ToggleLeft className="h-4 w-4" />
            )}
          </span>
        </button>

        {/* Auto-reply On/Off */}
        {aiEnabled && (
          <button
            type="button"
            disabled={isUpdatingAuto}
            className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-sm hover:bg-secondary disabled:opacity-50"
            onClick={handleToggleAutoReply}
          >
            <span className="text-xs">Auto-reply</span>
            <span className={autoReplyEnabled ? "text-emerald-600" : "text-muted-foreground"}>
              {isUpdatingAuto ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : autoReplyEnabled ? (
                <ToggleRight className="h-4 w-4" />
              ) : (
                <ToggleLeft className="h-4 w-4" />
              )}
            </span>
          </button>
        )}

        {/* Escalation indicator */}
        {escalationRequired && (
          <div className="flex items-center gap-1.5 rounded-md bg-amber-50 px-2 py-1.5 text-[11px] font-medium text-amber-700 ring-1 ring-amber-200">
            <MessageSquare className="h-3 w-3 shrink-0" />
            Human assistance requested
          </div>
        )}

        {/* Handoff button */}
        {aiEnabled && !escalationRequired && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={handingOff}
            className="h-7 w-full gap-1.5 text-[11px]"
            onClick={handleHandoff}
          >
            {handingOff ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <UserRound className="h-3 w-3" />
            )}
            Request human handoff
          </Button>
        )}
      </div>
    </Card>
  );
}
