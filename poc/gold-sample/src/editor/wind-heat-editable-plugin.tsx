/** @jsxImportSource preact */
import {Img, Node, Scene2D, Txt} from '@revideo/2d';
import {
  SceneRenderEvent,
  Vector2,
  transformVector,
  transformVectorAsPoint,
} from '@revideo/core';
import {
  MouseButton,
  OverlayWrapper,
  makeEditorPlugin,
  useApplication,
  useCurrentScene,
  useViewportContext,
  useViewportMatrix,
} from '@revideo/ui';
import {signal, useSignalEffect} from '@preact/signals';
import {ComponentChildren, createContext} from 'preact';
import {createPortal} from 'preact/compat';
import {useContext, useEffect, useRef, useState} from 'preact/hooks';

type LayerTransform = {
  x?: number;
  y?: number;
  scale?: number;
  rotation?: number;
  /** Multiplier applied to the authored/animated opacity. */
  opacity?: number;
};

type LayerPatch = {
  transform?: LayerTransform;
  /** Legacy flat transform fields kept for saved candidate compatibility. */
  x?: number;
  y?: number;
  scale?: number;
  rotation?: number;
  opacity?: number;
  src?: string;
  text?: string;
  fontSize?: number;
  fill?: string;
};

type PatchMap = Record<string, LayerPatch>;

type NormalizedTransform = {
  x: number;
  y: number;
  scale: number;
  rotation: number;
  opacity: number;
};

type Bounds = {
  left: number;
  top: number;
  right: number;
  bottom: number;
  width: number;
  height: number;
  center: Vector2;
};

type EditorState = {
  selectedKeys: ReturnType<typeof signal<string[]>>;
  patches: ReturnType<typeof signal<PatchMap>>;
  history: ReturnType<typeof signal<PatchMap[]>>;
  historyIndex: ReturnType<typeof signal<number>>;
  status: ReturnType<typeof signal<string>>;
  scene: ReturnType<typeof signal<Scene2D | null>>;
  afterRender: ReturnType<typeof signal<number>>;
};

type EditorUiState = {
  selectedKeys: string[];
};

const EDITABLE_PREFIX = 'editable:';
const UI_STORAGE_KEY = 'wind-heat-editor-ui-state';
const stateContext = createContext<EditorState | null>(null);
const lastApplied = new WeakMap<
  Node,
  {
    transform: NormalizedTransform;
    src?: string;
    text?: string;
    fontSize?: number;
    fill?: string;
    baseSrc?: string;
    baseText?: string;
    baseFontSize?: number;
    baseFill?: string;
    baseOpacity?: number;
    appliedPosition: Vector2;
    appliedScale: Vector2;
    appliedRotation: number;
    appliedOpacity: number;
  }
>();
const editorGlobal = globalThis as typeof globalThis & {
  __windHeatEditorState?: EditorState;
};
const sharedState =
  editorGlobal.__windHeatEditorState ??
  (editorGlobal.__windHeatEditorState = {
    selectedKeys: signal<string[]>([]),
    patches: signal<PatchMap>({}),
    history: signal<PatchMap[]>([{}]),
    historyIndex: signal(0),
    status: signal('未保存调整'),
    scene: signal<Scene2D | null>(null),
    afterRender: signal(0),
  });
let stateLoaded = false;
let stateLoading: Promise<void> | null = null;

function readEditorUiState(): Partial<EditorUiState> {
  if (typeof sessionStorage === 'undefined') return {};
  try {
    return JSON.parse(sessionStorage.getItem(UI_STORAGE_KEY) ?? '{}');
  } catch {
    return {};
  }
}

function persistEditorUiState(state: EditorState) {
  if (typeof sessionStorage === 'undefined') return;
  sessionStorage.setItem(
    UI_STORAGE_KEY,
    JSON.stringify({
      selectedKeys: state.selectedKeys.peek(),
    } satisfies EditorUiState),
  );
}

function setSelectedKeys(state: EditorState, keys: string[]) {
  const scene = state.scene.peek();
  state.selectedKeys.value = Array.from(new Set(keys)).filter(key => {
    const node = scene?.getNode(key);
    return node ? isBusinessEditable(node) : true;
  });
  persistEditorUiState(state);
}

function copyPatches(patches: PatchMap): PatchMap {
  return JSON.parse(JSON.stringify(patches)) as PatchMap;
}

function normalizeTransform(patch?: LayerPatch): NormalizedTransform {
  return {
    x: patch?.transform?.x ?? patch?.x ?? 0,
    y: patch?.transform?.y ?? patch?.y ?? 0,
    scale: patch?.transform?.scale ?? patch?.scale ?? 1,
    rotation: patch?.transform?.rotation ?? patch?.rotation ?? 0,
    opacity: patch?.transform?.opacity ?? patch?.opacity ?? 1,
  };
}

function withTransform(
  patch: LayerPatch | undefined,
  transform: NormalizedTransform,
): LayerPatch {
  return {...patch, transform};
}

function near(a: number, b: number) {
  return Math.abs(a - b) < 0.001;
}

function nearVector(a: Vector2, b: Vector2) {
  return near(a.x, b.x) && near(a.y, b.y);
}

function useEditorState() {
  const value = useContext(stateContext);
  if (!value) throw new Error('Wind-heat editor state is unavailable.');
  return value;
}

function editableAncestor(node: Node | null): Node | null {
  let current = node;
  while (current) {
    if (current.key.startsWith(EDITABLE_PREFIX)) return current;
    current = current.parent();
  }
  return null;
}

function isBusinessEditable(node: Node) {
  if (
    !node.key.startsWith(EDITABLE_PREFIX) ||
    node.key.includes(':master:') ||
    node.key.includes(':subtitle') ||
    node.key.includes(':safe-area:')
  ) {
    return false;
  }
  if (node instanceof Img || node instanceof Txt) return true;
  return (
    node.key.includes(':group:') &&
    !/:group:\d+:/.test(node.key) &&
    !node.key.includes(':item:')
  );
}

/**
 * Multi-scene projects: keep editor state.scene in lockstep with PlaybackManager
 * so hit-testing does not stay stuck on the first scene after scrubbing.
 */
function syncSceneFromPlayback(state: EditorState): Scene2D | null {
  const current = state.scene.peek();
  if (!current) return null;
  try {
    const mgr = (current as unknown as {playback?: {playback?: {
      currentScene?: Scene2D;
      currentSceneReference?: Scene2D;
    }}}).playback?.playback;
    const live = mgr?.currentScene ?? mgr?.currentSceneReference;
    if (live && live !== current) {
      state.scene.value = live;
      return live;
    }
  } catch {
    // ignore — fall back to current
  }
  return current;
}

function editableAtPoint(scene: Scene2D | null, point: Vector2): Node | null {
  if (!scene) return null;
  const candidates = scene
    .getView()
    .findAll(
      node => isBusinessEditable(node) && node.absoluteOpacity() > 0.01,
    )
    .filter(node => {
      const local = transformVectorAsPoint(point, node.worldToLocal());
      return node.cacheBBox().includes(local);
    })
    .map(node => {
      let depth = 0;
      let parent = node.parent();
      while (parent) {
        depth++;
        parent = parent.parent();
      }
      const box = node.cacheBBox();
      const priority = node instanceof Img ? 0 : node instanceof Txt ? 1 : 2;
      return {node, depth, area: box.width * box.height, priority};
    })
    .sort(
      (a, b) =>
        a.priority - b.priority ||
        a.area - b.area ||
        b.depth - a.depth,
    );
  return candidates[0]?.node ?? null;
}

