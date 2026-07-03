import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const webSocketMock = vi.hoisted(() => ({
  connect: vi.fn(),
  disconnect: vi.fn(),
  send: vi.fn(),
}))

const demoThemeManifest = {
  themeId: 'demo-campus',
  displayName: 'Demo Campus Simulator',
  locale: 'zh-CN',
  terms: {
    institution: '星桥学院',
    institution_short: '星桥',
    campus: '星桥校区',
    feed: '星桥公告',
    forum: '星桥论坛',
    messenger: '校内信',
    server: '星桥云端',
    player: '学员',
    player_nickname: '星桥人',
    semester: '阶段',
    course: '模块',
    item: '补给',
    rules: '星桥守则',
    notice: '星桥简章',
  },
  storage: {
    prefix: 'simlab_demo',
  },
  assets: {},
}

function setupDemoTheme() {
  vi.resetModules()
  webSocketMock.connect.mockClear()
  webSocketMock.disconnect.mockClear()
  webSocketMock.send.mockClear()
  vi.doMock('@/data/theme.generated', () => ({
    THEME_MANIFEST: demoThemeManifest,
  }))
  vi.doMock('@/composables/useGameWebSocket.ts', () => ({
    useGameWebSocket: () => ({
      connect: webSocketMock.connect,
      disconnect: webSocketMock.disconnect,
      isConnected: { value: false },
      send: webSocketMock.send,
    }),
  }))
}

describe('theme-driven runtime labels', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.doUnmock('@/data/theme.generated')
    vi.doUnmock('@/composables/useGameWebSocket.ts')
    vi.resetModules()
  })

  it('boots a returning demo-theme player with theme-scoped storage and loading copy', async () => {
    setupDemoTheme()
    const { default: App } = await import('../App.vue')
    const { PROLOGUE_SEEN_STORAGE_KEY } = await import('@/data/prologue')
    const { STORAGE_KEYS } = await import('@/utils/storageKeys')

    localStorage.setItem(PROLOGUE_SEEN_STORAGE_KEY, '1')
    localStorage.setItem(STORAGE_KEYS.jwt, 'header.payload.signature')
    localStorage.setItem(STORAGE_KEYS.token, 'header.payload.signature')
    localStorage.setItem(STORAGE_KEYS.gameStarted, '1')
    localStorage.setItem('simlab_token', 'legacy-token-that-should-not-be-read')

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia()],
        stubs: {
          LoginView: { template: '<main data-testid="login-view">login</main>' },
          SaveSelect: { template: '<main data-testid="save-select">saves</main>' },
          CharacterCreate: { template: '<main data-testid="character-create">create</main>' },
          TopNav: true,
          HudBar: true,
          CourseList: true,
          MidPanel: true,
          RightPanel: true,
          TranscriptModal: true,
          RandomEventModal: true,
          FeedbackModal: true,
          ExamConfirmModal: true,
          ExitConfirmModal: true,
          EndScreen: true,
        },
      },
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('正在连接「星桥云端」')
    expect(wrapper.text()).not.toContain('zdbk')
    expect(webSocketMock.connect).toHaveBeenCalledWith(
      'header.payload.signature',
      expect.stringMatching(/^ws:\/\/|^wss:\/\//),
    )

    wrapper.unmount()
  })

  it('renders the active theme course term in the course loading state', async () => {
    setupDemoTheme()
    const { default: CourseList } = await import('./CourseList.vue')
    const pinia = createPinia()
    setActivePinia(pinia)

    const wrapper = mount(CourseList, {
      global: {
        plugins: [pinia],
      },
    })

    expect(wrapper.text()).toContain('正在加载模块大纲')
    expect(wrapper.text()).not.toContain('正在加载课程大纲')
  })

  it('renders the active theme item term in the item panel', async () => {
    setupDemoTheme()
    const { default: MidPanel } = await import('./MidPanel.vue')
    const { useGameStore } = await import('@/stores/gameStore')
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useGameStore()
    store.setItemsState({
      version: 1,
      updated_at: 1,
      items: [],
      owned: [],
      bonuses: {},
    })

    const wrapper = mount(MidPanel, {
      global: {
        plugins: [pinia],
      },
    })
    await wrapper.findAll('.nav-link')[2].trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.item-search').attributes('placeholder')).toBe('搜索补给、分类或标签')
    expect(wrapper.text()).toContain('暂无匹配补给')
    expect(wrapper.text()).not.toContain('暂无匹配道具')
  })
})
