import { describe, expect, it, beforeEach } from 'vitest'
import { API_ENDPOINTS } from '@/utils/apiConfig'

describe('apiConfig - API_ENDPOINTS', () => {
  it('BASE_URL is defined', () => {
    expect(API_ENDPOINTS.BASE_URL).toBeDefined()
    expect(typeof API_ENDPOINTS.BASE_URL).toBe('string')
  })

  describe('USER endpoints', () => {
    it('AVATAR generates correct URL', () => {
      const path = '/avatars/user1.png'
      const url = API_ENDPOINTS.USER.AVATAR(path)
      expect(url).toContain(path)
      expect(url.startsWith('http')).toBe(true)
    })

    it('AVATAR handles path with special chars', () => {
      const path = '/uploads/user 1/photo.jpg'
      const url = API_ENDPOINTS.USER.AVATAR(path)
      expect(url).toContain('/uploads/user 1/photo.jpg')
    })
  })

  describe('FILES endpoints', () => {
    it('ALL_DOCUMENTS is a string URL', () => {
      expect(typeof API_ENDPOINTS.FILES.ALL_DOCUMENTS).toBe('string')
      expect(API_ENDPOINTS.FILES.ALL_DOCUMENTS).toContain('documents')
    })

    it('DOCUMENT_PREVIEW encodes file path', () => {
      const filePath = '/path/to/my document.pdf'
      const url = API_ENDPOINTS.FILES.DOCUMENT_PREVIEW(filePath)
      expect(url).toContain('file_path=')
      // encodeURIComponent should encode spaces as %20
      expect(url).not.toContain(' ')
    })

    it('DELETE_DOCUMENT encodes file path', () => {
      const filePath = '/path/to/file.pdf'
      const url = API_ENDPOINTS.FILES.DELETE_DOCUMENT(filePath)
      expect(url).toContain('file_path=')
      expect(typeof url).toBe('string')
    })
  })

  describe('KNOWLEDGE endpoints', () => {
    it('GET_ITEM generates correct URL', () => {
      const id = 'kb-001'
      const url = API_ENDPOINTS.KNOWLEDGE.GET_ITEM(id)
      expect(url).toContain(id)
    })

    it('DOCUMENTS_LIST generates correct URL', () => {
      const id = 'kb-test'
      const url = API_ENDPOINTS.KNOWLEDGE.DOCUMENTS_LIST(id)
      expect(url).toContain(id)
    })

    it('INGEST is a string', () => {
      expect(typeof API_ENDPOINTS.KNOWLEDGE.INGEST).toBe('string')
    })

    it('QUERY is a string', () => {
      expect(typeof API_ENDPOINTS.KNOWLEDGE.QUERY).toBe('string')
    })

    it('NATIVE_INGEST is a string', () => {
      expect(typeof API_ENDPOINTS.KNOWLEDGE.NATIVE_INGEST).toBe('string')
    })

    it('NATIVE_QUERY is a string', () => {
      expect(typeof API_ENDPOINTS.KNOWLEDGE.NATIVE_QUERY).toBe('string')
    })
  })

  describe('KNOWLEDGE_GRAPH endpoints', () => {
    it('GET_MERGED_GRAPH generates URL with kbId', () => {
      const kbId = 'my-kb'
      const url = API_ENDPOINTS.KNOWLEDGE_GRAPH.GET_MERGED_GRAPH(kbId)
      expect(url).toContain(kbId)
    })

    it('SEARCH_NODES encodes keyword', () => {
      const kbId = 'kb1'
      const keyword = 'hello world'
      const url = API_ENDPOINTS.KNOWLEDGE_GRAPH.SEARCH_NODES(kbId, keyword)
      expect(url).toContain('keyword=')
      expect(url).not.toContain(' ')
    })

    it('GRAPH_STATS generates URL with kbId', () => {
      const url = API_ENDPOINTS.KNOWLEDGE_GRAPH.GRAPH_STATS('test-kb')
      expect(url).toContain('test-kb')
    })

    it('GET_KB_FILE_GRAPH encodes filename', () => {
      const url = API_ENDPOINTS.KNOWLEDGE_GRAPH.GET_KB_FILE_GRAPH('kb1', 'my file.pdf')
      expect(url).not.toContain(' ')
    })
  })

  describe('OLLAMA endpoints', () => {
    it('MODELS is a string', () => {
      expect(typeof API_ENDPOINTS.OLLAMA.MODELS).toBe('string')
    })

    it('BASE is a valid URL', () => {
      expect(API_ENDPOINTS.OLLAMA.BASE.startsWith('http')).toBe(true)
    })
  })

  describe('CHAT endpoints', () => {
    it('all chat endpoints are defined strings', () => {
      const { BASE, SEND_MESSAGE, SESSIONS, SAVE_SESSION, DELETE_SESSION, DOWNLOAD_CHAT } =
        API_ENDPOINTS.CHAT
      ;[BASE, SEND_MESSAGE, SESSIONS, SAVE_SESSION, DELETE_SESSION, DOWNLOAD_CHAT].forEach(url => {
        expect(typeof url).toBe('string')
        expect(url.length).toBeGreaterThan(0)
      })
    })
  })
})
