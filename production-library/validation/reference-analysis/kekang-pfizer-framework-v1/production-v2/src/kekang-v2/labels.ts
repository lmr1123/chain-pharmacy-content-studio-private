/** Split subtitle into short node labels without inventing medical claims. */
export function nodeLabels(subtitle: string, max = 4): string[] {
  const cleaned = subtitle
    .replace(/·/g, '、')
    .replace(/\//g, '、')
    .replace(/，/g, '、')
    .replace(/：/g, '、')
    .trim();
  const parts = cleaned
    .split('、')
    .map((s) => s.trim())
    .filter(Boolean);
  if (parts.length === 0) return [subtitle.slice(0, 10)];
  return parts.slice(0, max).map((p) => (p.length > 12 ? `${p.slice(0, 11)}…` : p));
}

export function isBlocked(shot: {production_ready?: boolean; content_approval?: string}): boolean {
  if (shot.production_ready) return false;
  const a = shot.content_approval || '';
  return (
    a.includes('blocked') ||
    a.includes('review-required') ||
    a.includes('source-aligned')
  );
}

export function gateLabel(shot: {
  production_ready?: boolean;
  content_approval?: string;
}): string {
  if (shot.production_ready) return 'READY';
  const a = shot.content_approval || 'blocked';
  if (a.includes('high-risk')) return 'HIGH-RISK';
  if (a.includes('asset')) return 'ASSET';
  if (a.includes('evidence')) return 'EVIDENCE';
  if (a.includes('medical')) return 'MEDICAL';
  if (a.includes('content')) return 'CONTENT';
  return 'REVIEW';
}
