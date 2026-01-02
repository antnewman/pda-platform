# Canonical Model v1.0

Universal data model for project management information.

## Overview

The Canonical Model provides a unified schema for representing project management data from any source. It enables lossless conversion between different PM tools and standards.

## Entities

The model includes 12 core entity types:

1. **Project** - Top-level container with metadata
2. **Task** - Work items with WBS, schedule, and costs
3. **Resource** - People, equipment, and materials
4. **Assignment** - Task-resource allocations
5. **Dependency** - Task relationships (FS, SS, FF, SF)
6. **Calendar** - Working time definitions
7. **Risk** - Risk register entries
8. **Milestone** - Key project dates
9. **Baseline** - Snapshot comparisons
10. **CustomField** - User-defined attributes
11. **Document** - Attached files and links
12. **Note** - Comments and annotations

## Schema

See [project.schema.json](project.schema.json) for the complete JSON Schema definition.

## Design Principles

- **Superset approach**: Includes all fields from supported formats
- **Lossless conversion**: Roundtrip conversions preserve all data
- **NISTA alignment**: Compatible with UK government standards
- **Extensibility**: Custom fields support format-specific attributes

## Usage

The canonical model serves as the intermediate format for all conversions:

```
Source Format → Parser → Canonical Model → Writer → Target Format
```

This ensures:
- Consistent validation across all formats
- N-to-M conversion with N+M parsers (not N×M converters)
- Single source of truth for data semantics

## Authors

Members of the PDA Task Force

## Acknowledgments

This specification was developed to support the NISTA Programme and Project Data Standard trial.
