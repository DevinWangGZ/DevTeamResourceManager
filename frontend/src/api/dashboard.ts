/**
 * 仪表盘API
 */
import request from './index'

export interface TaskSummary {
  total: number
  in_progress: number
  submitted: number
  confirmed: number
  pending_eval: number
}

export interface WorkloadSummary {
  total_man_days: number
  project_count: number
  period_start?: string
  period_end?: string
}

export interface TodoReminder {
  type: string
  title: string
  count: number
  link?: string
}

export interface RecentTask {
  id: number
  title: string
  status: string
  project_id?: number
  estimated_man_days?: number
  actual_man_days?: number
  updated_at?: string
}

export interface CollaboratingTask {
  id: number
  title: string
  status: string
  project_id?: number
  /** 分配给当前用户的人天数 */
  allocated_man_days?: number
  estimated_man_days?: number
  updated_at?: string
}

export interface CompletedTask {
  id: number
  title: string
  status: string
  project_id?: number
  estimated_man_days?: number
  actual_man_days?: number
  /** 是否以协助人身份参与 */
  is_collaborator: boolean
  updated_at?: string
}

export interface TodayTask {
  id: number
  title: string
  status: string
  priority: string
  project_id?: number
  estimated_man_days?: number
  actual_man_days?: number
  deadline?: string
  start_date?: string
  end_date?: string
  /** 是否以协助人身份参与 */
  is_collaborator: boolean
  updated_at?: string
}

export interface DeveloperDashboard {
  task_summary: TaskSummary
  workload_summary?: WorkloadSummary
  todo_reminders: TodoReminder[]
  /** 最近活跃任务（不含已提交/已确认） */
  recent_tasks: RecentTask[]
  /** 当前用户作为协助人参与的活跃任务列表（不含已提交/已确认） */
  collaborating_tasks: CollaboratingTask[]
  /** 今日需处理的任务列表 */
  today_tasks: TodayTask[]
  /** 最近已完成任务（已提交/已确认，含认领人和协助人身份） */
  completed_tasks: CompletedTask[]
}

export interface ProjectTaskSummary {
  project_id: number
  project_name: string
  total_tasks: number
  completed_tasks: number
  in_progress_tasks: number
  pending_confirmation: number
}

export interface ProjectOutputSummary {
  project_id: number
  project_name: string
  estimated_value: number
  task_output_value: number
  allocated_output_value: number
  is_over_budget: boolean
}

export interface ProjectManagerDashboard {
  project_summaries: ProjectTaskSummary[]
  output_summaries: ProjectOutputSummary[]
  pending_confirmation_count: number
  todo_reminders: TodoReminder[]
}

export interface TeamMemberSummary {
  user_id: number
  username: string
  full_name?: string
  workload_status: string
  total_man_days: number
  active_tasks: number
}

export interface TeamDashboard {
  total_members: number
  total_workload: number
  task_completion_rate: number
  member_summaries: TeamMemberSummary[]
  todo_reminders: TodoReminder[]
}

/**
 * 获取开发人员工作台数据
 */
export function getDeveloperDashboard(): Promise<DeveloperDashboard> {
  return request.get('/api/v1/dashboard/developer')
}

/**
 * 获取项目经理仪表盘数据
 */
export function getProjectManagerDashboard(): Promise<ProjectManagerDashboard> {
  return request.get('/api/v1/dashboard/project-manager')
}

/**
 * 获取开发组长团队仪表盘数据
 */
export function getTeamDashboard(): Promise<TeamDashboard> {
  return request.get('/api/v1/dashboard/team')
}
