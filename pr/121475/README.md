# PR 121475: Missed finalization

Related to PR 121472 (finalization issues).

## Summary

Function result not finalized after assignment when using defined assignment
from parent class.

## Bug

For `i=rm()`:
1. Destructor should be called on `i` (LHS finalization)
2. `rm()` constructor creates function result
3. Defined assignment copies to `i`
4. Function result should be finalized (MISSED)

## Expected (ifort)

```
construct our instance
type(rm) constructor called
type(rm) destructor called      <- LHS finalized
class(r) assignment(=) called
type(rm) destructor called      <- function result finalized
finished
type(rm) destructor called      <- end block
```

## Actual (gfortran)

```
construct our instance
type(rm) constructor called
type(rm) destructor called      <- LHS finalized
class(r) assignment(=) called
finished                        <- MISSING: function result finalization
type(rm) destructor called      <- end block
```

## Key factors

- Defined assignment in parent class `r`
- Finalizer in derived type `rm`
- Function result of type `rm`

## Standard reference

ISO/IEC 1539-1:2018 7.5.6.3: Function results finalized after use.
