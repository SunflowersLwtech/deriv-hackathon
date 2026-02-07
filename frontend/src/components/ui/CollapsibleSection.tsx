"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface CollapsibleSectionProps {
  title: string;
  defaultOpen?: boolean;
  className?: string;
  headerClassName?: string;
  children: React.ReactNode;
  badge?: React.ReactNode;
}

export default function CollapsibleSection({
  title,
  defaultOpen = false,
  className,
  headerClassName,
  children,
  badge,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={cn("border border-border rounded-md overflow-hidden", className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "w-full flex items-center justify-between px-4 py-3 hover:bg-surface transition-colors",
          headerClassName
        )}
      >
        <div className="flex items-center gap-2.5">
          <span
            className={cn(
              "text-xs mono-data text-muted transition-transform duration-200",
              isOpen && "rotate-90"
            )}
          >
            ▶
          </span>
          <span className="text-xs font-semibold tracking-wider text-muted uppercase mono-data">
            {title}
          </span>
        </div>
        {badge}
      </button>

      {isOpen && (
        <div className="border-t border-border animate-fade-in">
          {children}
        </div>
      )}
    </div>
  );
}