function boundsFromPoints(points: Vector2[]): Bounds | null {
  if (!points.length) return null;
  const xs = points.map(point => point.x);
  const ys = points.map(point => point.y);
  const left = Math.min(...xs);
  const top = Math.min(...ys);
  const right = Math.max(...xs);
  const bottom = Math.max(...ys);
  return {
    left,
    top,
    right,
    bottom,
    width: right - left,
    height: bottom - top,
    center: new Vector2((left + right) / 2, (top + bottom) / 2),
  };
}

function nodeWorldBounds(node: Node): Bounds | null {
  return boundsFromPoints(
    node
      .cacheBBox()
      .corners.map(point => transformVectorAsPoint(point, node.localToWorld())),
  );
}

function nodesWorldBounds(nodes: Node[]): Bounds | null {
  return boundsFromPoints(
    nodes.flatMap(node => {
      const bounds = nodeWorldBounds(node);
      if (!bounds) return [];
      return [
        new Vector2(bounds.left, bounds.top),
        new Vector2(bounds.right, bounds.top),
        new Vector2(bounds.right, bounds.bottom),
        new Vector2(bounds.left, bounds.bottom),
      ];
    }),
  );
}

function boundsIntersect(a: Bounds, b: Bounds) {
  return !(
    a.right < b.left ||
    a.left > b.right ||
    a.bottom < b.top ||
    a.top > b.bottom
  );
}

function marqueeBounds(start: Vector2, current: Vector2): Bounds {
  return boundsFromPoints([start, current])!;
}

function editableInBounds(scene: Scene2D | null, bounds: Bounds): string[] {
  if (!scene) return [];
  const candidates = scene
    .getView()
    .findAll(
      node => isBusinessEditable(node) && node.absoluteOpacity() > 0.01,
    )
    .filter(node => {
      const nodeBounds = nodeWorldBounds(node);
      return nodeBounds ? boundsIntersect(bounds, nodeBounds) : false;
    });
  return candidates
    .filter(
      node =>
        !candidates.some(other => {
          if (other === node) return false;
          let parent = other.parent();
          while (parent) {
            if (parent === node) return true;
            parent = parent.parent();
          }
          return false;
        }),
    )
    .map(node => node.key);
}

function worldDeltaToParent(node: Node, delta: Vector2) {
  return node.parent()
    ? transformVector(delta, node.parent()!.worldToLocal())
    : delta;
}

function moveSelectedByWorldDelta(
  state: EditorState,
  source: PatchMap,
  delta: Vector2,
) {
  const next = copyPatches(source);
  for (const key of state.selectedKeys.peek()) {
    const node = state.scene.peek()?.getNode(key);
    if (!node) continue;
    const initial = normalizeTransform(next[key]);
    const localDelta = worldDeltaToParent(node, delta);
    next[key] = withTransform(next[key], {
      ...initial,
      x: initial.x + localDelta.x,
      y: initial.y + localDelta.y,
    });
  }
  return next;
}

function applyPatches(scene: Scene2D | null, patches: PatchMap) {
  if (!scene) return;
  for (const node of scene
    .getView()
    .findAll(node => node.key.startsWith(EDITABLE_PREFIX))) {
    const previous = lastApplied.get(node);
    if (!previous || patches[node.key]) continue;
    const position = node.position();
    const scale = node.scale();
    if (nearVector(position, previous.appliedPosition)) {
      node.position([
        position.x - previous.transform.x,
        position.y - previous.transform.y,
      ]);
    }
    if (nearVector(scale, previous.appliedScale)) {
      node.scale([
        scale.x / previous.transform.scale,
        scale.y / previous.transform.scale,
      ]);
    }
    if (near(node.rotation(), previous.appliedRotation)) {
      node.rotation(node.rotation() - previous.transform.rotation);
    }
    if (near(node.opacity(), previous.appliedOpacity)) {
      node.opacity(
        previous.transform.opacity === 0
          ? (previous.baseOpacity ?? node.opacity())
          : node.opacity() / previous.transform.opacity,
      );
    }
    if (
      node instanceof Img &&
      previous.baseSrc &&
      previous.src === node.src()
    ) {
      node.src(previous.baseSrc);
    }
    if (node instanceof Txt) {
      if (
        previous.baseText !== undefined &&
        previous.text === node.text()
      ) {
        node.text(previous.baseText);
      }
      if (
        previous.baseFontSize !== undefined &&
        previous.fontSize === node.fontSize()
      ) {
        node.fontSize(previous.baseFontSize);
      }
      if (
        previous.baseFill !== undefined &&
        previous.fill === String(node.fill())
      ) {
        node.fill(previous.baseFill);
      }
    }
    lastApplied.delete(node);
  }

  for (const [key, patch] of Object.entries(patches)) {
    const node = scene.getNode(key);
    if (!node) continue;

    const previous = lastApplied.get(node);
    const previousTransform = previous?.transform ?? normalizeTransform();
    const transform = normalizeTransform(patch);
    const position = node.position();
    const scale = node.scale();
    const positionContainsPrevious =
      previous && nearVector(position, previous.appliedPosition);
    const scaleContainsPrevious =
      previous && nearVector(scale, previous.appliedScale);
    const rotationContainsPrevious =
      previous && near(node.rotation(), previous.appliedRotation);
    const opacityContainsPrevious =
      previous && near(node.opacity(), previous.appliedOpacity);
    const baseX = positionContainsPrevious
      ? position.x - previousTransform.x
      : position.x;
    const baseY = positionContainsPrevious
      ? position.y - previousTransform.y
      : position.y;
    const baseScaleX = scaleContainsPrevious
      ? scale.x / previousTransform.scale
      : scale.x;
    const baseScaleY = scaleContainsPrevious
      ? scale.y / previousTransform.scale
      : scale.y;
    const baseRotation = rotationContainsPrevious
      ? node.rotation() - previousTransform.rotation
      : node.rotation();
    const baseOpacity = opacityContainsPrevious
      ? previousTransform.opacity === 0
        ? (previous?.baseOpacity ?? node.opacity())
        : node.opacity() / previousTransform.opacity
      : node.opacity();
    const baseSrc =
      previous?.baseSrc ??
      (node instanceof Img && !previous?.src ? node.src() : undefined);
    const baseText =
      previous?.baseText ??
      (node instanceof Txt && previous?.text === undefined
        ? node.text()
        : undefined);
    const baseFontSize =
      previous?.baseFontSize ??
      (node instanceof Txt && previous?.fontSize === undefined
        ? node.fontSize()
        : undefined);
    const baseFill =
      previous?.baseFill ??
      (node instanceof Txt && previous?.fill === undefined
        ? String(node.fill())
        : undefined);
    node.position([baseX + transform.x, baseY + transform.y]);
    node.scale([
      baseScaleX * transform.scale,
      baseScaleY * transform.scale,
    ]);
    node.rotation(baseRotation + transform.rotation);
    node.opacity(baseOpacity * transform.opacity);

    if (node instanceof Img && patch.src) {
      node.src(patch.src);
    }
    if (node instanceof Txt) {
      if (patch.text !== undefined) node.text(patch.text);
      if (patch.fontSize !== undefined) node.fontSize(patch.fontSize);
      if (patch.fill !== undefined) node.fill(patch.fill);
    }
    lastApplied.set(node, {
      transform,
      src: patch.src,
      text: patch.text,
      fontSize: patch.fontSize,
      fill: patch.fill,
      baseSrc,
      baseText,
      baseFontSize,
      baseFill,
      baseOpacity,
      appliedPosition: node.position(),
      appliedScale: node.scale(),
      appliedRotation: node.rotation(),
      appliedOpacity: node.opacity(),
    });
  }
}

