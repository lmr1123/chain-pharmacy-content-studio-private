/**
 * Content-driven helpers for product training video projects.
 * Prefer fields from the segment JSON (`product_name`, `screen`, `assets`)
 * so theme replication can replace text and media without editing TSX.
 */

export type ProductScreenContent = {
  product_name?: string;
  labels?: string[];
  efficacy_title?: string;
  efficacy_sections?: string[];
  feature_sections?: string[];
  combo_sections?: string[];
  audience_title?: string;
  summary?: {
    headers?: string[];
    cells?: string[];
    brand?: string;
    slogan?: string;
  };
  pack_badge?: string;
  meter_label?: string;
};

export function productName(data: {
  product_name?: string;
  title?: string;
  screen?: ProductScreenContent;
}): string {
  return (
    data.product_name ||
    data.screen?.product_name ||
    data.title ||
    '辅酶Q10'
  );
}

export function screenOf(data: {screen?: ProductScreenContent}): ProductScreenContent {
  return data.screen || {};
}
