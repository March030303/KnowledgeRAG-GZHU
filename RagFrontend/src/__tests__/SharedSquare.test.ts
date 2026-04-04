import { describe, expect, it } from 'vitest'

describe('SharedSquare view', () => {
  it('compiles successfully', async () => {
    const module = await import('@/views/SharedKnowledge/SharedSquare.vue')

    expect(module.default).toBeTruthy()
    expect(typeof module.default).toBe('object')
  })
})
