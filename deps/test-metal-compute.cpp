// Test Metal compute kernel execution
#define NS_PRIVATE_IMPLEMENTATION
#define MTL_PRIVATE_IMPLEMENTATION
#include "metal-cpp/Metal/Metal.hpp"
#include "metal-cpp/Foundation/Foundation.hpp"
#include <cstdio>
#include <cmath>

int main() {
    const size_t N = 1024;

    // Create device and queue
    MTL::Device* device = MTL::CreateSystemDefaultDevice();
    if (!device) {
        printf("ERROR: No Metal device found\n");
        return 1;
    }
    printf("Device: %s\n", device->name()->utf8String());

    MTL::CommandQueue* queue = device->newCommandQueue();

    // Load metallib
    NS::Error* error = nullptr;
    NS::String* libPath = NS::String::string("vector_add.metallib", NS::UTF8StringEncoding);
    NS::URL* libURL = NS::URL::fileURLWithPath(libPath);
    MTL::Library* library = device->newLibrary(libURL, &error);
    if (!library) {
        printf("ERROR: Failed to load metallib: %s\n",
               error ? error->localizedDescription()->utf8String() : "unknown");
        return 1;
    }
    printf("Library loaded\n");

    // Get kernel function
    NS::String* funcName = NS::String::string("vector_add", NS::UTF8StringEncoding);
    MTL::Function* function = library->newFunction(funcName);
    if (!function) {
        printf("ERROR: Function 'vector_add' not found\n");
        return 1;
    }
    printf("Function found\n");

    // Create compute pipeline
    MTL::ComputePipelineState* pipeline = device->newComputePipelineState(function, &error);
    if (!pipeline) {
        printf("ERROR: Failed to create pipeline: %s\n",
               error ? error->localizedDescription()->utf8String() : "unknown");
        return 1;
    }
    printf("Pipeline created (max threads/group: %lu)\n", pipeline->maxTotalThreadsPerThreadgroup());

    // Allocate buffers
    size_t bufferSize = N * sizeof(float);
    MTL::Buffer* bufferA = device->newBuffer(bufferSize, MTL::ResourceStorageModeShared);
    MTL::Buffer* bufferB = device->newBuffer(bufferSize, MTL::ResourceStorageModeShared);
    MTL::Buffer* bufferResult = device->newBuffer(bufferSize, MTL::ResourceStorageModeShared);

    // Initialize input data
    float* a = static_cast<float*>(bufferA->contents());
    float* b = static_cast<float*>(bufferB->contents());
    for (size_t i = 0; i < N; i++) {
        a[i] = static_cast<float>(i);
        b[i] = static_cast<float>(i * 2);
    }
    printf("Input data initialized\n");

    // Create command buffer and encoder
    MTL::CommandBuffer* cmdBuffer = queue->commandBuffer();
    MTL::ComputeCommandEncoder* encoder = cmdBuffer->computeCommandEncoder();

    encoder->setComputePipelineState(pipeline);
    encoder->setBuffer(bufferA, 0, 0);
    encoder->setBuffer(bufferB, 0, 1);
    encoder->setBuffer(bufferResult, 0, 2);

    // Dispatch threads
    MTL::Size gridSize = MTL::Size(N, 1, 1);
    MTL::Size threadgroupSize = MTL::Size(std::min(N, pipeline->maxTotalThreadsPerThreadgroup()), 1, 1);
    encoder->dispatchThreads(gridSize, threadgroupSize);
    encoder->endEncoding();

    // Execute and wait
    cmdBuffer->commit();
    cmdBuffer->waitUntilCompleted();
    printf("Kernel executed\n");

    // Verify results
    float* result = static_cast<float*>(bufferResult->contents());
    int errors = 0;
    for (size_t i = 0; i < N; i++) {
        float expected = a[i] + b[i];
        if (std::fabs(result[i] - expected) > 1e-5) {
            if (errors < 5) {
                printf("ERROR at %zu: got %f, expected %f\n", i, result[i], expected);
            }
            errors++;
        }
    }

    if (errors == 0) {
        printf("\nSUCCESS: All %zu results correct!\n", N);
        printf("Sample: result[0]=%f (expected %f)\n", result[0], a[0] + b[0]);
        printf("Sample: result[%zu]=%f (expected %f)\n", N-1, result[N-1], a[N-1] + b[N-1]);
    } else {
        printf("\nFAILED: %d errors\n", errors);
    }

    // Cleanup
    bufferResult->release();
    bufferB->release();
    bufferA->release();
    pipeline->release();
    function->release();
    library->release();
    queue->release();
    device->release();

    return errors > 0 ? 1 : 0;
}
