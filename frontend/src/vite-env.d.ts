/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
}

/** Demo-account password, injected by vite.config.ts for the local dev server only ('' in every build). */
declare const __DEMO_PASSWORD__: string;
