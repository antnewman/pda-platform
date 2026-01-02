# PM-MCP-Servers Implementation Roadmap

## Status: Phase 1 - Dependencies Configured ✅

### Completed
- ✅ Version bumped to 0.2.0
- ✅ Added pm-data-tools>=0.2.0 dependency
- ✅ Added dev dependencies (pytest-cov, mypy)
- ✅ Git configured with antnewman author

### Phase 2: Real Parser Integration (IN PROGRESS)

Replace mock implementations in `src/pm_mcp_servers/pm_data/tools.py` with real pm-data-tools integration.

**Key Changes Needed:**
1. Import real pm-data-tools parsers, models, exceptions, exporters
2. Replace mock project store with dataclass-based ProjectStore
3. Update all 6 tools to use real parsers:
   - `load_project()` - Use detect_format() and create_parser()
   - `query_tasks()` - Work with real Project.tasks
   - `get_critical_path()` - Calculate from real task data
   - `get_dependencies()` - Use real Project.dependencies
   - `convert_format()` - Use create_exporter()
   - `get_project_summary()` - Aggregate real metrics

**Error Handling:**
- UnsupportedFormatError - Invalid format
- ParseError - Malformed file
- Generic Exception - Unexpected errors

### Phase 3: PM-Validate Server (TODO)

Create new validation MCP server at `src/pm_mcp_servers/pm_validate/`

**Structure:**
```
pm_validate/
├── __init__.py
├── tools.py      # 4 validation tools
└── server.py     # MCP server setup
```

**4 Tools:**
1. `validate_structure()` - Check references, hierarchy, cycles
2. `validate_semantic()` - Business rules, schedule logic
3. `validate_nista()` - UK government NISTA compliance
4. `validate_custom()` - Custom rule engine

**NISTA Compliance:**
- Required fields: department, DCA, SRO, dates
- Valid DCA values: green, amber_green, amber, amber_red, red
- Strictness levels: lenient, standard, strict

### Phase 4: Testing (TODO)

Create comprehensive test suite:
- `tests/test_pm_data_integration.py` - Real parser tests
- `tests/test_pm_validate.py` - Validation tests

Target: 90%+ coverage

### Phase 5: Documentation (TODO)

Update README with:
- Real parser capabilities
- Format support matrix
- NISTA validation guide
- Usage examples

## Next Steps

1. Complete Phase 2 (real parser integration)
2. Test with sample MSPDI/NISTA files
3. Commit and push Phase 2
4. Build Phase 3 (pm-validate)
5. Commit and push Phase 3
6. Add tests and documentation

## Attribution

All work: antnewman <antjsnewman@outlook.com>
For: PDA Task Force
Supporting: NISTA Programme and Project Data Standard trial
