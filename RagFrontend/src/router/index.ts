import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import KnowledgeBase from '../views/KnowledgePages/KnowledgeBase.vue'
import NotFound from '../components/ERS-Pages/404.vue'

interface UserResponse {
  status: string
  data?: {
    role?: string
    email?: string
  }
}

const ROLE_ROUTE_MAP: Record<string, string[]> = {
  guest: ['/knowledge', '/chat', '/history'],
  viewer: ['/knowledge', '/chat', '/history', '/agent'],
  editor: ['/knowledge', '/chat', '/history', '/agent', '/creation'],
  admin: ['*'],
  super_admin: ['*']
}

function canAccessRoute(role: string, path: string): boolean {
  // 单用户模式下所有路由均可访问（未设置或为 true 均视为开启）
  const singleUserMode = import.meta.env.VITE_SINGLE_USER_MODE
  if (singleUserMode === undefined || singleUserMode === '' || singleUserMode === 'true')
    return true
  const allowed = ROLE_ROUTE_MAP[role] || ROLE_ROUTE_MAP.guest
  if (allowed.includes('*')) return true
  return allowed.some(r => path.startsWith(r))
}

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/knowledge'
  },
  {
    path: '/knowledge',
    name: 'KnowledgeBase',
    component: KnowledgeBase
  },
  {
    path: '/knowledge/knowledgeDetail/:id',
    name: 'KnowledgeDetail',
    component: () => import('../views/KnowledgePages/KnowledgeDetail.vue')
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/Chat.vue')
  },
  {
    path: '/chat/:id',
    name: 'chatID',
    component: () => import('../views/Chat.vue')
  },
  {
    path: '/service',
    name: 'Search',
    component: () => import('../views/Ollama_Pages/ollama_basic_pages.vue')
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/History.vue')
  },
  {
    path: '/agent',
    name: 'Agent',
    component: () => import('../views/Agent.vue')
  },
  {
    path: '/files',
    name: 'FileManagement',
    component: () => import('../views/FileManagement.vue')
  },
  {
    path: '/DOC',
    name: '开发文档',
    component: () => import('../views/DOC.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue')
  },
  {
    path: '/LogonOrRegister',
    name: '登录',
    component: () => import('../views/LogonOrRegister/LogonOrRegister.vue')
  },
  {
    path: '/user',
    name: '用户界面',
    component: () => import('../views/TabHeader/User_Page.vue'),
    children: [
      {
        path: '/user/userInfo',
        name: '用户信息',
        component: () => import('../components/user-primary/user-primary.vue')
      },
      {
        path: '/user/coming-soon/:id',
        name: '功能即将上线',
        component: () => import('../components/user-primary/ComingSoon.vue')
      }
    ]
  },
  {
    path: '/testrange',
    name: 'CTE',
    component: () => import('../components/graph-unit/graph-main.vue')
  },
  {
    path: '/square',
    name: 'SharedSquare',
    component: () => import('../views/SharedKnowledge/SharedSquare.vue')
  },
  {
    path: '/shared/:id',
    name: 'SharedDetail',
    component: () => import('../views/SharedKnowledge/SharedDetail.vue')
  },
  {
    path: '/devtools',
    name: 'DevTools',
    component: () => import('../views/DevTools.vue'),
    meta: { devOnly: true }
  },
  {
    path: '/creation',
    name: 'Creation',
    component: () => import('../views/Creation.vue')
  },
  {
    path: '/architecture',
    name: 'Architecture',
    component: () => import('../views/Architecture.vue')
  },
  // 添加专门的404页面路由
  {
    path: '/404',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: '页面未找到'
    }
  },

  // 捕获所有未匹配的路由并重定向到404
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const publicRoutes = ['/LogonOrRegister', '/devtools']

// ── 用户角色本地缓存（带 TTL）───────────────────────────────────────
// 解决"每次导航都远程请求GetUserData导致后端抖动时全站崩溃"的核心问题

const CACHE_TTL_MS = 5 * 60 * 1000 // 5 分钟

let _cachedRole: string | null = null // null = 未缓存/已过期
let _cacheTimestamp = 0 // 上次远程获取成功的时间戳

/**
 * 从本地缓存获取角色，如果缓存有效则返回缓存值。
 * 注意：返回 'admin' 作为默认角色而非 'viewer'——因为：
 *   1. 大多数单用户部署场景下 admin 更合理
 *   2. 即使是首次加载，也不应因为网络慢就降级到 viewer 导致功能打不开
 *   3. 真正的权限校验由后端 API 负责，前端只是 UX 层面的路由过滤
 */
