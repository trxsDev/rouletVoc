"""
Single source of truth for the application version.
All build scripts, installers, and workflows read from this file.

Versioning follows Semantic Versioning (semver.org):
  MAJOR.MINOR.PATCH
  - MAJOR: Breaking changes / major redesign
  - MINOR: New features (backward compatible)
  - PATCH: Bug fixes
"""

__version__ = "1.0.2"
