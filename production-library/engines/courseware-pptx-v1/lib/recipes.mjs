/**
 * Load page-type recipes + cw4 scene.type map.
 * Resolution: scene.type → map entry → recipe → impl builder name.
 */
import fs from 'node:fs/promises';
import path from 'node:path';

/**
 * @param {string} recipesDir absolute path to page-types/.../recipes
 * @returns {Promise<{recipes: Record<string, object>, sceneMap: object, byScene: Record<string, object>}>}
 */
export async function loadRecipes(recipesDir) {
  const recipes = {};
  const byScene = {};
  let sceneMap = {};

  let entries = [];
  try {
    entries = await fs.readdir(recipesDir);
  } catch (e) {
    throw new Error(`recipes dir not found: ${recipesDir}\n${e.message}`);
  }

  for (const f of entries) {
    if (!f.endsWith('.json')) continue;
    const full = path.join(recipesDir, f);
    const data = JSON.parse(await fs.readFile(full, 'utf8'));

    if (f === 'scene-type-map.json' || data.scene_type_map) {
      sceneMap = data.scene_type_map || {};
      continue;
    }

    if (!data.page_type) continue;
    recipes[data.page_type] = {...data, _file: f};

    const sceneTypes = data.scene_types || [];
    for (const st of sceneTypes) {
      byScene[st] = {
        page_type: data.page_type,
        recipe: data,
        impl: (data.impl_by_scene && data.impl_by_scene[st]) || data.default_impl || st,
      };
    }
  }

  // scene-type-map wins for impl/page_type when present
  for (const [st, entry] of Object.entries(sceneMap)) {
    const pageType = entry.page_type;
    const recipe = recipes[pageType] || null;
    byScene[st] = {
      page_type: pageType,
      recipe,
      impl: entry.impl || (recipe && recipe.default_impl) || st,
      variant: entry.variant || null,
      from_map: true,
    };
  }

  return {recipes, sceneMap, byScene, recipesDir};
}

/**
 * Resolve how to render a content-model scene.
 * @param {object} loaded from loadRecipes
 * @param {{type?: string, page_type?: string, id?: string}} scene
 */
export function resolveSceneRecipe(loaded, scene) {
  const type = scene.type || scene.scene_type || '';
  const pageTypeHint = scene.page_type || '';

  if (type && loaded.byScene[type]) {
    return {
      ok: true,
      scene_type: type,
      ...loaded.byScene[type],
    };
  }

  if (pageTypeHint && loaded.recipes[pageTypeHint]) {
    const recipe = loaded.recipes[pageTypeHint];
    return {
      ok: true,
      scene_type: type || pageTypeHint,
      page_type: pageTypeHint,
      recipe,
      impl: recipe.default_impl || pageTypeHint,
      variant: null,
    };
  }

  // direct type == page_type id
  if (type && loaded.recipes[type]) {
    const recipe = loaded.recipes[type];
    return {
      ok: true,
      scene_type: type,
      page_type: type,
      recipe,
      impl: recipe.default_impl || type,
      variant: null,
    };
  }

  return {
    ok: false,
    scene_type: type,
    page_type: pageTypeHint || null,
    recipe: null,
    impl: type || null,
    error: `no recipe for scene type=${type || '?'} page_type=${pageTypeHint || '?'} id=${scene.id || '?'}`,
  };
}
