"use client";

import { AlertTriangle } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <div
          style={{
            display: "flex",
            minHeight: "100vh",
            alignItems: "center",
            justifyContent: "center",
            padding: "2rem",
            backgroundColor: "hsl(var(--background))",
            color: "hsl(var(--foreground))",
            fontFamily:
              'Inter, system-ui, -apple-system, sans-serif',
          }}
        >
          <div
            style={{
              display: "flex",
              maxWidth: "28rem",
              flexDirection: "column",
              alignItems: "center",
              gap: "1rem",
              textAlign: "center",
            }}
          >
            <div
              style={{
                display: "flex",
                height: "3.5rem",
                width: "3.5rem",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "9999px",
                backgroundColor: "hsl(var(--destructive) / 0.1)",
              }}
            >
              <AlertTriangle
                style={{
                  height: "1.75rem",
                  width: "1.75rem",
                  color: "hsl(var(--destructive))",
                }}
              />
            </div>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 600 }}>
              Error cr&iacute;tico
            </h1>
            <p
              style={{
                fontSize: "0.875rem",
                lineHeight: 1.5,
                color: "hsl(var(--muted-foreground))",
              }}
            >
              Ocurri&oacute; un error cr&iacute;tico en la aplicaci&oacute;n.
              Por favor recarga la p&aacute;gina.
            </p>
            <button
              type="button"
              onClick={reset}
              style={{
                display: "inline-flex",
                height: "2.5rem",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "0.5rem",
                padding: "0 1rem",
                fontSize: "0.875rem",
                fontWeight: 500,
                border: "1px solid hsl(var(--border))",
                backgroundColor: "hsl(var(--card))",
                color: "hsl(var(--foreground))",
                cursor: "pointer",
              }}
            >
              Recargar p&aacute;gina
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
