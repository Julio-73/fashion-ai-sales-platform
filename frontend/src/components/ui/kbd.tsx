import { cn } from "@/lib/utils";

type KbdProps = {
  children: React.ReactNode;
  className?: string;
};

export function Kbd({ children, className }: KbdProps) {
  return <kbd className={cn("kbd", className)}>{children}</kbd>;
}

type KbdShortcutProps = {
  keys: string[];
  className?: string;
};

export function KbdShortcut({ keys, className }: KbdShortcutProps) {
  return (
    <span className={cn("inline-flex items-center gap-1", className)}>
      {keys.map((k, i) => (
        <Kbd key={i}>{k}</Kbd>
      ))}
    </span>
  );
}
