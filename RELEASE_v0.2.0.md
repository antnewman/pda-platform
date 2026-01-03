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

## Manual Tasks Required ⚠️

### 1. Create GitHub Release
**Action Required:** Create release from tag v0.2.0

**Steps:**
1. Go to: https://github.com/PDA-Task-Force/pda-platform/releases/new?tag=v0.2.0
2. Title: "Release v0.2.0 - Production-ready infrastructure"
3. Copy the tag description as release notes
4. Publish release
5. **Result:** Zenodo will automatically create a DOI for this version

### 2. Upload to PyPI
**Action Required:** Upload packages using your PyPI API token

**Method 1: Environment Variables**
```bash
cd C:/Users/antjs/pda-platform

export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here

python -m twine upload packages/pm-data-tools/dist/*
python -m twine upload packages/pm-mcp-servers/dist/*
python -m twine upload packages/agent-task-planning/dist/*
```

**Method 2: Using .pypirc**
Create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-your-token-here
```

Then upload:
```bash
python -m twine upload packages/*/dist/*
```

**Expected Output:**
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading pm_data_tools-0.2.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 87.0/87.0 kB • 00:00
Uploading pm_data_tools-0.2.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 127.0/127.0 kB • 00:00

View at:
https://pypi.org/project/pm-data-tools/0.2.0/
```

### 3. Verify PyPI Publication
**Action Required:** Verify packages are installable

**Steps:**
```bash
# Create fresh environment
python -m venv /tmp/test-install
source /tmp/test-install/bin/activate  # On Windows: /tmp/test-install/Scripts/activate

# Install from PyPI (wait 1-2 minutes after upload)
pip install pm-data-tools==0.2.0
pip install pm-mcp-servers==0.2.0
pip install agent-task-planning==0.2.0

# Verify imports
python -c "
from pm_data_tools import parse_project
from pm_mcp_servers.pm_data.tools import load_project
from pm_mcp_servers.pm_validate.tools import validate_nista
from agent_task_planning import generate_plan
print('✅ All imports successful!')
"

# Cleanup
deactivate
rm -rf /tmp/test-install
```

### 4. Update Documentation (After Zenodo DOI Generated)
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

After PyPI publication:
- [ ] Install pm-data-tools from PyPI
- [ ] Install pm-mcp-servers from PyPI
- [ ] Install agent-task-planning from PyPI
- [ ] Verify imports work
- [ ] Test basic functionality
- [ ] Check PyPI project pages
- [ ] Verify DOI badge on README

## Links

- **GitHub Repository:** https://github.com/PDA-Task-Force/pda-platform
- **GitHub Release:** https://github.com/PDA-Task-Force/pda-platform/releases/tag/v0.2.0
- **Zenodo:** https://zenodo.org/record/18133574
- **PyPI pm-data-tools:** https://pypi.org/project/pm-data-tools/
- **PyPI pm-mcp-servers:** https://pypi.org/project/pm-mcp-servers/
- **PyPI agent-task-planning:** https://pypi.org/project/agent-task-planning/

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
3. Tag: `v0.2.0` with comprehensive release notes

## Completion Date

Automated preparation completed: 2026-01-03
Awaiting manual PyPI upload and GitHub release creation.
