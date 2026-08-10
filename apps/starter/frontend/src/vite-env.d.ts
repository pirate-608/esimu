/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_ESIMU_API_BASE?: string
  readonly VITE_ESIMU_WS_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}