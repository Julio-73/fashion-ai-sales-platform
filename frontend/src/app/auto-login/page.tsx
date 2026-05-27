"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AutoLoginPage() {
  const router = useRouter();

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "demo@fashionsales.ai", password: "Demo@2024!" }),
    })
      .then((r) => r.json())
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
      Iniciando sesión...
    </div>
  );
}
