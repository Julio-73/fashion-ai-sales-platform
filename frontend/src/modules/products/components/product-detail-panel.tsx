"use client";

import { useState } from "react";
import { DollarSign, ImageIcon, Package, Trash2, Type } from "lucide-react";

import { t } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProductStatusBadge } from "@/modules/products/components/product-status-badge";
import { ProductVariantForm } from "@/modules/products/components/product-variant-form";
import type { ProductImageCreatePayload, ProductSummary, ProductVariantCreatePayload, ProductVariantUpdatePayload } from "@/types/product";

const D = t.products.detail;

type ProductDetailPanelProps = {
  product: ProductSummary | null;
  accessToken: string;
  onEdit: (product: ProductSummary) => void;
  onDelete: (product: ProductSummary) => Promise<void>;
  onAddVariant: (productId: string, payload: ProductVariantCreatePayload) => Promise<void>;
  onUpdateVariant: (productId: string, variantId: string, payload: ProductVariantUpdatePayload) => Promise<void>;
  onDeleteVariant: (productId: string, variantId: string) => Promise<void>;
  onAddImage: (productId: string, payload: ProductImageCreatePayload) => Promise<void>;
  onDeleteImage: (productId: string, imageId: string) => Promise<void>;
};

export function ProductDetailPanel({
  product,
  accessToken,
  onEdit,
  onDelete,
  onAddVariant,
  onUpdateVariant,
  onDeleteVariant,
  onAddImage,
  onDeleteImage
}: ProductDetailPanelProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState("");
  const [isAddingImage, setIsAddingImage] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);

  if (!product) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>{D.emptyTitle}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-dashed p-6 text-sm leading-6 text-muted-foreground">
            {D.emptyDesc}
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentProduct = product;

  async function handleAddVariant(payload: ProductVariantCreatePayload) {
    await onAddVariant(currentProduct.id, payload);
  }

  async function handleAddImage() {
    if (!imageUrl.trim()) return;
    setIsAddingImage(true);
    setImageError(null);
    try {
      await onAddImage(currentProduct.id, { image_url: imageUrl.trim() });
      setImageUrl("");
    } catch (err) {
            setImageError(err instanceof Error ? err.message : D.errorAddImage);
    } finally {
      setIsAddingImage(false);
    }
  }

  return (
    <Card className="h-full">
      <CardHeader className="border-b">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-secondary text-primary">
              <Package className="h-5 w-5" aria-hidden="true" />
            </div>
            <CardTitle>{product.name}</CardTitle>
            <p className="mt-1 text-xs text-muted-foreground">/{product.slug}</p>
          </div>
          <ProductStatusBadge status={product.status} />
        </div>
      </CardHeader>
      <CardContent className="grid gap-5 pt-5">
        <div className="grid gap-3">
          {product.category ? (
            <div className="flex items-center gap-3 rounded-lg border bg-background px-3 py-2">
              <Type className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">{D.category}</p>
                <p className="truncate text-sm font-medium">{product.category}</p>
              </div>
            </div>
          ) : null}
          {product.base_price ? (
            <div className="flex items-center gap-3 rounded-lg border bg-background px-3 py-2">
              <DollarSign className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">{D.basePrice}</p>
                <p className="truncate text-sm font-medium">${parseFloat(product.base_price).toFixed(2)}</p>
              </div>
            </div>
          ) : null}
        </div>

        {product.description ? (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{D.description}</p>
            <p className="mt-2 rounded-lg border bg-background p-3 text-sm leading-6 text-muted-foreground">
              {product.description}
            </p>
          </div>
        ) : null}

        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {D.variantsSection.replace("{count}", String(product.variants.length))}
          </p>
          {product.variants.length > 0 ? (
            <div className="grid gap-2">
              {product.variants.map((variant) => (
                <div key={variant.id} className="flex items-center justify-between rounded-lg border bg-background px-3 py-2 text-sm">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{variant.sku}</p>
                    <p className="text-xs text-muted-foreground">
                      {[variant.talla, variant.color].filter(Boolean).join(" / ") || D.noAttributes}
                      {variant.variant_price ? ` — $${parseFloat(variant.variant_price).toFixed(2)}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="tabular-nums">
                      <span className="text-muted-foreground">{D.stock}</span>
                      <span className="font-medium">{variant.available_stock}</span>
                      {variant.reserved_stock > 0 ? (
                        <span className="text-muted-foreground"> ({variant.reserved_stock}{D.reserved})</span>
                      ) : null}
                    </span>
                    <button
                      type="button"
                      className="text-muted-foreground hover:text-destructive"
                      onClick={async () => {
                        try {
                          await onDeleteVariant(product.id, variant.id);
                        } catch {
                          // error handled upstream
                        }
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                      <span className="sr-only">{D.deleteVariant}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">
              {D.noVariants}
            </p>
          )}
          <div className="mt-3">
            <ProductVariantForm existingVariants={product.variants} onAdd={handleAddVariant} />
          </div>
        </div>

        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {D.imagesSection.replace("{count}", String(product.images.length))}
          </p>
          {product.images.length > 0 ? (
            <div className="grid grid-cols-3 gap-2">
              {product.images.map((image) => (
                <div key={image.id} className="group relative aspect-square overflow-hidden rounded-lg border bg-muted">
                  <img
                    src={image.image_url}
                    alt=""
                    className="h-full w-full object-cover"
                      onError={(event) => {
                      (event.target as HTMLImageElement).src = `data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'><rect fill='%23f1f5f9' width='100' height='100'/><text x='50%25' y='50%25' fill='%2394a3b8' text-anchor='middle' dy='.3em' font-size='10'>${D.noImage}</text></svg>`;
                    }}
                  />
                  <button
                    type="button"
                    className="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-background/80 text-muted-foreground opacity-0 shadow-sm transition-opacity hover:text-destructive group-hover:opacity-100"
                    onClick={async () => {
                      try {
                        await onDeleteImage(product.id, image.id);
                      } catch {
                        // error handled upstream
                      }
                    }}
                  >
                    <Trash2 className="h-3 w-3" aria-hidden="true" />
                    <span className="sr-only">{D.deleteImage}</span>
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">
              {D.noImages}
            </p>
          )}
          <div className="mt-3 flex gap-2">
            <input
              className="h-9 flex-1 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder={D.imageUrlPlaceholder}
              value={imageUrl}
              onChange={(event) => setImageUrl(event.target.value)}
            />
            <Button type="button" size="sm" disabled={isAddingImage || !imageUrl.trim()} onClick={handleAddImage}>
              {isAddingImage ? D.adding : D.add}
            </Button>
          </div>
          {imageError ? (
            <p className="mt-1 text-sm text-destructive">{imageError}</p>
          ) : null}
        </div>

        {deleteError ? (
          <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {deleteError}
          </div>
        ) : null}

        <div className="grid gap-2 sm:grid-cols-2">
          <Button type="button" variant="secondary" onClick={() => onEdit(product)}>
            {D.edit}
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={isDeleting}
            onClick={async () => {
              setIsDeleting(true);
              setDeleteError(null);
              try {
                await onDelete(product);
              } catch (err) {
                setDeleteError(err instanceof Error ? err.message : D.errorDelete);
              } finally {
                setIsDeleting(false);
              }
            }}
          >
            {isDeleting ? D.deleting : D.delete}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
