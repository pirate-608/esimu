import { describe, expect, it, vi } from 'vitest'

describe('theme metadata helpers', () => {
  it('derive visible terms and storage keys from generated metadata', async () => {
    vi.resetModules()
    vi.doMock('@/data/theme.generated', () => ({
      THEME_MANIFEST: {
        themeId: 'demo-campus',
        displayName: 'Demo Campus Simulator',
        locale: 'zh-CN',
        terms: {
          feed: '星桥动态',
          forum: '星桥论坛',
          messenger: '校内信',
          server: '星桥服务器',
        },
        storage: {
          prefix: 'simlab_demo',
        },
        assets: {},
      },
    }))

    const { themeDisplayName, themeStorageKey, themeTerm } = await import('./theme')

    expect(themeDisplayName).toBe('Demo Campus Simulator')
    expect(themeTerm('messenger')).toBe('校内信')
    expect(themeTerm('forum')).toBe('星桥论坛')
    expect(themeTerm('feed')).toBe('星桥动态')
    expect(themeStorageKey('jwt')).toBe('simlab_demo_jwt')
    expect(
      [
        themeDisplayName,
        themeTerm('messenger'),
        themeTerm('forum'),
        themeTerm('server'),
        themeStorageKey('jwt'),
      ].join('\n'),
    ).not.toMatch(/折姜|浙江大学|CC98|钉钉/)
  })
})
