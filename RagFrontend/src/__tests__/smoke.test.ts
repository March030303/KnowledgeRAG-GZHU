import { describe, expect, it } from 'vitest'

describe('frontend toolchain smoke test', () => {
  it('runs vitest successfully', () => {
    expect('KnowledgeRAG-GZHU').toContain('RAG')
  })
})
