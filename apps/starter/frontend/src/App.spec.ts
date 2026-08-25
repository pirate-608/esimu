import { createPinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App.vue'

const config = {
  core_version: '0.2.0b5',
  protocol_version: 1,
  state_version: 1,
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
  story: {},
  stats: { initialBudget: 300, stats: [] },
  items: { items: [] },
  relax_actions: ['walk'],
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
})
