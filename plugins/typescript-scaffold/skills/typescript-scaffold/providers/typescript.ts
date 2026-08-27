export function strictTypeScriptOptions(): Record<string, boolean> {
  return {
    strict: true,
    noUncheckedIndexedAccess: true,
    exactOptionalPropertyTypes: true,
    noImplicitOverride: true,
    noFallthroughCasesInSwitch: true,
    noUncheckedSideEffectImports: true,
    forceConsistentCasingInFileNames: true,
    isolatedModules: true,
    resolveJsonModule: true,
  };
}
