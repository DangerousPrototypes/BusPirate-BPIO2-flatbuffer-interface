# BPIO2 FlatBuffer Tooling

This directory contains auto-generated FlatBuffer tooling for the BPIO2 protocol.

## Documentation

See the main [BPIO2 documentation](https://docs.buspirate.com/docs/binmode-reference/protocol-bpio2) for protocol details and usage examples.

See [flatc](https://flatbuffers.dev/quick_start/) for language-specific usage instructions.

## Source Schema
- Schema file: bpio.fbs
- Generated on: Wed Feb  4 16:29:32 CET 2026

## Generated Languages

- **C**: `c/tooling/`
- **Cpp**: `cpp/tooling/`
- **Csharp**: `csharp/tooling/`
- **Dart**: `dart/tooling/`
- **Go**: `go/tooling/`
- **Java**: `java/tooling/`
- **Kotlin**: `kotlin/tooling/`
- **Lobster**: `lobster/tooling/`
- **Php**: `php/tooling/`
- **Python**: `python/tooling/`
- **Rust**: `rust/tooling/`
- **Swift**: `swift/tooling/`
- **Typescript**: `typescript/tooling/`

## Usage

Each language directory contains the generated FlatBuffer code for that language.
Include the appropriate files in your project according to your language's conventions.

See [flatc](https://flatbuffers.dev/quick_start/) for language-specific usage instructions.

## Flat Buffer Includes

In addition to the generated tooling, you will need to include the flat buffer support library for your language in the /include/ folder.

## Compilers Used
- **flatc**: For C++, C#, Dart, Go, Java, JavaScript, Kotlin, Lobster, Lua, PHP, Python, Rust, Swift, TypeScript
- **flatcc**: For C 

Javascript is deprecated in the latest flatc. Instead transpile from TypeScript to JavaScript if needed.

## Example Usage

### Python
```python
# Add the python/tooling directory to your Python path
import sys
sys.path.append('python/tooling')

# Import generated modules
from StatusRequest import StatusRequest
from StatusResponse import StatusResponse
```

### C
```c
// Include the generated headers
#include "bpio2_reader.h"
#include "bpio2_builder.h"
```
