/**
 * Theme-scoped browser storage keys.
 *
 * A reference app can be rebuilt with another esimu theme, so browser state
 * must use the active theme prefix instead of a fixed simulator-lab prefix.
 */
import { themeStorageKey } from '@/utils/theme'

export const STORAGE_KEYS = {
  token: themeStorageKey('token'),
  jwt: themeStorageKey('jwt'),
  userToken: themeStorageKey('user_token'),
  username: themeStorageKey('username'),
  saves: themeStorageKey('saves'),
  gameStarted: themeStorageKey('game_started'),
  selectedSaveSlot: themeStorageKey('selected_save_slot'),
  guideShown: themeStorageKey('guide_shown'),
  consoleTheme: themeStorageKey('console_theme'),
} as const
