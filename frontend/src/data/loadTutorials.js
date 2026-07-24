import { load as loadYaml } from 'js-yaml'

const rawModules = import.meta.glob('../../../db/*.yaml', {
  query: '?raw',
  import: 'default',
  eager: true,
})

/** 后端/前端源码：供 yaml files[].path 引用，避免教程代码与实现脱节 */
const sourceModules = import.meta.glob(
  [
    '../../../backend/app/**/*.py',
    '../../../frontend/src/**/*.{js,jsx,css}',
  ],
  {
    query: '?raw',
    import: 'default',
    eager: true,
  },
)

function normalizeRepoPath(p) {
  return String(p || '')
    .replace(/\\/g, '/')
    .replace(/^\.\//, '')
    .replace(/^\/+/, '')
}

function resolveSourceContent(repoPath) {
  const want = normalizeRepoPath(repoPath)
  const entry = Object.entries(sourceModules).find(([key]) => {
    const norm = normalizeRepoPath(key.replace(/^\.\.\/\.\.\/\.\.\//, ''))
    return norm === want || norm.endsWith(`/${want}`) || key.endsWith(`/${want}`)
  })
  if (!entry) return null
  return String(entry[1] ?? '').replace(/\n$/, '')
}

function buildCodeFiles(ex) {
  const fromList = Array.isArray(ex.files) ? ex.files : []
  const files = fromList
    .map((f, index) => {
      const name = f.name || f.path?.split(/[/\\]/).pop() || `file-${index + 1}`
      let content = ''
      if (f.path) {
        content = resolveSourceContent(f.path) || ''
      }
      if (!content && typeof f.code === 'string') {
        content = f.code.replace(/\n$/, '')
      }
      return { id: f.id || name, name, content }
    })
    .filter((f) => f.name)

  if (files.length > 0) return files

  // 兼容旧字段 code:
  if (typeof ex.code === 'string' && ex.code.trim()) {
    return [
      {
        id: 'main',
        name: ex.codeFileName || 'main.py',
        content: ex.code.replace(/\n$/, ''),
      },
    ]
  }
  return []
}

/**
 * 从 db/*.yaml 加载全部分类教程。
 * 新增分类：在 db/ 下加一个 yaml 文件即可。
 * 多文件代码：examples[].files: [{ name, path }] 或 { name, code }
 */
export function loadCategories() {
  return Object.entries(rawModules)
    .map(([path, raw]) => {
      const data = loadYaml(raw)
      const fileName = path.split('/').pop().replace(/\.yaml$/, '')
      return {
        id: data.category || fileName,
        label: data.label || fileName,
        examples: (data.examples || []).map((ex) => {
          const files = buildCodeFiles(ex)
          return {
            id: ex.id,
            title: ex.title,
            code: files[0]?.content ?? '',
            files,
            ui: ex.ui || null,
            notes: Array.isArray(ex.notes) ? ex.notes : [],
            graphImage: typeof ex.graphImage === 'string' ? ex.graphImage : null,
            kind: ex.kind || null,
            window: {
              width: ex.window?.width || 480,
              height: ex.window?.height || 720,
            },
            problem: ex.problem
              ? {
                  link: ex.problem.link || '',
                  statement: (ex.problem.statement || '').trim(),
                  hints: Array.isArray(ex.problem.hints) ? ex.problem.hints : [],
                  examples: Array.isArray(ex.problem.examples) ? ex.problem.examples : [],
                }
              : null,
          }
        }),
      }
    })
    .sort((a, b) => a.label.localeCompare(b.label, 'zh-CN'))
}
