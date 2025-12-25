// Minimal Metal test - device enumeration and buffer allocation
#define NS_PRIVATE_IMPLEMENTATION
#define MTL_PRIVATE_IMPLEMENTATION
#include "metal-cpp/Metal/Metal.hpp"
#include "metal-cpp/Foundation/Foundation.hpp"
#include <cstdio>

int main() {
    // Get default device
    MTL::Device* device = MTL::CreateSystemDefaultDevice();
    if (!device) {
        printf("ERROR: No Metal device found\n");
        return 1;
    }

    printf("Metal device: %s\n", device->name()->utf8String());
    printf("Unified memory: %s\n", device->hasUnifiedMemory() ? "yes" : "no");
    printf("Max buffer length: %lu MB\n", device->maxBufferLength() / (1024*1024));

    // Test buffer allocation
    const size_t bufferSize = 1024 * sizeof(float);
    MTL::Buffer* buffer = device->newBuffer(bufferSize, MTL::ResourceStorageModeShared);
    if (!buffer) {
        printf("ERROR: Failed to allocate buffer\n");
        device->release();
        return 1;
    }

    printf("Buffer allocated: %lu bytes at %p\n", buffer->length(), buffer->contents());

    // Write test data
    float* data = static_cast<float*>(buffer->contents());
    for (int i = 0; i < 1024; i++) {
        data[i] = static_cast<float>(i);
    }
    printf("Data written: first=%f, last=%f\n", data[0], data[1023]);

    // Create command queue
    MTL::CommandQueue* queue = device->newCommandQueue();
    if (!queue) {
        printf("ERROR: Failed to create command queue\n");
        buffer->release();
        device->release();
        return 1;
    }
    printf("Command queue created\n");

    // Cleanup
    queue->release();
    buffer->release();
    device->release();

    printf("\nSUCCESS: Metal runtime is working\n");
    return 0;
}
