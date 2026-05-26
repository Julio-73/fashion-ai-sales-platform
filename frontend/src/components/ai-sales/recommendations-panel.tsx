"use client";

import { AlertCircle, Ban, Handshake, Sparkles, Target, TrendingUp, Users } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { t } from "@/lib/i18n";
import type { CustomerRecommendation, SalesRecommendationsResponse } from "@/types/sales";
import { cn } from "@/lib/utils";

const S = t.sales.recommendations;

type RecommendationCardProps = {
  title: string;
  icon: ReactNode;
  items: CustomerRecommendation[];
  emptyMessage: string;
  accentClass: string;
  onSelectCustomer: (customerId: string) => void;
};

function RecommendationCard({ title, icon, items, emptyMessage, accentClass, onSelectCustomer }: RecommendationCardProps) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <span className={cn("rounded-md p-1", accentClass)}>{icon}</span>
        <span>{title}</span>
        <span className="ml-auto rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-muted-foreground">{emptyMessage}</p>
      ) : (
        <div className="space-y-2">
          {items.slice(0, 5).map((item) => (
            <div key={item.customer_id} className="flex items-center justify-between rounded-md border bg-background px-3 py-2">
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{item.full_name}</p>
                <p className="truncate text-xs text-muted-foreground">{item.reason}</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="ml-2 shrink-0 text-xs"
                onClick={() => onSelectCustomer(item.customer_id)}
              >
                {S.viewProfile}
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

type RecommendationsPanelProps = {
  data: SalesRecommendationsResponse | null;
  isLoading: boolean;
  error: string | null;
  onSelectCustomer: (customerId: string) => void;
};

export function RecommendationsPanel({ data, isLoading, error, onSelectCustomer }: RecommendationsPanelProps) {
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
          <Skeleton className="h-3 w-48" />
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-lg border p-4">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="mt-3 h-16 w-full" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const sections = [
    {
      title: S.followUp,
      icon: <Target className="h-3.5 w-3.5 text-emerald-700" />,
      items: data?.customers_to_follow_up ?? [],
      emptyMessage: S.noFollowUp,
      accentClass: "bg-emerald-50",
    },
    {
      title: S.hotLeads,
      icon: <TrendingUp className="h-3.5 w-3.5 text-red-700" />,
      items: data?.hot_leads ?? [],
      emptyMessage: S.noHotLeads,
      accentClass: "bg-red-50",
    },
    {
      title: S.negotiation,
      icon: <Handshake className="h-3.5 w-3.5 text-amber-700" />,
      items: data?.negotiation_leads ?? [],
      emptyMessage: S.noNegotiation,
      accentClass: "bg-amber-50",
    },
    {
      title: S.inactive,
      icon: <Ban className="h-3.5 w-3.5 text-slate-600" />,
      items: data?.inactive_customers ?? [],
      emptyMessage: S.noInactive,
      accentClass: "bg-slate-100",
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">{S.title}</CardTitle>
        <p className="text-xs text-muted-foreground">{S.description}</p>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2">
          {sections.map((section) => (
            <RecommendationCard
              key={section.title}
              title={section.title}
              icon={section.icon}
              items={section.items}
              emptyMessage={section.emptyMessage}
              accentClass={section.accentClass}
              onSelectCustomer={onSelectCustomer}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
