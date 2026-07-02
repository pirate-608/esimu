/**
 * Theme metadata helpers generated from the active framework theme manifest.
 */
import { THEME_MANIFEST, type ThemeTermKey } from '@/data/theme.generated'

export const themeDisplayName = THEME_MANIFEST.displayName

export function themeTerm(key: ThemeTermKey, fallback = ''): string {
  return THEME_MANIFEST.terms[key] || fallback
}

export function themeStorageKey(key: string): string {
  return `${THEME_MANIFEST.storage.prefix}_${key}`
}

