"use client";

import { ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { t } from "@/lib/i18n";
import { ApiError } from "@/services/api-client";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [empresaId, setEmpresaId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const L = t.auth.login;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login({
        email,
        password,
        ...(empresaId ? { empresa_id: empresaId } : {})
      });
      router.replace("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(L.errorFallback);
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-background lg:grid-cols-[1.05fr_0.95fr]">
      <section className="flex items-center justify-center px-4 py-10 sm:px-6 lg:px-10">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold">{L.brand}</p>
              <p className="text-xs text-muted-foreground">{L.subtitle}</p>
            </div>
          </div>

          <div className="rounded-lg border bg-card p-6 shadow-sm">
            <div className="mb-6">
              <h1 className="text-2xl font-semibold text-card-foreground">{L.heading}</h1>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {L.description}
              </p>
            </div>

            <form className="space-y-4" onSubmit={handleSubmit}>
              <label className="block">
                <span className="text-sm font-medium">{L.emailLabel}</span>
                <input
                  className="mt-1 h-10 w-full rounded-md border bg-background px-3 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-ring"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                  required
                />
              </label>

              <label className="block">
                <span className="text-sm font-medium">{L.passwordLabel}</span>
                <input
                  className="mt-1 h-10 w-full rounded-md border bg-background px-3 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-ring"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  required
                />
              </label>

              <label className="block">
                <span className="text-sm font-medium">{L.companyIdLabel}</span>
                <input
                  className="mt-1 h-10 w-full rounded-md border bg-background px-3 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-ring"
                  type="text"
                  value={empresaId}
                  onChange={(event) => setEmpresaId(event.target.value)}
                  placeholder={L.companyIdPlaceholder}
                />
              </label>

              {error ? (
                <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </div>
              ) : null}

              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? L.signingIn : L.signIn}
              </Button>
            </form>
          </div>
        </div>
      </section>

      <section className="hidden border-l bg-card p-10 lg:flex lg:flex-col lg:justify-between">
        <div>
          <p className="text-sm font-semibold text-primary">{L.enterpriseAuth}</p>
          <h2 className="mt-4 max-w-lg text-4xl font-semibold leading-tight">
            {L.heroHeading}
          </h2>
          <p className="mt-4 max-w-xl text-sm leading-6 text-muted-foreground">
            {L.heroDescription}
          </p>
        </div>
        <div className="grid gap-3 text-sm text-muted-foreground">
          <div className="rounded-lg border bg-background p-4">{L.featureTenant}</div>
          <div className="rounded-lg border bg-background p-4">{L.featureRoles}</div>
          <div className="rounded-lg border bg-background p-4">{L.featureTokens}</div>
        </div>
      </section>
    </main>
  );
}

