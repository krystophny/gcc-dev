# PR 92613: Response to Harald Anlauf Review (2025-12-09)

## Summary of Anlauf's Comments

### Technical Points

1. **Traditional mode preprocessing**: gfortran uses cpp in traditional mode,
   unlike other Fortran compilers that are Fortran-aware.

2. **Fixed-form comment characters**: Fortran comments can start with `!`, but
   in fixed-form also with `c` (and `C`, `*`).

3. **Both quote types affected**: The issue occurs with both `'` and `"`.

### Test Case Concerns

4. **Test execution question**: How should the test run? With `-cpp -E` or
   without `-E`? What exactly is being tested?
   - With `-E`: test fails as-is
   - Without `-E`: test is silent
   - The `dg-bogus` lines seem pointless given current behavior

5. **"That is really bogus" comment**: Why should one ever get a warning at all
   for quotes in comments? The current situation is fundamentally wrong.

### Style/Documentation Concerns

6. **Excessive comments in source**: Anlauf finds the comments too verbose and
   requests more concise formulation.

7. **"fully" not needed**: In documentation, "fully preprocessed" should just
   be "preprocessed" (what does "fully" mean?).

### Alternative Approach Suggested

8. **Warning for contradicting options**: Anlauf suggests we should perhaps warn
   if someone combines `-cpp -fpreprocessed` as contradicting options, rather
   than silently handling it. He acknowledges the cmake issue though.

## Analysis and Proposed Response

### On Traditional Mode (Point 1)
This is informational context. Our fix already accounts for this - we bypass
libcpp entirely for `-fpreprocessed` input precisely because libcpp (even in
traditional mode) does not understand Fortran comment syntax.

### On Fixed-Form Comments (Point 2)
**Action needed**: The test case should also verify fixed-form comment
characters. Add test with `c` comment line in fixed-form source.

### On Both Quote Types (Point 3)
**Already addressed**: The test includes both `'` and `"` examples.

### On Test Execution (Point 4)
**Critical issue**: Anlauf is right - the `dg-bogus` directives are
questionable. The test should verify:
- Compilation succeeds without warnings (the actual goal)
- The `dg-bogus` pattern would only match if a warning were emitted

**Options**:
a) Use `dg-do compile` without `dg-bogus` - if warning appears, test fails
b) Use `dg-warning` with `!` to verify no warning: not standard DejaGnu
c) Simply rely on `dg-do compile` passing cleanly

**Recommendation**: Remove `dg-bogus` lines. The test passes if it compiles
without warnings. If the bug regresses, the warning would cause test failure.

### On "That is really bogus" (Point 5)
Anlauf questions why we even need to test for absence of warning. This
reinforces that the test should simply be: compile succeeds, no warnings.
The very existence of the warning was the bug.

### On Verbose Comments (Point 6)
**Action needed**: Condense source code comments. Keep essential information,
remove redundant explanations.

### On "fully" (Point 7)
**Action needed**: Remove "fully" from documentation. "preprocessed" already
implies complete preprocessing.

### On Warning for Contradicting Options (Point 8)
**Key discussion point**: Anlauf raises whether `-cpp -fpreprocessed` should
warn as contradicting options rather than being silently handled.

**Arguments for silent handling (current approach)**:
- cmake and similar tools may pass both flags
- `-fpreprocessed` has clear semantics: input is already preprocessed
- User intent is clear: "I know it is preprocessed, do not reprocess"
- No information is lost; behavior is well-defined

**Arguments for warning**:
- The combination is unusual and might indicate user error
- Makes the interaction more visible to users

**Recommendation**: Keep silent handling but improve documentation. The cmake
use case is real and common. A warning would just add noise for legitimate
workflows.

## Proposed Patch Changes

1. **Test case**: Remove `dg-bogus` lines; rely on clean compilation
2. **Test case**: Add fixed-form variant with `c` comment character
3. **Source comments**: Condense to essential information only
4. **Documentation**: Remove "fully" from "fully preprocessed"
5. **Documentation**: Perhaps add note that the combination is intentionally
   supported for build systems like cmake

## Questions for User

Before implementing changes:

1. Do you agree with removing `dg-bogus` and relying on clean compilation?
2. Should we add a fixed-form test variant, or is free-form sufficient?
3. On Anlauf's suggestion about warning for contradicting options - should we
   engage in that discussion or keep the current silent handling approach?