function Provider({children}: {children?: ComponentChildren}) {
  const currentScene = useCurrentScene() as Scene2D;
  const state = sharedState;

  state.scene.value = currentScene;

  useEffect(() => {
    const uiState = readEditorUiState();
    setSelectedKeys(
      state,
      uiState.selectedKeys ?? state.selectedKeys.peek(),
    );
    if (stateLoaded) {
      applyPatches(currentScene, state.patches.peek());
      return;
    }
    if (!stateLoading) {
      stateLoading = fetch('/__wind_heat_editor/state')
        .then(response => response.json())
        .then((data: {patches?: PatchMap}) => {
          const patches = data.patches ?? {};
          state.patches.value = patches;
          state.history.value = [copyPatches(patches)];
          state.historyIndex.value = 0;
          state.status.value = Object.keys(patches).length
            ? '已恢复上次保存的模板调整'
            : '未保存调整';
          stateLoaded = true;
        })
        .catch(() => {
          state.status.value = '本地保存服务未连接';
        });
    }
    stateLoading.then(() => applyPatches(currentScene, state.patches.peek()));
  }, []);

  useSignalEffect(() =>
    state.scene.value?.onRenderLifecycle.subscribe(([event]) => {
      if (event === SceneRenderEvent.BeginRender) {
        syncSceneFromPlayback(state);
        applyPatches(state.scene.peek(), state.patches.peek());
      }
      if (event === SceneRenderEvent.AfterRender) {
        state.afterRender.value++;
      }
    }),
  );

  return (
    <stateContext.Provider value={state}>{children}</stateContext.Provider>
  );
}

function commit(state: EditorState, next: PatchMap) {
  const retained = state.history.peek().slice(0, state.historyIndex.peek() + 1);
  retained.push(copyPatches(next));
  state.history.value = retained;
  state.historyIndex.value = retained.length - 1;
  state.patches.value = next;
  state.status.value = '有未保存调整';
  applyPatches(state.scene.peek(), next);
}

function undo(state: EditorState) {
  const nextIndex = Math.max(0, state.historyIndex.peek() - 1);
  state.historyIndex.value = nextIndex;
  state.patches.value = copyPatches(state.history.peek()[nextIndex] ?? {});
  state.status.value = '已撤销，尚未保存';
  applyPatches(state.scene.peek(), state.patches.peek());
}

function redo(state: EditorState) {
  const nextIndex = Math.min(
    state.history.peek().length - 1,
    state.historyIndex.peek() + 1,
  );
  state.historyIndex.value = nextIndex;
  state.patches.value = copyPatches(state.history.peek()[nextIndex] ?? {});
  state.status.value = '已重做，尚未保存';
  applyPatches(state.scene.peek(), state.patches.peek());
}