function getCachedRole(): string {
  if (_cachedRole && Date.now() - _cacheTimestamp < CACHE_TTL_MS) {
    return _cachedRole
  }
  // 缓存过期或从未加载 → 返回 admin（不阻塞导航）
  // 原因：即使 GetUserData 失败，也不应让用户卡在 /knowledge 无法访问其他页面
  return localStorage.getItem('user_role') || 'admin'
}

/**
 * 写入本地缓存，供后续导航使用。
 */
function setCachedRole(role: string): void {
  _cachedRole = role
  _cacheTimestamp = Date.now()
  if (role) {
    localStorage.setItem('user_role', role)
  }
}

/**
 * 使缓存失效（强制下次导航时重新获取），用于登录成功或角色变更时调用。
 */
export function invalidateUserCache(): void {
  _cachedRole = null
  _cacheTimestamp = 0
}

// Flag: set to true right after login/register so the first navigation
// skips the remote JWT check (avoids race condition where the JWT was
// just written but the /api/users/me call hasn't resolved yet).
let _justAuthenticated = false

export function markJustAuthenticated() {
  _justAuthenticated = true
  invalidateUserCache() // 登录后清除缓存，确保获取最新角色
}

router.beforeEach((to, from, next) => {
  // 公开路由始终放行
  if (publicRoutes.includes(to.path)) {
    return next()
  }

  // ── 单用户模式（默认开启）────────────────────────────────────
  // VITE_SINGLE_USER_MODE 未设置或为 true 时，完全跳过 JWT 校验
  // 真正的权限由后端 API 负责，前端只做 UX 层面优化
  const singleUserMode = import.meta.env.VITE_SINGLE_USER_MODE
  if (singleUserMode === undefined || singleUserMode === '' || singleUserMode === 'true') {
    return next()
  }

  const jwt = localStorage.getItem('jwt')
  if (!jwt) {
    return next(`/LogonOrRegister?redirect=${encodeURIComponent(to.fullPath)}`)
  }

  if (_justAuthenticated) {
    _justAuthenticated = false
    return next()
  }

  // ── 快速路径：使用本地缓存角色放行，不阻塞导航 ──
  const cachedRole = getCachedRole()
  if (canAccessRoute(cachedRole, to.path)) {
    // 本地判断通过 → 立即放行，后台静默刷新缓存（不阻塞）
    refreshUserRoleInBackground(jwt)
    return next()
  }

  // ── 慢速路径：本地无权限 → 需要远程确认（可能角色已升级）
  fetch('/api/user/GetUserData', {
    method: 'GET',
    headers: { Authorization: `Bearer ${jwt}`, Accept: 'application/json' }
  })
    .then(async response => {
      if (response.status === 401) {
        localStorage.removeItem('jwt')
        invalidateUserCache()
        next(`/LogonOrRegister?redirect=${encodeURIComponent(to.fullPath)}`)
        return null
      }
      return response.json()
    })
    .then((res: UserResponse | null) => {
      if (!res) return
      if (res.status === 'success') {
        const userRole = res.data?.role || 'admin' // 默认 admin 而非 viewer！
        setCachedRole(userRole)
        if (!canAccessRoute(userRole, to.path)) {
          next('/knowledge')
        } else {
          next()
        }
      } else {
        localStorage.removeItem('jwt')
        invalidateUserCache()
        next(`/LogonOrRegister?redirect=${encodeURIComponent(to.fullPath)}`)
      }
    })
    .catch(() => {
      // 远程失败时不降级到 viewer！使用缓存角色（可能是 admin）
      // 这样即使后端短暂不可用，已登录用户仍可正常访问所有页面
      const fallbackRole = getCachedRole()
      if (!canAccessRoute(fallbackRole, to.path)) {
        next('/knowledge')
      } else {
        next()
      }
    })
})

// ── 后台静默刷新用户角色（不阻塞导航）────────────────────────────
let _refreshPromise: Promise<void> | null = null

function refreshUserRoleInBackground(jwt: string): void {
  // 防止并发刷新：如果已有刷新任务在进行中，跳过
  if (_refreshPromise) return

  _refreshPromise = fetch('/api/user/GetUserData', {
    method: 'GET',
    headers: { Authorization: `Bearer ${jwt}`, Accept: 'application/json' }
  })
    .then(async response => {
      if (response.status === 401) {
        localStorage.removeItem('jwt')
        invalidateUserCache()
        return
      }
      const res: UserResponse = await response.json()
      if (res?.status === 'success' && res.data?.role) {
        setCachedRole(res.data.role)
      }
    })
    .catch(() => {
      // 静默失败不影响用户体验，下次导航时会重试
    })
    .finally(() => {
      _refreshPromise = null
    })
}

export default router
