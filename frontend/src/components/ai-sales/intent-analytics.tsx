"use client";

import { BarChart3, HelpCircle, ShoppingBag, Tag, Truck } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { t } from "@/lib/i18n";
import type { IntentCount } from "@/types/sales";
import { cn } from "@/lib/utils";

const S = t.sales.intents;

const intentMeta: Record<string, { label: string; icon: typeof ShoppingBag; color: string }> = {
  purchase_intent: { label: S.purchase, icon: ShoppingBag, color: "bg-emerald-500" },
  pricing_intent: { label: S.pricing, icon: Tag, color: "bg-blue-500" },
  negotiation_intent: { label: S.negotiation, icon: BarChart3, color: "bg-amber-500" },
  shipping_intent: { label: S.shipping, icon: Truck, color: "bg-purple-500" },
};

type IntentAnalyticsProps = {
  intents: IntentCount[];
  isLoading: boolean;
  error: string | null;
};

export function IntentAnalytics({ intents, isLoading, error }: IntentAnalyticsProps) {
  const total = intents.reduce((sum, i) => sum + i.count, 0);

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{S.title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{S.title}</CardTitle>
          <Skeleton className="h-3 w-40" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1">
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="mt-1 h-2 w-full" />
                </div>
                <Skeleton className="h-4 w-8" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (total === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{S.title}</CardTitle>
          <p className="text-xs text-muted-foreground">{S.description}</p>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center gap-2 py-8 text-center">
            <HelpCircle className="h-8 w-8 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">{S.noData}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">{S.title}</CardTitle>
        <p className="text-xs text-muted-foreground">{S.description}</p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {intents.map((item) => {
            const meta = intentMeta[item.intent] ?? { label: item.intent, icon: HelpCircle, color: "bg-slate-400" };
            const percentage = Math.round((item.count / total) * 100);
            const Icon = meta.icon;
            return (
              <div key={item.intent} className="flex items-center gap-3">
                <div className={cn("flex h-8 w-8 items-center justify-center rounded-lg text-white", meta.color)}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="font-medium">{meta.label}</span>
                    <span className="text-xs text-muted-foreground">{item.count} ({percentage}%)</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className={cn("h-full rounded-full transition-all duration-500", meta.color)}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