function OverlayComponent() {
  const state = useEditorState();
  const {player} = useApplication();
  const viewport = useViewportContext();
  const matrix = useViewportMatrix();
  const [panelOpen, setPanelOpen] = useState(
    () => typeof window === 'undefined' || window.innerWidth > 900,
  );
  const [marquee, setMarquee] = useState<{
    start: Vector2;
    current: Vector2;
  } | null>(null);
  const [clipboardCount, setClipboardCount] = useState(0);
  const [exporting, setExporting] = useState<'video' | 'pptx' | null>(null);
  const [exportMessage, setExportMessage] = useState(
    '导出只生成当前作品，不会保存成模板。',
  );
  const [saveConfirming, setSaveConfirming] = useState(false);
  const [segAvailable, setSegAvailable] = useState(false);
  const [segLoading, setSegLoading] = useState(false);
  const [segMessage, setSegMessage] = useState('');
  const [segScenes, setSegScenes] = useState<
    {
      id: string;
      title: string;
      enabled: boolean;
      narration_text: string;
      audio_source?: string;
      duration_s: number;
      timeline_start?: number | null;
      timeline_end?: number | null;
    }[]
  >([]);
  const [segTotal, setSegTotal] = useState(0);
  const [segActiveId, setSegActiveId] = useState<string | null>(null);
  const [segDraft, setSegDraft] = useState('');
  /** auto=优先 Qwen3 参考声线克隆；edge=微软；clone=强制克隆 */
  const [segBackend, setSegBackend] = useState<'auto' | 'clone' | 'edge'>('auto');
  const clipboard = useRef<LayerPatch[]>([]);
  const textInput = useRef<HTMLTextAreaElement | null>(null);
  const saveConfirmationAt = useRef(0);
  const saveConfirmationTimer = useRef<number | undefined>();
  const drag = useRef<{
    mode: 'move' | 'scale' | 'rotate' | 'marquee';
    start: Vector2;
    current?: Vector2;
    patches: PatchMap;
    changed: boolean;
    selectionBefore: string[];
    additive: boolean;
    groupBounds?: Bounds;
    nodeCenters?: Record<string, Vector2>;
  } | null>(null);

  state.afterRender.value;
  state.selectedKeys.value;
  state.patches.value;

  useSignalEffect(() => {
    state.patches.value;
    player.requestSeek(player.status.frame);
  });

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target?.isContentEditable
      ) {
        return;
      }
      const command = event.metaKey || event.ctrlKey;
      const key = event.key.toLowerCase();
      if (command && key === 'z') {
        event.preventDefault();
        event.shiftKey ? redo(state) : undo(state);
        return;
      }
      if (command && key === 'c' && state.selectedKeys.peek().length) {
        event.preventDefault();
        clipboard.current = state.selectedKeys
          .peek()
          .map(selectedKey =>
            copyPatches({value: state.patches.peek()[selectedKey] ?? {}}).value,
          );
        setClipboardCount(clipboard.current.length);
        state.status.value = `已复制 ${clipboard.current.length} 个图层的调整`;
        return;
      }
      if (command && key === 'v' && clipboard.current.length) {
        event.preventDefault();
        const next = copyPatches(state.patches.peek());
        state.selectedKeys.peek().forEach((selectedKey, index) => {
          next[selectedKey] = copyPatches({
            value:
              clipboard.current[index % clipboard.current.length] ?? {},
          }).value;
        });
        commit(state, next);
        return;
      }
      if (event.key === 'Escape') {
        setSelectedKeys(state, []);
        setMarquee(null);
        return;
      }
      if (
        (event.key === 'Delete' || event.key === 'Backspace') &&
        state.selectedKeys.peek().length
      ) {
        event.preventDefault();
        const next = copyPatches(state.patches.peek());
        for (const selectedKey of state.selectedKeys.peek()) {
          const transform = normalizeTransform(next[selectedKey]);
          next[selectedKey] = withTransform(next[selectedKey], {
            ...transform,
            opacity: 0,
          });
        }
        commit(state, next);
        state.status.value = '已隐藏所选图层，可撤销恢复';
        return;
      }
      const arrowDelta: Record<string, Vector2> = {
        ArrowLeft: new Vector2(-1, 0),
        ArrowRight: new Vector2(1, 0),
        ArrowUp: new Vector2(0, -1),
        ArrowDown: new Vector2(0, 1),
      };
      if (arrowDelta[event.key] && state.selectedKeys.peek().length) {
        event.preventDefault();
        const step = event.shiftKey ? 10 : 1;
        commit(
          state,
          moveSelectedByWorldDelta(
            state,
            state.patches.peek(),
            arrowDelta[event.key].scale(step),
          ),
        );
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  useEffect(() => {
    document.body.classList.toggle('wind-heat-editor-panel-open', panelOpen);
    return () => {
      document.body.classList.remove('wind-heat-editor-panel-open');
    };
  }, [panelOpen]);

  const canvasPoint = (event: PointerEvent) => {
    const viewportPoint = new Vector2(
      event.clientX - viewport.rect.x,
      event.clientY - viewport.rect.y,
    );
    return transformVectorAsPoint(viewportPoint, matrix.inverse());
  };

  const beginDrag = (
    event: PointerEvent,
    mode: 'move' | 'scale' | 'rotate' | 'marquee',
  ) => {
    if (event.button !== MouseButton.Left) return;
    syncSceneFromPlayback(state);
    event.preventDefault();
    event.stopPropagation();
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
    const selectedNodes = state.selectedKeys
      .peek()
      .map(key => state.scene.peek()?.getNode(key) ?? null)
      .filter((node): node is Node => Boolean(node));
    drag.current = {
      mode,
      start: canvasPoint(event),
      patches: copyPatches(state.patches.peek()),
      changed: false,
      selectionBefore: [...state.selectedKeys.peek()],
      additive: event.shiftKey,
      groupBounds: nodesWorldBounds(selectedNodes) ?? undefined,
      nodeCenters: Object.fromEntries(
        selectedNodes.flatMap(node => {
          const bounds = nodeWorldBounds(node);
          return bounds ? [[node.key, bounds.center]] : [];
        }),
      ),
    };
    if (mode === 'marquee') {
      const start = canvasPoint(event);
      setMarquee({start, current: start});
      state.status.value = '拖动框选图层…';
    }
  };

  const onPointerMove = (event: PointerEvent) => {
    if (!drag.current) return;
    const current = canvasPoint(event);
    const delta = current.sub(drag.current.start);
    if (Math.abs(delta.x) + Math.abs(delta.y) < 0.5) return;
    drag.current.changed = true;
    if (drag.current.mode === 'marquee') {
      drag.current.current = current;
      setMarquee({start: drag.current.start, current});
      return;
    }
    const next = copyPatches(drag.current.patches);
    const groupBounds = drag.current.groupBounds;
    const nodeCenters = drag.current.nodeCenters ?? {};
    const startDistance = groupBounds
      ? Math.max(1, drag.current.start.sub(groupBounds.center).magnitude)
      : 1;
    const currentDistance = groupBounds
      ? Math.max(1, current.sub(groupBounds.center).magnitude)
      : 1;
    const scaleFactor = Math.max(
      0.1,
      Math.min(10, currentDistance / startDistance),
    );
    const startAngle = groupBounds
      ? Math.atan2(
          drag.current.start.y - groupBounds.center.y,
          drag.current.start.x - groupBounds.center.x,
        )
      : 0;
    const currentAngle = groupBounds
      ? Math.atan2(
          current.y - groupBounds.center.y,
          current.x - groupBounds.center.x,
        )
      : 0;
    const rotationRadians = currentAngle - startAngle;
    const rotationDegrees = (rotationRadians * 180) / Math.PI;
    for (const key of state.selectedKeys.peek()) {
      const initial = normalizeTransform(next[key]);
      const node = state.scene.peek()?.getNode(key);
      if (!node) continue;
      if (drag.current.mode === 'move') {
        const localDelta = worldDeltaToParent(node, delta);
        next[key] = withTransform(next[key], {
          ...initial,
          x: initial.x + localDelta.x,
          y: initial.y + localDelta.y,
        });
      } else if (drag.current.mode === 'scale' && groupBounds) {
        const center = nodeCenters[key] ?? groupBounds.center;
        const scaledCenter = groupBounds.center.add(
          center.sub(groupBounds.center).scale(scaleFactor),
        );
        const localDelta = worldDeltaToParent(
          node,
          scaledCenter.sub(center),
        );
        next[key] = withTransform(next[key], {
          ...initial,
          x: initial.x + localDelta.x,
          y: initial.y + localDelta.y,
          scale: Math.max(0.1, Math.min(10, initial.scale * scaleFactor)),
        });
      } else if (drag.current.mode === 'rotate' && groupBounds) {
        const center = nodeCenters[key] ?? groupBounds.center;
        const relative = center.sub(groupBounds.center);
        const rotatedCenter = groupBounds.center.add(
          new Vector2(
            relative.x * Math.cos(rotationRadians) -
              relative.y * Math.sin(rotationRadians),
            relative.x * Math.sin(rotationRadians) +
              relative.y * Math.cos(rotationRadians),
          ),
        );
        const localDelta = worldDeltaToParent(
          node,
          rotatedCenter.sub(center),
        );
        next[key] = withTransform(next[key], {
          ...initial,
          x: initial.x + localDelta.x,
          y: initial.y + localDelta.y,
          rotation: initial.rotation + rotationDegrees,
        });
      }
    }
    state.patches.value = next;
    state.status.value = '有未保存调整';
    applyPatches(state.scene.peek(), next);
  };

  const finishDrag = () => {
    if (!drag.current) return;
    if (drag.current.mode === 'marquee') {
      const currentPoint = drag.current.current ?? drag.current.start;
      if (drag.current.changed) {
        const boxed = editableInBounds(
          state.scene.peek(),
          marqueeBounds(drag.current.start, currentPoint),
        );
        setSelectedKeys(
          state,
          drag.current.additive
            ? Array.from(
                new Set([...drag.current.selectionBefore, ...boxed]),
              )
            : boxed,
        );
        state.status.value = boxed.length
          ? `已框选 ${boxed.length} 个图层`
          : '框选范围内没有可编辑图层';
      } else if (!drag.current.additive) {
        setSelectedKeys(state, []);
        state.status.value = '已取消选择';
      }
      setMarquee(null);
      drag.current = null;
      return;
    }
    if (!drag.current.changed) {
      drag.current = null;
      return;
    }
    const finalPatches = copyPatches(state.patches.peek());
    state.patches.value = drag.current.patches;
    commit(state, finalPatches);
    drag.current = null;
  };

  const select = (event: PointerEvent) => {
    if (event.button !== MouseButton.Left) return;
    syncSceneFromPlayback(state);
    const point = canvasPoint(event);
    const node = editableAtPoint(state.scene.peek(), point);
    if (!node) {
      beginDrag(event, 'marquee');
      return;
    }
    const current = state.selectedKeys
      .peek()
      .filter(key => Boolean(state.scene.peek()?.getNode(key)));
    const additive = event.shiftKey;
    if (additive && current.includes(node.key)) {
      setSelectedKeys(
        state,
        current.filter(key => key !== node.key),
      );
      return;
    }
    setSelectedKeys(state, additive ? [...current, node.key] : current.includes(node.key) ? current : [node.key]);
    state.status.value = '已选择 1 个图层';
    beginDrag(event, 'move');
  };

  const selectedNodes = state.selectedKeys.value
    .map(key => state.scene.peek()?.getNode(key) ?? null)
    .filter((node): node is Node => Boolean(node));
  const canReplace =
    selectedNodes.length > 0 && selectedNodes.every(node => node instanceof Img);
  const canEditText =
    selectedNodes.length > 0 && selectedNodes.every(node => node instanceof Txt);
  const selectedKind = canReplace ? '图片' : canEditText ? '文字' : '组合';
  const selectedWorldBounds = nodesWorldBounds(selectedNodes);
  const selectedOverlayBounds = selectedWorldBounds
    ? boundsFromPoints(
        [
          new Vector2(selectedWorldBounds.left, selectedWorldBounds.top),
          new Vector2(selectedWorldBounds.right, selectedWorldBounds.top),
          new Vector2(selectedWorldBounds.right, selectedWorldBounds.bottom),
          new Vector2(selectedWorldBounds.left, selectedWorldBounds.bottom),
        ].map(point => transformVectorAsPoint(point, matrix)),
      )
    : null;
  const marqueeOverlayBounds = marquee
    ? boundsFromPoints(
        [
          new Vector2(
            marqueeBounds(marquee.start, marquee.current).left,
            marqueeBounds(marquee.start, marquee.current).top,
          ),
          new Vector2(
            marqueeBounds(marquee.start, marquee.current).right,
            marqueeBounds(marquee.start, marquee.current).bottom,
          ),
        ].map(point => transformVectorAsPoint(point, matrix)),
      )
    : null;
  const selectedOpacity = selectedNodes.length
    ? Math.round(
        (state.selectedKeys.value.reduce(
          (sum, key) => sum + normalizeTransform(state.patches.value[key]).opacity,
          0,
        ) /
          selectedNodes.length) *
          100,
      )
    : 100;
  const allHidden =
    selectedNodes.length > 0 &&
    state.selectedKeys.value.every(
      key => normalizeTransform(state.patches.value[key]).opacity === 0,
    );
  const selectedFontSize =
    canEditText && selectedNodes[0] instanceof Txt
      ? Math.round(selectedNodes[0].fontSize())
      : 48;
  const selectedFill =
    canEditText && selectedNodes[0] instanceof Txt
      ? String(selectedNodes[0].fill())
      : '#ffffff';
  const selectedHexFill = /^#[0-9a-f]{6}$/i.test(selectedFill)
    ? selectedFill
    : '#ffffff';

  const replaceAssets = (event: Event) => {
    const input = event.currentTarget as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const next = copyPatches(state.patches.peek());
      for (const key of state.selectedKeys.peek()) {
        next[key] = {
          ...next[key],
          src: String(reader.result),
        };
      }
      commit(state, next);
      input.value = '';
    };
    reader.readAsDataURL(file);
  };

  const applyText = () => {
    const text = textInput.current?.value;
    if (text === undefined || !canEditText) return;
    const next = copyPatches(state.patches.peek());
    for (const key of state.selectedKeys.peek()) {
      next[key] = {...next[key], text};
    }
    commit(state, next);
  };

  const focusTextEditor = () => {
    if (!canEditText) return;
    setPanelOpen(true);
    requestAnimationFrame(() => {
      textInput.current?.focus();
      textInput.current?.select();
    });
  };

  const setOpacity = (opacity: number) => {
    if (!selectedNodes.length) return;
    const next = copyPatches(state.patches.peek());
    for (const key of state.selectedKeys.peek()) {
      const transform = normalizeTransform(next[key]);
      next[key] = withTransform(next[key], {...transform, opacity});
    }
    commit(state, next);
  };

  const setTextStyle = (patch: Pick<LayerPatch, 'fontSize' | 'fill'>) => {
    if (!canEditText) return;
    const next = copyPatches(state.patches.peek());
    for (const key of state.selectedKeys.peek()) {
      next[key] = {...next[key], ...patch};
    }
    commit(state, next);
  };

  const toggleVisibility = () => {
    setOpacity(allHidden ? 1 : 0);
    state.status.value = allHidden
      ? '已恢复所选图层'
      : '已隐藏所选图层，可撤销恢复';
  };

  const resetSelected = () => {
    if (!selectedNodes.length) return;
    const next = copyPatches(state.patches.peek());
    for (const key of state.selectedKeys.peek()) delete next[key];
    commit(state, next);
    state.status.value = '已重置所选图层';
  };

  const alignSelected = (axis: 'x' | 'y') => {
    if (!selectedNodes.length) return;
    const firstBounds = nodeWorldBounds(selectedNodes[0]);
    if (!firstBounds) return;
    const target =
      selectedNodes.length === 1
        ? 0
        : axis === 'x'
          ? firstBounds.center.x
          : firstBounds.center.y;
    const next = copyPatches(state.patches.peek());
    for (const node of selectedNodes) {
      const bounds = nodeWorldBounds(node);
      if (!bounds) continue;
      const delta =
        axis === 'x'
          ? new Vector2(target - bounds.center.x, 0)
          : new Vector2(0, target - bounds.center.y);
      const localDelta = worldDeltaToParent(node, delta);
      const transform = normalizeTransform(next[node.key]);
      next[node.key] = withTransform(next[node.key], {
        ...transform,
        x: transform.x + localDelta.x,
        y: transform.y + localDelta.y,
      });
    }
    commit(state, next);
  };

  const copyAdjustments = () => {
    clipboard.current = state.selectedKeys
      .peek()
      .map(selectedKey =>
        copyPatches({value: state.patches.peek()[selectedKey] ?? {}}).value,
      );
    setClipboardCount(clipboard.current.length);
    state.status.value = `已复制 ${clipboard.current.length} 个图层的调整`;
  };

  const pasteAdjustments = () => {
    if (!clipboard.current.length || !selectedNodes.length) return;
    const next = copyPatches(state.patches.peek());
    state.selectedKeys.peek().forEach((selectedKey, index) => {
      next[selectedKey] = copyPatches({
        value: clipboard.current[index % clipboard.current.length] ?? {},
      }).value;
    });
    commit(state, next);
  };

  const save = async () => {
    if (!saveConfirming) {
      saveConfirmationAt.current = Date.now();
      setSaveConfirming(true);
      state.status.value = '请再次点击“确认另存新版本”';
      saveConfirmationTimer.current = window.setTimeout(() => {
        setSaveConfirming(false);
        state.status.value = '确认已取消，未保存新模板版本';
      }, 10000);
      return;
    }
    if (Date.now() - saveConfirmationAt.current < 600) return;

    window.clearTimeout(saveConfirmationTimer.current);
    setSaveConfirming(false);
    state.status.value = '正在另存新模板版本…';
    const response = await fetch('/__wind_heat_editor/save', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({patches: state.patches.peek()}),
    });
    const result = (await response.json()) as {
      ok: boolean;
      version?: string;
      error?: string;
    };
    state.status.value = result.ok
      ? `已另存新版本（${result.version}），原模板和历史版本未修改`
      : `另存失败：${result.error ?? '未知错误'}`;
  };

  const refreshSegments = async () => {
    try {
      const res = await fetch('/__cw4_segments/list');
      if (!res.ok) {
        setSegAvailable(false);
        return;
      }
      const data = await res.json();
      if (!data?.ok && !data?.scenes) {
        setSegAvailable(false);
        return;
      }
      setSegAvailable(true);
      setSegScenes(data.scenes ?? []);
      setSegTotal(Number(data.total_duration_s) || 0);
      if (!segActiveId && data.scenes?.length) {
        const first = data.scenes.find((s: {enabled: boolean}) => s.enabled) ?? data.scenes[0];
        setSegActiveId(first.id);
        setSegDraft(first.narration_text || '');
      }
    } catch {
      setSegAvailable(false);
    }
  };

  useEffect(() => {
    void refreshSegments();
  }, []);

  const runSegmentAction = async (
    path: string,
    body: Record<string, unknown>,
    okMsg: string,
  ) => {
    setSegLoading(true);
    setSegMessage('处理中…');
    try {
      const res = await fetch(path, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok || data.ok === false) {
        throw new Error(data.error || '请求失败');
      }
      setSegMessage(okMsg);
      await refreshSegments();
      if (path.includes('rebuild') || path.includes('regen')) {
        setSegMessage(
          `${okMsg} 请刷新页面（Cmd+Shift+R）以加载新时间轴与旁白。`,
        );
      }
      return data;
    } catch (e) {
      setSegMessage(
        `失败：${String(e instanceof Error ? e.message : e)}`,
      );
      return null;
    } finally {
      setSegLoading(false);
    }
  };

  const exportCurrentProject = async (format: 'video' | 'pptx') => {
    const label = format === 'video' ? '视频' : '可编辑课件';
    setExporting(format);
    setExportMessage(`正在生成${label}，可以继续查看画面…`);
    try {
      const response = await fetch('/__wind_heat_editor/export', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          format,
          patches: state.patches.peek(),
        }),
      });
      const result = (await response.json()) as {
        ok: boolean;
        status_url?: string;
        error?: string;
      };
      if (!result.ok || !result.status_url) {
        throw new Error(result.error ?? '无法开始生成');
      }

      let finished = false;
      for (let attempt = 0; attempt < 1200; attempt++) {
        await new Promise(resolve => window.setTimeout(resolve, 1500));
        const statusResponse = await fetch(result.status_url);
        const status = (await statusResponse.json()) as {
          status: 'queued' | 'running' | 'completed' | 'failed';
          download_url?: string;
          error?: string;
        };
        if (status.status === 'failed') {
          throw new Error(status.error ?? '生成失败');
        }
        if (status.status !== 'completed' || !status.download_url) continue;

        const link = document.createElement('a');
        link.href = status.download_url;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        link.remove();
        setExportMessage(`${label}已生成，下载已开始。`);
        finished = true;
        break;
      }
      if (!finished) throw new Error('生成时间较长，请稍后重试');
    } catch (error) {
      setExportMessage(
        `${label}生成失败：${String(
          error instanceof Error ? error.message : error,
        )}`,
      );
    } finally {
      setExporting(null);
    }
  };

  return (
    <OverlayWrapper
      onPointerDown={select}
      onPointerMove={onPointerMove}
      onPointerUp={finishDrag}
      onPointerCancel={finishDrag}
      onDblClick={focusTextEditor}
      style={{cursor: selectedNodes.length ? 'move' : 'default'}}
    >
      <style>{`
        body {
          transition: width 180ms ease;
        }
        body.wind-heat-editor-panel-open {
          overflow-x: hidden;
        }
        body > main {
          transition: width 180ms ease;
        }
        body.wind-heat-editor-panel-open > main {
          width: calc(100vw - 320px);
        }
        .wind-heat-editor-panel {
          position: fixed;
          top: 0;
          right: 0;
          bottom: 0;
          width: 320px;
          box-sizing: border-box;
          display: flex;
          flex-direction: column;
          border-left: 1px solid #30414f;
          background: #111c26;
          color: #eaf7f7;
          font: 13px/1.4 system-ui, sans-serif;
          box-shadow: -10px 0 30px rgba(0, 0, 0, .24);
          pointer-events: auto;
          z-index: 9999;
        }
        .wind-heat-editor-panel-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          min-height: 56px;
          box-sizing: border-box;
          padding: 0 14px 0 16px;
          border-bottom: 1px solid #30414f;
        }
        .wind-heat-editor-title {
          display: grid;
          gap: 1px;
          font-weight: 700;
          color: #f6fbfb;
        }
        .wind-heat-editor-title small {
          color: #83a2aa;
          font-size: 11px;
          font-weight: 500;
        }
        .wind-heat-editor-close {
          width: 30px;
          min-height: 30px !important;
          padding: 0 !important;
          font-size: 18px !important;
        }
        .wind-heat-editor-panel-body {
          display: grid;
          align-content: start;
          gap: 0;
          min-height: 0;
          overflow-y: auto;
        }
        .wind-heat-editor-section {
          display: grid;
          gap: 10px;
          padding: 16px;
          border-bottom: 1px solid #293946;
        }
        .wind-heat-editor-section-title {
          color: #91a9b0;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: .08em;
        }
        .wind-heat-editor-selection {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }
        .wind-heat-editor-selection strong {
          color: #fff;
          font-size: 16px;
        }
        .wind-heat-editor-selection span {
          padding: 3px 7px;
          border-radius: 999px;
          background: rgba(126, 242, 237, .12);
          color: #7ef2ed;
          font-size: 11px;
        }
        .wind-heat-editor-help {
          color: #b8d6d8;
          font-size: 12px;
        }
        .wind-heat-editor-actions {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        .wind-heat-editor-field {
          display: grid;
          gap: 7px;
          color: #a9c0c6;
          font-size: 12px;
        }
        .wind-heat-editor-field textarea {
          width: 100%;
          min-height: 76px;
          resize: vertical;
          box-sizing: border-box;
          padding: 9px 10px;
          border: 1px solid #405766;
          border-radius: 6px;
          background: #0b1720;
          color: #f5fbfb;
          font: 13px/1.5 system-ui, sans-serif;
        }
        .wind-heat-editor-field input[type="range"] {
          width: 100%;
          accent-color: #48c6c3;
        }
        .wind-heat-editor-field input[type="color"] {
          width: 100%;
          height: 34px;
          box-sizing: border-box;
          padding: 3px;
          border: 1px solid #405766;
          border-radius: 6px;
          background: #0b1720;
        }
        .wind-heat-editor-shortcuts {
          color: #78949c;
          font-size: 11px;
        }
        .wind-heat-editor-panel button,
        .wind-heat-editor-file-action {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-height: 38px;
          box-sizing: border-box;
          padding: 7px 10px;
          border: 1px solid rgba(126, 242, 237, .45);
          border-radius: 6px;
          background: #152737;
          color: #eefafa;
          font: 600 12px/1.2 system-ui, sans-serif;
          cursor: pointer;
        }
        .wind-heat-editor-panel-tab {
          position: fixed;
          top: 76px;
          right: 0;
          z-index: 9999;
          padding: 10px 9px;
          border: 1px solid #405766;
          border-right: 0;
          border-radius: 8px 0 0 8px;
          background: #167078;
          color: #fff;
          font: 700 12px/1.2 system-ui, sans-serif;
          box-shadow: -6px 4px 18px rgba(0, 0, 0, .25);
          cursor: pointer;
          pointer-events: auto;
          writing-mode: vertical-rl;
        }
        .wind-heat-editor-file-action[data-disabled="true"] {
          opacity: .42;
          pointer-events: none;
          cursor: not-allowed;
        }
        .wind-heat-editor-panel button:disabled {
          opacity: .42;
          cursor: not-allowed;
        }
        .wind-heat-editor-save {
          width: 100%;
          background: #167078 !important;
          border-color: #7ef2ed !important;
        }
        .wind-heat-editor-export {
          width: 100%;
          min-height: 42px !important;
          background: #1c5260 !important;
          border-color: #6cd6d6 !important;
        }
        .wind-heat-editor-export-note {
          color: #9bb9bf;
          font-size: 11px;
          line-height: 1.45;
        }
        .wind-heat-editor-status {
          color: #82d6d8;
          font-size: 12px;
        }
        .wind-heat-editor-narrow-warning {
          display: none;
          padding: 7px 9px;
          border-radius: 7px;
          background: rgba(255, 184, 77, .14);
          color: #ffd08a;
          font-size: 12px;
        }
        .wind-heat-editor-selection-frame,
        .wind-heat-editor-marquee {
          position: absolute;
          box-sizing: border-box;
          pointer-events: none;
        }
        .wind-heat-editor-selection-frame {
          border: 1px solid #7ef2ed;
          box-shadow: 0 0 0 1px rgba(9, 24, 34, .8);
        }
        .wind-heat-editor-marquee {
          border: 1px solid #57d8d3;
          background: rgba(87, 216, 211, .14);
        }
        .wind-heat-editor-handle {
          position: absolute;
          width: 12px;
          height: 12px;
          box-sizing: border-box;
          padding: 0;
          border: 2px solid #0b1821;
          border-radius: 3px;
          background: #7ef2ed;
          cursor: nwse-resize;
          pointer-events: auto;
        }
        .wind-heat-editor-handle[data-corner="ne"],
        .wind-heat-editor-handle[data-corner="sw"] {
          cursor: nesw-resize;
        }
        .wind-heat-editor-rotate-line {
          position: absolute;
          width: 1px;
          height: 26px;
          background: #7ef2ed;
          pointer-events: none;
        }
        .wind-heat-editor-rotate-handle {
          position: absolute;
          width: 18px;
          height: 18px;
          box-sizing: border-box;
          padding: 0;
          border: 2px solid #0b1821;
          border-radius: 50%;
          background: #ffd167;
          color: #0b1821;
          cursor: grab;
          pointer-events: auto;
        }
        @media (max-width: 900px) {
          body.wind-heat-editor-panel-open {
            width: 100vw;
          }
          body.wind-heat-editor-panel-open > main {
            width: 100vw;
          }
          .wind-heat-editor-panel {
            width: min(320px, calc(100vw - 24px));
          }
          .wind-heat-editor-narrow-warning {
            display: block;
          }
        }
      `}</style>
      {typeof document !== 'undefined' &&
        createPortal(panelOpen ? (
          <div
            className="wind-heat-editor-panel"
            data-testid="wind-heat-layer-toolbar"
            data-selected-keys={state.selectedKeys.value.join(',')}
            data-selected-types={selectedNodes
              .map(node => node.constructor.name)
              .join(',')}
            onPointerDown={event => event.stopPropagation()}
          >
            <div className="wind-heat-editor-panel-header">
              <div className="wind-heat-editor-title">
                <span>画面属性</span>
                <small>业务图层编辑</small>
              </div>
              <button
                className="wind-heat-editor-close"
                aria-label="收起属性面板"
                title="收起属性面板"
                onClick={() => setPanelOpen(false)}
              >
                ›
              </button>
            </div>
            <div className="wind-heat-editor-panel-body">
              <section className="wind-heat-editor-section">
                <div className="wind-heat-editor-section-title">当前选中</div>
                <div className="wind-heat-editor-selection">
                  <strong>
                    {selectedNodes.length
                      ? `${selectedNodes.length} 个图层`
                      : '未选择图层'}
                  </strong>
                  <span>{selectedNodes.length ? selectedKind : '请点选画面'}</span>
                </div>
                <div className="wind-heat-editor-narrow-warning">
                  当前窗口较窄，属性栏会覆盖画布；操作时可先收起，或将浏览器拖宽至至少
                  900px。
                </div>
                <div className="wind-heat-editor-help">
                  拖对象移动；拖四角缩放；拖顶部圆点旋转；空白处框选，Shift 追加选择。
                </div>
              </section>
              <section className="wind-heat-editor-section">
                <div className="wind-heat-editor-section-title">内容与属性</div>
                <div className="wind-heat-editor-actions">
                  <label
                    className="wind-heat-editor-file-action"
                    data-disabled={canReplace ? 'false' : 'true'}
                    aria-disabled={!canReplace}
                  >
                    {selectedNodes.length > 1 ? '批量替换图片' : '替换图片'}
                    <input
                      type="file"
                      accept="image/*"
                      multiple={false}
                      disabled={!canReplace}
                      onChange={replaceAssets}
                      style={{display: 'none'}}
                    />
                  </label>
                  <button disabled={!canEditText} onClick={focusTextEditor}>
                    修改文字
                  </button>
                  <button
                    disabled={!selectedNodes.length}
                    onClick={() => alignSelected('x')}
                  >
                    水平居中
                  </button>
                  <button
                    disabled={!selectedNodes.length}
                    onClick={() => alignSelected('y')}
                  >
                    垂直居中
                  </button>
                  <button
                    disabled={!selectedNodes.length}
                    onClick={toggleVisibility}
                  >
                    {allHidden ? '恢复显示' : '隐藏图层'}
                  </button>
                  <button disabled={!selectedNodes.length} onClick={resetSelected}>
                    重置所选
                  </button>
                </div>
                {canEditText && (
                  <div className="wind-heat-editor-field">
                    <span>文字内容</span>
                    <textarea
                      ref={textInput}
                      key={`${state.selectedKeys.value.join(',')}:${String(
                        (selectedNodes[0] as Txt).text(),
                      )}`}
                      defaultValue={String((selectedNodes[0] as Txt).text())}
                      onKeyDown={event => {
                        if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
                          applyText();
                        }
                      }}
                    />
                    <button onClick={applyText}>应用文字</button>
                    <span>字号 {selectedFontSize}px</span>
                    <input
                      type="range"
                      min="18"
                      max="160"
                      value={selectedFontSize}
                      onChange={event =>
                        setTextStyle({
                          fontSize: Number(
                            (event.currentTarget as HTMLInputElement).value,
                          ),
                        })
                      }
                    />
                    <span>文字颜色</span>
                    <input
                      type="color"
                      value={selectedHexFill}
                      onChange={event =>
                        setTextStyle({
                          fill: (event.currentTarget as HTMLInputElement).value,
                        })
                      }
                    />
                  </div>
                )}
                <label className="wind-heat-editor-field">
                  <span>透明度 {selectedOpacity}%</span>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={selectedOpacity}
                    disabled={!selectedNodes.length}
                    onChange={event =>
                      setOpacity(
                        Number((event.currentTarget as HTMLInputElement).value) /
                          100,
                      )
                    }
                  />
                </label>
                <div className="wind-heat-editor-actions">
                  <button disabled={!selectedNodes.length} onClick={copyAdjustments}>
                    复制调整
                  </button>
                  <button
                    disabled={!selectedNodes.length || clipboardCount === 0}
                    onClick={pasteAdjustments}
                  >
                    粘贴调整
                  </button>
                </div>
                <div className="wind-heat-editor-shortcuts">
                  框选：空白处拖动　微移：方向键／Shift+方向键　隐藏：Delete　复制粘贴：⌘C／⌘V
                </div>
              </section>
              <section className="wind-heat-editor-section">
                <div className="wind-heat-editor-section-title">撤销与恢复</div>
                <div className="wind-heat-editor-actions">
                  <button
                    disabled={state.historyIndex.value === 0}
                    onClick={() => undo(state)}
                  >
                    ↶ 撤销
                  </button>
                  <button
                    disabled={
                      state.historyIndex.value >= state.history.value.length - 1
                    }
                    onClick={() => redo(state)}
                  >
                    ↷ 重做
                  </button>
                </div>
              </section>
              {segAvailable && (
                <section className="wind-heat-editor-section">
                  <div className="wind-heat-editor-section-title">
                    片段编排 · 旁白
                  </div>
                  <div className="wind-heat-editor-export-note">
                    全长 {segTotal.toFixed(1)}s · 删段 / 改稿 TTS / 时长回填
                  </div>
                  <div
                    style={{
                      maxHeight: 160,
                      overflow: 'auto',
                      display: 'grid',
                      gap: 4,
                      marginBottom: 8,
                    }}
                  >
                    {segScenes.map(sc => (
                      <button
                        key={sc.id}
                        type="button"
                        disabled={segLoading}
                        onClick={() => {
                          setSegActiveId(sc.id);
                          setSegDraft(sc.narration_text || '');
                        }}
                        style={{
                          textAlign: 'left',
                          padding: '6px 8px',
                          borderRadius: 6,
                          border:
                            sc.id === segActiveId
                              ? '1px solid #3ecf8e'
                              : '1px solid #30414f',
                          background: sc.enabled ? '#182430' : '#1a1515',
                          color: sc.enabled ? '#eaf7f7' : '#887878',
                          cursor: 'pointer',
                          fontSize: 12,
                        }}
                      >
                        <div style={{fontWeight: 700}}>
                          {sc.enabled ? '' : '（已删）'}
                          {sc.id}
                        </div>
                        <div style={{opacity: 0.85}}>
                          {(sc.title || '').slice(0, 18)} ·{' '}
                          {sc.duration_s?.toFixed?.(1) ?? sc.duration_s}s
                          {sc.audio_source === 'tts' ? ' · TTS' : ''}
                        </div>
                      </button>
                    ))}
                  </div>
                  {segActiveId && (
                    <>
                      <label className="wind-heat-editor-field">
                        <span>本段讲解稿</span>
                        <textarea
                          value={segDraft}
                          rows={4}
                          disabled={segLoading}
                          onChange={e =>
                            setSegDraft(
                              (e.currentTarget as HTMLTextAreaElement).value,
                            )
                          }
                          style={{
                            width: '100%',
                            boxSizing: 'border-box',
                            background: '#0d161e',
                            color: '#eaf7f7',
                            border: '1px solid #30414f',
                            borderRadius: 6,
                            padding: 8,
                            resize: 'vertical',
                          }}
                        />
                      </label>
                      <div className="wind-heat-editor-actions">
                        <button
                          disabled={segLoading || !segActiveId}
                          onClick={() =>
                            runSegmentAction(
                              '/__cw4_segments/set-narration',
                              {id: segActiveId, text: segDraft},
                              '讲解稿已保存（需「重生成旁白」生效）',
                            )
                          }
                        >
                          保存文案
                        </button>
                        <button
                          disabled={segLoading || !segActiveId}
                          onClick={() =>
                            runSegmentAction(
                              '/__cw4_segments/regen-tts',
                              {
                                id: segActiveId,
                                text: segDraft,
                                backend: segBackend,
                              },
                              '旁白已重生成，时长已回填',
                            )
                          }
                        >
                          重生成旁白
                        </button>
                      </div>
                      <label className="wind-heat-editor-field">
                        <span>声线后端</span>
                        <select
                          value={segBackend}
                          disabled={segLoading}
                          onChange={e =>
                            setSegBackend(
                              (e.currentTarget as HTMLSelectElement).value as
                                | 'auto'
                                | 'clone'
                                | 'edge',
                            )
                          }
                          style={{
                            width: '100%',
                            background: '#0d161e',
                            color: '#eaf7f7',
                            border: '1px solid #30414f',
                            borderRadius: 6,
                            padding: 6,
                          }}
                        >
                          <option value="auto">
                            自动（优先 Qwen3 克隆参考声）
                          </option>
                          <option value="clone">强制参考声线克隆</option>
                          <option value="edge">edge-tts 通用中文</option>
                        </select>
                      </label>
                      <div className="wind-heat-editor-actions">
                        <button
                          disabled={segLoading || !segActiveId}
                          onClick={() => {
                            const sc = segScenes.find(s => s.id === segActiveId);
                            if (!sc) return;
                            if (sc.enabled) {
                              void runSegmentAction(
                                '/__cw4_segments/hide',
                                {id: segActiveId},
                                `已删除片段 ${segActiveId}`,
                              );
                            } else {
                              void runSegmentAction(
                                '/__cw4_segments/enable',
                                {id: segActiveId},
                                `已恢复片段 ${segActiveId}`,
                              );
                            }
                          }}
                        >
                          {segScenes.find(s => s.id === segActiveId)?.enabled
                            ? '删除此片段'
                            : '恢复此片段'}
                        </button>
                        <button
                          disabled={segLoading}
                          onClick={() =>
                            runSegmentAction(
                              '/__cw4_segments/rebuild',
                              {film: true},
                              '时间轴+旁白+成片已重建',
                            )
                          }
                        >
                          {segLoading ? '重建中…' : '应用并重建成片'}
                        </button>
                      </div>
                    </>
                  )}
                  <div className="wind-heat-editor-export-note">{segMessage}</div>
                </section>
              )}
              <section className="wind-heat-editor-section">
                <div className="wind-heat-editor-section-title">
                  导出当前作品
                </div>
                <button
                  className="wind-heat-editor-export"
                  aria-label="导出视频"
                  disabled={exporting !== null}
                  onClick={() => exportCurrentProject('video')}
                >
                  {exporting === 'video' ? '正在生成视频…' : '导出视频'}
                </button>
                <button
                  className="wind-heat-editor-export"
                  aria-label="导出可编辑课件"
                  disabled={exporting !== null}
                  onClick={() => exportCurrentProject('pptx')}
                >
                  {exporting === 'pptx'
                    ? '正在生成课件…'
                    : '导出可编辑课件'}
                </button>
                <div className="wind-heat-editor-export-note">
                  {exportMessage}
                </div>
              </section>
              <section className="wind-heat-editor-section">
                <div className="wind-heat-editor-section-title">
                  以后继续复用
                </div>
                <button
                  className="wind-heat-editor-save"
                  aria-label="另存为新模板版本"
                  onClick={save}
                >
                  {saveConfirming
                    ? '确认另存新版本'
                    : '另存为新模板版本'}
                </button>
                <div className="wind-heat-editor-export-note">
                  {saveConfirming
                    ? '请在 10 秒内再次点击；不确认就不会保存。'
                    : '点击后还需确认；原模板和历史版本不会被修改。'}
                </div>
                <div className="wind-heat-editor-status">
                  {state.status.value}
                </div>
              </section>
            </div>
          </div>
        ) : (
          <button
            className="wind-heat-editor-panel-tab"
            data-testid="wind-heat-layer-toolbar"
            onClick={() => setPanelOpen(true)}
          >
            画面属性
          </button>
        ),
          document.body,
        )}
      {marqueeOverlayBounds && (
        <div
          className="wind-heat-editor-marquee"
          style={{
            left: `${marqueeOverlayBounds.left}px`,
            top: `${marqueeOverlayBounds.top}px`,
            width: `${marqueeOverlayBounds.width}px`,
            height: `${marqueeOverlayBounds.height}px`,
          }}
        />
      )}
      {selectedOverlayBounds && (
        <>
          <div
            className="wind-heat-editor-selection-frame"
            style={{
              left: `${selectedOverlayBounds.left}px`,
              top: `${selectedOverlayBounds.top}px`,
              width: `${selectedOverlayBounds.width}px`,
              height: `${selectedOverlayBounds.height}px`,
            }}
          />
          {[
            ['nw', selectedOverlayBounds.left, selectedOverlayBounds.top],
            ['ne', selectedOverlayBounds.right, selectedOverlayBounds.top],
            ['se', selectedOverlayBounds.right, selectedOverlayBounds.bottom],
            ['sw', selectedOverlayBounds.left, selectedOverlayBounds.bottom],
          ].map(([corner, x, y]) => (
            <button
              key={String(corner)}
              className="wind-heat-editor-handle"
              data-corner={String(corner)}
              aria-label={`${String(corner)} 缩放手柄`}
              title="拖动缩放所选图层"
              onPointerDown={event => beginDrag(event, 'scale')}
              onPointerMove={onPointerMove}
              onPointerUp={finishDrag}
              onPointerCancel={finishDrag}
              style={{
                left: `${Number(x) - 6}px`,
                top: `${Number(y) - 6}px`,
              }}
            />
          ))}
          <div
            className="wind-heat-editor-rotate-line"
            style={{
              left: `${selectedOverlayBounds.center.x}px`,
              top: `${selectedOverlayBounds.top - 26}px`,
            }}
          />
          <button
            className="wind-heat-editor-rotate-handle"
            aria-label="旋转手柄"
            title="拖动旋转所选图层"
            onPointerDown={event => beginDrag(event, 'rotate')}
            onPointerMove={onPointerMove}
            onPointerUp={finishDrag}
            onPointerCancel={finishDrag}
            style={{
              left: `${selectedOverlayBounds.center.x - 9}px`,
              top: `${selectedOverlayBounds.top - 43}px`,
            }}
          >
            ↻
          </button>
        </>
      )}
    </OverlayWrapper>
  );
}

function drawHook() {
  const state = useEditorState();
  state.afterRender.value;
  state.selectedKeys.value;
  return (ctx: CanvasRenderingContext2D, matrix: DOMMatrix) => {
    const scene = state.scene.peek();
    if (!scene) return;
    for (const key of state.selectedKeys.peek()) {
      scene.drawOverlay(key, matrix, ctx);
    }
  };
}

export default makeEditorPlugin(() => ({
  name: 'wind-heat-editable-layers',
  provider: Provider,
  previewOverlay: {
    component: OverlayComponent,
    drawHook,
  },
}));
