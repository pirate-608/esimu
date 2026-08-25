<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { useGameSocket } from './composables/useGameSocket'
import { ALLOCATABLE_STATS, STAT_DEFINITIONS, STAT_INITIAL_BUDGET } from './data/statDefinitions.generated'
import { THEME_MANIFEST } from './data/theme.generated'
import { useGameStore } from './stores/game'
import type { ConfigPayload, CourseInfo, ItemInfo } from './types'

const store = useGameStore()
const { connect, disconnect, send } = useGameSocket()
const apiBase = (import.meta.env.VITE_ESIMU_API_BASE ?? '').replace(/\/$/, '')
const username = ref('')
const majors = ref<Array<{ abbr: string; name: string; desc?: string }>>([])
const selectedMajor = ref('')
const allocations = reactive<Record<string, number>>(
  Object.fromEntries(ALLOCATABLE_STATS.map((stat) => [stat.id, stat.default])),
)
const selectedContact = ref('')
const showExamConfirm = ref(false)

const terms = computed(() => store.config?.theme.terms ?? THEME_MANIFEST.terms)
const storageKey = computed(() => `${store.config?.theme.storage.prefix ?? THEME_MANIFEST.storage.prefix}_token`)
const allocationTotal = computed(() => Object.values(allocations).reduce((sum, value) => sum + Number(value), 0))
const hudStats = computed(() => STAT_DEFINITIONS.filter((stat) => stat.showInHud))
const courseInfo = computed<CourseInfo[]>(() => {
  try {
    return JSON.parse(String(store.stats.course_info_json ?? '[]')) as CourseInfo[]
  } catch {
    return []
  }
})
const itemCatalog = computed<ItemInfo[]>(() => store.config?.items.items ?? [])
const contacts = computed(() => Object.values(
  (store.messenger.contacts as Record<string, Record<string, any>>) ?? {},
))
const currentContact = computed(() => contacts.value.find((contact) => contact.contact_id === selectedContact.value) ?? contacts.value[0])
const timeLabel = computed(() => {
  const minutes = Math.floor(store.semesterTimeLeft / 60)
  const seconds = store.semesterTimeLeft % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
})

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) throw new Error(await response.text())
  return response.json() as Promise<T>
}

async function bootstrap(): Promise<void> {
  try {
    const [config, majorList] = await Promise.all([
      readJson<ConfigPayload>(await fetch(`${apiBase}/config`)),
      readJson<typeof majors.value>(await fetch(`${apiBase}/api/majors`)),
    ])
    store.config = config
    majors.value = majorList
    selectedMajor.value = majorList[0]?.abbr ?? ''
    const savedToken = localStorage.getItem(`${config.theme.storage.prefix}_token`)
    if (savedToken) {
      const auth = await readJson<{ status: string; token: string }>(await fetch(`${apiBase}/api/auth`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: savedToken }),
      }))
      store.token = auth.token
      localStorage.setItem(storageKey.value, auth.token)
      if (auth.status === 'returning') {
        const restored = await readJson<any>(await fetch(`${apiBase}/api/init_character`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: auth.token }),
        }))
        store.applyRuntime(restored.init)
        store.phase = 'playing'
        connect()
      }
    }
  } catch (error) {
    store.error = error instanceof Error ? error.message : String(error)
  }
}

async function beginProfile(): Promise<void> {
  try {
    const auth = await readJson<{ token: string }>(await fetch(`${apiBase}/api/auth`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value || terms.value.player }),
    }))
    store.token = auth.token
    localStorage.setItem(storageKey.value, auth.token)
    store.phase = 'create'
  } catch (error) {
    store.error = error instanceof Error ? error.message : String(error)
  }
}

async function createCharacter(): Promise<void> {
  if (allocationTotal.value !== STAT_INITIAL_BUDGET) {
    store.error = `属性总和必须为 ${STAT_INITIAL_BUDGET}`
    return
  }
  try {
    const result = await readJson<any>(await fetch(`${apiBase}/api/init_character`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: store.token,
        username: username.value || terms.value.player,
        major: selectedMajor.value,
        stats: allocations,
      }),
    }))
    store.applyRuntime(result.init)
    store.phase = 'playing'
    connect()
  } catch (error) {
    store.error = error instanceof Error ? error.message : String(error)
  }
}

function togglePause(): void {
  send(store.running ? 'pause' : 'resume')
}

function actionLabel(action: string): string {
  const labels = terms.value as Record<string, string>
  return labels[`action_${action}`] ?? action.replace(/_/g, ' ')
}

function settleExam(): void {
  showExamConfirm.value = false
  send('exam')
}

function continueAfterExam(): void {
  const ended = Boolean(store.transcript?.ended)
  store.transcript = null
  if (ended) send('ending')
  else send('next_semester')
}

