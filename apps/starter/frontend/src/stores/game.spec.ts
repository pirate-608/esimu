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
    })

    expect(store.stats.energy).toBe(88)
    expect(store.courses.systems).toBe(12)
    expect(store.courseStates.systems).toBe(2)
    expect(store.ownedItems.has('planner')).toBe(true)
    expect(store.running).toBe(true)
    expect(store.speed).toBe(1.5)
  })
})
