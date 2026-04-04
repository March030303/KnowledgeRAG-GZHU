import { existsSync, readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const routerFilePath = fileURLToPath(new URL('../router/index.ts', import.meta.url))
const routerDirectory = dirname(routerFilePath)
const routerSource = readFileSync(routerFilePath, 'utf8')

describe('router lazy imports', () => {
  it('all lazy-loaded view components resolve to existing files', () => {
    const lazyImportPaths = Array.from(
      routerSource.matchAll(/import\('([^']+\.vue)'\)/g),
      match => match[1]
    )

    expect(lazyImportPaths.length).toBeGreaterThan(0)

    for (const componentPath of lazyImportPaths) {
      const resolvedPath = resolve(routerDirectory, componentPath)
      expect(existsSync(resolvedPath), `${componentPath} should exist`).toBe(true)
    }
  })

  it('uses the normalized ACMD route and keeps legacy redirect compatibility', () => {
    expect(routerSource).toContain("path: '/acmd_search'")
    expect(routerSource).toContain("redirect: '/acmd_search'")
    expect(routerSource).toContain("import('../views/ACMD_search/ACMD_search.vue')")
  })
})
