import { createApp } from '@backstage/frontend-defaults';
import catalogPlugin from '@backstage/plugin-catalog/alpha';
import { authModule } from './modules/auth';
import { navModule } from './modules/nav';
import { techDocsStyleModule } from './modules/techdocs-style';

export default createApp({
  features: [catalogPlugin, authModule, navModule, techDocsStyleModule],
});
