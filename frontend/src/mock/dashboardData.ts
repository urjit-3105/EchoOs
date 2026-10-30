import { generateEmployees } from './generateData'

const employees = generateEmployees(100)

// Aggregations
export const totalEmployees = employees.length
export const completedWorkflows = employees.filter(e => e.status === 'success').length
export const pendingWorkflows = employees.filter(e => e.status === 'warning' || e.status === 'info').length
export const delayedWorkflows = employees.filter(e => e.status === 'error').length

// Compliance Average
export const averageCompliance = Math.round(
  employees.reduce((acc, curr) => acc + curr.complianceScore, 0) / employees.length
)

// Department Distribution for Chart
const deptCounts = employees.reduce((acc, emp) => {
  acc[emp.department] = (acc[emp.department] || 0) + 1
  return acc
}, {} as Record<string, number>)

export const departmentDistributionData = Object.entries(deptCounts).map(([name, value]) => ({
  name,
  value
}))

// Workflow Status Data for Chart
export const workflowStatusData = [
  { name: 'Success', value: completedWorkflows, fill: 'var(--color-success)' },
  { name: 'Pending', value: pendingWorkflows, fill: 'var(--color-warning)' },
  { name: 'Delayed', value: delayedWorkflows, fill: 'var(--color-error)' },
]

// Weekly Onboarding Dummy Data for Chart
export const weeklyOnboardingData = [
  { week: 'Week 1', onboarded: 12 },
  { week: 'Week 2', onboarded: 19 },
  { week: 'Week 3', onboarded: 15 },
  { week: 'Week 4', onboarded: 22 },
  { week: 'Week 5', onboarded: 18 },
  { week: 'Week 6', onboarded: 27 },
]

// System Health Data for Chart
export const systemHealthData = [
  { time: '00:00', uptime: 99.9, latency: 120 },
  { time: '04:00', uptime: 99.9, latency: 110 },
  { time: '08:00', uptime: 99.8, latency: 180 },
  { time: '12:00', uptime: 99.9, latency: 150 },
  { time: '16:00', uptime: 99.7, latency: 210 },
  { time: '20:00', uptime: 99.9, latency: 140 },
]

export const recentEmployees = employees.sort((a, b) => 
  new Date(b.onboardingDate).getTime() - new Date(a.onboardingDate).getTime()
).slice(0, 5)

export const announcements = [
  { id: 1, title: 'Q3 Townhall Meeting', date: 'Oct 15, 2026', type: 'Event' },
  { id: 2, title: 'New Security Policy', date: 'Oct 12, 2026', type: 'Policy' },
  { id: 3, title: 'Platform Maintenance', date: 'Oct 10, 2026', type: 'System' },
]
