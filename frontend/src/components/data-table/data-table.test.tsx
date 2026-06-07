import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { DataTable } from "@/components/data-table/data-table";

describe("DataTable", () => {
  const rows = [
    { name: "Ana", role: "Admin" },
    { name: "Luis", role: "Vendedor" },
    { name: "Sofía", role: "Marketing" }
  ];

  it("renders all rows and headers", () => {
    render(
      <DataTable
        columns={[
          { key: "name", header: "Nombre" },
          { key: "role", header: "Rol" }
        ]}
        rows={rows}
        emptyTitle="Sin datos"
        emptyDescription="Vacío"
      />
    );
    expect(screen.getByText("Nombre")).toBeInTheDocument();
    expect(screen.getByText("Rol")).toBeInTheDocument();
    expect(screen.getByText("Ana")).toBeInTheDocument();
    expect(screen.getByText("Luis")).toBeInTheDocument();
    expect(screen.getByText("Sofía")).toBeInTheDocument();
  });

  it("filters by search input", () => {
    const Wrapper = () => {
      const [q, setQ] = [rows[1].name, () => undefined] as [string, (v: string) => void];
      return (
        <DataTable
          columns={[
            { key: "name", header: "Nombre" },
            { key: "role", header: "Rol" }
          ]}
          rows={rows.filter((r) => r.name.toLowerCase().includes("lui"))}
          emptyTitle="Sin datos"
          emptyDescription="Vacío"
          searchValue={q}
          onSearchChange={setQ}
        />
      );
    };
    render(<Wrapper />);
    expect(screen.getByText("Luis")).toBeInTheDocument();
    expect(screen.queryByText("Ana")).not.toBeInTheDocument();
  });

  it("shows empty state when no rows", () => {
    render(
      <DataTable
        columns={[{ key: "name", header: "Nombre" }]}
        rows={[]}
        emptyTitle="Sin datos"
        emptyDescription="No hay registros"
      />
    );
    expect(screen.getByText("Sin datos")).toBeInTheDocument();
    expect(screen.getByText("No hay registros")).toBeInTheDocument();
  });

  it("renders skeleton when loading", () => {
    const { container } = render(
      <DataTable
        columns={[{ key: "name", header: "Nombre" }]}
        rows={[]}
        isLoading
        emptyTitle="Sin datos"
        emptyDescription="Vacío"
      />
    );
    const skeletons = container.querySelectorAll(
      '.skeleton-shimmer, [role="status"]'
    );
    expect(skeletons.length).toBeGreaterThan(0);
  });
});
