# Test Suite Failures Summary

## Current Status

✅ **No unexpected test failures** as of the full `make -j32 -k check-gfortran` run on 2025-11-15.

- Expected passes: 3392
- Unexpected failures: 0
- Unsupported: 2

All previously failing finalization tests (finalize_43/47/51/55/56 and finalize_constructor_1) now pass at every optimization level after guarding duplicate finalizations.

## Notes

- Regression tracking for finalize_39/41/42/45/47/48/49 is closed; behavior matches ISO/IEC 1539-1:2018 §7.5.6.3 and matches Intel ifx / NVIDIA nvfortran outputs.
- This document will be updated again if future runs surface new failures.
