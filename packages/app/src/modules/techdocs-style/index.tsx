import { useEffect } from 'react';
import { createFrontendModule } from '@backstage/frontend-plugin-api';
import { TechDocsAddonLocations, useShadowRoot } from '@backstage/plugin-techdocs-react';
import { AddonBlueprint } from '@backstage/plugin-techdocs-react/alpha';
import { docsCss } from './css';

/**
 * TechDocs removes every <link> and <style> from the documentation it shows (only MkDocs' own stylesheet survives), so a
 * repository cannot bring its own CSS. The shared look of all our sites (hero, fact tiles, cards, tables, diagrams) is therefore
 * injected here, once, into the shadow DOM of every docs page. It uses only the theme's CSS variables, so it follows light/dark.
 */
const PlatformDocsStyle = () => {
  const root = useShadowRoot();
  useEffect(() => {
    if (!root) return undefined;
    const style = document.createElement('style');
    style.setAttribute('data-platform-demo', 'docs-style');
    style.textContent = docsCss;
    root.appendChild(style);
    return () => style.remove();
  }, [root]);
  return null;
};

const docsStyleAddon = AddonBlueprint.make({
  name: 'platform-demo-style',
  params: {
    name: 'PlatformDemoStyle',
    location: TechDocsAddonLocations.Content,
    component: PlatformDocsStyle,
  },
});

export const techDocsStyleModule = createFrontendModule({
  pluginId: 'techdocs',
  extensions: [docsStyleAddon],
});
