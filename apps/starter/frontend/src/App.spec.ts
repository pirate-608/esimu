import { createPinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App.vue'
import { useGameStore } from './stores/game'
import type { ConfigPayload } from './types'

const config: ConfigPayload = {
  core_version: '0.3.0b2',
  protocol_version: 2,
  state_version: 2,
  theme: {
    themeId: 'demo-campus',
    displayName: 'Demo Campus Simulator',
    locale: 'zh-CN',
    terms: {
      campus: '星桥学院', player: '学生', course: '课程', item: '道具',
      feed: '星桥动态', forum: '星桥论坛', messenger: '校内信',
    },
    storage: { prefix: 'esimu_demo' },
  },
  story: { endings: {} },
  stats: { initialBudget: 300, stats: [] },
  items: { items: [] },
  relax_actions: ['walk'],
  achievements: {},
  content_modes: ['library', 'hybrid', 'ai'],
  llm_available: false,
  default_content_mode: 'library',
}

describe('Starter App', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      const body = url.endsWith('/api/majors')
        ? [{ abbr: 'GEN', name: '通识探索' }]
        : config
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }))
  })

  it('renders the theme-driven welcome flow without opening a socket', async () => {
    const websocket = vi.fn()
    vi.stubGlobal('WebSocket', websocket)
    const wrapper = mount(App, { global: { plugins: [createPinia()] } })
    await flushPromises()

    expect(wrapper.text()).toContain('星桥学院')
    expect(wrapper.text()).toContain('本地玩家名称')
    expect(websocket).not.toHaveBeenCalled()
  })

  it('renders cooldowns, unread contacts, save controls, and content modes', async () => {
    vi.stubGlobal('WebSocket', vi.fn())
    const pinia = createPinia()
    const wrapper = mount(App, { global: { plugins: [pinia] } })
    await flushPromises()
    const store = useGameStore(pinia)
    store.config = config
    store.phase = 'playing'
    store.running = true
    store.stats = { semester: '第一学期', course_info_json: '[]', gold: 100 }
    store.cooldowns = { walk: 9 }
    store.messenger = {
      contacts: {
        a: { contact_id: 'a', sender: 'A', unread_count: 2, messages: [], pending_options: [] },
      },
    }
    await nextTick()

    expect(wrapper.text()).toContain('9s')
    expect(wrapper.text()).toContain('校内信 · 2')
    expect(wrapper.text()).toContain('保存')
    expect(wrapper.find('select[aria-label="内容模式"]').exists()).toBe(true)
  })
})
