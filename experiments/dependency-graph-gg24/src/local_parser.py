"""
Local dependency parser for repositories that timeout on GitHub API.

This script clones repositories and parses dependency files locally:
- package.json / package-lock.json / yarn.lock / pnpm-lock.yaml (JavaScript/TypeScript)
- Cargo.toml / Cargo.lock (Rust)
- requirements.txt / pyproject.toml / poetry.lock (Python)
- go.mod / go.sum (Go)
- And other common dependency files
"""

import os
import json
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import toml
import yaml
import re

def clone_repo(owner: str, repo: str, temp_dir: Path) -> Optional[Path]:
    """Clone a repository to a temporary directory."""
    repo_url = f"https://github.com/{owner}/{repo}.git"
    repo_path = temp_dir / repo
    
    try:
        print(f"  Cloning {owner}/{repo}...")
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(repo_path)],
            check=True,
            capture_output=True,
            timeout=300  # 5 minute timeout for cloning
        )
        return repo_path
    except subprocess.TimeoutExpired:
        print(f"  ✗ Clone timeout for {owner}/{repo}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Clone failed for {owner}/{repo}: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Error cloning {owner}/{repo}: {e}")
        return None

def find_dependency_files(repo_path: Path) -> List[Path]:
    """Find all dependency manifest files in the repository."""
    patterns = [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "Cargo.toml",
        "Cargo.lock",
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "Pipfile",
        "Pipfile.lock",
        "go.mod",
        "go.sum",
        "composer.json",
        "composer.lock",
        "Gemfile",
        "Gemfile.lock",
    ]
    
    manifest_files = []
    
    # Walk through the repository
    for root, dirs, files in os.walk(repo_path):
        # Skip common directories that shouldn't contain manifests
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'vendor', 'target', '__pycache__', '.venv', 'venv']]
        
        for file in files:
            if file in patterns:
                manifest_files.append(Path(root) / file)
    
    return manifest_files

def parse_package_json(file_path: Path) -> List[Dict]:
    """Parse package.json for JavaScript/TypeScript dependencies."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        dependencies = []
        
        # Regular dependencies
        for name, version in data.get('dependencies', {}).items():
            dependencies.append({
                'packageName': name,
                'requirements': version,
                'relationship': 'direct',
                'packageManager': 'NPM',
            })
        
        # Dev dependencies
        for name, version in data.get('devDependencies', {}).items():
            dependencies.append({
                'packageName': name,
                'requirements': version,
                'relationship': 'direct',
                'packageManager': 'NPM',
            })
        
        return dependencies
    except Exception as e:
        print(f"    Error parsing {file_path}: {e}")
        return []

def parse_cargo_toml(file_path: Path) -> List[Dict]:
    """Parse Cargo.toml for Rust dependencies."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
        
        dependencies = []
        
        # Regular dependencies
        for name, spec in data.get('dependencies', {}).items():
            if isinstance(spec, str):
                version = spec
            elif isinstance(spec, dict):
                version = spec.get('version', '*')
            else:
                version = '*'
            
            dependencies.append({
                'packageName': name,
                'requirements': version,
                'relationship': 'direct',
                'packageManager': 'CARGO',
            })
        
        # Dev dependencies
        for name, spec in data.get('dev-dependencies', {}).items():
            if isinstance(spec, str):
                version = spec
            elif isinstance(spec, dict):
                version = spec.get('version', '*')
            else:
                version = '*'
            
            dependencies.append({
                'packageName': name,
                'requirements': version,
                'relationship': 'direct',
                'packageManager': 'CARGO',
            })
        
        return dependencies
    except Exception as e:
        print(f"    Error parsing {file_path}: {e}")
        return []

def parse_cargo_lock(file_path: Path) -> List[Dict]:
    """Parse Cargo.lock for Rust dependencies."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
        
        dependencies = []
        
        for package in data.get('package', []):
            name = package.get('name')
            version = package.get('version', '*')
            
            if name:
                dependencies.append({
                    'packageName': name,
                    'requirements': version,
                    'relationship': 'unknown',  # Lock files don't distinguish direct vs transitive
                    'packageManager': 'CARGO',
                })
        
        return dependencies
    except Exception as e:
        print(f"    Error parsing {file_path}: {e}")
        return []

def parse_requirements_txt(file_path: Path) -> List[Dict]:
    """Parse requirements.txt for Python dependencies."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        dependencies = []
        
        for line in lines:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse package name and version
            match = re.match(r'^([a-zA-Z0-9_\-\.]+)([>=<~!]+.*)?$', line)
            if match:
                name = match.group(1)
                version = match.group(2) or '*'
                
                dependencies.append({
                    'packageName': name,
                    'requirements': version,
                    'relationship': 'direct',
                    'packageManager': 'PIP',
                })
        
        return dependencies
    except Exception as e:
        print(f"    Error parsing {file_path}: {e}")
        return []

