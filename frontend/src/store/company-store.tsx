"use client";

import { createContext, type ReactNode, useContext } from "react";

import type { CompanySummary } from "@/types/company";

type CompanyStore = {
  activeCompany: CompanySummary | null;
};

const defaultStore: CompanyStore = {
  activeCompany: null
};

const CompanyStoreContext = createContext<CompanyStore>(defaultStore);

export function CompanyStoreProvider({
  value,
  children
}: {
  value: CompanyStore;
  children: ReactNode;
}) {
  return <CompanyStoreContext.Provider value={value}>{children}</CompanyStoreContext.Provider>;
}

export function useCompanyStore() {
  return useContext(CompanyStoreContext);
}

