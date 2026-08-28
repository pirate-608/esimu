import { onBeforeUnmount, ref } from 'vue'

import { useGameStore } from '../stores/game'
import type { AchievementInfo } from '../types'

const wsBase = (
  import.meta.env.VITE_ESIMU_WS_BASE
  ?? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
).replace(/\/$/, '')

export function useGameSocket() {
  const store = useGameStore()
  const socket = ref<WebSocket | null>(null)
  let heartbeat: ReturnType<typeof setInterval> | null = null
  let pendingExit = false
  let receivedExitConfirmation = false

  function stopHeartbeat(): void {
    if (heartbeat !== null) clearInterval(heartbeat)
    heartbeat = null
  }

  function connect(): void {
    socket.value?.close()
    const ws = new WebSocket(`${wsBase}/ws`)
    socket.value = ws
    ws.addEventListener('open', () => {
      ws.send(JSON.stringify({
        token: store.token,
        protocol_version: store.config?.protocol_version ?? 1,
      }))
      stopHeartbeat()
      heartbeat = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'ping' }))
        }
      }, 20_000)
    })
    ws.addEventListener('close', () => {
      stopHeartbeat()
      store.connected = false
      store.savePending = false
      if (pendingExit && !receivedExitConfirmation) {
        store.error = '连接在退出确认前断开，请重新连接后再试。'
      }
      pendingExit = false
    })
    ws.addEventListener('error', () => {
      store.error = '无法连接 Starter 后端，请检查服务是否已启动。'
    })
    ws.addEventListener('message', (event) => {
      const message = JSON.parse(String(event.data)) as Record<string, any>
      const type = String(message.type ?? '')
      if (type === 'auth_ok') {
        store.connected = true
      } else if (type === 'init' || type === 'tick') {
        store.applyRuntime(message)
        store.phase = message.ended ? 'ending' : 'playing'
      } else if (type === 'event') {
        store.event = message.data
      } else if (type === 'feedback') {
        store.feedback = message.data
        store.addLog(String(message.data?.desc ?? '行动已结算'))
        if (message.data?.tick) store.applyRuntime(message.data.tick)
      } else if (type === 'forum_post') {
        store.activeTab = 'forum'
        store.addLog(String(message.data?.content ?? '论坛出现了新动态'))
      } else if (type === 'messenger_round') {
        const contact = message.data?.contact
        if (contact?.contact_id) {
          const contacts = { ...((store.messenger.contacts as Record<string, unknown>) ?? {}) }
          contacts[contact.contact_id] = {
            ...contact,
            messages: [{ speaker: 'npc', content: message.data.content }],
            pending_options: message.data.reply_options ?? [],
          }
          store.messenger = { contacts }
        }
        store.activeTab = 'messenger'
      } else if (type === 'messenger_reply' || type === 'messenger_update') {
        const contacts = { ...((message.data?.state?.contacts as Record<string, unknown>) ?? {}) }
        if (Object.keys(contacts).length) store.messenger = { contacts }
        if (message.phase === 'opening') store.addLog('收到一条新的私聊消息')
      } else if (type === 'items_state') {
        store.itemsState = message.data
        store.addLog('道具状态已更新')
      } else if (type === 'semester_summary') {
        store.transcript = message.data
        store.examCompleted = true
      } else if (type === 'new_semester') {
        if (message.data?.tick) store.applyRuntime(message.data.tick)
        if (message.data?.ended) store.phase = 'ending'
        store.transcript = null
      } else if (type === 'ending') {
        store.ending = message.data
        store.endingKind = message.data?.outcome ?? 'graduation'
        store.endingReason = String(message.data?.reason ?? '')
        store.phase = 'ending'
      } else if (type === 'game_over') {
        store.ending = { ...message.data, outcome: 'game_over' }
        store.endingKind = 'game_over'
        store.endingReason = String(message.data?.reason ?? '')
        store.phase = 'ending'
      } else if (type === 'achievement_unlocked') {
        const achievement = message.data as AchievementInfo
        store.addAchievement(achievement)
        store.addLog(`${achievement.icon} 解锁成就：${achievement.name}`)
        store.feedback = {
          desc: `解锁成就：${achievement.name}`,
          changes: [],
        }
      } else if (type === 'mode_changed') {
        store.contentMode = message.mode
        store.addLog(`内容模式已切换为 ${message.mode}`)
      } else if (type === 'save_result') {
        store.savePending = false
        store.saveStatus = String(message.message ?? (message.success ? '保存成功' : '保存失败'))
        if (!message.success) {
          pendingExit = false
          store.error = store.saveStatus
        }
      } else if (type === 'exit_confirmed') {
        receivedExitConfirmation = true
        store.savePending = false
        store.connected = false
        store.phase = 'welcome'
      } else if (type === 'toast' || type === 'error') {
        store.error = String(message.message ?? '请求失败')
      }
    })
  }

  function send(action: string, data: Record<string, unknown> = {}): void {
    if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
      store.error = '连接尚未就绪。'
      return
    }
    if (action === 'save_game' || action === 'save_and_exit') {
      store.savePending = true
      store.saveStatus = '正在保存...'
    }
    if (action === 'save_and_exit' || action === 'exit_without_save') {
      pendingExit = true
      receivedExitConfirmation = false
    }
    socket.value.send(JSON.stringify({ action, ...data }))
  }

  function disconnect(): void {
    stopHeartbeat()
    pendingExit = false
    socket.value?.close(1000, 'client_disconnect')
    socket.value = null
    store.connected = false
  }

  onBeforeUnmount(disconnect)
  return { connect, send, disconnect }
}
