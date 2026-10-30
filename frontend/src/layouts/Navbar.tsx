import Link from "next/link";
import { User, Bell, Search } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function Navbar() {
  return (
    <nav className="flex items-center justify-between p-4 border-b bg-background sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <div className="font-bold text-xl tracking-tight text-primary">Enterprise AI</div>
      </div>
      <div className="flex items-center gap-4">
        <button className="p-2 hover:bg-muted rounded-full"><Search size={20} /></button>
        <button className="p-2 hover:bg-muted rounded-full"><Bell size={20} /></button>
        <ThemeToggle />
        <button className="p-2 hover:bg-muted rounded-full bg-secondary text-secondary-foreground"><User size={20} /></button>
      </div>
    </nav>
  );
}
