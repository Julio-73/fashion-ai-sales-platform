import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { Avatar, AvatarStack } from "@/components/ui/avatar";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { EmptyState } from "@/components/feedback/empty-state";
import { Toaster, useToasts } from "@/components/feedback/toast";
import { MetricCard } from "@/components/ui/metric-card";
import { Sparkles, Users } from "lucide-react";

describe("Avatar", () => {
  it("renders initials from full name", () => {
    render(<Avatar name="María López" />);
    const avatar = screen.getByText("ML");
    expect(avatar).toBeInTheDocument();
  });

  it("renders placeholder for empty names", () => {
    const { container } = render(<Avatar name="" />);
    expect(container.querySelector("span span")?.textContent).toBe("");
  });

  it("renders up to 2 characters for one-word names", () => {
    render(<Avatar name="Cher" />);
    expect(screen.getByText("CH")).toBeInTheDocument();
  });
});

describe("AvatarStack", () => {
  it("renders up to 3 visible avatars and a +N counter", () => {
    render(
      <AvatarStack
        names={["Ana Pérez", "Luis García", "Sofía López", "Mateo Ruiz", "Eva Soto"]}
      />
    );
    expect(screen.getByText("AP")).toBeInTheDocument();
    expect(screen.getByText("LG")).toBeInTheDocument();
    expect(screen.getByText("SL")).toBeInTheDocument();
    expect(screen.getByText("+2")).toBeInTheDocument();
  });

  it("does not render a counter when 3 or fewer", () => {
    render(<AvatarStack names={["Ana Pérez", "Luis García"]} />);
    expect(screen.queryByText(/\+\d/)).not.toBeInTheDocument();
  });
});

describe("Breadcrumbs", () => {
  it("renders all items joined by /", () => {
    render(
      <Breadcrumbs
        items={[
          { label: "CRM", href: "/dashboard/customers" },
          { label: "Detalle" }
        ]}
      />
    );
    expect(screen.getByText("CRM")).toBeInTheDocument();
    expect(screen.getByText("Detalle")).toBeInTheDocument();
  });
});

describe("EmptyState", () => {
  it("renders with icon, title and description", () => {
    render(
      <EmptyState
        icon={Users}
        title="Sin datos"
        description="Aún no hay información para mostrar."
      />
    );
    expect(screen.getByText("Sin datos")).toBeInTheDocument();
    expect(screen.getByText("Aún no hay información para mostrar.")).toBeInTheDocument();
  });

  it("supports action as a node", () => {
    render(
      <EmptyState
        icon={Users}
        title="Sin datos"
        description="Crea un cliente"
        action={<button>Crear</button>}
      />
    );
    expect(screen.getByRole("button", { name: "Crear" })).toBeInTheDocument();
  });
});

describe("Toaster", () => {
  function Demo() {
    const { push, dismiss } = useToasts();
    return (
      <>
        <button onClick={() => push({ title: "Hola" })}>show</button>
        <Toaster toasts={[]} onDismiss={dismiss} />
      </>
    );
  }

  it("renders without crashing", () => {
    render(<Demo />);
  });
});

describe("MetricCard", () => {
  it("renders title, value and icon", () => {
    render(
      <MetricCard
        title="Total"
        value="1.250"
        icon={Sparkles}
        iconTone="primary"
        description="Clientes"
      />
    );
    expect(screen.getByText("Total")).toBeInTheDocument();
    expect(screen.getByText("1.250")).toBeInTheDocument();
    expect(screen.getByText("Clientes")).toBeInTheDocument();
  });
});
