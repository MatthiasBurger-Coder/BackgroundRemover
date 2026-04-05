import type {
  AssetMetadata,
  AssetRegistrationResponse,
  CreatePromptPayload,
  UpdateWorkbenchSettingsPayload,
  VideoFrameData,
  WorkbenchSnapshot,
  WorkbenchStateResponse,
} from '../../models/workspace'
import { deleteJson, getJson, postFormData, postJson, putJson } from './client'

export function buildAssetSourceUrl(assetId: string): string {
  return `/api/assets/${assetId}/source`
}

export async function registerAsset(file: File): Promise<AssetRegistrationResponse> {
  const body = new FormData()
  body.append('file', file)
  return postFormData<AssetRegistrationResponse>('/assets', body)
}

export async function getAssetMetadata(assetId: string): Promise<AssetMetadata> {
  return getJson<AssetMetadata>(`/assets/${assetId}`)
}

export async function deleteAsset(assetId: string): Promise<void> {
  await deleteJson<undefined>(`/assets/${assetId}`)
}

export async function getFrame(assetId: string, frameIndex: number): Promise<VideoFrameData> {
  return getJson<VideoFrameData>(`/assets/${assetId}/frames/${frameIndex}`)
}

export async function getWorkbenchSnapshot(assetId: string): Promise<WorkbenchSnapshot> {
  return getJson<WorkbenchSnapshot>(`/assets/${assetId}/workbench`)
}

export async function syncWorkbenchFrame(assetId: string, frameIndex: number): Promise<WorkbenchSnapshot> {
  return putJson<WorkbenchSnapshot, { frameIndex: number }>(
    `/assets/${assetId}/workbench/frame`,
    { frameIndex },
  )
}

export async function addWorkbenchPrompt(
  assetId: string,
  payload: CreatePromptPayload,
): Promise<WorkbenchStateResponse> {
  return postJson<WorkbenchStateResponse, CreatePromptPayload>(
    `/assets/${assetId}/workbench/prompts`,
    payload,
  )
}

export async function clearWorkbenchPrompts(assetId: string): Promise<WorkbenchStateResponse> {
  return deleteJson<WorkbenchStateResponse>(`/assets/${assetId}/workbench/prompts`)
}

export async function updateWorkbenchSettings(
  assetId: string,
  payload: UpdateWorkbenchSettingsPayload,
): Promise<WorkbenchStateResponse> {
  return putJson<
    WorkbenchStateResponse,
    {
      threshold: number
      feather: number
      invert: boolean
      showDebugOverlay: boolean
    }
  >(`/assets/${assetId}/workbench/settings`, payload)
}

export async function refreshWorkbenchPreview(assetId: string): Promise<WorkbenchStateResponse> {
  return postJson<WorkbenchStateResponse, undefined>(`/assets/${assetId}/workbench/preview-refresh`)
}
