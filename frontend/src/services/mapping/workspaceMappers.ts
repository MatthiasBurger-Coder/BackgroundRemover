import type {
  AssetMetadata,
  PlaybackState,
  PlaybackStateModel,
  SourceState,
  VideoFrameData,
  WorkbenchSnapshot,
  WorkbenchState,
  WorkbenchStateResponse,
} from '../../models/workspace'
import { buildAssetSourceUrl } from '../api/workspaceApi'

export function createEmptySourceState(): SourceState {
  return {
    activeAssetId: null,
    videoName: 'No source selected',
    sourceFingerprint: null,
    metadata: null,
    sourceStatus: 'idle',
    sourceUrl: null,
    errorMessage: null,
  }
}

export function createEmptyPlaybackState(): PlaybackState {
  return {
    playbackRunning: false,
    playbackFrameIndex: 0,
    playbackTimestampSeconds: 0,
    playbackFps: 0,
    previewStatus: 'idle',
  }
}

export function createEmptyWorkbenchState(): WorkbenchState {
  return {
    workbenchFrameIndex: 0,
    workbenchTimestampSeconds: 0,
    workbenchFrameData: null,
    workbenchFrameRequestKey: null,
    promptEntries: [],
    overlayState: {
      showDebugOverlay: true,
    },
    selectedMaskSettings: {
      threshold: 0.62,
      feather: 8,
      invert: false,
    },
    workbenchStatus: 'idle',
    previewRefreshGeneration: 0,
    errorMessage: null,
  }
}

export function mapAssetToSourceState(asset: AssetMetadata, sourceFingerprint: string): SourceState {
  return {
    activeAssetId: asset.assetId,
    videoName: asset.filename,
    sourceFingerprint,
    metadata: asset,
    sourceStatus: 'ready',
    sourceUrl: buildAssetSourceUrl(asset.assetId),
    errorMessage: null,
  }
}

export function mapPlaybackResponse(playback: PlaybackStateModel): PlaybackState {
  return {
    playbackRunning: playback.playbackRunning,
    playbackFrameIndex: playback.playbackFrameIndex,
    playbackTimestampSeconds: playback.playbackTimestampSeconds,
    playbackFps: playback.playbackFps,
    previewStatus: playback.previewStatus,
  }
}

export function mapWorkbenchSnapshot(snapshot: WorkbenchSnapshot): WorkbenchState {
  return mapWorkbenchState(snapshot.state, snapshot.frame)
}

export function mapWorkbenchState(
  state: WorkbenchStateResponse,
  frame: VideoFrameData | null,
): WorkbenchState {
  return {
    workbenchFrameIndex: state.workbenchFrameIndex,
    workbenchTimestampSeconds: state.workbenchTimestampSeconds,
    workbenchFrameData: frame,
    workbenchFrameRequestKey: state.workbenchFrameRequestKey,
    promptEntries: state.promptEntries,
    overlayState: state.overlayState,
    selectedMaskSettings: state.selectedMaskSettings,
    workbenchStatus: state.workbenchStatus === 'ready' ? 'ready' : 'loading',
    previewRefreshGeneration: state.previewRefreshGeneration,
    errorMessage: null,
  }
}
