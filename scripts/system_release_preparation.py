#!/usr/bin/env python3
"""
System Release Preparation

This script prepares the Deep Thinking Engine for release by performing
final optimizations, documentation checks, and deployment preparation.

Requirements: 发布准备，版本管理
"""

import json
import logging
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sys

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


@dataclass
class ReleaseCheckResult:
    """Result of a release preparation check"""
    check_name: str
    category: str
    success: bool
    severity: str  # 'critical', 'warning', 'info'
    message: str
    details: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None


@dataclass
class ReleaseMetrics:
    """Release readiness metrics"""
    total_checks: int
    passed_checks: int
    failed_checks: int
    critical_issues: int
    warning_issues: int
    info_issues: int
    overall_readiness_score: float
    deployment_ready: bool


class SystemReleasePreparator:
    """System release preparation manager"""
    
    def __init__(self):
        """Initialize the release preparator"""
        self.project_root = project_root
        self.logger = logging.getLogger(__name__)
        
        # Release check results
        self.check_results: List[ReleaseCheckResult] = []
        self.release_metrics: Optional[ReleaseMetrics] = None
        
        # Release configuration
        self.release_config = self._load_release_config()
    
    def _load_release_config(self) -> Dict[str, Any]:
        """Load release configuration"""
        return {
            'version': '1.0.0',
            'release_name': 'Deep Thinking Engine v1.0',
            'target_environments': ['development', 'staging', 'production'],
            'required_files': [
                'README.md',
                'LICENSE',
                'pyproject.toml',
                'Makefile',
                'src/mcps/deep_thinking/__init__.py'
            ],
            'required_directories': [
                'src/mcps/deep_thinking',
                'tests/deep_thinking',
                'docs',
                'config',
                'templates',
                'scripts'
            ],
            'documentation_files': [
                'docs/README.md',
                'docs/user-guide/README.md',
                'docs/developer/README.md',
                'docs/deployment/README.md'
            ],
            'critical_components': [
                'mcp_tools',
                'session_manager',
                'template_manager',
                'database',
                'flow_manager'
            ]
        }
    
    def run_release_preparation_checks(self) -> List[ReleaseCheckResult]:
        """Run all release preparation checks"""
        self.logger.info("Starting system release preparation checks...")
        
        # Define all checks to run
        checks = [
            ('project_structure', 'structure', self._check_project_structure),
            ('required_files', 'files', self._check_required_files),
            ('documentation', 'documentation', self._check_documentation),
            ('code_quality', 'quality', self._check_code_quality),
            ('test_coverage', 'testing', self._check_test_coverage),
            ('configuration', 'config', self._check_configuration),
            ('dependencies', 'dependencies', self._check_dependencies),
            ('security', 'security', self._check_security),
            ('performance', 'performance', self._check_performance),
            ('deployment_readiness', 'deployment', self._check_deployment_readiness),
            ('version_management', 'versioning', self._check_version_management),
            ('integration_tests', 'testing', self._check_integration_tests)
        ]
        
        # Run all checks
        for check_name, category, check_func in checks:
            try:
                result = check_func()
                result.check_name = check_name
                result.category = category
                self.check_results.append(result)
                
                status = "✅ PASS" if result.success else "❌ FAIL"
                self.logger.info(f"{status} {check_name}: {result.message}")
                
            except Exception as e:
                error_result = ReleaseCheckResult(
                    check_name=check_name,
                    category=category,
                    success=False,
                    severity='critical',
                    message=f"Check failed with error: {str(e)}",
                    recommendations=['Fix the underlying issue and re-run the check']
                )
                self.check_results.append(error_result)
                self.logger.error(f"❌ ERROR {check_name}: {str(e)}")
        
        # Calculate release metrics
        self.release_metrics = self._calculate_release_metrics()
        
        self.logger.info(f"Release preparation checks completed: {len(self.check_results)} checks run")
        
        return self.check_results
    
    def _check_project_structure(self) -> ReleaseCheckResult:
        """Check project structure completeness"""
        missing_dirs = []
        
        for required_dir in self.release_config['required_directories']:
            dir_path = self.project_root / required_dir
            if not dir_path.exists():
                missing_dirs.append(required_dir)
        
        if missing_dirs:
            return ReleaseCheckResult(
                check_name='project_structure',
                category='structure',
                success=False,
                severity='critical',
                message=f"Missing required directories: {', '.join(missing_dirs)}",
                details={'missing_directories': missing_dirs},
                recommendations=[
                    'Create missing directories',
                    'Ensure project structure follows the specification'
                ]
            )
        
        # Check for additional structure quality
        src_files = list((self.project_root / "src" / "mcps" / "deep_thinking").rglob("*.py"))
        test_files = list((self.project_root / "tests" / "deep_thinking").rglob("*.py"))
        
        return ReleaseCheckResult(
            check_name='project_structure',
            category='structure',
            success=True,
            severity='info',
            message=f"Project structure is complete with {len(src_files)} source files and {len(test_files)} test files",
            details={
                'source_files_count': len(src_files),
                'test_files_count': len(test_files),
                'structure_complete': True
            }
        )
    
    def _check_required_files(self) -> ReleaseCheckResult:
        """Check required files existence"""
        missing_files = []
        
        for required_file in self.release_config['required_files']:
            file_path = self.project_root / required_file
            if not file_path.exists():
                missing_files.append(required_file)
        
        if missing_files:
            return ReleaseCheckResult(
                check_name='required_files',
                category='files',
                success=False,
                severity='critical',
                message=f"Missing required files: {', '.join(missing_files)}",
                details={'missing_files': missing_files},
                recommendations=[
                    'Create missing required files',
                    'Ensure all essential project files are present'
                ]
            )
        
        return ReleaseCheckResult(
            check_name='required_files',
            category='files',
            success=True,
            severity='info',
            message="All required files are present",
            details={'all_files_present': True}
        )
    
    def _check_documentation(self) -> ReleaseCheckResult:
        """Check documentation completeness"""
        missing_docs = []
        incomplete_docs = []
        
        for doc_file in self.release_config['documentation_files']:
            doc_path = self.project_root / doc_file
            
            if not doc_path.exists():
                missing_docs.append(doc_file)
            else:
                # Check if documentation is substantial (more than just a title)
                try:
                    content = doc_path.read_text(encoding='utf-8')
                    if len(content.strip()) < 100:  # Very basic check
                        incomplete_docs.append(doc_file)
                except Exception:
                    incomplete_docs.append(doc_file)
        
        issues = []
        severity = 'info'
        
        if missing_docs:
            issues.append(f"Missing documentation: {', '.join(missing_docs)}")
            severity = 'critical'
        
        if incomplete_docs:
            issues.append(f"Incomplete documentation: {', '.join(incomplete_docs)}")
            if severity != 'critical':
                severity = 'warning'
        
        if issues:
            return ReleaseCheckResult(
                check_name='documentation',
                category='documentation',
                success=False,
                severity=severity,
                message='; '.join(issues),
                details={
                    'missing_docs': missing_docs,
                    'incomplete_docs': incomplete_docs
                },
                recommendations=[
                    'Complete missing documentation',
                    'Expand incomplete documentation sections',
                    'Review documentation for clarity and completeness'
                ]
            )
        
        return ReleaseCheckResult(
            check_name='documentation',
            category='documentation',
            success=True,
            severity='info',
            message="Documentation is complete and substantial",
            details={'documentation_complete': True}
        )
    
    def _check_code_quality(self) -> ReleaseCheckResult:
        """Check code quality metrics"""
        try:
            # Count Python files
            src_files = list((self.project_root / "src").rglob("*.py"))
            
            # Basic code quality checks
            total_lines = 0
            files_with_docstrings = 0
            files_with_type_hints = 0
            
            for file_path in src_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    total_lines += len(lines)
                    
                    # Check for docstrings
                    if '"""' in content or "'''" in content:
                        files_with_docstrings += 1
                    
                    # Check for type hints
                    if ': ' in content and '->' in content:
                        files_with_type_hints += 1
                        
                except Exception:
                    continue
            
            docstring_coverage = files_with_docstrings / max(len(src_files), 1)
            type_hint_coverage = files_with_type_hints / max(len(src_files), 1)
            
            # Determine quality level
            quality_issues = []
            severity = 'info'
            
            if docstring_coverage < 0.7:
                quality_issues.append(f"Low docstring coverage: {docstring_coverage:.1%}")
                severity = 'warning'
            
            if type_hint_coverage < 0.5:
                quality_issues.append(f"Low type hint coverage: {type_hint_coverage:.1%}")
                if severity != 'warning':
                    severity = 'warning'
            
            if quality_issues:
                return ReleaseCheckResult(
                    check_name='code_quality',
                    category='quality',
                    success=False,
                    severity=severity,
                    message='; '.join(quality_issues),
                    details={
                        'total_files': len(src_files),
                        'total_lines': total_lines,
                        'docstring_coverage': docstring_coverage,
                        'type_hint_coverage': type_hint_coverage
                    },
                    recommendations=[
                        'Add docstrings to more functions and classes',
                        'Improve type hint coverage',
                        'Consider using code quality tools like pylint or flake8'
                    ]
                )
            
            return ReleaseCheckResult(
                check_name='code_quality',
                category='quality',
                success=True,
                severity='info',
                message=f"Code quality is good: {len(src_files)} files, {docstring_coverage:.1%} docstring coverage",
                details={
                    'total_files': len(src_files),
                    'total_lines': total_lines,
                    'docstring_coverage': docstring_coverage,
                    'type_hint_coverage': type_hint_coverage
                }
            )
            
        except Exception as e:
            return ReleaseCheckResult(
                check_name='code_quality',
                category='quality',
                success=False,
                severity='warning',
                message=f"Could not assess code quality: {str(e)}",
                recommendations=['Manually review code quality']
            )
    
    def _check_test_coverage(self) -> ReleaseCheckResult:
        """Check test coverage"""
        try:
            # Count test files
            test_files = list((self.project_root / "tests").rglob("test_*.py"))
            src_files = list((self.project_root / "src" / "mcps" / "deep_thinking").rglob("*.py"))
            
            # Exclude __init__.py files from source count
            src_files = [f for f in src_files if f.name != '__init__.py']
            
            test_to_src_ratio = len(test_files) / max(len(src_files), 1)
            
            # Check for integration tests
            integration_tests = [f for f in test_files if 'integration' in f.name.lower()]
            
            coverage_issues = []
            severity = 'info'
            
            if test_to_src_ratio < 0.5:
                coverage_issues.append(f"Low test coverage ratio: {test_to_src_ratio:.2f}")
                severity = 'warning'
            
            if len(integration_tests) < 3:
                coverage_issues.append(f"Few integration tests: {len(integration_tests)}")
                if severity != 'warning':
                    severity = 'warning'
            
            if coverage_issues:
                return ReleaseCheckResult(
                    check_name='test_coverage',
                    category='testing',
                    success=False,
                    severity=severity,
                    message='; '.join(coverage_issues),
                    details={
                        'test_files': len(test_files),
                        'src_files': len(src_files),
                        'test_to_src_ratio': test_to_src_ratio,
                        'integration_tests': len(integration_tests)
                    },
                    recommendations=[
                        'Add more unit tests',
                        'Create more integration tests',
                        'Consider using coverage tools to measure actual coverage'
                    ]
                )
            
            return ReleaseCheckResult(
                check_name='test_coverage',
                category='testing',
                success=True,
                severity='info',
                message=f"Good test coverage: {len(test_files)} test files for {len(src_files)} source files",
                details={
                    'test_files': len(test_files),
                    'src_files': len(src_files),
                    'test_to_src_ratio': test_to_src_ratio,
                    'integration_tests': len(integration_tests)
                }
            )
            
        except Exception as e:
            return ReleaseCheckResult(
                check_name='test_coverage',
                category='testing',
                success=False,
                severity='warning',
                message=f"Could not assess test coverage: {str(e)}",
                recommendations=['Manually review test coverage']
            )
    
    def _check_configuration(self) -> ReleaseCheckResult:
        """Check configuration completeness"""
        try:
            config_files = []
            missing_configs = []
            
            # Check for configuration files
            config_patterns = ['*.yaml', '*.yml', '*.json', '*.toml']
            for pattern in config_patterns:
                config_files.extend(list(self.project_root.rglob(pattern)))
            
            # Check for essential configurations
            essential_configs = [
                'pyproject.toml',
                'config/system.yaml',
                'config/flows.yaml'
            ]
            
            for config in essential_configs:
                config_path = self.project_root / config
                if not config_path.exists():
                    missing_configs.append(config)
            
            if missing_configs:
                return ReleaseCheckResult(
                    check_name='configuration',
                    category='config',
                    success=False,
                    severity='warning',
                    message=f"Missing configuration files: {', '.join(missing_configs)}",
                    details={
                        'total_config_files': len(config_files),
                        'missing_configs': missing_configs
                    },
                    recommendations=[
                        'Create missing configuration files',
                        'Ensure all components have proper configuration'
                    ]
                )
            
            return ReleaseCheckResult(
                check_name='configuration',
                category='config',
                success=True,
                severity='info',
                message=f"Configuration is complete: {len(config_files)} config files found",
                details={
                    'total_config_files': len(config_files),
                    'configuration_complete': True
                }
            )
            
        except Exception as e:
            return ReleaseCheckResult(
                check_name='configuration',
                category='config',
                success=False,
                severity='warning',
                message=f"Could not check configuration: {str(e)}",
                recommendations=['Manually verify configuration files']
            )
    
    def _check_dependencies(self) -> ReleaseCheckResult:
        """Check dependency management"""
        try:
            # Check pyproject.toml
            pyproject_path = self.project_root / 'pyproject.toml'
            
            if not pyproject_path.exists():
                return ReleaseCheckResult(
                    check_name='dependencies',
                    category='dependencies',
                    success=False,
                    severity='critical',
                    message="pyproject.toml not found",
                    recommendations=['Create pyproject.toml with proper dependencies']
                )
            
            # Read and check pyproject.toml
            content = pyproject_path.read_text(encoding='utf-8')
            
            # Basic checks
            has_dependencies = 'dependencies' in content
            has_build_system = 'build-system' in content
            has_project_info = 'project' in content
            
            issues = []
            if not has_dependencies:
                issues.append("No dependencies section")
            if not has_build_system:
                issues.append("No build-system section")
            if not has_project_info:
                issues.append("No project information section")
            
            if issues:
                return ReleaseCheckResult(
                    check_name='dependencies',
                    category='dependencies',
                    success=False,
                    severity='warning',
                    message=f"pyproject.toml issues: {', '.join(issues)}",
                    details={
                        'has_dependencies': has_dependencies,
                        'has_build_system': has_build_system,
                        'has_project_info': has_project_info
                    },
                    recommendations=[
                        'Complete pyproject.toml configuration',
                        'Ensure all dependencies are properly specified'
                    ]
                )
            
            return ReleaseCheckResult(
                check_name='dependencies',
                category='dependencies',
                success=True,
                severity='info',
                message="Dependency management is properly configured",
                details={
                    'has_dependencies': has_dependencies,
                    'has_build_system': has_build_system,
                    'has_project_info': has_project_info
                }
            )
            
        except Exception as e:
            return ReleaseCheckResult(
                check_name='dependencies',
                category='dependencies',
                success=False,
                severity='warning',
                message=f"Could not check dependencies: {str(e)}",
                recommendations=['Manually verify dependency configuration']
            )
    
    def _check_security(self) -> ReleaseCheckResult:
        """Check security considerations"""
        try:
            security_issues = []
            
            # Check for common security files
            security_files = [
                '.gitignore',
                'LICENSE'
            ]
            
            missing_security_files = []
            for sec_file in security_files:
                if not (self.project_root / sec_file).exists():
                    missing_security_files.append(sec_file)
            
            if missing_security_files:
                security_issues.append(f"Missing security files: {', '.join(missing_security_files)}")
            
            # Check for sensitive data patterns in code
            sensitive_patterns = ['password', 'secret', 'key', 'token']
            src_files = list((self.project_root / "src").rglob("*.py"))
            
            files_with_sensitive_data = []
            for file_path in src_files:
                try:
                    content = file_path.read_text(encoding='utf-8').lower()
                    for pattern in sensitive_patterns:
                        if pattern in content and 'test' not in file_path.name.lower():
                            files_with_sensitive_data.append(str(file_path.relative_to(self.project_root)))
                            break
                except Exception:
                    continue
            
            if files_with_sensitive_data:
                security_issues.append(f"Files with potential sensitive data: {len(files_with_sensitive_data)}")
            
            if security_issues:
                severity = 'critical' if missing_security_files else 'warning'
                return ReleaseCheckResult(
                    check_name='security',
                    category='security',
                    success=False,
                    severity=severity,
                    message='; '.join(security_issues),
                    details={
                        'missing_security_files': missing_security_files,
                        'files_with_sensitive_data': files_with_sensitive_data
                    },
                    recommendations=[
                        'Add missing security files',
                        'Review files for hardcoded sensitive data',
                        'Ensure proper .gitignore configuration'
                    ]
                )
            
            return ReleaseCheckResult(
                check_name='security',
                category='security',
                success=True,
                severity='info',
                message="Security considerations are properly addressed",
                details={'security_files_present': True}
            )
            
        except Exception as e:
            return ReleaseCheckResult(
                check_name='security',
                category='security',
                success=False,
                severity='warning',
                message=f"Could not check security: {str(e)}",
                recommendations=['Manually review security considerations']
            )
    
    def _check_performance(self) -> ReleaseCheckResult:
        """Check performance considerations"""
        try:
            # Check for performance-related files
            perf_files = list(self.project_root.rglob("*performance*"))
            optimization_files = list(self.project_root.rglob("*optim*"))
            
            total_perf_files = len(perf_files) + len(optimization_files)
            
            # Check for performance tests
            perf_tests = [f for f in perf_files if 'test' in f.name.lower()]
            
            if total_perf_files == 0:
                return ReleaseCheckResult(
                    check_name='performance',
                    category='performance',
                    success=False,
                    severity='warning',
                    message="No performance optimization files found",
                    recommendations=[
                        'Consider adding performance monitoring',
                        'Add performance optimization modules',
                        'Create performance benchmarks'
                    ]
                )
            
            return ReleaseCheckResult(
                check_name='performance',
                category='performance',
                success=True,
                severity='info',
                message=f"Performance considerations addressed: {total_perf_files} related files",
                details={
                    'performance_files': len(perf_files),
                    'optimization_files': len(optimization_files),
                    'performance_tests': len(perf_tests)
                }
            )
            
        except Exception as e:
            return ReleaseCheckResult(
                check_name='performance',
                category='performance',
                success=False,
                severity='warning',
                message=f"Could not check performance: {str(e)}",
                recommendations=['Manually review performance considerations']
            )
    
    def _check_deployment_readiness(self) -> ReleaseCheckResult:
        """Check deployment readiness"""
        try:
            deployment_files = []
            
            # Check for deployment-related files
            deployment_patterns = [
                'Dockerfile',
                'docker-compose.yml',
                'deploy.sh',
                'deployment.yaml',
                'requirements.txt'
            ]
            
            for pattern in deployment_patterns:
                if (self.project_root / pattern).exists():
                    deployment_files.append(pattern)
            
            # Check deployment directory
            deploy_dir = self.project_root / 'docs' / 'deployment'
            has_deploy_docs = deploy_dir.exists() and any(deploy_dir.iterdir())
            
            # Check scripts directory
            scripts_dir = self.project_root / 'scripts'
            has_scripts = scripts_dir.exists() and any(scripts_dir.glob('*.py'))
            
            readiness_score = 0
            if deployment_files:
                readiness_score += 40
            if has_deploy_docs:
                readiness_score += 30
            if has_scripts:
                readiness_score += 30
            
            if readiness_score < 60:
                return ReleaseCheckResult(
                    check_name='deployment_readiness',
                    category='deployment',
                    success=False,
                    severity='warning',
                    message=f"Deployment readiness score: {readiness_score}/100",
                    details={
                        'deployment_files': deployment_files,
                        'has_deploy_docs': has_deploy_docs,
                        'has_scripts': has_scripts,
                        'readiness_score': readiness_score
                    },
                    recommendations=[
                        'Add deployment scripts and configuration',
                        'Create deployment documentation',
                        'Add automation scripts'
                    ]
                )
            
            return ReleaseCheckResult(
                check_name='deployment_readiness',
                category='deployment',
                success=True,
                severity='info',
                message=f"Deployment ready: {readiness_score}/100 score",
                details={
                    'deployment_files': deployment_files,
                    'has_deploy_docs': has_deploy_docs,
                    'has_scripts': has_scripts,
                    'readiness_score': readiness_score
                }
            )
            
        except Exception as e:
            return ReleaseCheckResult(
                check_name='deployment_readiness',
                category='deployment',
                success=False,
                severity='warning',
                message=f"Could not check deployment readiness: {str(e)}",
                recommendations=['Manually verify deployment configuration']
            )
    
    def _check_version_management(self) -> ReleaseCheckResult:
        """Check version management"""
        try:
            version_indicators = []
            
            # Check pyproject.toml for version
            pyproject_path = self.project_root / 'pyproject.toml'
            if pyproject_path.exists():
                content = pyproject_path.read_text(encoding='utf-8')
                if 'version' in content:
                    version_indicators.append('pyproject.toml')
            
            # Check __init__.py for version
            init_path = self.project_root / 'src' / 'mcps' / 'deep_thinking' / '__init__.py'
            if init_path.exists():
                content = init_path.read_text(encoding='utf-8')
                if '__version__' in content:
                    version_indicators.append('__init__.py')
            
            # Check for git tags (if .git exists)
            git_dir = self.project_root / '.git'
            has_git = git_dir.exists()
            
            if not version_indicators:
                return ReleaseCheckResult(
                    check_name='version_management',
                    category='versioning',
                    success=False,
                    severity='warning',
                    message="No version information found",
                    details={
                        'version_indicators': version_indicators,
                        'has_git': has_git
                    },
                    recommendations=[
                        'Add version information to pyproject.toml',
                        'Add __version__ to __init__.py',
                        'Consider using git tags for versioning'
                    ]
                )
            
            return ReleaseCheckResult(
                check_name='version_management',
                category='versioning',
                success=True,
                severity='info',
                message=f"Version management in place: {', '.join(version_indicators)}",
                details={
                    'version_indicators': version_indicators,
                    'has_git': has_git
                }
            )
            
        except Exception as e:
            return ReleaseCheckResult(
                check_name='version_management',
                category='versioning',
                success=False,
                severity='warning',
                message=f"Could not check version management: {str(e)}",
                recommendations=['Manually verify version management']
            )
    
    def _check_integration_tests(self) -> ReleaseCheckResult:
        """Check integration test status"""
        try:
            # Look for integration test files
            integration_test_files = []
            test_dir = self.project_root / 'tests'
            
            if test_dir.exists():
                integration_test_files = list(test_dir.rglob("*integration*"))
            
            # Look for test scripts
            scripts_dir = self.project_root / 'scripts'
            test_scripts = []
            
            if scripts_dir.exists():
                test_scripts = [f for f in scripts_dir.glob("*test*.py")]
            
            total_integration_assets = len(integration_test_files) + len(test_scripts)
            
            if total_integration_assets < 3:
                return ReleaseCheckResult(
                    check_name='integration_tests',
                    category='testing',
                    success=False,
                    severity='warning',
                    message=f"Limited integration testing: {total_integration_assets} assets",
                    details={
                        'integration_test_files': len(integration_test_files),
                        'test_scripts': len(test_scripts),
                        'total_assets': total_integration_assets
                    },
                    recommendations=[
                        'Add more integration tests',
                        'Create comprehensive test scenarios',
                        'Add automated testing scripts'
                    ]
                )
            
            return ReleaseCheckResult(
                check_name='integration_tests',
                category='testing',
                success=True,
                severity='info',
                message=f"Integration testing ready: {total_integration_assets} test assets",
                details={
                    'integration_test_files': len(integration_test_files),
                    'test_scripts': len(test_scripts),
                    'total_assets': total_integration_assets
                }
            )
            
        except Exception as e:
            return ReleaseCheckResult(
                check_name='integration_tests',
                category='testing',
                success=False,
                severity='warning',
                message=f"Could not check integration tests: {str(e)}",
                recommendations=['Manually verify integration test coverage']
            )
    
    def _calculate_release_metrics(self) -> ReleaseMetrics:
        """Calculate overall release metrics"""
        if not self.check_results:
            return ReleaseMetrics(0, 0, 0, 0, 0, 0, 0.0, False)
        
        total_checks = len(self.check_results)
        passed_checks = sum(1 for r in self.check_results if r.success)
        failed_checks = total_checks - passed_checks
        
        critical_issues = sum(1 for r in self.check_results if r.severity == 'critical' and not r.success)
        warning_issues = sum(1 for r in self.check_results if r.severity == 'warning' and not r.success)
        info_issues = sum(1 for r in self.check_results if r.severity == 'info' and not r.success)
        
        # Calculate readiness score
        base_score = (passed_checks / total_checks) * 100
        
        # Penalties for issues
        critical_penalty = critical_issues * 20
        warning_penalty = warning_issues * 10
        info_penalty = info_issues * 5
        
        readiness_score = max(0, base_score - critical_penalty - warning_penalty - info_penalty)
        
        # Deployment ready if score >= 80 and no critical issues
        deployment_ready = readiness_score >= 80 and critical_issues == 0
        
        return ReleaseMetrics(
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            critical_issues=critical_issues,
            warning_issues=warning_issues,
            info_issues=info_issues,
            overall_readiness_score=readiness_score,
            deployment_ready=deployment_ready
        )
    
    def generate_release_report(self) -> str:
        """Generate comprehensive release preparation report"""
        if not self.check_results or not self.release_metrics:
            return "No release preparation results available."
        
        metrics = self.release_metrics
        
        report_lines = [
            "=" * 100,
            "DEEP THINKING ENGINE - SYSTEM RELEASE PREPARATION REPORT",
            "=" * 100,
            "",
            f"Release Version: {self.release_config['version']}",
            f"Release Name: {self.release_config['release_name']}",
            f"Report Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "RELEASE READINESS SUMMARY",
            "-" * 50,
            f"Total Checks: {metrics.total_checks}",
            f"Passed Checks: {metrics.passed_checks}",
            f"Failed Checks: {metrics.failed_checks}",
            f"Success Rate: {metrics.passed_checks/metrics.total_checks:.1%}",
            "",
            "ISSUE BREAKDOWN",
            "-" * 50,
            f"🔴 Critical Issues: {metrics.critical_issues}",
            f"🟡 Warning Issues: {metrics.warning_issues}",
            f"🔵 Info Issues: {metrics.info_issues}",
            "",
            f"OVERALL READINESS SCORE: {metrics.overall_readiness_score:.1f}/100",
            "",
            "DETAILED CHECK RESULTS",
            "-" * 50
        ]
        
        # Group results by category
        categories = {}
        for result in self.check_results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        for category, results in categories.items():
            report_lines.extend([
                f"",
                f"📁 {category.upper()} CHECKS:"
            ])
            
            for result in results:
                status = "✅ PASS" if result.success else "❌ FAIL"
                severity_icon = {
                    'critical': '🔴',
                    'warning': '🟡',
                    'info': '🔵'
                }.get(result.severity, '⚪')
                
                report_lines.append(f"  {status} {severity_icon} {result.check_name}: {result.message}")
                
                if result.recommendations and not result.success:
                    report_lines.append("    Recommendations:")
                    for rec in result.recommendations[:2]:  # Show top 2 recommendations
                        report_lines.append(f"      • {rec}")
        
        # Release decision
        if metrics.deployment_ready:
            release_status = "🚀 READY FOR RELEASE"
            release_recommendation = "System is ready for deployment to production"
        elif metrics.critical_issues == 0 and metrics.overall_readiness_score >= 60:
            release_status = "⚠️ READY FOR BETA/STAGING"
            release_recommendation = "System is ready for beta testing or staging deployment"
        else:
            release_status = "❌ NOT READY FOR RELEASE"
            release_recommendation = "Critical issues must be resolved before release"
        
        report_lines.extend([
            "",
            "RELEASE DECISION",
            "-" * 50,
            f"Status: {release_status}",
            f"Recommendation: {release_recommendation}",
            "",
            "NEXT STEPS",
            "-" * 50
        ])
        
        if metrics.deployment_ready:
            report_lines.extend([
                "1. ✅ Perform final system backup",
                "2. ✅ Execute deployment scripts",
                "3. ✅ Monitor system after deployment",
                "4. ✅ Prepare rollback plan if needed"
            ])
        else:
            # Prioritize recommendations
            all_recommendations = []
            for result in self.check_results:
                if not result.success and result.recommendations:
                    all_recommendations.extend(result.recommendations)
            
            # Get unique recommendations
            unique_recommendations = list(dict.fromkeys(all_recommendations))
            
            for i, rec in enumerate(unique_recommendations[:5], 1):
                report_lines.append(f"{i}. {rec}")
        
        report_lines.extend([
            "",
            "=" * 100
        ])
        
        return "\n".join(report_lines)
    
    def save_release_results(self, output_directory: Optional[str] = None):
        """Save release preparation results"""
        output_dir = Path(output_directory or "release_preparation_results")
        output_dir.mkdir(exist_ok=True)
        
        # Save comprehensive report
        report = self.generate_release_report()
        with open(output_dir / "release_preparation_report.txt", 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save raw results as JSON
        def convert_for_json(obj):
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)
        
        results_data = {
            'release_config': self.release_config,
            'check_results': [asdict(result) for result in self.check_results],
            'release_metrics': asdict(self.release_metrics) if self.release_metrics else None,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(output_dir / "release_preparation_results.json", 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False, default=convert_for_json)
        
        self.logger.info(f"Release preparation results saved to: {output_dir}")
        return output_dir


def main():
    """Main entry point for system release preparation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deep Thinking Engine System Release Preparation')
    parser.add_argument('--output-dir', help='Output directory for results')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 100)
    print("DEEP THINKING ENGINE - SYSTEM RELEASE PREPARATION")
    print("=" * 100)
    
    preparator = None
    
    try:
        # Initialize preparator
        preparator = SystemReleasePreparator()
        print(f"✅ Release preparation initialized")
        
        # Run release preparation checks
        print("\n🔍 Running release preparation checks...")
        results = preparator.run_release_preparation_checks()
        
        # Generate and display report
        report = preparator.generate_release_report()
        print("\n" + report)
        
        # Save results
        output_dir = preparator.save_release_results(args.output_dir)
        print(f"\n📄 Release preparation results saved to: {output_dir}")
        
        # Determine readiness
        metrics = preparator.release_metrics
        
        if metrics.deployment_ready:
            print("\n🎉 SYSTEM IS READY FOR RELEASE!")
            print("✅ All critical checks passed - proceed with deployment!")
            return True
        elif metrics.critical_issues == 0 and metrics.overall_readiness_score >= 60:
            print(f"\n⚠️  System is ready for beta/staging deployment")
            print(f"Readiness score: {metrics.overall_readiness_score:.1f}/100")
            print("🟡 Address remaining issues before production release")
            return True
        else:
            print(f"\n❌ System is not ready for release")
            print(f"Critical issues: {metrics.critical_issues}, Readiness score: {metrics.overall_readiness_score:.1f}/100")
            print("🔴 Resolve critical issues before deployment")
            return False
        
    except Exception as e:
        print(f"❌ Release preparation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)