"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Plus, Search, SlidersHorizontal, UsersRound } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { t } from "@/lib/i18n";
import { DataTable } from "@/components/data-table/data-table";
import { EmptyState } from "@/components/feedback/empty-state";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CustomerFormModal } from "@/modules/customers/components/customer-form-modal";
import { CustomerProfilePanel } from "@/modules/customers/components/customer-profile-panel";
import { CustomerStatusBadge, statusLabel } from "@/modules/customers/components/customer-status-badge";
import { ApiError } from "@/services/api-client";
import { createCustomer, deleteCustomer, listCustomers, updateCustomer } from "@/modules/customers/services/customers-api";
import { useAuthStore } from "@/store/auth-store";
import type { CustomerCreatePayload, CustomerSummary, LeadStatus } from "@/types/customer";

const W = t.customers.workspace;
const leadStatuses: Array<LeadStatus | "all"> = ["all", "new", "interested", "negotiating", "won", "lost"];

export function CustomersCrmWorkspace() {
  const { accessToken, refreshSession } = useAuthStore();
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerSummary | null>(null);
  const [search, setSearch] = useState("");
  const [leadStatus, setLeadStatus] = useState<LeadStatus | "all">("all");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const limit = 10;
  const activeRef = useRef(true);

  useEffect(() => {
    if (!accessToken) return;
    activeRef.current = true;

    loadCustomers();

    return () => {
      activeRef.current = false;
    };
  }, [accessToken, leadStatus, offset, search]);

  async function loadCustomers(retried = false) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listCustomers({
        accessToken: accessToken!,
        search: search || undefined,
        leadStatus,
        limit,
        offset,
      });
      if (!activeRef.current) return;
      setCustomers(response.items);
      setTotal(response.total);
      setSelectedCustomer((current) => current ?? response.items[0] ?? null);
    } catch (err) {
      if (!activeRef.current) return;
      if (!retried && err instanceof ApiError && err.status === 401) {
        try {
          await refreshSession();
        } catch {
          setError(W.errorLoad);
          setCustomers([]);
          setTotal(0);
          return;
        }
        return loadCustomers(true);
      }
      setError(W.errorLoad);
      setCustomers([]);
      setTotal(0);
    } finally {
      if (activeRef.current) setIsLoading(false);
    }
  }

  const tableRows = useMemo(
    () =>
      customers.map((customer) => ({
        customer: (
          <button
            type="button"
            className="text-left"
            onClick={() => setSelectedCustomer(customer)}
          >
            <span className="block font-medium text-foreground">{customer.full_name}</span>
            <span className="text-xs text-muted-foreground">{customer.email ?? customer.phone ?? W.fallbackNotSet}</span>
          </button>
        ),
        status: <CustomerStatusBadge status={customer.lead_status} />,
        channel: customer.whatsapp || customer.instagram_username || customer.phone || W.fallbackNotSet,
        tags: (
          <div className="flex flex-wrap gap-1">
            {customer.tags.slice(0, 3).map((tag) => (
              <span key={tag} className="rounded-md bg-secondary px-2 py-1 text-xs">
                {tag}
              </span>
            ))}
          </div>
        ),
        source: customer.source ?? W.fallbackSource
      })),
    [customers]
  );

  function openCreateModal() {
    setModalMode("create");
    setSelectedCustomer(null);
    setIsModalOpen(true);
  }

  function openEditModal(customer: CustomerSummary) {
    setModalMode("edit");
    setSelectedCustomer(customer);
    setIsModalOpen(true);
  }

  async function handleSubmit(payload: CustomerCreatePayload) {
    if (!accessToken) throw new Error("No access token available");
    if (modalMode === "create") {
      const created = await createCustomer(accessToken, payload);
      setCustomers((current) => [created, ...current]);
      setSelectedCustomer(created);
      setTotal((current) => current + 1);
      return;
    }

    if (!selectedCustomer) throw new Error("No customer selected for editing");
    const updated = await updateCustomer(accessToken, selectedCustomer.id, payload);
    setCustomers((current) => current.map((customer) => (customer.id === updated.id ? updated : customer)));
    setSelectedCustomer(updated);
  }

  async function handleDelete(customer: CustomerSummary) {
    if (!accessToken) throw new Error("No access token available");
    await deleteCustomer(accessToken, customer.id);
    setCustomers((current) => current.filter((item) => item.id !== customer.id));
    setSelectedCustomer((current) => (current?.id === customer.id ? null : current));
    setTotal((current) => Math.max(0, current - 1));
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
      <div className="grid gap-5">
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_220px_auto]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                className="h-10 w-full rounded-md border bg-background pl-9 pr-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder={W.searchPlaceholder}
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setOffset(0);
                }}
              />
            </div>
            <select
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={leadStatus}
              onChange={(event) => {
                setLeadStatus(event.target.value as LeadStatus | "all");
                setOffset(0);
              }}
            >
              {leadStatuses.map((status) => (
                <option key={status} value={status}>
                  {status === "all" ? W.allStatuses : statusLabel[status]}
                </option>
              ))}
            </select>
            <Button type="button" variant="outline">
              <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
              {W.filters}
            </Button>
          </div>
        </div>

        {error ? (
          <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        ) : null}

        <DashboardSection
          title={W.tableHeaderCustomer}
          description={`${total} ${total === 1 ? t.customers.page.title.toLowerCase() : `${t.customers.page.title.toLowerCase()}`}`}
          action={
            <Button type="button" onClick={openCreateModal}>
              <Plus className="h-4 w-4" aria-hidden="true" />
              {W.createButton}
            </Button>
          }
        >
          <div className="hidden lg:block">
            <DataTable
              columns={[
                { key: "customer", header: W.tableHeaderCustomer },
                { key: "status", header: W.tableHeaderLeadStatus },
                { key: "channel", header: W.tableHeaderChannel },
                { key: "tags", header: W.tableHeaderTags },
                { key: "source", header: W.tableHeaderSource }
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
            ) : customers.length ? (
              <AnimatePresence>
                {customers.map((customer) => (
                  <motion.button
                    key={customer.id}
                    type="button"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 8 }}
                    className="rounded-lg border bg-card p-4 text-left shadow-sm"
                    onClick={() => setSelectedCustomer(customer)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium">{customer.full_name}</p>
                        <p className="mt-1 text-sm text-muted-foreground">{customer.email ?? customer.phone}</p>
                      </div>
                      <CustomerStatusBadge status={customer.lead_status} />
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {customer.tags.map((tag) => (
                        <span key={tag} className="rounded-md bg-secondary px-2 py-1 text-xs">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </motion.button>
                ))}
              </AnimatePresence>
            ) : (
              <EmptyState
                icon={UsersRound}
                title={W.emptyTitle}
                description={W.emptyDesc}
              />
            )}
          </div>

          <div className="flex items-center justify-between pt-2 text-sm text-muted-foreground">
            <span>
              {total > 0
                ? W.paginationShowing.replace("{start}", String(offset + 1)).replace("{end}", String(offset + customers.length)).replace("{total}", String(total))
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

      <CustomerProfilePanel customer={selectedCustomer} onEdit={openEditModal} onDelete={handleDelete} />

      <CustomerFormModal
        open={isModalOpen}
        mode={modalMode}
        customer={modalMode === "edit" ? selectedCustomer : null}
        onOpenChange={setIsModalOpen}
        onSubmit={handleSubmit}
      />
    </div>
  );
}

