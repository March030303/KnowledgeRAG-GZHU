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
  // 单用户模式下所有路由均可访问
  if (import.meta.env.VITE_SINGLE_USER_MODE === 'true') return true
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

// Flag: set to true right after login/register so the first navigation
// skips the remote JWT check (avoids race condition where the JWT was
// just written but the /api/users/me call hasn't resolved yet).
let _justAuthenticated = false

export function markJustAuthenticated() {
  _justAuthenticated = true
}

router.beforeEach((to, from, next) => {
  if (publicRoutes.includes(to.path)) {
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

  fetch('/api/user/GetUserData', {
    method: 'GET',
    headers: { Authorization: `Bearer ${jwt}`, Accept: 'application/json' }
  })
    .then(async response => {
      if (response.status === 401) {
        localStorage.removeItem('jwt')
        next(`/LogonOrRegister?redirect=${encodeURIComponent(to.fullPath)}`)
        return null
      }
      return response.json()
    })
    .then((res: UserResponse | null) => {
      if (!res) return
      if (res.status === 'success') {
        const userRole = res.data?.role || localStorage.getItem('user_role') || 'viewer'
        if (res.data?.role) {
          localStorage.setItem('user_role', res.data.role)
        }
        if (!canAccessRoute(userRole, to.path)) {
          next('/knowledge')
        } else {
          next()
        }
      } else {
        localStorage.removeItem('jwt')
        next(`/LogonOrRegister?redirect=${encodeURIComponent(to.fullPath)}`)
      }
    })
    .catch(() => {
      const userRole = localStorage.getItem('user_role') || 'viewer'
      if (!canAccessRoute(userRole, to.path)) {
        next('/knowledge')
      } else {
        next()
      }
    })
})

export default router
