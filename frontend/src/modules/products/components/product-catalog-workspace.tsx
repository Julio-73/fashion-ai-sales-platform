"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Package, Plus, Search, SlidersHorizontal } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { t } from "@/lib/i18n";
import { DataTable } from "@/components/data-table/data-table";
import { EmptyState } from "@/components/feedback/empty-state";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ProductDetailPanel } from "@/modules/products/components/product-detail-panel";
import { ProductFormModal } from "@/modules/products/components/product-form-modal";
import { ProductStatusBadge, statusLabel } from "@/modules/products/components/product-status-badge";
import {
  addProductImage,
  createProduct,
  createVariant,
  deleteProduct,
  deleteProductImage,
  deleteVariant,
  listProducts,
  updateProduct,
  updateVariant
} from "@/modules/products/services/products-api";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";
import type { ProductCreatePayload, ProductImageCreatePayload, ProductStatus, ProductSummary, ProductVariantCreatePayload, ProductVariantUpdatePayload } from "@/types/product";

const W = t.products.workspace;
const productStatuses: Array<ProductStatus | "all"> = ["all", "active", "inactive", "draft"];

export function ProductCatalogWorkspace() {
  const { accessToken, refreshSession } = useAuthStore();
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<ProductSummary | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ProductStatus | "all">("all");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const limit = 10;

  useEffect(() => {
    if (!accessToken) return;
    let isActive = true;
    let retried = false;

    setIsLoading(true);
    setError(null);

    listProducts({
      accessToken,
      search: search || undefined,
      status: statusFilter !== "all" ? statusFilter : undefined,
      limit,
      offset
    })
      .then((response) => {
        if (!isActive) return;
        setProducts(response.items);
        setTotal(response.total);
        setSelectedProduct((current) => current ?? response.items[0] ?? null);
      })
      .catch((err) => {
        if (!isActive) return;
        if (!retried && err instanceof ApiError && err.status === 401) {
          retried = true;
          refreshSession();
          return;
        }
        setError(W.errorLoad);
        setProducts([]);
        setTotal(0);
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, [accessToken, statusFilter, offset, search, refreshSession]);

  const tableRows = useMemo(
    () =>
      products.map((product) => ({
        product: (
          <button
            type="button"
            className="text-left"
            onClick={() => setSelectedProduct(product)}
          >
            <span className="block font-medium text-foreground">{product.name}</span>
            <span className="text-xs text-muted-foreground">{product.slug}</span>
          </button>
        ),
        status: <ProductStatusBadge status={product.status} />,
        category: product.category ?? "—",
        variants: String(product.variants.length),
        price: product.base_price ? `$${parseFloat(product.base_price).toFixed(2)}` : "—"
      })),
    [products]
  );

  function openCreateModal() {
    setModalMode("create");
    setSelectedProduct(null);
    setIsModalOpen(true);
  }

  function openEditModal(product: ProductSummary) {
    setModalMode("edit");
    setSelectedProduct(product);
    setIsModalOpen(true);
  }

  async function handleSubmit(payload: ProductCreatePayload) {
    if (!accessToken) throw new Error("No access token available");
    if (modalMode === "create") {
      const created = await createProduct(accessToken, payload);
      setProducts((current) => [created, ...current]);
      setSelectedProduct(created);
      setTotal((current) => current + 1);
      return;
    }

    if (!selectedProduct) throw new Error("No product selected for editing");
    const updated = await updateProduct(accessToken, selectedProduct.id, payload);
    setProducts((current) => current.map((p) => (p.id === updated.id ? updated : p)));
    setSelectedProduct(updated);
  }

  async function handleDelete(product: ProductSummary) {
    if (!accessToken) throw new Error("No access token available");
    await deleteProduct(accessToken, product.id);
    setProducts((current) => current.filter((item) => item.id !== product.id));
    setSelectedProduct((current) => (current?.id === product.id ? null : current));
    setTotal((current) => Math.max(0, current - 1));
  }

  async function handleAddVariant(productId: string, payload: ProductVariantCreatePayload) {
    if (!accessToken) throw new Error("No access token available");
    const variant = await createVariant(accessToken, productId, payload);
    setProducts((current) =>
      current.map((p) =>
        p.id === productId
          ? { ...p, variants: [...p.variants, variant] }
          : p
      )
    );
    setSelectedProduct((current) =>
      current?.id === productId
        ? { ...current, variants: [...current.variants, variant] }
        : current
    );
  }

  async function handleUpdateVariant(productId: string, variantId: string, payload: ProductVariantUpdatePayload) {
    if (!accessToken) throw new Error("No access token available");
    const updated = await updateVariant(accessToken, productId, variantId, payload);
    setProducts((current) =>
      current.map((p) =>
        p.id === productId
          ? { ...p, variants: p.variants.map((v) => (v.id === variantId ? updated : v)) }
          : p
      )
    );
    setSelectedProduct((current) =>
      current?.id === productId
        ? { ...current, variants: current.variants.map((v) => (v.id === variantId ? updated : v)) }
        : current
    );
  }

  async function handleDeleteVariant(productId: string, variantId: string) {
    if (!accessToken) throw new Error("No access token available");
    await deleteVariant(accessToken, productId, variantId);
    setProducts((current) =>
      current.map((p) =>
        p.id === productId
          ? { ...p, variants: p.variants.filter((v) => v.id !== variantId) }
          : p
      )
    );
    setSelectedProduct((current) =>
      current?.id === productId
        ? { ...current, variants: current.variants.filter((v) => v.id !== variantId) }
        : current
    );
  }

  async function handleAddImage(productId: string, payload: ProductImageCreatePayload) {
    if (!accessToken) throw new Error("No access token available");
    const image = await addProductImage(accessToken, productId, payload);
    setProducts((current) =>
      current.map((p) =>
        p.id === productId
          ? { ...p, images: [...p.images, image] }
          : p
      )
    );
    setSelectedProduct((current) =>
      current?.id === productId
        ? { ...current, images: [...current.images, image] }
        : current
    );
  }

  async function handleDeleteImage(productId: string, imageId: string) {
    if (!accessToken) throw new Error("No access token available");
    await deleteProductImage(accessToken, productId, imageId);
    setProducts((current) =>
      current.map((p) =>
        p.id === productId
          ? { ...p, images: p.images.filter((img) => img.id !== imageId) }
          : p
      )
    );
    setSelectedProduct((current) =>
      current?.id === productId
        ? { ...current, images: current.images.filter((img) => img.id !== imageId) }
        : current
    );
  }

  function refreshSelectedProduct() {
    if (!accessToken || !selectedProduct) return;
    listProducts({
      accessToken,
      search: search || undefined,
      status: statusFilter !== "all" ? statusFilter : undefined,
      limit,
      offset
    }).then((response) => {
      const updated = response.items.find((p) => p.id === selectedProduct.id);
      if (updated) setSelectedProduct(updated);
    }).catch(() => undefined);
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
      <div className="grid gap-5">
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_200px_auto]">
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
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value as ProductStatus | "all");
                setOffset(0);
              }}
            >
              {productStatuses.map((status) => (
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
          title={W.tableHeaderProduct}
          description={`${total} ${total === 1 ? t.products.page.title.toLowerCase() : `${t.products.page.title.toLowerCase()}`}`}
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
                { key: "product", header: W.tableHeaderProduct },
                { key: "status", header: W.tableHeaderStatus },
                { key: "category", header: W.tableHeaderCategory },
                { key: "variants", header: W.tableHeaderVariants },
                { key: "price", header: W.tableHeaderPrice }
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
            ) : products.length ? (
              <AnimatePresence>
                {products.map((product) => (
                  <motion.button
                    key={product.id}
                    type="button"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 8 }}
                    className="rounded-lg border bg-card p-4 text-left shadow-sm"
                    onClick={() => setSelectedProduct(product)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium">{product.name}</p>
                        <p className="mt-1 text-sm text-muted-foreground">{product.category ?? W.fallbackCategory}</p>
                      </div>
                      <ProductStatusBadge status={product.status} />
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                      <span>{product.variants.length} variant{product.variants.length === 1 ? "" : "s"}</span>
                      {product.base_price ? (
                        <span>${parseFloat(product.base_price).toFixed(2)}</span>
                      ) : null}
                    </div>
                  </motion.button>
                ))}
              </AnimatePresence>
            ) : (
              <EmptyState
                icon={Package}
                title={W.emptyTitle}
                description={W.emptyDesc}
              />
            )}
          </div>

          <div className="flex items-center justify-between pt-2 text-sm text-muted-foreground">
            <span>
              {total > 0
                ? W.paginationShowing.replace("{start}", String(offset + 1)).replace("{end}", String(offset + products.length)).replace("{total}", String(total))
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

      <ProductDetailPanel
        product={selectedProduct}
        accessToken={accessToken ?? ""}
        onEdit={openEditModal}
        onDelete={handleDelete}
        onAddVariant={handleAddVariant}
        onUpdateVariant={handleUpdateVariant}
        onDeleteVariant={handleDeleteVariant}
        onAddImage={handleAddImage}
        onDeleteImage={handleDeleteImage}
      />

      <ProductFormModal
        open={isModalOpen}
        mode={modalMode}
        product={modalMode === "edit" ? selectedProduct : null}
        onOpenChange={setIsModalOpen}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
