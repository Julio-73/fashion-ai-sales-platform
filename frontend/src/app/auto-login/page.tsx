"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

const ENABLED = process.env.NEXT_PUBLIC_ENABLE_AUTO_LOGIN === "true";

export default function AutoLoginPage() {
  const router = useRouter();

  useEffect(() => {
    if (!ENABLED) {
      router.replace("/login");
      return;
    }

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
    const email = process.env.NEXT_PUBLIC_DEMO_EMAIL ?? "demo@fashionsales.ai";
    const password = process.env.NEXT_PUBLIC_DEMO_PASSWORD ?? "Demo@2024!";

    fetch(`${apiBaseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })
      .then((r) => {
        if (!r.ok) throw new Error("Login failed");
        return r.json();
      })
      .then((data) => {
        localStorage.setItem(
          "ai-sales-agent-auth",
          JSON.stringify({
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            user: data.user,
          })
        );
        router.replace("/dashboard");
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
      Iniciando sesi&oacute;n...
    </div>
  );
}
