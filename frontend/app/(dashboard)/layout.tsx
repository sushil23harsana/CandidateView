import Link from "next/link";
import { LayoutGrid, ListChecks } from "lucide-react";

import { DashboardHeader } from "@/components/dashboard/header";
import { Separator } from "@/components/ui/separator";

const navigation = [
  {
    name: "Jobs",
    href: "/jobs",
    icon: ListChecks
  },
  {
    name: "Insights",
    href: "/insights",
    icon: LayoutGrid
  }
];

export default function DashboardLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-muted/40">
      <div className="flex">
        <aside className="hidden min-h-screen w-64 border-r border-border bg-background px-4 py-6 lg:block">
          <div className="px-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              HireRank
            </p>
            <h2 className="mt-2 text-lg font-semibold">Manager Console</h2>
          </div>
          <Separator className="my-4" />
          <nav className="space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground"
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </Link>
            ))}
          </nav>
        </aside>
        <div className="flex min-h-screen flex-1 flex-col">
          <DashboardHeader />
          <main className="flex-1 px-6 py-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
