import { STAT_DEFINITIONS } from './data/statDefinitions.generated'
import { STORY_CONTENT } from './data/story.generated'
import { THEME_MANIFEST } from './data/theme.generated'
import './style.css'

type InitPayload = {
  status: string
  courses: Array<{ id: string; name: string; credits: number }>
  init: {
    data: Record<string, unknown>
    semester_time_left: number
  }
}

const app = document.querySelector<HTMLDivElement>('#app')

if (!app) {
  throw new Error('missing #app root')
}

const apiBase = (import.meta.env.VITE_ESIMU_API_BASE ?? '').replace(/\/$/, '')
const wsBase = (
  import.meta.env.VITE_ESIMU_WS_BASE
  ?? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
).replace(/\/$/, '')
const hudStats = STAT_DEFINITIONS.filter((stat) => stat.showInHud)

app.innerHTML = `
  <section class="shell">
    <p class="eyebrow">${THEME_MANIFEST.displayName}</p>
    <h1>${THEME_MANIFEST.terms.campus} starter</h1>
    <p class="lede">${STORY_CONTENT.prologue.dedication_lines[0] ?? 'Welcome.'}</p>
    <div class="actions">
      <button id="start">Start smoke</button>
      <button id="forum">Forum</button>
      <button id="messenger">Messenger</button>
      <button id="exam">Exam</button>
    </div>
    <section class="panel">
      <h2>Runtime</h2>
      <pre id="output">Waiting for starter backend...</pre>
    </section>
    <section class="stats">
      ${hudStats.map((stat) => `<span>${stat.icon} ${stat.label}</span>`).join('')}
    </section>
  </section>
`

const output = document.querySelector<HTMLPreElement>('#output')
const startButton = document.querySelector<HTMLButtonElement>('#start')
let token = ''
let socket: WebSocket | null = null

function print(value: unknown): void {
  if (output) {
    output.textContent = JSON.stringify(value, null, 2)
  }
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`${response.status} ${response.statusText}: ${detail}`)
  }
  return response.json() as Promise<T>
}

async function startSmoke(): Promise<void> {
  startButton?.setAttribute('disabled', '')
  print({ status: 'connecting' })
  try {
    const auth = await readJson<{ token: string }>(await fetch(`${apiBase}/api/auth`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: THEME_MANIFEST.terms.player_nickname ?? 'Player' }),
    }))
    token = auth.token
    const init = await readJson<InitPayload>(await fetch(`${apiBase}/api/init_character`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, major: 'GEN' }),
    }))

    socket?.close()
    socket = new WebSocket(`${wsBase}/ws`)
    socket.addEventListener('open', () => {
      socket?.send(JSON.stringify({ token }))
    })
    socket.addEventListener('message', (event) => {
      print(JSON.parse(String(event.data)))
    })
    socket.addEventListener('error', () => {
      print({ error: 'WebSocket connection failed.', endpoint: `${wsBase}/ws` })
    })
    print(init)
  } catch (error) {
    print({
      error: error instanceof Error ? error.message : String(error),
      endpoint: apiBase || window.location.origin,
    })
  } finally {
    startButton?.removeAttribute('disabled')
  }
}

function send(action: string): void {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    print({ error: 'Start smoke first.' })
    return
  }
  socket.send(JSON.stringify({ action }))
}

document.querySelector('#start')?.addEventListener('click', () => {
  void startSmoke()
})
document.querySelector('#forum')?.addEventListener('click', () => send('forum'))
document.querySelector('#messenger')?.addEventListener('click', () => send('messenger'))
document.querySelector('#exam')?.addEventListener('click', () => send('exam'))
