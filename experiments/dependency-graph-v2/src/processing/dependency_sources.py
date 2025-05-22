"""
Dependency source implementations for fetching dependencies from different sources.
"""
import base64
import json
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any

import google.generativeai as genai
import requests
from dotenv import load_dotenv

from ..config.prompts.dependency_prompts import DEPENDENCY_ANALYSIS_PROMPT
from ..config.settings import GITHUB_HEADERS


class DependencySource(ABC):
    """Base class for dependency sources."""
    
    @abstractmethod
    def fetch_dependencies(self, repo_url: str) -> List[Dict]:
        """Fetch dependencies for a repository."""
        pass
    
    @abstractmethod
    def get_source_type(self) -> str:
        """Get the type of dependency source."""
        pass


class GitHubApiSource(DependencySource):
    """Fetch dependencies using GitHub's GraphQL API."""
    
    def __init__(self):
        load_dotenv()
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        # GraphQL endpoint
        self.graphql_url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json",
        }
    
    def _extract_repo_info(self, repo_url: str) -> tuple[str, str]:
        """Extract owner and repo name from GitHub URL."""
        parts = repo_url.strip("/").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        return parts[-2], parts[-1]
    
    def fetch_dependencies(self, repo_url: str) -> List[Dict]:
        """Fetch repository dependencies using GitHub's GraphQL API."""
        owner, repo = self._extract_repo_info(repo_url)
        
        query = """
        query($owner: String!, $repo: String!) {
            repository(owner: $owner, name: $repo) {
                dependencyGraphManifests(first: 100) {
                    nodes {
                        filename
                        dependencies {
                            nodes {
                                hasDependencies
                                packageName
                                packageManager
                                packageUrl
                                requirements
                                relationship
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "owner": owner,
            "repo": repo
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                headers=self.headers,
                json={"query": query, "variables": variables}
            )
            response.raise_for_status()
            data = response.json()
            
            # Add debug logging
            print(f"\nFetching dependencies for {owner}/{repo}")
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return []
            
            # Check if we got a valid response
            if not data.get("data", {}).get("repository"):
                print(f"No repository data found for {owner}/{repo}")
                return []
            
            manifests = data["data"]["repository"]["dependencyGraphManifests"]["nodes"]
            if not manifests:
                print(f"No dependency manifests found for {owner}/{repo}")
                return []
            
            # Extract all dependencies from all manifests
            all_dependencies = []
            for manifest in manifests:
                deps = manifest.get("dependencies", {}).get("nodes", [])
                print(f"Manifest {manifest.get('filename')}: {len(deps)} dependencies")
                
                for dep in deps:
                    # Add source_type to each dependency
                    dep["source_type"] = self.get_source_type()
                    all_dependencies.append(dep)
            
            return all_dependencies
            
        except Exception as e:
            print(f"Error fetching dependencies for {owner}/{repo}: {str(e)}")
            return []
    
    def get_source_type(self) -> str:
        return "github_api"


class PackageFileSource(DependencySource):
    """Analyze package files to extract dependencies."""
    
    def __init__(self):
        load_dotenv()
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3.raw"
        }
    
    def _extract_repo_info(self, repo_url: str) -> tuple[str, str]:
        """Extract owner and repo name from GitHub URL."""
        parts = repo_url.strip("/").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        return parts[-2], parts[-1]
    
    def _get_dependency_files(self, repo_url: str) -> List[str]:
        """Get dependency files for a repository from seed_repos_dependency_files.json."""
        try:
            with open("data/seed_repos_dependency_files.json", "r") as f:
                repos_data = json.load(f)
            
            for repo_data in repos_data:
                if repo_data["repo_url"] == repo_url:
                    return repo_data.get("dependency_files", [])
            
            return []
        except Exception as e:
            print(f"Error getting dependency files for {repo_url}: {str(e)}")
            return []
    
    def _extract_file_info(self, file_url: str) -> tuple[str, str, str]:
        """Extract owner, repo, and file path from GitHub URL."""
        # Remove 'blob/master/' or 'blob/main/' from the URL
        clean_url = file_url.replace('/blob/master/', '/').replace('/blob/main/', '/')
        # Remove 'https://github.com/' from the URL
        clean_url = clean_url.replace('https://github.com/', '')
        parts = clean_url.strip("/").split("/")
        if len(parts) < 3:
            raise ValueError(f"Invalid GitHub file URL: {file_url}")
        return parts[0], parts[1], "/".join(parts[2:])
    
    def _fetch_file_content(self, file_url: str) -> str:
        """Fetch raw content of a file from GitHub."""
        owner, repo, path = self._extract_file_info(file_url)
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        print(f"\nFetching file from: {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Try to parse as JSON first
            try:
                resp_json = response.json()
                if "content" in resp_json:
                    content = base64.b64decode(resp_json["content"]).decode("utf-8")
                    print(f"Successfully fetched file content ({len(content)} bytes) [json]")
                    return content
                else:
                    print(f"Unexpected response JSON: {resp_json}")
                    # Try to get raw content if JSON parsing fails
                    content = response.text
                    if content:
                        print(f"Successfully fetched file content ({len(content)} bytes) [raw]")
                        return content
                    return ""
            except json.JSONDecodeError as e:
                print(f"Error parsing response as JSON: {str(e)}")
                # If not JSON, treat as raw text
                content = response.text
                if content:
                    print(f"Successfully fetched file content ({len(content)} bytes) [raw]")
                    return content
                return ""
        except requests.exceptions.RequestException as e:
            print(f"Error fetching file {file_url}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response content: {e.response.text[:500]}...")  # Print first 500 chars
            return ""
    
    def _analyze_dependencies(self, file_content: str, file_url: str) -> List[Dict]:
        """Use Gemini to analyze dependencies in a file."""
        print(f"Analyzing dependencies for file: {file_url}")
        prompt = DEPENDENCY_ANALYSIS_PROMPT.format(
            file_url=file_url,
            file_content=file_content
        )

        try:
            print("Sending request to Gemini...")
            response = self.model.generate_content(prompt)
            print("Received response from Gemini")
            
            # Extract JSON from the response
            content = response.text
            
            # Try different ways to extract JSON
            json_str = None
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                print("Found JSON in ```json``` block")
            elif "```" in content:
                json_str = content.split("```")[1].strip()
                print("Found JSON in ``` block")
            else:
                json_str = content.strip()
                print("Using raw content as JSON")
            
            if not json_str:
                print("No JSON content found in response")
                return []
            
            try:
                # First attempt: direct JSON parsing
                print("Attempting direct JSON parsing")
                deps = json.loads(json_str)
                if not isinstance(deps, list):
                    print(f"Expected list of dependencies, got {type(deps)}")
                    return []
                print(f"Successfully parsed {len(deps)} dependencies")
                
                # Add source_type to each dependency
                for dep in deps:
                    dep["source_type"] = self.get_source_type()
                
                return deps
            except json.JSONDecodeError as e:
                print(f"Direct JSON parsing failed: {str(e)}")
                print(f"Failed JSON string: {json_str}")
                
                # Second attempt: try to extract just the array part
                try:
                    print("Attempting to extract array from response")
                    # Look for array-like content
                    array_match = re.search(r'\[\s*\{.*\}\s*\]', json_str, re.DOTALL)
                    if array_match:
                        array_str = array_match.group(0)
                        print(f"Found potential array: {array_str[:200]}...")
                        deps = json.loads(array_str)
                        if isinstance(deps, list):
                            print(f"Successfully parsed {len(deps)} dependencies from extracted array")
                            
                            # Add source_type to each dependency
                            for dep in deps:
                                dep["source_type"] = self.get_source_type()
                            
                            return deps
                except Exception as e:
                    print(f"Array extraction failed: {str(e)}")
                
                # Third attempt: try to parse individual objects
                try:
                    print("Attempting to parse individual objects")
                    # Find all object-like content
                    objects = re.findall(r'\{[^{}]*\}', json_str)
                    if objects:
                        deps = []
                        for obj_str in objects:
                            try:
                                dep = json.loads(obj_str)
                                if isinstance(dep, dict) and all(k in dep for k in ['packageName', 'packageManager', 'requirements']):
                                    dep["source_type"] = self.get_source_type()
                                    deps.append(dep)
                            except json.JSONDecodeError:
                                continue
                        if deps:
                            print(f"Successfully parsed {len(deps)} dependencies from individual objects")
                            return deps
                except Exception as e:
                    print(f"Individual object parsing failed: {str(e)}")
                
                print("All parsing attempts failed")
                return []
                
        except Exception as e:
            print(f"Error analyzing dependencies: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response content: {e.response.text[:500] if hasattr(e.response, 'text') else str(e.response)}...")
            return []
    
    def analyze_file(self, repo_url: str, file_url: str) -> List[Dict]:
        """
        Analyze a single dependency file.
        
        Args:
            repo_url: URL of the repository.
            file_url: URL of the dependency file.
            
        Returns:
            List of dependencies extracted from the file.
        """
        file_content = self._fetch_file_content(file_url)
        if not file_content:
            return []
        
        return self._analyze_dependencies(file_content, file_url)
    
    def fetch_dependencies(self, repo_url: str) -> List[Dict]:
        """Fetch dependencies by analyzing package files."""
        dependency_files = self._get_dependency_files(repo_url)
        if not dependency_files:
            print(f"No dependency files found for {repo_url}")
            return []
        
        all_dependencies = []
        for file_url in dependency_files:
            deps = self.analyze_file(repo_url, file_url)
            if deps:
                all_dependencies.extend(deps)
        
        return all_dependencies
    
    def get_source_type(self) -> str:
        return "package_files"


class SpdxSbomSource(DependencySource):
    """Import and process SPDX SBOM files."""
    
    def __init__(self):
        pass
    
    def fetch_dependencies(self, repo_url: str) -> List[Dict]:
        """Fetch dependencies from SPDX SBOM.
        
        This method doesn't actually fetch anything by default,
        as SBOM files need to be imported separately.
        """
        print(f"SpdxSbomSource doesn't fetch dependencies directly. Use import_sbom method instead.")
        return []
    
    def import_sbom(self, file_path: str, repo_url: str) -> List[Dict]:
        """Import dependencies from an SPDX SBOM file."""
        try:
            with open(file_path, 'r') as f:
                if file_path.lower().endswith('.json'):
                    sbom_data = json.load(f)
                    return self.parse_spdx_sbom(sbom_data)
                elif file_path.lower().endswith('.csv'):
                    return self.parse_csv_sbom(f, repo_url)
                else:
                    print(f"Unsupported file format: {file_path}. Only JSON and CSV formats are supported.")
                    return []
        except Exception as e:
            print(f"Error importing SBOM from {file_path}: {str(e)}")
            return []
    
    def parse_spdx_sbom(self, sbom_data: Dict) -> List[Dict]:
        """Parse SPDX SBOM data into dependency objects."""
        dependencies = []
        
        # Create a mapping of SPDXID to package info
        package_map = {pkg["SPDXID"]: pkg for pkg in sbom_data.get("packages", [])}
        
        # Find the root package (usually the first one or the one with the document describes relationship)
        root_pkg_id = None
        for rel in sbom_data.get("relationships", []):
            if rel.get("relationshipType") == "DESCRIBES":
                root_pkg_id = rel.get("relatedSpdxElement")
                break
        
        # If no DESCRIBES relationship, try to find the document itself
        if not root_pkg_id and "documentDescribes" in sbom_data:
            if isinstance(sbom_data["documentDescribes"], list) and sbom_data["documentDescribes"]:
                root_pkg_id = sbom_data["documentDescribes"][0]
        
        # Process relationships to determine direct vs. transitive dependencies
        direct_deps = set()
        transitive_deps = set()
        
        for rel in sbom_data.get("relationships", []):
            rel_type = rel.get("relationshipType")
            source_id = rel.get("spdxElementId")
            target_id = rel.get("relatedSpdxElement")
            
            if rel_type == "DEPENDS_ON":
                # If the source is the root package, this is a direct dependency
                if source_id == root_pkg_id:
                    direct_deps.add(target_id)
                # Otherwise, it's a transitive dependency
                elif source_id in package_map and target_id in package_map:
                    transitive_deps.add(target_id)
        
        # For NPM packages, we can also look at the package.json dependencies vs devDependencies
        npm_direct_deps = set()
        npm_dev_deps = set()
        
        # Process each package
        for pkg_id, pkg in package_map.items():
            pkg_name = pkg.get("name")
            pkg_version = pkg.get("versionInfo", "")
            
            # Extract package manager from PURL
            pkg_manager = "UNKNOWN"
            purl = ""
            for ref in pkg.get("externalRefs", []):
                if ref.get("referenceType") == "purl":
                    purl = ref.get("referenceLocator", "")
                    if purl.startswith("pkg:"):
                        pkg_manager = purl.split("/")[0].split(":")[1].upper()
                        break
            
            # For NPM packages, try to determine if it's a direct or dev dependency
            if pkg_manager == "NPM" and "comment" in pkg:
                comment = pkg.get("comment", "").lower()
                if "direct dependency" in comment or "production dependency" in comment:
                    npm_direct_deps.add(pkg_id)
                elif "dev dependency" in comment or "development dependency" in comment:
                    npm_dev_deps.add(pkg_id)
            
            # Determine relationship (direct or transitive)
            relationship = "transitive"  # Default to transitive
            
            if pkg_id == root_pkg_id:
                # Skip the root package itself
                continue
            elif pkg_id in direct_deps or pkg_id in npm_direct_deps:
                relationship = "direct"
            
            dependencies.append({
                "packageName": pkg_name,
                "packageManager": pkg_manager,
                "requirements": pkg_version,
                "relationship": relationship,
                "packageUrl": purl,
                "source_type": self.get_source_type()
            })
        
        return dependencies
    
    def parse_csv_sbom(self, file_obj, repo_url: str) -> List[Dict]:
        """Parse CSV export from GitHub SBOM into dependency objects.
        
        Expected CSV format:
        package_url,name,version,type,namespace,license,dependency_type
        """
        import csv
        
        dependencies = []
        reader = csv.DictReader(file_obj)
        
        for row in reader:
            # Extract package manager from package_url
            pkg_manager = "UNKNOWN"
            pkg_url = row.get("package_url", "")
            if pkg_url.startswith("pkg:"):
                pkg_manager = pkg_url.split("/")[0].split(":")[1].upper()
            
            # Use type field as fallback for package manager
            if pkg_manager == "UNKNOWN" and "type" in row:
                pkg_manager = row["type"].upper()
            
            # Determine relationship (direct or transitive)
            relationship = "transitive"  # Default to transitive
            
            # Check if dependency_type column exists
            if "dependency_type" in row:
                dep_type = row["dependency_type"].lower()
                if dep_type in ["direct", "production", "runtime"]:
                    relationship = "direct"
            # For NPM packages, we can try to infer from the depth
            elif pkg_manager == "NPM" and "depth" in row:
                try:
                    depth = int(row["depth"])
                    if depth == 1:  # Direct dependencies are usually at depth 1
                        relationship = "direct"
                except (ValueError, TypeError):
                    pass
            
            dependencies.append({
                "packageName": row.get("name", ""),
                "packageManager": pkg_manager,
                "requirements": row.get("version", ""),
                "relationship": relationship,
                "packageUrl": pkg_url,
                "namespace": row.get("namespace", ""),
                "license": row.get("license", ""),
                "source_type": self.get_source_type()
            })
        
        return dependencies
    
    def get_source_type(self) -> str:
        return "spdx_sbom"
