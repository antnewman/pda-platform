# Release v0.2.0 - Publication Checklist

## Automated Tasks Completed ✅

### Part A: Zenodo DOI
- [x] Created `.zenodo.json` with comprehensive metadata
- [x] Updated `CITATION.cff` to version 0.2.0
- [x] Updated all package versions to 0.2.0
- [x] Created git tag v0.2.0 with detailed release notes
- [x] Pushed tag to GitHub

### Part B: PyPI Publication
- [x] Installed build tools (build, twine)
- [x] Built all three packages:
  - pm-data-tools 0.2.0
  - pm-mcp-servers 0.2.0
  - agent-task-planning 0.2.0
- [x] Verified all packages with `twine check` (ALL PASSED)
- [x] Uploaded pm-data-tools 0.2.0 to PyPI
- [x] Uploaded pm-mcp-servers 0.2.0 to PyPI
- [x] Uploaded agent-task-planning 0.2.0 to PyPI
- [x] Verified all packages are installable from PyPI

**PyPI Publication URLs:**
- pm-data-tools: https://pypi.org/project/pm-data-tools/0.2.0/
- pm-mcp-servers: https://pypi.org/project/pm-mcp-servers/0.2.0/
- agent-task-planning: https://pypi.org/project/agent-task-planning/0.2.0/

## Manual Tasks Required ⚠️

### 1. Create GitHub Release
**Action Required:** Create release from tag v0.2.0

**Steps:**
1. Go to: https://github.com/PDA-Task-Force/pda-platform/releases/new?tag=v0.2.0
2. Title: "Release v0.2.0 - Production-ready infrastructure"
3. Copy the tag description as release notes
4. Publish release
5. **Result:** Zenodo will automatically create a DOI for this version

### 2. Update Documentation (After Zenodo DOI Generated)
**Action Required:** Add new DOI to README

Once Zenodo generates the new DOI:
1. Go to: https://zenodo.org/account/settings/github/
2. Find DOI for v0.2.0 (format: 10.5281/zenodo.XXXXXXX)
3. Update README.md badge if DOI changed
4. Commit and push changes

## Package Details

### pm-data-tools 0.2.0
- **Size:** 127 KB (source), 87 KB (wheel)
- **Features:**
  - 8 format parsers (MSPDI, P6 XER, Jira, Monday, Asana, Smartsheet, GMPP, NISTA)
  - Full dependency and resource extraction
  - Unified data model

### pm-mcp-servers 0.2.0
- **Size:** 19 KB (source), 15 KB (wheel)
- **Features:**
  - 6 data tools (load, query, dependencies, convert, summary, critical path)
  - 4 validation tools (structure, semantic, NISTA, custom)
  - Shared project store

### agent-task-planning 0.2.0
- **Size:** 67 KB (source), 50 KB (wheel)
- **Features:**
  - Task decomposition framework
  - Confidence extraction
  - Outlier mining

## Testing Checklist

PyPI publication verified:
- [x] Install pm-data-tools from PyPI
- [x] Install pm-mcp-servers from PyPI
- [x] Install agent-task-planning from PyPI
- [x] Verify imports work
- [x] Check PyPI project pages

Remaining tasks:
- [ ] Create GitHub release
- [ ] Verify Zenodo DOI generation
- [ ] Update README with DOI badge (if needed)

## Links

- **GitHub Repository:** https://github.com/PDA-Task-Force/pda-platform
- **GitHub Release:** https://github.com/PDA-Task-Force/pda-platform/releases/tag/v0.2.0
- **Zenodo:** https://zenodo.org/record/18133574
- **PyPI pm-data-tools:** https://pypi.org/project/pm-data-tools/0.2.0/
- **PyPI pm-mcp-servers:** https://pypi.org/project/pm-mcp-servers/0.2.0/
- **PyPI agent-task-planning:** https://pypi.org/project/agent-task-planning/0.2.0/

## Troubleshooting

### PyPI Upload Issues

**403 Forbidden Error:**
- Token may have expired
- Generate new token at: https://pypi.org/manage/account/token/
- Ensure token has "Upload packages" scope

**Package Already Exists:**
- Cannot overwrite existing version on PyPI
- Must increment version number
- Delete local dist/ and rebuild with new version

**Import Errors After Install:**
- Check package dependencies are installed
- Verify Python version compatibility (>=3.10)
- Check for namespace conflicts

## Git Commits Made

1. `chore: add Zenodo and citation metadata for v0.2.0`
2. `chore: update agent-task-planning to version 0.2.0`
3. `docs: add release v0.2.0 publication checklist`
4. Tag: `v0.2.0` with comprehensive release notes

## Completion Status

**Automated tasks completed:** 2026-01-03
- All packages built and published to PyPI
- Git tag created and pushed
- Zenodo metadata configured

**Awaiting manual action:**
- GitHub release creation (triggers Zenodo DOI generation)
- Optional: README update with new DOI badge

