"""Diagnose pm-data-tools actual data structures."""

import json
from pathlib import Path
from datetime import date, datetime

# Check if pm-data-tools is installed
try:
    import pm_data_tools
    print(f"pm-data-tools version: {pm_data_tools.__version__}")
except ImportError:
    print("ERROR: pm-data-tools not installed")
    print("Run: pip install pm-data-tools")
    exit(1)

# Check available functions
print("\n=== Available in pm_data_tools ===")
print(dir(pm_data_tools))

# Check if parse_project exists
if hasattr(pm_data_tools, 'parse_project'):
    print("\n✓ parse_project exists")
else:
    print("\n✗ parse_project NOT found")
    # Try alternate imports
    print("\nTrying alternate imports...")
    try:
        from pm_data_tools.parsers import parse_project
        print("  ✓ from pm_data_tools.parsers import parse_project")
    except ImportError as e:
        print(f"  ✗ {e}")

    try:
        from pm_data_tools import ProjectParser
        print("  ✓ from pm_data_tools import ProjectParser")
    except ImportError as e:
        print(f"  ✗ {e}")

# Check if detect_format exists
if hasattr(pm_data_tools, 'detect_format'):
    print("✓ detect_format exists")
else:
    print("✗ detect_format NOT found")

# Check models
print("\n=== Checking models ===")
try:
    from pm_data_tools.models import Project, Task, Resource, Dependency
    print("✓ Can import Project, Task, Resource, Dependency")

    # Check Project attributes
    p = Project.__dataclass_fields__ if hasattr(Project, '__dataclass_fields__') else {}
    print(f"\nProject fields: {list(p.keys()) if p else 'Not a dataclass'}")

    # Try to instantiate
    try:
        proj = Project(name="Test")
        print(f"Project attributes: {[a for a in dir(proj) if not a.startswith('_')]}")
    except Exception as e:
        print(f"Cannot instantiate Project: {e}")

except ImportError as e:
    print(f"✗ Cannot import models: {e}")

# Check exporters
print("\n=== Checking exporters ===")
try:
    from pm_data_tools.exporters import NISTAExporter
    print("✓ NISTAExporter exists")
except ImportError as e:
    print(f"✗ NISTAExporter: {e}")

# Check exceptions
print("\n=== Checking exceptions ===")
try:
    from pm_data_tools.exceptions import ParseError, UnsupportedFormatError
    print("✓ ParseError, UnsupportedFormatError exist")
except ImportError as e:
    print(f"✗ {e}")
    # Try alternate
    try:
        from pm_data_tools import ParseError
        print("  ✓ from pm_data_tools import ParseError")
    except:
        pass

# Create a test file and try to parse it
print("\n=== Testing actual parsing ===")
test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="http://schemas.microsoft.com/project">
    <Name>Test Project</Name>
    <StartDate>2026-01-01T08:00:00</StartDate>
    <FinishDate>2026-06-30T17:00:00</FinishDate>
    <Tasks>
        <Task>
            <UID>1</UID>
            <ID>1</ID>
            <Name>Task 1</Name>
            <Start>2026-01-01T08:00:00</Start>
            <Finish>2026-01-31T17:00:00</Finish>
            <Duration>PT240H0M0S</Duration>
            <PercentComplete>50</PercentComplete>
        </Task>
    </Tasks>
</Project>'''

test_file = Path("C:/Users/antjs/test_project.xml")
test_file.write_text(test_xml)

try:
    # Try to parse
    if hasattr(pm_data_tools, 'parse_project'):
        project = pm_data_tools.parse_project(str(test_file))
    else:
        from pm_data_tools.parsers import MSPDIParser
        parser = MSPDIParser()
        project = parser.parse(str(test_file))

    print(f"\n✓ Parsed successfully!")
    print(f"  Type: {type(project)}")
    print(f"  Name: {project.name if hasattr(project, 'name') else 'N/A'}")

    # Check tasks
    tasks = getattr(project, 'tasks', None)
    if tasks:
        print(f"  Tasks: {len(tasks)}")
        if tasks:
            t = tasks[0]
            print(f"  First task type: {type(t)}")
            print(f"  Task attributes: {[a for a in dir(t) if not a.startswith('_')][:20]}")
            print(f"  Task.id: {getattr(t, 'id', 'N/A')}")
            print(f"  Task.name: {getattr(t, 'name', 'N/A')}")
            print(f"  Task.start_date: {getattr(t, 'start_date', 'N/A')}")
            print(f"  Task.finish_date: {getattr(t, 'finish_date', 'N/A')}")
            print(f"  Task.duration: {getattr(t, 'duration', 'N/A')}")
            print(f"  Task.status: {getattr(t, 'status', 'N/A')}")
    else:
        print("  Tasks: None or empty")

    # Check if project has to_dict
    if hasattr(project, 'to_dict'):
        print("\n✓ project.to_dict() exists")
    else:
        print("\n✗ project.to_dict() NOT found")

except Exception as e:
    print(f"\n✗ Parse failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Summary ===")
print("Use the above to understand actual pm-data-tools API")
print("Then update tools.py to match reality")
