"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown, Search } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";

import { EmptyState } from "@/components/feedback/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export type DataTableColumn<T> = {
  id?: string;
  key: keyof T | string;
  header: string;
  className?: string;
  render?: (row: T) => ReactNode;
  sortable?: boolean;
  accessor?: (row: T) => string | number;
  sortAccessor?: (row: T) => string | number;
};

type DataTableProps<T> = {
  columns: Array<DataTableColumn<T>>;
  rows: T[];
  isLoading?: boolean;
  emptyTitle: string;
  emptyDescription: string;
  emptyIcon?: LucideIcon;
  searchPlaceholder?: string;
  searchValue?: string;
  onSearchChange?: (v: string) => void;
  pageSize?: number;
  toolbar?: ReactNode;
  rowKey?: (row: T) => string;
  onRowClick?: (row: T) => void;
  className?: string;
};

export function DataTable<T extends Record<string, ReactNode>>({
  columns,
  rows,
  isLoading = false,
  emptyTitle,
  emptyDescription,
  emptyIcon,
  searchPlaceholder = "Buscar…",
  searchValue,
  onSearchChange,
  pageSize = 10,
  toolbar,
  rowKey,
  onRowClick,
  className
}: DataTableProps<T>) {
  const [sorting, setSorting] = useState<{ id: string; desc: boolean } | null>(
    null
  );
  const [internalSearch, setInternalSearch] = useState("");
  const [page, setPage] = useState(0);

  const search = searchValue ?? internalSearch;
  const handleSearch = (v: string) => {
    if (onSearchChange) onSearchChange(v);
    else setInternalSearch(v);
    setPage(0);
  };

  const filtered = useMemo(() => {
    if (!search) return rows;
    const lc = search.toLowerCase();
    return rows.filter((r) => {
      return Object.values(r as Record<string, unknown>).some((v) => {
        if (v === null || v === undefined) return false;
        return String(v).toLowerCase().includes(lc);
      });
    });
  }, [rows, search]);

  const sorted = useMemo(() => {
    if (!sorting) return filtered;
    const col = columns.find(
      (c) => (c.id ?? String(c.key)) === sorting.id
    );
    if (!col) return filtered;
    const accessor = col.sortAccessor ?? col.accessor;
    const getValue = accessor ?? ((row: T) => {
      const v = row[col.key as keyof T];
      if (typeof v === "string" || typeof v === "number") return v;
      return "";
    });
    return [...filtered].sort((a, b) => {
      const va = getValue(a);
      const vb = getValue(b);
      if (va < vb) return sorting.desc ? 1 : -1;
      if (va > vb) return sorting.desc ? -1 : 1;
      return 0;
    });
  }, [filtered, sorting, columns]);

  const total = sorted.length;
  const start = page * pageSize;
  const visible = sorted.slice(start, start + pageSize);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  if (isLoading) {
    return (
      <div className="card-surface overflow-hidden">
        <div className="space-y-2 p-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </div>
    );
  }

  const showToolbar = !!toolbar || !!onSearchChange || searchValue !== undefined;

  return (
    <div className={cn("card-surface overflow-hidden", className)}>
      {showToolbar ? (
        <div className="flex flex-col gap-3 border-b bg-secondary/30 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          {onSearchChange || searchValue !== undefined ? (
            <div className="relative max-w-sm flex-1">
              <Search
                className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground"
                aria-hidden="true"
              />
              <input
                type="search"
                placeholder={searchPlaceholder}
                value={search}
                onChange={(e) => handleSearch(e.target.value)}
                className="h-9 w-full rounded-md border bg-card pl-8 pr-3 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-ring"
                aria-label="Buscar en la tabla"
              />
            </div>
          ) : null}
          {toolbar ? <div className="flex items-center gap-2">{toolbar}</div> : null}
        </div>
      ) : null}

      {total === 0 ? (
        <div className="p-4">
          <EmptyState
            title={emptyTitle}
            description={emptyDescription}
            icon={emptyIcon}
            variant="minimal"
          />
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead className="border-b bg-secondary/40 text-left">
                <tr>
                  {columns.map((column, idx) => {
                    const id = column.id ?? String(column.key);
                    const isSorted = sorting?.id === id;
                    return (
                      <th
                        key={id + idx}
                        className={cn(
                          "px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground",
                          column.className
                        )}
                        scope="col"
                      >
                        {column.sortable ? (
                          <button
                            type="button"
                            onClick={() => {
                              setSorting((prev) => {
                                if (prev?.id !== id) return { id, desc: false };
                                if (!prev.desc) return { id, desc: true };
                                return null;
                              });
                            }}
                            className="inline-flex items-center gap-1.5 transition-colors hover:text-foreground"
                          >
                            {column.header}
                            {isSorted && sorting?.desc ? (
                              <ArrowDown className="h-3 w-3" aria-hidden="true" />
                            ) : isSorted ? (
                              <ArrowUp className="h-3 w-3" aria-hidden="true" />
                            ) : (
                              <ChevronsUpDown
                                className="h-3 w-3 opacity-50"
                                aria-hidden="true"
                              />
                            )}
                          </button>
                        ) : (
                          column.header
                        )}
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {visible.map((row, rowIndex) => (
                  <tr
                    key={rowKey ? rowKey(row as T) : start + rowIndex}
                    onClick={onRowClick ? () => onRowClick(row as T) : undefined}
                    className={cn(
                      "border-b border-border/60 last:border-b-0 transition-colors",
                      onRowClick && "cursor-pointer hover:bg-secondary/50"
                    )}
                  >
                    {columns.map((column, colIdx) => (
                      <td
                        key={String(column.key) + colIdx}
                        className={cn("px-4 py-3 align-middle", column.className)}
                      >
                        {column.render
                          ? column.render(row as T)
                          : (row[column.key as keyof T] as ReactNode)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {total > pageSize ? (
            <div className="flex items-center justify-between border-t bg-secondary/30 px-4 py-2.5 text-xs text-muted-foreground">
              <span>
                Mostrando {start + 1}–{Math.min(start + pageSize, total)} de {total}
              </span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  className="rounded-md border bg-card px-2.5 py-1 transition hover:bg-secondary disabled:opacity-50"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  Anterior
                </button>
                <span className="px-1 font-medium">
                  {page + 1} / {totalPages}
                </span>
                <button
                  type="button"
                  className="rounded-md border bg-card px-2.5 py-1 transition hover:bg-secondary disabled:opacity-50"
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                >
                  Siguiente
                </button>
              </div>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