function reply(option: Record<string, unknown>): void {
  if (!currentContact.value) return
  send('messenger_reply', {
    contact_id: currentContact.value.contact_id,
    option_id: option.id,
    content: option.text,
  })
}

function returnHome(): void {
  disconnect()
  localStorage.removeItem(storageKey.value)
  store.resetLocal()
}

onMounted(() => { void bootstrap() })
</script>

<template>
  <main class="app-shell">
    <header class="topbar">
      <div>
        <span class="brand-mark">E</span>
        <strong>{{ store.config?.theme.displayName ?? THEME_MANIFEST.displayName }}</strong>
      </div>
      <div v-if="store.phase === 'playing'" class="runtime-status">
        <span :class="['connection-dot', { online: store.connected }]" />
        <span>{{ store.connected ? '已连接' : '连接中' }}</span>
        <span>{{ store.stats.semester }}</span>
        <strong>{{ timeLabel }}</strong>
      </div>
    </header>

    <section v-if="store.phase === 'welcome'" class="welcome-band">
      <div class="welcome-copy">
        <p class="eyebrow">ESIMU BETA STARTER</p>
        <h1>{{ terms.campus }}</h1>
        <p>从一个主题包开始，体验完整的单主题叙事模拟循环。</p>
        <form class="profile-form" @submit.prevent="beginProfile">
          <label>本地玩家名称<input v-model="username" maxlength="24" placeholder="输入名称" /></label>
          <button class="primary" type="submit">开始</button>
        </form>
      </div>
    </section>

    <section v-else-if="store.phase === 'create'" class="create-layout">
      <div class="section-heading">
        <p class="eyebrow">CHARACTER SETUP</p>
        <h1>创建你的{{ terms.player }}</h1>
      </div>
      <div class="create-columns">
        <section class="surface">
          <h2>方向</h2>
          <button
            v-for="major in majors" :key="major.abbr"
            :class="['choice-row', { selected: selectedMajor === major.abbr }]"
            @click="selectedMajor = major.abbr"
          >
            <strong>{{ major.name }}</strong><span>{{ major.desc }}</span>
          </button>
        </section>
        <section class="surface">
          <div class="allocation-title"><h2>初始属性</h2><strong>{{ allocationTotal }} / {{ STAT_INITIAL_BUDGET }}</strong></div>
          <label v-for="stat in ALLOCATABLE_STATS" :key="stat.id" class="stat-control">
            <span>{{ stat.icon }} {{ stat.label }}</span>
            <input v-model.number="allocations[stat.id]" type="range" :min="stat.min" :max="stat.max" step="1" />
            <output>{{ allocations[stat.id] }}</output>
          </label>
          <button class="primary wide" :disabled="allocationTotal !== STAT_INITIAL_BUDGET" @click="createCharacter">进入{{ terms.campus }}</button>
        </section>
      </div>
    </section>

    <section v-else-if="store.phase === 'playing'" class="game-layout">
      <section class="hud-band">
        <div v-for="stat in hudStats" :key="stat.id" class="hud-stat">
          <span>{{ stat.icon }} {{ stat.label }}</span>
          <strong>{{ Number(store.stats[stat.id] ?? stat.default).toFixed(0) }}</strong>
          <progress :max="stat.max" :value="Number(store.stats[stat.id] ?? stat.default)" />
        </div>
      </section>

      <div class="console-grid">
        <aside class="course-panel surface">
          <div class="panel-title"><h2>{{ terms.course }}</h2><span>{{ store.stats.major }}</span></div>
          <article v-for="course in courseInfo" :key="course.id" class="course-row">
            <div><strong>{{ course.name }}</strong><span>{{ course.credits }} 学分</span></div>
            <progress max="120" :value="store.courses[course.id] ?? 0" />
            <div class="segmented">
              <button v-for="(label, state) in ['暂停', '常规', '专注']" :key="state" :class="{ active: store.courseStates[course.id] === state }" @click="send('change_course_state', { course_id: course.id, state })">{{ label }}</button>
            </div>
          </article>
        </aside>

        <section class="activity-panel surface">
          <nav class="tabs">
            <button v-for="tab in ['feed', 'forum', 'messenger', 'items'] as const" :key="tab" :class="{ active: store.activeTab === tab }" @click="store.activeTab = tab">
              {{ tab === 'feed' ? terms.feed : tab === 'forum' ? terms.forum : tab === 'messenger' ? terms.messenger : terms.item }}
            </button>
          </nav>
          <div v-if="store.activeTab === 'feed'" class="scroll-area feed-list">
            <p v-if="!store.logs.length" class="empty">等待新的校园动态。</p>
            <p v-for="(log, index) in store.logs" :key="index">{{ log }}</p>
          </div>
          <div v-else-if="store.activeTab === 'forum'" class="scroll-area action-view">
            <h3>{{ terms.forum }}</h3><p>浏览主题本地内容库或由可选 AI 生成的新帖子。</p>
            <button class="primary" @click="send('forum')">刷新帖子</button>
            <p v-for="(log, index) in store.logs.slice(0, 8)" :key="index">{{ log }}</p>
          </div>
          <div v-else-if="store.activeTab === 'messenger'" class="messenger-layout">
            <aside>
              <button v-for="contact in contacts" :key="contact.contact_id" :class="{ active: currentContact?.contact_id === contact.contact_id }" @click="selectedContact = contact.contact_id">{{ contact.sender }}</button>
              <button class="quiet" @click="send('messenger')">新对话</button>
            </aside>
            <div class="conversation">
              <p v-if="!currentContact" class="empty">还没有联系人。</p>
              <template v-else>
                <h3>{{ currentContact.sender }}</h3>
                <div v-for="(message, index) in currentContact.messages" :key="index" :class="['message', message.speaker]">{{ message.content }}</div>
                <div class="reply-options">
                  <button v-for="option in currentContact.pending_options" :key="option.id" :disabled="!store.running" @click="reply(option)">{{ option.text }}</button>
                </div>
              </template>
            </div>
          </div>
          <div v-else class="scroll-area item-grid">
            <article v-for="item in itemCatalog" :key="item.id">
              <div><strong>{{ item.name }}</strong><span>{{ item.price }} 点</span></div>
              <p>{{ item.description }}</p>
              <small>{{ Object.entries(item.effects).map(([key, value]) => `${key} ${value > 0 ? '+' : ''}${value}`).join(' · ') }}</small>
              <button :disabled="!store.running" @click="send(store.ownedItems.has(item.id) ? 'item_sell' : 'item_buy', { item_id: item.id })">{{ store.ownedItems.has(item.id) ? '出售' : '购买' }}</button>
            </article>
          </div>
        </section>

        <aside class="action-panel surface">
          <div class="panel-title"><h2>行动</h2><span>{{ store.stats.gold ?? 0 }} 点</span></div>
          <button v-for="action in store.config?.relax_actions" :key="action" :disabled="!store.running" @click="send('relax', { target: action })">{{ actionLabel(action) }}</button>
          <button :disabled="!store.running" @click="send('event')">触发事件</button>
          <button class="exam-button" @click="showExamConfirm = true">期末结算</button>
          <div class="runtime-controls">
            <button :title="store.running ? '暂停' : '继续'" @click="togglePause">{{ store.running ? 'Ⅱ' : '▶' }}</button>
            <button v-for="value in [1, 1.5, 2]" :key="value" :class="{ active: store.speed === value }" @click="send('set_speed', { speed: value })">{{ value }}x</button>
          </div>
        </aside>
      </div>
    </section>

    <section v-else class="ending-screen">
      <p class="eyebrow">ENDING</p><h1>这一段旅程告一段落</h1>
      <p>{{ store.ending?.summary ?? '你完成了当前主题配置中的全部学期。' }}</p>
      <div><button class="primary" @click="send('restart'); store.phase = 'playing'">重新开始</button><button @click="returnHome">回到首页</button></div>
    </section>

    <div v-if="store.event" class="modal-backdrop"><section class="modal"><p class="eyebrow">RANDOM EVENT</p><h2>{{ store.event.title }}</h2><p>{{ store.event.desc }}</p><button v-for="(option, index) in (store.event.options as any[])" :key="index" @click="send('event_choice', { option_index: index }); store.event = null">{{ option.text }}</button></section></div>
    <div v-if="store.feedback" class="modal-backdrop"><section class="modal"><h2>行动反馈</h2><p>{{ store.feedback.desc }}</p><ul><li v-for="change in (store.feedback.changes as any[])" :key="change.field">{{ change.label ?? change.field }} {{ change.delta > 0 ? '+' : '' }}{{ change.delta }}</li></ul><button @click="store.feedback = null">知道了</button></section></div>
    <div v-if="showExamConfirm" class="modal-backdrop"><section class="modal"><h2>确认期末结算？</h2><p>结算后本学期将结束，未完成的安排不会继续推进。</p><div><button @click="showExamConfirm = false">取消</button><button class="danger" @click="settleExam">确认结算</button></div></section></div>
    <div v-if="store.transcript" class="modal-backdrop"><section class="modal transcript"><p class="eyebrow">SEMESTER SUMMARY</p><h2>本学期成绩</h2><div class="gpa"><strong>{{ Number(store.transcript.term_gpa).toFixed(2) }}</strong><span>累计 {{ Number(store.transcript.cgpa).toFixed(2) }}</span></div><button class="primary" @click="continueAfterExam">{{ store.transcript.ended ? '查看结局' : '进入下学期' }}</button></section></div>
    <p v-if="store.error" class="error-toast" @click="store.error = ''">{{ store.error }}</p>
  </main>
</template>
