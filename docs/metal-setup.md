# Metal Development Environment Setup (macOS)

## Prerequisites

- macOS with Apple Silicon or Intel Mac with Metal support
- Xcode installed (full Xcode.app, not just Command Line Tools)

## 1. Install Metal Toolchain

The Metal compiler requires the Metal Toolchain component:

```bash
# Set DEVELOPER_DIR to use Xcode (not Command Line Tools)
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer

# Download Metal Toolchain (about 700 MB)
xcodebuild -downloadComponent MetalToolchain

# Verify installation
xcrun -sdk macosx metal --version
```

Expected output:
```
Apple metal version 32023.850 (metalfe-32023.850.10)
Target: air64-apple-darwin25.2.0
```

**Note:** If `xcode-select -p` returns `/Library/Developer/CommandLineTools`, you must either:
- Run `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer`, or
- Set `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer` before each command

## 2. Download metal-cpp

metal-cpp is Apple's header-only C++ wrapper for Metal (Apache 2.0 license):

```bash
mkdir -p deps && cd deps
curl -L -o metal-cpp.zip \
  "https://developer.apple.com/metal/cpp/files/metal-cpp_macOS15.2_iOS18.2.zip"
unzip -o metal-cpp.zip
```

## 3. Verify Setup

### Test 1: Device Enumeration

Create `test-metal.cpp`:

```cpp
#define NS_PRIVATE_IMPLEMENTATION
#define MTL_PRIVATE_IMPLEMENTATION
#include "metal-cpp/Metal/Metal.hpp"
#include "metal-cpp/Foundation/Foundation.hpp"
#include <cstdio>

int main() {
    MTL::Device* device = MTL::CreateSystemDefaultDevice();
    if (!device) {
        printf("ERROR: No Metal device found\n");
        return 1;
    }
    printf("Device: %s\n", device->name()->utf8String());
    printf("Unified memory: %s\n", device->hasUnifiedMemory() ? "yes" : "no");
    device->release();
    return 0;
}
```

Compile and run:

```bash
clang++ -std=c++17 -I./metal-cpp -framework Metal -framework Foundation \
  test-metal.cpp -o test-metal
./test-metal
```

Expected output (Apple Silicon):
```
Device: Apple M3 Ultra
Unified memory: yes
```

### Test 2: Compute Shader

Create `vector_add.metal`:

```metal
kernel void vector_add(
    device const float* a [[buffer(0)]],
    device const float* b [[buffer(1)]],
    device float* result [[buffer(2)]],
    uint id [[thread_position_in_grid]])
{
    result[id] = a[id] + b[id];
}
```

Compile to metallib:

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
xcrun -sdk macosx metal -c vector_add.metal -o vector_add.air
xcrun -sdk macosx metallib vector_add.air -o vector_add.metallib
```

## 4. Build Configuration for GCC Plugin

When building the Metal plugin for libgomp, use:

```makefile
METAL_CPP_PATH = $(srcdir)/../deps/metal-cpp
METAL_CXXFLAGS = -std=c++17 -I$(METAL_CPP_PATH)
METAL_LDFLAGS = -framework Metal -framework Foundation
```

## Verified Working Configuration

| Component | Version |
|-----------|---------|
| macOS | 15.2 (Sequoia) |
| Xcode | 16.2 |
| Metal Toolchain | 17C48 |
| metal-cpp | macOS15.2_iOS18.2 |
| Hardware | Apple M3 Ultra |

## Troubleshooting

### "metal: command not found" or "missing Metal Toolchain"

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
xcodebuild -downloadComponent MetalToolchain
```

### "No Metal device found"

- Ensure running on Mac with Metal support
- Check `system_profiler SPDisplaysDataType | grep Metal`

### Include errors with metal-cpp

Use `-I./metal-cpp` (not `-I.`), the headers use `#include <Foundation/Foundation.hpp>`.
