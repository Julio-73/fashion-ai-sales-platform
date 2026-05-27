import { Sparkles, Loader2, AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { SuggestedReply } from "@/types/ai-live";

type SuggestedRepliesProps = {
  replies: SuggestedReply[];
  isLoading: boolean;
  error: string | null;
  onSelect: (text: string) => void;
};

const MAX_VISIBLE = 3;

export function SuggestedReplies({ replies, isLoading, error, onSelect }: SuggestedRepliesProps) {
  if (isLoading) {
    return (
      <Card className="p-3">
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground mb-2">
          <Loader2 className="h-3 w-3 animate-spin" />
          Generating suggestions...
        </div>
        <div className="space-y-1.5">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-8 animate-pulse rounded-md bg-muted" />
          ))}
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-3">
        <div className="flex items-center gap-2 text-xs font-medium text-destructive mb-1">
          <AlertCircle className="h-3 w-3" />
          Suggestions unavailable
        </div>
        <p className="text-[11px] text-muted-foreground">{error}</p>
      </Card>
    );
  }

  if (!replies.length) {
    return null;
  }

  const visible = replies.slice(0, MAX_VISIBLE);

  return (
    <Card className="p-3">
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground mb-2">
        <Sparkles className="h-3 w-3" />
        Suggested replies
      </div>
      <div className="space-y-1.5">
        {visible.map((reply, i) => (
          <Button
            key={i}
            type="button"
            variant="outline"
            size="sm"
            className="h-auto w-full justify-start whitespace-normal break-words px-2.5 py-1.5 text-left text-[11px] leading-snug"
            onClick={() => onSelect(reply.text)}
          >
            {reply.text}
          </Button>
        ))}
      </div>
    </Card>
  );
}
