"use client";

import { PipelineDashboard } from "./pipeline-dashboard";
import { PipelineStoreProvider } from "@/store/pipeline-store";

export function PipelineWorkspace() {
  return (
    <PipelineStoreProvider>
      <PipelineDashboard />
    </PipelineStoreProvider>
  );
}
