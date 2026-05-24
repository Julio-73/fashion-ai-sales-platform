"use client";

import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

import { t } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

type LogoutButtonProps = {
  isCollapsed?: boolean;
};

export function LogoutButton({ isCollapsed = false }: LogoutButtonProps) {
  const router = useRouter();
  const { logout } = useAuthStore();

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <Button
      type="button"
      variant="ghost"
      className={cn("w-full justify-start", isCollapsed && "lg:justify-center lg:px-0")}
      onClick={handleLogout}
    >
      <LogOut className="h-4 w-4" aria-hidden="true" />
      <span className={cn(isCollapsed && "lg:hidden")}>{t.auth.logout.button}</span>
    </Button>
  );
}
