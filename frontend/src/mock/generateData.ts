import { faker } from '@faker-js/faker'

export type EmployeeStatus = 'success' | 'warning' | 'error' | 'info' | 'default'

export interface Document {
  id: string
  name: string
  type: string
  uploadDate: string
  size: string
}

export interface TimelineEvent {
  id: string
  title: string
  description: string
  date: string
  status: 'completed' | 'in-progress' | 'pending'
}

export interface Activity {
  id: string
  action: string
  timestamp: string
}

export interface Employee {
  id: string
  name: string
  email: string
  role: string
  department: string
  status: EmployeeStatus
  onboardingDate: string
  complianceScore: number
  manager: string
  workflowStage: string
  documents: Document[]
  timeline: TimelineEvent[]
  recentActivity: Activity[]
}

const DEPARTMENTS = ['Engineering', 'Product', 'Design', 'Marketing', 'Sales', 'HR', 'Finance']
const ROLES = ['Manager', 'Senior Engineer', 'Software Engineer', 'Designer', 'Product Manager', 'Analyst', 'Specialist']
const STATUSES: EmployeeStatus[] = ['success', 'warning', 'error', 'info', 'default']
const STAGES = ['Offer Accepted', 'Verification', 'Document Review', 'Compliance', 'IT Provisioning', 'Finance', 'Learning', 'Manager Approval', 'Completed']

export function generateEmployees(count: number = 100): Employee[] {
  faker.seed(123)
  
  return Array.from({ length: count }).map(() => ({
    id: faker.string.uuid(),
    name: faker.person.fullName(),
    email: faker.internet.email(),
    role: faker.helpers.arrayElement(ROLES),
    department: faker.helpers.arrayElement(DEPARTMENTS),
    status: faker.helpers.arrayElement(STATUSES),
    onboardingDate: faker.date.recent({ days: 90 }).toISOString(),
    complianceScore: faker.number.int({ min: 60, max: 100 }),
    manager: faker.person.fullName(),
    workflowStage: faker.helpers.arrayElement(STAGES),
    documents: [
      { id: faker.string.uuid(), name: 'Offer_Letter.pdf', type: 'PDF', uploadDate: faker.date.recent().toISOString(), size: '2.4 MB' },
      { id: faker.string.uuid(), name: 'ID_Verification.jpg', type: 'Image', uploadDate: faker.date.recent().toISOString(), size: '1.1 MB' },
      { id: faker.string.uuid(), name: 'Tax_Form.pdf', type: 'PDF', uploadDate: faker.date.recent().toISOString(), size: '800 KB' }
    ],
    timeline: [
      { id: faker.string.uuid(), title: 'Offer Accepted', description: 'Candidate signed the offer', date: faker.date.past().toISOString(), status: 'completed' },
      { id: faker.string.uuid(), title: 'Background Check', description: 'Verification in progress', date: faker.date.recent().toISOString(), status: 'in-progress' },
      { id: faker.string.uuid(), title: 'IT Provisioning', description: 'Waiting for laptop delivery', date: faker.date.future().toISOString(), status: 'pending' }
    ],
    recentActivity: [
      { id: faker.string.uuid(), action: 'Logged into portal', timestamp: faker.date.recent().toISOString() },
      { id: faker.string.uuid(), action: 'Uploaded Tax Form', timestamp: faker.date.recent().toISOString() }
    ]
  }))
}

export const mockEmployees = generateEmployees(100)
