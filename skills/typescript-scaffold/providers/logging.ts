import type { ProviderContribution } from "../src/types.js";

export const loggingProviders: ProviderContribution[] = [
  {
    id: "logging-pino",
    selected: (profile) => profile.logging === "pino",
    dependencies: { pino: "^10.3.1" },
    files: () => ({
      "src/logger.ts": "import pino from \"pino\";\n\nexport const logger = pino({\n  level: process.env.LOG_LEVEL ?? \"info\",\n  redact: [\"req.headers.authorization\", \"req.headers.cookie\"],\n});\n",
    }),
  },
  {
    id: "logging-winston",
    selected: (profile) => profile.logging === "winston",
    dependencies: { winston: "^3.19.0" },
    files: () => ({
      "src/logger.ts": "import { createLogger, format, transports } from \"winston\";\n\nexport const logger = createLogger({\n  level: process.env.LOG_LEVEL ?? \"info\",\n  format: format.json(),\n  transports: [new transports.Console()],\n});\n",
    }),
  },
];
