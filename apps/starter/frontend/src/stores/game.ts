import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import type { AchievementInfo, ConfigPayload, GamePhase, RuntimePayload } from '../types'

export const useGameStore = defineStore('game', () => {
  const phase = ref<GamePhase>('welcome')
  const config = ref<ConfigPayload | null>(null)
  const token = ref('')
  const connected = ref(false)
  const stats = ref<Record<string, unknown>>({})
  const courses = ref<Record<string, number>>({})
  const courseStates = ref<Record<string, number>>({})
  const itemsState = ref<Record<string, unknown>>({ owned: [] })
  const semesterTimeLeft = ref(0)
  const running = ref(false)
  const speed = ref(1)
  const examCompleted = ref(false)
  const logs = ref<string[]>([])
  const event = ref<Record<string, unknown> | null>(null)
  const feedback = ref<Record<string, unknown> | null>(null)
  const transcript = ref<Record<string, unknown> | null>(null)
  const ending = ref<Record<string, unknown> | null>(null)
  const messenger = ref<Record<string, unknown>>({ contacts: {} })
  const cooldowns = ref<Record<string, number>>({})
  const achievements = ref<AchievementInfo[]>([])
  const contentMode = ref<'library' | 'hybrid' | 'ai'>('library')
  const endingKind = ref<'graduation' | 'game_over' | null>(null)
  const endingReason = ref('')
  const savePending = ref(false)
  const saveStatus = ref('')
  const activeTab = ref<'feed' | 'forum' | 'messenger' | 'items'>('feed')
  const error = ref('')

  const ownedItems = computed(() => new Set(
    Array.isArray(itemsState.value.owned) ? itemsState.value.owned as string[] : [],
  ))
  const unreadMessages = computed(() => Object.values(
    (messenger.value.contacts as Record<string, Record<string, unknown>>) ?? {},
  ).reduce((sum, contact) => sum + Number(contact.unread_count ?? 0), 0))

  function applyRuntime(payload: RuntimePayload): void {
    stats.value = { ...(payload.data ?? payload.stats ?? stats.value) }
    courses.value = { ...(payload.courses ?? courses.value) }
    courseStates.value = { ...(payload.course_states ?? courseStates.value) }
    if (payload.items_state) itemsState.value = { ...payload.items_state }
    if (payload.messenger_state) messenger.value = { ...payload.messenger_state }
    if (payload.relax_cooldowns) cooldowns.value = { ...payload.relax_cooldowns }
    if (payload.achievements) achievements.value = [...payload.achievements]
    if (payload.content_mode) contentMode.value = payload.content_mode
    if (payload.ending_kind !== undefined) endingKind.value = payload.ending_kind
    if (payload.ending_reason !== undefined) endingReason.value = payload.ending_reason ?? ''
    if (payload.current_event !== undefined) event.value = payload.current_event
    if (typeof payload.semester_time_left === 'number') {
      semesterTimeLeft.value = payload.semester_time_left
    }
    if (typeof payload.is_running === 'boolean') running.value = payload.is_running
    if (typeof payload.speed_multiplier === 'number') speed.value = payload.speed_multiplier
    if (typeof payload.exam_completed === 'boolean') examCompleted.value = payload.exam_completed
    if (payload.ended) phase.value = 'ending'
  }

  function addLog(message: string): void {
    logs.value.unshift(message)
    logs.value = logs.value.slice(0, 60)
  }

  function resetLocal(): void {
    phase.value = 'welcome'
    token.value = ''
    connected.value = false
    stats.value = {}
    courses.value = {}
    courseStates.value = {}
    event.value = null
    feedback.value = null
    transcript.value = null
    ending.value = null
    logs.value = []
    error.value = ''
    cooldowns.value = {}
    achievements.value = []
    contentMode.value = config.value?.default_content_mode ?? 'library'
    endingKind.value = null
    endingReason.value = ''
    savePending.value = false
    saveStatus.value = ''
  }

  function addAchievement(achievement: AchievementInfo): void {
    if (!achievements.value.some((item) => item.code === achievement.code)) {
      achievements.value.push(achievement)
    }
  }

  return {
    phase, config, token, connected, stats, courses, courseStates, itemsState,
    semesterTimeLeft, running, speed, examCompleted, logs, event, feedback,
    transcript, ending, messenger, cooldowns, achievements, contentMode,
    endingKind, endingReason, savePending, saveStatus, activeTab, error,
    ownedItems, unreadMessages, applyRuntime, addLog, addAchievement, resetLocal,
  }
})
