import { createPinia, setActivePinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useGameStore } from '../stores/game'
import { useGameSocket } from './useGameSocket'

class FakeSocket extends EventTarget {
  static OPEN = 1
  readyState = FakeSocket.OPEN
  sent: string[] = []

  constructor(public url: string) {
    super()
    sockets.push(this)
  }

  send(payload: string): void {
    this.sent.push(payload)
  }

  close(): void {
    this.readyState = 3
    this.dispatchEvent(new Event('close'))
  }

  open(): void {
    this.dispatchEvent(new Event('open'))
  }

  receive(payload: Record<string, unknown>): void {
    this.dispatchEvent(new MessageEvent('message', { data: JSON.stringify(payload) }))
  }
}

const sockets: FakeSocket[] = []

describe('useGameSocket protocol v2', () => {
  beforeEach(() => {
    sockets.length = 0
    setActivePinia(createPinia())
    vi.stubGlobal('WebSocket', FakeSocket)
  })

  afterEach(() => vi.unstubAllGlobals())

  it('applies two-phase messenger, achievements, mode, save, and game over', () => {
    const store = useGameStore()
    store.token = 'token'
    store.config = {
      core_version: '0.3.0b1', protocol_version: 2, state_version: 2,
      theme: { themeId: 'demo-campus', displayName: 'Demo', locale: 'zh-CN', terms: {}, storage: { prefix: 'demo' } },
      story: {}, stats: { initialBudget: 0, stats: [] }, items: { items: [] },
      relax_actions: [], achievements: {}, content_modes: ['library', 'hybrid', 'ai'],
      llm_available: true, default_content_mode: 'library',
    }
    let gameSocket!: ReturnType<typeof useGameSocket>
    const wrapper = mount(defineComponent({
      setup() {
        gameSocket = useGameSocket()
        return () => h('div')
      },
    }))
    gameSocket.connect()
    const socket = sockets[0]
    socket.open()
    expect(JSON.parse(socket.sent[0])).toMatchObject({ token: 'token', protocol_version: 2 })

    socket.receive({ type: 'auth_ok' })
    socket.receive({
      type: 'messenger_update', phase: 'player',
      data: { state: { contacts: { a: { sender: 'A', unread_count: 0, awaiting_reply: true, messages: [{ speaker: 'player', content: 'Hi' }] } } } },
    })
    expect((store.messenger.contacts as any).a.awaiting_reply).toBe(true)

    socket.receive({ type: 'achievement_unlocked', data: { code: 'first', name: 'First', desc: 'Done', icon: '🏅' } })
    socket.receive({ type: 'mode_changed', mode: 'hybrid' })
    socket.receive({ type: 'save_result', success: true, message: 'saved' })
    socket.receive({ type: 'game_over', data: { reason: 'done' } })
    expect(store.achievements).toHaveLength(1)
    expect(store.contentMode).toBe('hybrid')
    expect(store.saveStatus).toBe('saved')
    expect(store.phase).toBe('ending')
    expect(store.endingKind).toBe('game_over')
    wrapper.unmount()
  })
})
