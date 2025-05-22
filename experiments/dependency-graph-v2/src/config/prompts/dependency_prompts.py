"""Prompts for dependency analysis."""

DEPENDENCY_ANALYSIS_PROMPT = """Analyze this dependency file and extract all external dependencies. For each dependency, provide:
1. packageName: The name of the package (e.g., 'com.fasterxml.jackson.core:jackson-databind' for Gradle, '@types/node' for NPM)
2. packageManager: The package manager used (e.g., GO, NPM, PIP, GRADLE)
3. requirements: The version requirement (e.g., '2.19.0', '^1.0.0', '>=1.2.3')
4. relationship: Whether it's a direct or indirect dependency

File-specific parsing rules:

For Gradle files (build.gradle, versions.gradle):
- Each 'dependency' line represents a direct dependency
- For 'dependencySet' blocks, each 'entry' is a separate dependency with the same group and version
- The format is typically 'group:artifact:version' or 'group:artifact'
- Look for both 'implementation', 'api', 'compile', and 'test' dependencies
- For versions.gradle, extract version declarations and their usage in dependencies

For package.json files:
- 'dependencies' section contains direct runtime dependencies
- 'devDependencies' section contains direct development dependencies
- 'peerDependencies' section contains direct peer dependencies
- 'optionalDependencies' section contains direct optional dependencies
- Version formats can be:
  * Exact: "1.2.3"
  * Range: "^1.2.3", "~1.2.3", ">=1.2.3"
  * URL: "github:user/repo#branch"
  * Tag: "latest", "next"

For requirements.txt files:
- Each line represents a direct dependency
- Version specifiers can be: ==, >=, <=, >, <, ~=
- Comments and blank lines should be ignored

For go.mod files:
- Each 'require' line represents a direct dependency
- Version format is typically 'v1.2.3' or commit hash
- 'replace' and 'exclude' directives should be noted

For Cargo.toml files:
- [dependencies] section contains direct runtime dependencies
- [dev-dependencies] section contains direct development dependencies
- Version formats can be: "1.2.3", "^1.2.3", "=1.2.3"

File URL: {file_url}
File Content:
{file_content}

Return the results as a JSON array of objects with these fields. If you can't determine a field, use null.
Example output format:
[
  {{
    "packageName": "com.fasterxml.jackson.core:jackson-databind",
    "packageManager": "GRADLE",
    "requirements": "2.19.0",
    "relationship": "direct"
  }},
  {{
    "packageName": "@types/node",
    "packageManager": "NPM",
    "requirements": "^18.0.0",
    "relationship": "direct"
  }}
]""" 