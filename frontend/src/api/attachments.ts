import http from './http'
import type { Attachment } from './entries'

export interface UploadResult {
  id: number
  file_name: string
  file_size: number
  mime_type: string
}

export function uploadAttachment(entryId: number, file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append('file', file)
  return http.post('/attachments', form, {
    params: { entry_id: entryId },
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
}

export function deleteAttachment(id: number): Promise<unknown> {
  return http.delete(`/attachments/${id}`)
}

export async function downloadAttachment(att: Pick<Attachment, 'id' | 'file_name'>): Promise<void> {
  const blob = (await http.get(`/attachments/${att.id}/download`, {
    responseType: 'blob',
    timeout: 60000,
  })) as Blob
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = att.file_name
  a.click()
  URL.revokeObjectURL(url)
}
