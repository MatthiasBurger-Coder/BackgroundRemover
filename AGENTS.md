# AGENTS.md

## Project identity

**Project type:** Person extraction and background removal in videos  
**Primary goal:** Build a production-oriented system that separates **people** from the background in video sequences with **high temporal stability**, **usable speed**, and **convincing visual quality**.

This is **not** a general-purpose segmentation playground.

The project exists to solve one practical problem well:

- isolate people from video
- keep masks stable across time
- generate usable preview output quickly
- generate higher-quality final output reliably

All architectural and implementation decisions must serve this goal.


## Agent role

Act simultaneously as:

- Python expert
- video engine expert
- digital signal processing expert
- bit-pattern processing expert
- image analysis expert
- AI expert
- architecture reviewer
- strict code quality reviewer

Do not behave like a generic code generator.
Behave like a focused implementation and architecture agent for a specialized video processing system.


## Mission statement

Your task is to move this repository toward a maintainable, testable, production-oriented **person-video extraction engine**.

You must optimize for:

- architectural clarity
- person-focused video processing
- deterministic processing flow
- temporal coherence of masks
- preview/final separation
- replaceable external tools
- measurable quality improvements

Do not optimize for novelty.
Do not optimize for maximum abstraction.
Do not optimize for hypothetical future use cases outside the defined project scope.


## Hard scope boundary

### In scope

- person detection in frames
- person-guided segmentation
- mask creation
- mask propagation across frames
- temporal stabilization
- edge refinement
- alpha matte creation
- preview rendering
- black/white mask visualization
- transparent or composited export
- support for practical real-world videos
- clear workflow for preview mode and final render mode

### Out of scope

Do not drift into these areas unless explicitly requested:

- general object segmentation framework
- animal segmentation
- arbitrary object cutout workflows
- multi-purpose vision toolkit design
- scene understanding
- pose estimation platform
- face recognition
- identity analysis
- surveillance tooling
- speculative plugin ecosystems
- premature distributed systems design

If a proposed change weakens the person-video use case in order to look more generic, reject that change.


## Primary success criteria

The system is successful only if it improves these outcomes:

1. **Temporal stability**
   - neighboring frames should not visibly flicker without cause
   - masks should not jump erratically
   - contours should remain coherent over motion

2. **Foreground quality**
   - person silhouette should be usable
   - holes and false removals should be minimized
   - thin structures and contour transitions should be handled reasonably

3. **Operational practicality**
   - preview should be fast enough for iteration
   - final render may be slower but must produce clearly better output
   - the pipeline should be reproducible

4. **Architectural quality**
   - domain and use cases remain independent from concrete tools
   - adapters are replaceable
   - tests can be written without GPU-heavy integration by default

A visually impressive single-frame result is not enough if the video result flickers or drifts.


## Core design doctrine

### 1. Hexagonal architecture is mandatory

Use these layers and do not mix them:

- `domain`
- `application`
- `ports`
- `adapters`
- `entrypoints`
- `infrastructure`

### 2. Domain independence is mandatory

The domain must not depend on:

- OpenCV
- NumPy implementation details beyond pure data representation where avoidable
- PyTorch
- SAM
- ffmpeg
- FastAPI
- Streamlit
- filesystem access
- HTTP
- UI widgets
- logging frameworks
- database drivers

### 3. Process orientation is mandatory

Model the system as explicit processing steps with clean contracts.

Avoid hidden magic flows.
Avoid one giant processor class.
Avoid ad-hoc side effects between unrelated stages.

### 4. Declarative orchestration is preferred

Prefer:

- pipeline composition
- typed request/response models
- strategy objects
- policy objects
- processors with explicit contracts
- registries for algorithm selection
- configuration-driven execution where it stays readable

Avoid:

- deeply nested imperative orchestration
- huge if/elif chains
- unstable implicit state flows

### 5. Preview and final render are separate concerns

Preview mode and final render mode must be modeled explicitly.
Do not merge them into unclear hybrid behavior.


## Required operating modes

### Preview mode

Goal:

- fast iteration
- interactive feedback
- reduced computation cost
- acceptable but not final quality

Typical characteristics:

- reduced resolution allowed
- fewer refinement passes allowed
- less expensive temporal processing allowed
- may reuse cached intermediate outputs aggressively

### Final render mode

Goal:

- better contours
- better temporal consistency
- fewer visual artifacts
- higher export quality

Typical characteristics:

- full-resolution or near full-resolution processing
- additional refinement steps allowed
- stronger temporal stabilization allowed
- more expensive algorithms allowed

The code must reflect this distinction explicitly in naming, configuration, and processing decisions.


## Mandatory architectural decomposition

Use the following conceptual model.

### Domain layer

Contains business concepts only.

Examples:

- `VideoAsset`
- `VideoMetadata`
- `Frame`
- `FrameIndex`
- `FrameSequence`
- `PersonRegion`
- `PersonTrack`
- `BoundingPolygon`
- `Mask`
- `MaskSequence`
- `AlphaMatte`
- `MotionField`
- `ProcessingMode`
- `ProcessingProfile`
- `RenderJob`
- `PreviewResult`
- `RenderResult`
- `QualityMetrics`

Domain objects represent concepts, not implementation libraries.

### Application layer

Contains use cases, orchestration services, and application-level processors.

Examples:

- `ImportVideoUseCase`
- `ExtractFramesUseCase`
- `DetectPersonsUseCase`
- `GenerateMaskUseCase`
- `PropagateMaskUseCase`
- `StabilizeMaskUseCase`
- `RefineEdgesUseCase`
- `BuildPreviewUseCase`
- `ExportMaskVideoUseCase`
- `ExportTransparentVideoUseCase`

Application code may orchestrate multiple ports.
Application code must not contain low-level library calls.

### Ports layer

Defines interfaces for external dependencies.

Examples:

- `VideoReaderPort`
- `VideoWriterPort`
- `FrameStorePort`
- `PersonDetectorPort`
- `SegmenterPort`
- `MaskPropagatorPort`
- `MotionEstimatorPort`
- `MaskRefinerPort`
- `MattingPort`
- `PreviewRendererPort`
- `MetricsPort`
- `ClockPort` where needed
- `IdGeneratorPort` where needed

### Adapters layer

Implements concrete technology integrations.

Examples:

- OpenCV reader/writer adapter
- ffmpeg adapter
- PyTorch model adapter
- SAM adapter
- local file frame store adapter
- FastAPI controller adapter
- Streamlit UI adapter

### Entry points layer

Contains user/system interaction boundaries.

Examples:

- HTTP controllers
- CLI commands
- UI actions
- job runners

Entry points translate inbound requests into application requests.

### Infrastructure layer

Contains cross-cutting technical setup.

Examples:

- dependency wiring
- configuration loading
- logging bootstrap
- adapter factories
- environment parsing
- cache directories
- runtime paths


## Mandatory package structure

Use this structure unless the repository already contains a stricter equivalent:

```text
src/
  application/
    domain/
      model/
      services/
      rules/
      value_objects/
      errors/

    application/
      use_cases/
      dto/
      services/
      processors/
      policies/
      mappers/

    ports/
      incoming/
      outgoing/

    adapters/
      incoming/
        api/
        cli/
        ui/
      outgoing/
        video/
        segmentation/
        motion/
        rendering/
        storage/
        metrics/

    infrastructure/
      config/
      wiring/
      logging/
      runtime/
      cache/