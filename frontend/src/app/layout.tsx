import type { Metadata } from "next";
import type { ReactNode } from "react";
import { t } from "@/lib/i18n";
import { AuthStoreProvider } from "@/store/auth-store";
import "./globals.css";

export const metadata: Metadata = {
  title: t.metadata.title,
  description: t.metadata.description
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang={t.metadata.lang}>
      <body>
        <AuthStoreProvider>{children}</AuthStoreProvider>
      </body>
    </html>
  );
}
