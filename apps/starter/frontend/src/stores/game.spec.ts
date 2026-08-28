import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { useGameStore } from './game'

describe('game store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('applies versioned runtime payloads without losing item state', () => {
    const store = useGameStore()
    store.applyRuntime({
      data: { energy: 88, semester: '第二学期' },
      courses: { systems: 12 },
      course_states: { systems: 2 },
      items_state: { owned: ['planner'] },
      semester_time_left: 120,
      is_running: true,
      speed_multiplier: 1.5,
      relax_cooldowns: { walk: 9 },
      content_mode: 'hybrid',
      achievements: [{ code: 'first', name: 'First', desc: 'Done', icon: '🏅' }],
    })

    expect(store.stats.energy).toBe(88)
    expect(store.courses.systems).toBe(12)
    expect(store.courseStates.systems).toBe(2)
    expect(store.ownedItems.has('planner')).toBe(true)
    expect(store.running).toBe(true)
    expect(store.speed).toBe(1.5)
    expect(store.cooldowns.walk).toBe(9)
    expect(store.contentMode).toBe('hybrid')
    expect(store.achievements[0].code).toBe('first')
  })

  it('deduplicates achievements and totals unread contacts', () => {
    const store = useGameStore()
    const achievement = { code: 'first', name: 'First', desc: 'Done', icon: '🏅' }
    store.addAchievement(achievement)
    store.addAchievement(achievement)
    store.messenger = {
      contacts: {
        a: { unread_count: 2 },
        b: { unread_count: 1 },
      },
    }
    expect(store.achievements).toHaveLength(1)
    expect(store.unreadMessages).toBe(3)
  })
})
