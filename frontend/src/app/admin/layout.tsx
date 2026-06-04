import type { ReactNode } from "react";

import { AdminStoreProvider } from "@/store/admin-store";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AdminStoreProvider>{children}</AdminStoreProvider>;
}
