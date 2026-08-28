export type GamePhase = 'welcome' | 'create' | 'playing' | 'ending'

export interface StatMeta {
  id: string
  label: string
  icon: string
  default: number
  min: number
  max: number
  allocatable: boolean
  showInHud: boolean
}

export interface CourseInfo {
  id: string
  name: string
  credits: number
}

export interface ItemInfo {
  id: string
  name: string
  description: string
  category: string
  price: number
  sell_price: number
  effects: Record<string, number>
}

export interface AchievementInfo {
  code: string
  name: string
  desc: string
  icon: string
}

export interface ConfigPayload {
  core_version: string
  protocol_version: number
  state_version: number
  theme: {
    themeId: string
    displayName: string
    locale: string
    terms: Record<string, string>
    storage: { prefix: string }
  }
  story: Record<string, unknown>
  stats: { initialBudget: number; stats: StatMeta[] }
  items: { items: ItemInfo[] }
  relax_actions: string[]
  achievements: Record<string, AchievementInfo>
  content_modes: Array<'library' | 'hybrid' | 'ai'>
  llm_available: boolean
  default_content_mode: 'library' | 'hybrid' | 'ai'
}

export interface RuntimePayload {
  data?: Record<string, unknown>
  stats?: Record<string, unknown>
  courses?: Record<string, number>
  course_states?: Record<string, number>
  items_state?: Record<string, unknown>
  messenger_state?: Record<string, unknown>
  relax_cooldowns?: Record<string, number>
  achievements?: AchievementInfo[]
  content_mode?: 'library' | 'hybrid' | 'ai'
  ending_kind?: 'graduation' | 'game_over' | null
  ending_reason?: string | null
  current_event?: Record<string, unknown> | null
  semester_time_left?: number
  is_running?: boolean
  speed_multiplier?: number
  exam_completed?: boolean
  ended?: boolean
}
