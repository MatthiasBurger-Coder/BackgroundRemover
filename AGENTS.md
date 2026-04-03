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
```


## Mandatory bugfix workflow

Whenever a bug, exception, incorrect behavior, defect, or regression is reported, the repository must be handled with a strict regression-first workflow.

No bug fix is complete unless all of the following are true:

1. an automated regression test exists for the reported behavior
2. the test is placed in the correct hexagonal layer
3. the production fix is applied in the correct hexagonal layer
4. the relevant surrounding behavior is verified after the fix

Do not silently patch bugs without test protection.

The required sequence is:

1. analyze the reported defect carefully
2. identify the failing behavior
3. identify the likely root cause
4. determine the correct hexagonal layer for the defect
5. determine the correct hexagonal layer for the regression test
6. create or update a failing automated regression test first
7. run the test and confirm it fails for the correct reason
8. implement the smallest correct production fix in the correct layer
9. run the regression test again and confirm it passes
10. run the relevant surrounding test suite
11. inspect nearby branches, fallbacks, and decision paths and add focused tests where needed
12. summarize root cause, layer placement, fix, and verification


## Layer-specific bug ownership

Fix defects in the layer where the responsibility belongs.

Do not:

- patch domain rule bugs in controllers or UI code
- patch application orchestration bugs in infrastructure code
- patch adapter translation bugs in domain code
- bury architecture mistakes under convenience conditionals
- move logic into random layers because it seems faster

If a bug exposes misplaced logic, move only the necessary part to the correct layer and keep the change as small as possible.


## Test placement rules

### Domain defects

Use domain unit tests for:

- invariants
- business rules
- domain transformations
- invalid state handling
- deterministic domain calculations

Do not primarily test these through adapters if the real defect is domain behavior.

### Application defects

Use application or use-case tests for:

- orchestration errors
- branching decisions across ports
- missing calls to ports
- wrong call order
- incorrect use-case coordination

Application tests should use mocked or fake ports where appropriate.

### Port contract defects

Use contract tests for:

- adapter-to-port mismatches
- incorrect return semantics
- missing required fields across boundaries
- semantic mismatches between application expectations and adapter behavior

### Driving adapter defects

Use adapter tests for:

- UI state translation bugs
- controller/request mapping bugs
- response mapping bugs
- malformed input handling at the system boundary

### Driven adapter defects

Use infrastructure or adapter tests for:

- file access bugs
- repository mapping bugs
- external tool integration bugs
- ffmpeg or video-decoding adapter bugs
- persistence or gateway translation defects

### Cross-boundary defects

Use focused integration tests only when the defect genuinely crosses layers and cannot be protected well in a narrower test.


## Coverage and branch protection rules

Every bugfix must consider branch coverage in the affected area.

Minimum expectations:

- protect the failing path with an automated assertion
- inspect nearby conditionals, fallbacks, null-handling, and empty-state behavior
- add a second focused test for the meaningful alternative branch when the reported bug exposes a branch boundary
- preserve or improve relevant coverage instead of weakening it

Prefer small, behavior-focused tests over broad shallow tests.


## Forbidden shortcuts for bug handling

Do not:

- fix a reported bug without adding or updating a regression test
- place the regression test in the wrong layer just because it is faster
- suppress an error instead of fixing the real cause unless suppression is explicitly the correct behavior
- weaken or delete valid tests to make the build green
- hide business logic in adapters
- bypass ports casually when the architecture already defines them


## Verification expectations after bugfixes

After every bugfix, explicitly verify:

- the new regression test passes
- the relevant surrounding tests pass
- the affected branch or fallback path is protected
- the fix preserves hexagonal boundaries

If exact reproduction is difficult, create the strongest valid characterization test possible from stack traces, logs, failing inputs, or observed behavior. Still do not skip test creation unless it is truly impossible.
