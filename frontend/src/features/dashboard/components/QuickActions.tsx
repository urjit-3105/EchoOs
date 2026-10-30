"use client"

import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { UserPlus, FileText, Settings, ShieldAlert } from "lucide-react"
import { toast } from "sonner"

const actions = [
  { label: "Onboard Employee", icon: <UserPlus size={16} />, href: "/employees/invite" },
  { label: "Generate Report", icon: <FileText size={16} />, onClick: () => toast("Reporting is coming soon") },
  { label: "System Settings", icon: <Settings size={16} />, href: "/settings" },
  { label: "Compliance Audit", icon: <ShieldAlert size={16} />, href: "/approvals" },
]

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-2">
        {actions.map((action) =>
          action.href ? (
            <Button
              key={action.label}
              variant="outline"
              className="h-auto py-4 flex flex-col gap-2 items-center justify-center text-xs whitespace-normal text-center"
              nativeButton={false}
              render={<Link href={action.href} />}
            >
              {action.icon}
              {action.label}
            </Button>
          ) : (
            <Button
              key={action.label}
              variant="outline"
              className="h-auto py-4 flex flex-col gap-2 items-center justify-center text-xs whitespace-normal text-center"
              onClick={action.onClick}
            >
              {action.icon}
              {action.label}
            </Button>
          )
        )}
      </CardContent>
    </Card>
  )
}
