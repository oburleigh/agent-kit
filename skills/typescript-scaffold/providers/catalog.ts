import type { ProviderContribution } from "../src/types.js";
import { buildProviders } from "./build.js";
import { checkProviders } from "./checks.js";
import { ciProviders } from "./ci.js";
import { commonProvider } from "./common.js";
import { hookProviders } from "./hooks.js";
import { httpProviders } from "./http.js";
import { loggingProviders } from "./logging.js";
import { moduleProviders } from "./modules.js";
import { presetProviders } from "./presets.js";
import { publishingProviders } from "./publishing.js";
import { qualityProviders } from "./quality.js";
import { testProviders } from "./tests.js";
import { validationProviders } from "./validation.js";
import { workspaceProviders } from "./workspace.js";

export const providerCatalog: readonly ProviderContribution[] = [
  commonProvider,
  ...presetProviders,
  ...moduleProviders,
  ...buildProviders,
  ...qualityProviders,
  ...testProviders,
  ...validationProviders,
  ...httpProviders,
  ...loggingProviders,
  ...hookProviders,
  ...ciProviders,
  ...publishingProviders,
  ...workspaceProviders,
  ...checkProviders,
];
