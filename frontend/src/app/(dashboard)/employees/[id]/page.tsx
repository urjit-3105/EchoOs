import { EmployeeDetails } from "@/features/employees/components/EmployeeDetails"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"

export default async function EmployeePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params

  return (
    <div className="space-y-6">
      <div>
        <Link href="/employees">
          <Button variant="ghost" size="sm" className="pl-0 text-muted-foreground hover:text-foreground">
            <ArrowLeft size={16} className="mr-2" /> Back to Employees
          </Button>
        </Link>
      </div>
      <EmployeeDetails employeeId={id} />
    </div>
  )
}
