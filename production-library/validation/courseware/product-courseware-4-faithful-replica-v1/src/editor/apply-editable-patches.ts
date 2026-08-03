import {Img, Node, Txt, View2D} from '@revideo/2d';
import {useScene, waitFor} from '@revideo/core';

export type EditableLayerTransform = {
  x?: number;
  y?: number;
  scale?: number;
  rotation?: number;
  /**
   * Multiplies the animated node opacity so fades remain intact.
   * `1` preserves the authored opacity and `0` hides the node.
   */
  opacity?: number;
};

export type EditableLayerPatch = {
  transform?: EditableLayerTransform;
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

export type EditableLayerPatches = Record<string, EditableLayerPatch>;

type AppliedTransform = {
  x: number;
  y: number;
  scale: number;
  rotation: number;
  opacity: number;
};

type AppliedPatch = EditableLayerPatch & {transform: AppliedTransform};

function normalizePatch(patch: EditableLayerPatch): AppliedPatch {
  return {
    ...patch,
    transform: {
      x: patch.transform?.x ?? patch.x ?? 0,
      y: patch.transform?.y ?? patch.y ?? 0,
      scale: patch.transform?.scale ?? patch.scale ?? 1,
      rotation: patch.transform?.rotation ?? patch.rotation ?? 0,
      opacity: patch.transform?.opacity ?? patch.opacity ?? 1,
    },
  };
}

function applyPatch(
  node: Node,
  patch: EditableLayerPatch,
  previous: AppliedPatch,
) {
  const normalized = normalizePatch(patch);
  const position = node.position();
  const scale = node.scale();
  const baseX = position.x - previous.transform.x;
  const baseY = position.y - previous.transform.y;
  const baseScaleX = scale.x / previous.transform.scale;
  const baseScaleY = scale.y / previous.transform.scale;
  const baseRotation = node.rotation() - previous.transform.rotation;
  const baseOpacity =
    previous.transform.opacity === 0
      ? node.opacity()
      : node.opacity() / previous.transform.opacity;

  node.position([
    baseX + normalized.transform.x,
    baseY + normalized.transform.y,
  ]);
  node.scale([
    baseScaleX * normalized.transform.scale,
    baseScaleY * normalized.transform.scale,
  ]);
  node.rotation(baseRotation + normalized.transform.rotation);
  node.opacity(baseOpacity * normalized.transform.opacity);
  if (node instanceof Img && normalized.src) {
    node.src(normalized.src);
  }
  if (node instanceof Txt) {
    if (normalized.text !== undefined) node.text(normalized.text);
    if (normalized.fontSize !== undefined) node.fontSize(normalized.fontSize);
    if (normalized.fill !== undefined) node.fill(normalized.fill);
  }
}

/**
 * Applies saved editor deltas after each animation step so the same candidate
 * state is visible in both the interactive editor and headless rendering.
 */
export function* applyEditablePatches(view: View2D, duration: number) {
  const patches = useScene().variables.get<EditableLayerPatches>(
    'editablePatches',
    {},
  )();
  const previous = new Map<string, AppliedPatch>();
  let elapsed = 0;

  while (elapsed < duration) {
    for (const [key, patch] of Object.entries(patches)) {
      const node = view.findKey(key);
      if (!node) continue;
      const prior = previous.get(key) ?? normalizePatch({});
      applyPatch(node, patch, prior);
      previous.set(key, normalizePatch(patch));
    }

    const step = Math.min(1 / 30, duration - elapsed);
    yield* waitFor(step);
    elapsed += step;
  }
}
