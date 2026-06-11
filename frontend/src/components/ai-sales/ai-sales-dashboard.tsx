"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { HeroMetrics } from "@/components/ai-sales/hero-metrics";
import { IntentAnalytics } from "@/components/ai-sales/intent-analytics";
import { RecommendationsPanel } from "@/components/ai-sales/recommendations-panel";
import { SalesActivityTimeline } from "@/components/ai-sales/sales-activity-timeline";
import { TopLeadsTable } from "@/components/ai-sales/top-leads-table";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/auth-store";
import type { SalesActivityResponse, SalesInsightsResponse, SalesRecommendationsResponse, TopLeadsResponse, CustomerSalesProfileResponse } from "@/types/sales";
import { CustomerProfileModal } from "@/components/ai-sales/customer-profile-modal";

const S = t.sales;
const S_LOADING = S.loading;
const S_ERRORS = S.errors;

export function AiSalesDashboard() {
  const { accessToken, refreshSession } = useAuthStore();
  const activeRef = useRef(true);

  const [insights, setInsights] = useState<SalesInsightsResponse | null>(null);
  const [leads, setLeads] = useState<TopLeadsResponse | null>(null);
  const [recommendations, setRecommendations] = useState<SalesRecommendationsResponse | null>(null);
  const [activity, setActivity] = useState<SalesActivityResponse | null>(null);

  const [loadingInsights, setLoadingInsights] = useState(true);
  const [loadingLeads, setLoadingLeads] = useState(true);
  const [loadingRecommendations, setLoadingRecommendations] = useState(true);
  const [loadingActivity, setLoadingActivity] = useState(true);

  const [errorInsights, setErrorInsights] = useState<string | null>(null);
  const [errorLeads, setErrorLeads] = useState<string | null>(null);
  const [errorRecommendations, setErrorRecommendations] = useState<string | null>(null);
  const [errorActivity, setErrorActivity] = useState<string | null>(null);

  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [profile, setProfile] = useState<CustomerSalesProfileResponse | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [errorProfile, setErrorProfile] = useState<string | null>(null);

  const fetchWithRetry = useCallback(async function fetchWithRetry<T>(
    fetcher: (token: string) => Promise<T>,
    setData: (data: T) => void,
    setLoading: (v: boolean) => void,
    setError: (v: string | null) => void,
    errorMsg: string,
    retried = false
  ) {
    if (!accessToken) return;
    try {
      setLoading(true);
      setError(null);
      const data = await fetcher(accessToken);
      if (activeRef.current) setData(data);
    } catch (err: unknown) {
      const apiErr = err as { status?: number; message?: string };
      if (apiErr?.status === 401 && !retried) {
        await refreshSession();
        return fetchWithRetry(fetcher, setData, setLoading, setError, errorMsg, true);
      }
      if (activeRef.current) setError(apiErr?.message ?? errorMsg);
    } finally {
      if (activeRef.current) setLoading(false);
    }
  }, [accessToken, refreshSession]);

  const loadAll = useCallback(() => {
    fetchWithRetry(
      (t) => import("@/services/sales.service").then((m) => m.getSalesInsights(t)),
      setInsights, setLoadingInsights, setErrorInsights, S_ERRORS.loadInsights
    );
    fetchWithRetry(
      (t) => import("@/services/sales.service").then((m) => m.getTopLeads(t, 20)),
      setLeads, setLoadingLeads, setErrorLeads, S_ERRORS.loadLeads
    );
    fetchWithRetry(
      (t) => import("@/services/sales.service").then((m) => m.getRecommendations(t)),
      setRecommendations, setLoadingRecommendations, setErrorRecommendations, S_ERRORS.loadRecommendations
    );
    fetchWithRetry(
      (t) => import("@/services/sales.service").then((m) => m.getSalesActivity(t, 20)),
      setActivity, setLoadingActivity, setErrorActivity, S_ERRORS.loadActivity
    );
  }, [fetchWithRetry]);

  useEffect(() => {
    activeRef.current = true;
    loadAll();
    return () => { activeRef.current = false; };
  }, [loadAll]);

  const handleSelectCustomer = useCallback((customerId: string) => {
    setSelectedCustomerId(customerId);
    setProfile(null);
    setErrorProfile(null);
    setLoadingProfile(true);
    fetchWithRetry(
      (t) => import("@/services/sales.service").then((m) => m.getCustomerSalesProfile(t, customerId)),
      setProfile, setLoadingProfile, setErrorProfile, S_ERRORS.loadProfile
    );
  }, [fetchWithRetry]);

  const intents = insights?.most_detected_intents ?? [];

  return (
    <div className="space-y-6">
      <HeroMetrics
        hotLeads={insights?.total_hot_leads ?? 0}
        interested={insights?.total_interested ?? 0}
        negotiation={insights?.total_negotiation ?? 0}
        converted={insights?.total_converted ?? 0}
        isLoading={loadingInsights}
      />

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <DashboardSection title={S.topLeads.title} description={S.topLeads.description}>
          <TopLeadsTable
            leads={leads?.leads ?? []}
            isLoading={loadingLeads}
            error={errorLeads}
            onSelectCustomer={handleSelectCustomer}
          />
        </DashboardSection>

        <DashboardSection title={S.intents.title} description={S.intents.description}>
          <IntentAnalytics intents={intents} isLoading={loadingInsights} error={errorInsights} />
        </DashboardSection>
      </div>

      <RecommendationsPanel
        data={recommendations}
        isLoading={loadingRecommendations}
        error={errorRecommendations}
        onSelectCustomer={handleSelectCustomer}
      />

      <SalesActivityTimeline
        events={activity?.events ?? []}
        isLoading={loadingActivity}
        error={errorActivity}
        onSelectCustomer={handleSelectCustomer}
      />

      {selectedCustomerId && (
        <CustomerProfileModal
          profile={profile}
          isLoading={loadingProfile}
          error={errorProfile}
          onClose={() => setSelectedCustomerId(null)}
        />
      )}
    </div>
  );
}
