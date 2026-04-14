export type SourceStatus = 'idle' | 'uploading' | 'ready' | 'error'
export type PreviewStatus = 'idle' | 'ready' | 'playing' | 'paused' | 'seeking' | 'error'
export type WorkbenchStatus = 'idle' | 'loading' | 'ready' | 'error'
export type PromptMode = 'foreground' | 'background'

export interface AssetMetadata {
  assetId: string
  filename: string
  fps: number
  frameCount: number
  durationSeconds: number
  width: number
  height: number
}

export interface PlaybackStateModel {
  playbackRunning: boolean
  playbackFrameIndex: number
  playbackTimestampSeconds: number
  playbackFps: number
  previewStatus: PreviewStatus
}

export interface PromptEntry {
  identifier: number
  mode: PromptMode
  frameIndex: number
  x: number
  y: number
  source: string
}

export interface OverlayState {
  showDebugOverlay: boolean
}

export interface MaskSettings {
  threshold: number
  feather: number
  invert: boolean
}

export interface VideoFrameData {
  assetId: string
  frameIndex: number
  timestampSeconds: number
  mimeType: string
  width: number
  height: number
  imageDataUrl: string
}

export interface RenderedImageData {
  mimeType: string
  width: number
  height: number
  imageDataUrl: string
}

export interface MaskPreview {
  mode: 'preview' | 'final'
  frameIndex: number
  sourceWidth: number
  sourceHeight: number
  previewWidth: number
  previewHeight: number
  promptCount: number
  coverageRatio: number
  overlayImage: RenderedImageData
  maskImage: RenderedImageData
}

export interface SourceState {
  activeAssetId: string | null
  videoName: string
  sourceFingerprint: string | null
  metadata: AssetMetadata | null
  sourceStatus: SourceStatus
  sourceUrl: string | null
  errorMessage: string | null
}

export interface PlaybackState {
  playbackRunning: boolean
  playbackFrameIndex: number
  playbackTimestampSeconds: number
  playbackFps: number
  previewStatus: PreviewStatus
}

export interface WorkbenchState {
  workbenchFrameIndex: number
  workbenchTimestampSeconds: number
  workbenchFrameData: VideoFrameData | null
  workbenchFrameRequestKey: string | null
  promptEntries: PromptEntry[]
  overlayState: OverlayState
  selectedMaskSettings: MaskSettings
  maskPreview: MaskPreview | null
  workbenchStatus: WorkbenchStatus
  previewRefreshGeneration: number
  errorMessage: string | null
}

export interface AssetRegistrationResponse {
  asset: AssetMetadata
  playback: PlaybackStateModel
  workbench: WorkbenchSnapshot
}

export interface WorkbenchStateResponse {
  workbenchFrameIndex: number
  workbenchTimestampSeconds: number
  workbenchFrameRequestKey: string
  previewRefreshGeneration: number
  promptEntries: PromptEntry[]
  overlayState: OverlayState
  selectedMaskSettings: MaskSettings
  maskPreview: MaskPreview | null
  workbenchStatus: string
}

export interface WorkbenchSnapshot {
  state: WorkbenchStateResponse
  frame: VideoFrameData
}

export interface CreatePromptPayload {
  mode: PromptMode
  x: number
  y: number
  source?: string
}

export interface UpdateWorkbenchSettingsPayload {
  threshold: number
  feather: number
  invert: boolean
  showDebugOverlay: boolean
}
