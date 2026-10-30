import http from './http'

export interface Tag {
  id: number
  name: string
}

export function getTags(): Promise<Tag[]> {
  return http.get('/tags')
}

export function createTag(name: string): Promise<Tag> {
  return http.post('/tags', { name })
}
