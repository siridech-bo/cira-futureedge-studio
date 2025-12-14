/**
 * CiRA FutureEdge Studio - Configuration
 * Target: cortex-m4
 */

#ifndef CONFIG_H
#define CONFIG_H

// Platform settings
#define TARGET_PLATFORM "cortex-m4"
#define WINDOW_SIZE 128
#define SAMPLE_RATE 1000

// Memory settings
#define MEMORY_LIMIT_KB 64
#define USE_FIXED_POINT 1
#define FIXED_POINT_BITS 16

// Optimization
#define OPTIMIZE_SIZE 1

#endif // CONFIG_H
