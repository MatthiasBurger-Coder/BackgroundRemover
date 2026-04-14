import fs from 'node:fs'

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
function resolveApiHost(): string {
  const configuredHost = process.env.BACKGROUND_REMOVER_API_HOST
  if (configuredHost && configuredHost.length > 0) {
    return configuredHost
  }

  if (process.env.WSL_DISTRO_NAME) {
    try {
      const resolvConf = fs.readFileSync('/etc/resolv.conf', 'utf-8')
      const nameserverLine = resolvConf
        .split('\n')
        .map((line) => line.trim())
        .find((line) => line.startsWith('nameserver '))
      const host = nameserverLine?.split(/\s+/)[1]
      if (host && host.length > 0) {
        return host
      }
    } catch {
      // Fall back to the local host when WSL host detection is unavailable.
    }
  }

  return '127.0.0.1'
}

const apiHost = resolveApiHost()
const apiPort = process.env.BACKGROUND_REMOVER_API_PORT ?? '8010'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `http://${apiHost}:${apiPort}`,
        changeOrigin: true,
      },
    },
  },
})
