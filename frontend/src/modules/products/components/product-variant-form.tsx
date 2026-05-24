"use client";

import { FormEvent, useState } from "react";

import { t } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import type { ProductVariant, ProductVariantCreatePayload } from "@/types/product";

const V = t.products.variantForm;

type ProductVariantFormProps = {
  existingVariants: ProductVariant[];
  onAdd: (payload: ProductVariantCreatePayload) => Promise<void>;
};

export function ProductVariantForm({ existingVariants, onAdd }: ProductVariantFormProps) {
  const [sku, setSku] = useState("");
  const [talla, setTalla] = useState("");
  const [color, setColor] = useState("");
  const [stock, setStock] = useState("0");
  const [variantPrice, setVariantPrice] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sku.trim()) {
      setError(V.skuRequired);
      return;
    }
    setIsAdding(true);
    setError(null);
    try {
      await onAdd({
        sku: sku.trim(),
        talla: talla.trim() || null,
        color: color.trim() || null,
        stock: Math.max(0, parseInt(stock, 10) || 0),
        variant_price: variantPrice || null
      });
      setSku("");
      setTalla("");
      setColor("");
      setStock("0");
      setVariantPrice("");
    } catch (err) {
      setError(err instanceof Error ? err.message : V.errorAdd);
    } finally {
      setIsAdding(false);
    }
  }

  return (
    <form className="grid gap-3 rounded-lg border bg-background p-4" onSubmit={handleSubmit}>
      <p className="text-sm font-semibold">{V.heading}</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <input
          className="h-9 rounded-md border bg-card px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          placeholder={V.skuPlaceholder}
          value={sku}
          onChange={(event) => setSku(event.target.value)}
          required
        />
        <input
          className="h-9 rounded-md border bg-card px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          placeholder={V.sizePlaceholder}
          value={talla}
          onChange={(event) => setTalla(event.target.value)}
        />
        <input
          className="h-9 rounded-md border bg-card px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          placeholder={V.colorPlaceholder}
          value={color}
          onChange={(event) => setColor(event.target.value)}
        />
        <input
          className="h-9 rounded-md border bg-card px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          type="number"
          min="0"
          placeholder={V.stockPlaceholder}
          value={stock}
          onChange={(event) => setStock(event.target.value)}
        />
        <input
          className="h-9 rounded-md border bg-card px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          type="number"
          step="0.01"
          min="0"
          placeholder={V.pricePlaceholder}
          value={variantPrice}
          onChange={(event) => setVariantPrice(event.target.value)}
        />
      </div>
      {error ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : null}
      <div className="flex justify-end">
        <Button type="submit" size="sm" disabled={isAdding}>
          {isAdding ? V.adding : V.add}
        </Button>
      </div>
    </form>
  );
}
