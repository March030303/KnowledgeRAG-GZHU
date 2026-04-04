import { readdirSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const srcRoot = fileURLToPath(new URL('..', import.meta.url))

function collectVueFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const entryPath = resolve(directory, entry.name)

    if (entry.isDirectory()) {
      return collectVueFiles(entryPath)
    }

    return entry.isFile() && entry.name.endsWith('.vue') ? [entryPath] : []
  })
}

describe('vue sfc inline handlers', () => {
  it('does not use multi-line inline click handlers', () => {
    const offenders = collectVueFiles(srcRoot).flatMap(filePath => {
      const source = readFileSync(filePath, 'utf8')

      return /@click\s*=\s*"\s*\n/m.test(source) ? [filePath] : []
    })

    expect(
      offenders,
      `Multi-line inline @click handlers found in:\n${offenders.join('\n')}`
    ).toEqual([])
  })
})
