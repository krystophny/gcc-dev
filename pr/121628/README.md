# PR121628 Deep Copy Reproducer

Artifacts and notes for Bug 121628 (recursive allocatable component deep copy).

Programs:
- `121628.f90` and derivatives capture the original reproducer.
- `deepcopy.f90` contains the simplified reproducer used in testing.

## Test Results

### Intel ifx 2025.2.1
- Status: PASS
- Compiles without errors

Refer to `ALLOCATABLE_DEEPCOPY_PLAYBOOK.md` for detailed analysis and steps.