def parse_pyproject_toml(file_path: Path) -> List[Dict]:
    """Parse pyproject.toml for Python dependencies."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
        
        dependencies = []
        
        # Poetry dependencies
        poetry_deps = data.get('tool', {}).get('poetry', {}).get('dependencies', {})
        for name, spec in poetry_deps.items():
            if name == 'python':  # Skip python version
                continue
            
            if isinstance(spec, str):
                version = spec
            elif isinstance(spec, dict):
                version = spec.get('version', '*')
            else:
                version = '*'
            
            dependencies.append({
                'packageName': name,
                'requirements': version,
                'relationship': 'direct',
                'packageManager': 'PIP',
            })
        
        # PEP 621 dependencies
        project_deps = data.get('project', {}).get('dependencies', [])
        for dep_spec in project_deps:
            # Parse "package>=1.0.0" format
            match = re.match(r'^([a-zA-Z0-9_\-\.]+)([>=<~!]+.*)?$', dep_spec)
            if match:
                name = match.group(1)
                version = match.group(2) or '*'
                
                dependencies.append({
                    'packageName': name,
                    'requirements': version,
                    'relationship': 'direct',
                    'packageManager': 'PIP',
                })
        
        return dependencies
    except Exception as e:
        print(f"    Error parsing {file_path}: {e}")
        return []

def parse_go_mod(file_path: Path) -> List[Dict]:
    """Parse go.mod for Go dependencies."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        dependencies = []
        
        # Parse require blocks
        require_pattern = r'require\s+\((.*?)\)'
        require_blocks = re.findall(require_pattern, content, re.DOTALL)
        
        for block in require_blocks:
            for line in block.split('\n'):
                line = line.strip()
                if not line or line.startswith('//'):
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1]
                    
                    dependencies.append({
                        'packageName': name,
                        'requirements': version,
                        'relationship': 'direct',
                        'packageManager': 'GO',
                    })
        
        # Parse single-line requires
        single_require_pattern = r'require\s+([^\s]+)\s+([^\s]+)'
        for match in re.finditer(single_require_pattern, content):
            if match.group(0) not in str(require_blocks):
                dependencies.append({
                    'packageName': match.group(1),
                    'requirements': match.group(2),
                    'relationship': 'direct',
                    'packageManager': 'GO',
                })
        
        return dependencies
    except Exception as e:
        print(f"    Error parsing {file_path}: {e}")
        return []

def parse_manifest_file(file_path: Path) -> List[Dict]:
    """Parse a dependency manifest file based on its type."""
    file_name = file_path.name
    
    parsers = {
        'package.json': parse_package_json,
        'Cargo.toml': parse_cargo_toml,
        'Cargo.lock': parse_cargo_lock,
        'requirements.txt': parse_requirements_txt,
        'pyproject.toml': parse_pyproject_toml,
        'go.mod': parse_go_mod,
    }
    
    parser = parsers.get(file_name)
    if parser:
        return parser(file_path)
    
    # For other files, return empty list (not supported yet)
    return []

def fetch_dependencies_locally(owner: str, repo: str) -> List[Dict]:
    """
    Fetch dependencies by cloning the repository and parsing locally.
    
    Returns:
        List of dependency records in the same format as GitHub API results
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Clone the repository
        repo_path = clone_repo(owner, repo, temp_path)
        if not repo_path:
            return []
        
        try:
            # Find all dependency files
            manifest_files = find_dependency_files(repo_path)
            print(f"  Found {len(manifest_files)} manifest files")
            
            # Parse each manifest
            all_records = []
            for manifest_file in manifest_files:
                relative_path = manifest_file.relative_to(repo_path)
                print(f"    Parsing {relative_path}...")
                
                dependencies = parse_manifest_file(manifest_file)
                
                # Convert to our record format
                for dep in dependencies:
                    record = {
                        'repo_name': f"{owner}/{repo}",
                        'owner': owner,
                        'repo': repo,
                        'manifest_filename': str(relative_path),
                        'package_name': dep.get('packageName', ''),
                        'package_manager': dep.get('packageManager', ''),
                        'package_url': '',  # Not available from local parsing
                        'requirements': dep.get('requirements', ''),
                        'relationship': dep.get('relationship', 'unknown'),
                        'has_dependencies': False,  # Not available from local parsing
                    }
                    all_records.append(record)
                
                if dependencies:
                    print(f"      ✓ Found {len(dependencies)} dependencies")
            
            return all_records
            
        finally:
            # Cleanup is automatic with TemporaryDirectory
            pass

if __name__ == "__main__":
    # Test with a small repo
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python local_parser.py <owner> <repo>")
        sys.exit(1)
    
    owner = sys.argv[1]
    repo = sys.argv[2]
    
    print(f"Fetching dependencies for {owner}/{repo} locally...")
    records = fetch_dependencies_locally(owner, repo)
    
    print(f"\nTotal dependencies found: {len(records)}")
    if records:
        print("\nSample records:")
        for record in records[:5]:
            print(f"  {record['manifest_filename']}: {record['package_name']} ({record['package_manager']})")

