import Link from "next/link";
import { NAV_ITEMS } from "@/constants";

export default function Sidebar() {
  return (
    <aside className="w-64 border-r h-[calc(100vh-65px)] p-4 flex flex-col gap-2 bg-background sticky top-[65px] overflow-y-auto">
      {NAV_ITEMS.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className="flex items-center gap-3 hover:bg-muted p-2 rounded text-muted-foreground hover:text-foreground transition-colors"
        >
          <item.icon size={18} />
          <span>{item.label}</span>
        </Link>
      ))}
    </aside>
  );
}
