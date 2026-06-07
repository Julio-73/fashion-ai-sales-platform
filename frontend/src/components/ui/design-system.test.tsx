import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { Button } from "@/components/ui/button";
import { Kbd, KbdShortcut } from "@/components/ui/kbd";
import { StatusPill } from "@/components/ui/status-pill";

describe("Button", () => {
  it("renders a button with the default classes", () => {
    render(<Button>Guardar</Button>);
    const btn = screen.getByRole("button", { name: "Guardar" });
    expect(btn).toBeInTheDocument();
    expect(btn.className).toMatch(/btn-base/);
  });

  it("renders destructive variant", () => {
    render(<Button variant="destructive">Eliminar</Button>);
    const btn = screen.getByRole("button", { name: "Eliminar" });
    expect(btn.className).toMatch(/bg-destructive/);
  });

  it("renders gradient variant", () => {
    render(<Button variant="gradient">Activar</Button>);
    const btn = screen.getByRole("button", { name: "Activar" });
    expect(btn.className).toMatch(/from-primary/);
  });

  it("renders all sizes", () => {
    const { rerender } = render(<Button size="sm">A</Button>);
    expect(screen.getByRole("button").className).toMatch(/h-8/);
    rerender(<Button size="lg">A</Button>);
    expect(screen.getByRole("button").className).toMatch(/h-11/);
    rerender(<Button size="icon">A</Button>);
    expect(screen.getByRole("button").className).toMatch(/h-10 w-10/);
  });
});

describe("Kbd", () => {
  it("renders children inside a kbd element", () => {
    render(<Kbd>Esc</Kbd>);
    const kbd = screen.getByText("Esc");
    expect(kbd.tagName.toLowerCase()).toBe("kbd");
  });
});

describe("KbdShortcut", () => {
  it("renders multiple keys separated visually", () => {
    render(<KbdShortcut keys={["⌘", "K"]} />);
    expect(screen.getByText("⌘")).toBeInTheDocument();
    expect(screen.getByText("K")).toBeInTheDocument();
  });
});

describe("StatusPill", () => {
  it("renders tone variants", () => {
    const tones: Array<"success" | "warning" | "destructive" | "primary"> = [
      "success",
      "warning",
      "destructive",
      "primary"
    ];
    tones.forEach((tone) => {
      const { unmount } = render(<StatusPill tone={tone}>{tone}</StatusPill>);
      const span = screen.getByText(tone);
      expect(span.className).toMatch(new RegExp(`text-${tone}`));
      unmount();
    });
  });

  it("renders the dot indicator when dot is true", () => {
    const { container } = render(<StatusPill dot>con dot</StatusPill>);
    expect(container.querySelectorAll("span").length).toBeGreaterThanOrEqual(2);
  });

  it("renders an icon when provided", () => {
    render(
      <StatusPill tone="primary" icon={<span data-testid="icon-x" />}>
        con icono
      </StatusPill>
    );
    expect(screen.getByTestId("icon-x")).toBeInTheDocument();
  });

  it("renders size variants", () => {
    const { rerender } = render(<StatusPill size="sm">A</StatusPill>);
    expect(screen.getByText("A").className).toMatch(/text-\[10px\]/);
    rerender(<StatusPill size="lg">A</StatusPill>);
    expect(screen.getByText("A").className).toMatch(/text-sm/);
  });
});
