"use client";

import { useCompanyStore } from "@/store/company-store";

export function useCompanyContext() {
  return useCompanyStore();
}

