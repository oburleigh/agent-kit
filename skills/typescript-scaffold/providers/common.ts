import apacheLicense from "spdx-license-list/licenses/Apache-2.0.json" with { type: "json" };
import mitLicense from "spdx-license-list/licenses/MIT.json" with { type: "json" };
import type { ProviderContribution } from "../src/types.js";

function readme(
  name: string,
  description: string,
  packageRun: string,
  stack: string[],
  scripts: string[],
  hasLicense: boolean,
  presetGuide: string,
  externalRequirements: string,
): string {
  const commands = scripts.map((script) => `${packageRun} ${script}`).join("\n");
  const license = hasLicense ? "\n\n## License\n\nSee [LICENSE](LICENSE)." : "";
  return `# ${name}\n\n${description}\n\n## Requirements\n\nUse the Node.js version declared in \`.node-version\` and the exact package-manager version declared in \`package.json\`.${externalRequirements}\n\n## Setup\n\n\`\`\`sh\n${packageRun === "npm run" ? "npm install" : `${packageRun.split(" ")[0]} install`}\n\`\`\`\n\n## Development\n\n\`\`\`sh\n${commands}\n\`\`\`${presetGuide}\n\n## Stack\n\n${stack.map((item) => `- ${item}`).join("\n")}\n\n## Contributing\n\nSee [CONTRIBUTING.md](CONTRIBUTING.md).${license}\n`;
}

function contributing(packageRun: string, scripts: string[], ciCommands: string[], hasLicense: boolean): string {
  const commands = [
    ...scripts.filter((script) => script !== "dev").map((script) => `${packageRun} ${script}`),
    ...ciCommands,
  ];
  const license = hasLicense ? " Contributions are provided under the repository licence." : "";
  return `# Contributing\n\n## Setup\n\nInstall the Node.js and package-manager versions declared by the repository, then install dependencies.\n\n## Before opening a pull request\n\nRun the repository checks:\n\n\`\`\`sh\n${commands.join("\n")}\n\`\`\`\n\nKeep changes focused. Add or update tests for changed behavior. Prefer maintained packages for solved, non-domain work. Write custom infrastructure only when an existing package cannot meet the repository's contract.\n\nUse Conventional Commits for commit messages.${license}\n`;
}

function documentedScripts(scripts: Readonly<Record<string, string>>): string[] {
  return ["dev", "test", "lint", "typecheck", "build", "duplication", "secrets"]
    .filter((script) => scripts[script] !== undefined);
}

function presetGuide(
  preset: string,
  framework: string,
  packageRun: string,
): string {
  if (framework === "vite-react") {
    return `\n\n## Application\n\nThis repository uses Vite and React. Start the development server with \`${packageRun} dev\`.`;
  }
  if (preset === "cli") {
    return `\n\n## Usage\n\nRun the CLI in development with \`${packageRun} dev -- Ada\`.`;
  }
  if (preset === "service") {
    return "\n\n## API\n\nThe starter service exposes `GET /health`.";
  }
  if (preset === "workspace") {
    return "\n\n## Packages\n\nThis scaffold creates an empty monorepo root so it does not prescribe one package stack for the whole workspace. Add each TypeScript package under `packages/` with its own package manifest and checks.";
  }
  return "\n\n## Usage\n\nImport public functions from the package entry point.";
}

function licenseText(
  license: "apache-2.0" | "mit" | "none",
  author: string,
): string | undefined {
  if (license === "none") return undefined;
  const entry = license === "apache-2.0" ? apacheLicense : mitLicense;
  const text = license === "mit"
    ? entry.licenseText
      .replace("<year>", String(new Date().getUTCFullYear()))
      .replace("<copyright holders>", author)
    : entry.licenseText;
  return `${text}\n`;
}

export const commonProvider: ProviderContribution = {
  id: "common",
  selected: () => true,
  ignore: [
    "node_modules/",
    ".pnp.*",
    ".yarn/cache/",
    ".yarn/install-state.gz",
    "dist/",
    "coverage/",
    ".env",
    ".env.*",
    "!.env.example",
    ".DS_Store",
    "*.log",
    "*.local",
    "dist-ssr/",
  ],
  files(context) {
    const scripts = documentedScripts(context.scripts);
    const hasLicense = context.profile.license !== "none";
    const stack = [
      `Preset: ${context.profile.preset}`,
      `Package manager: ${context.profile.package_manager} ${context.profile.package_manager_version}`,
      `Module system: ${context.profile.module}`,
      `Build: ${context.profile.build}`,
      `Quality: ${context.profile.quality}`,
      `Tests: ${context.profile.tests}`,
      `Runtime validation: ${context.profile.runtime_validation}`,
      `HTTP: ${context.profile.http}`,
      `Logging: ${context.profile.logging}`,
      `Hooks: ${context.profile.hooks}`,
      `CI: ${context.profile.ci}`,
      `Publishing: ${context.profile.publishing}`,
      `Workspace: ${context.profile.workspace}`,
      `Framework: ${context.profile.framework}`,
      `Secret scanning: ${context.profile.secret_scan === "gitleaks" ? "Gitleaks" : "none"}`,
      `Duplication: ${context.profile.duplication}`,
    ].filter((item) => !item.endsWith(": none"));
    const files: Record<string, string> = {
      ".node-version": "24\n",
      "AGENTS.md": "# Repository instructions\n\n- Read the existing code, configuration, and tests before changing behavior.\n- Prefer a maintained package for solved, non-domain work. Check its licence, security record, types, runtime support, and scope before adding it.\n- Write custom infrastructure only when no suitable package meets the repository contract. Keep that code narrow and test it.\n- Keep environment-specific values in typed configuration rather than source code.\n- Add or update tests for changed behavior. Run the repository checks before reporting completion.\n- Keep comments short. Explain constraints or intent that the code cannot express.\n",
      "CLAUDE.md": "# Claude Code\n\nRead and follow [AGENTS.md](AGENTS.md) before making changes.\n",
      "README.md": readme(
        context.project.name,
        context.project.description,
        context.packageRun,
        stack,
        scripts,
        hasLicense,
        presetGuide(context.profile.preset, context.profile.framework, context.packageRun),
        context.profile.secret_scan === "gitleaks"
          ? " Install Gitleaks before running the `secrets` check."
          : "",
      ),
      "CONTRIBUTING.md": contributing(
        context.packageRun,
        scripts,
        context.profile.ci_commands,
        hasLicense,
      ),
    };
    const selectedLicense = licenseText(context.profile.license, context.project.author);
    if (selectedLicense) files.LICENSE = selectedLicense;
    return files;
  },
};
