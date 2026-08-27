import type { ProviderContribution } from "../src/types.js";
import { defaultPackageVersions } from "../src/defaults.js";

export const loggingProviders: ProviderContribution[] = [
  {
    id: "logging-pino",
    selected: (profile) => profile.logging === "pino",
    dependencies: defaultPackageVersions(["pino"], "logging-pino"),
    files: () => ({
      "src/logger.ts": "import pino from \"pino\";\n\nexport const logger = pino({\n  level: process.env.LOG_LEVEL ?? \"info\",\n  redact: [\"req.headers.authorization\", \"req.headers.cookie\"],\n});\n",
    }),
  },
  {
    id: "logging-winston",
    selected: (profile) => profile.logging === "winston",
    dependencies: defaultPackageVersions(["winston"], "logging-winston"),
    files: () => ({
      "src/logger.ts": "import { createLogger, format, transports } from \"winston\";\n\nexport const logger = createLogger({\n  level: process.env.LOG_LEVEL ?? \"info\",\n  format: format.json(),\n  transports: [new transports.Console()],\n});\n",
    }),
  },
];
