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

describe('vue sfc style syntax', () => {
  it('does not use JavaScript-style comments inside style blocks', () => {
    const offenders = collectVueFiles(srcRoot).flatMap(filePath => {
      const source = readFileSync(filePath, 'utf8')
      const styleBlocks = Array.from(
        source.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/g),
        match => match[1]
      )

      return styleBlocks.some(block => /^\s*\/\//m.test(block)) ? [filePath] : []
    })

    expect(offenders, `Invalid style comments found in:\n${offenders.join('\n')}`).toEqual([])
  })
})
