import { describe, expect, it } from 'vitest'

import GlobalSearch from '@/components/GlobalSearch.vue'

describe('frontend toolchain smoke test', () => {
  it('runs vitest successfully', () => {
    expect('KnowledgeRAG-GZHU').toContain('RAG')
  })

  it('can import GlobalSearch component', () => {
    expect(GlobalSearch).toBeTruthy()
  })
})
