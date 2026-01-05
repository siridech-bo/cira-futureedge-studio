# Third-Party WebSocket Dependencies

## uWebSockets

**License**: Apache 2.0
**Repository**: https://github.com/uNetworking/uWebSockets
**Version**: v20.x (latest)

### Installation Instructions

uWebSockets is a header-only library. To install:

```bash
# Clone uWebSockets
cd third_party
git clone --depth 1 https://github.com/uNetworking/uWebSockets.git

# Clone uSockets dependency
git clone --depth 1 https://github.com/uNetworking/uSockets.git
```

### Build uSockets

```bash
cd uSockets
make
```

This will create `uSockets.a` static library.

## msgpack-c

**License**: Boost Software License
**Repository**: https://github.com/msgpack/msgpack-c
**Version**: cpp-6.x

### Installation Instructions

msgpack-c is header-only for C++11 and above:

```bash
cd third_party
git clone --depth 1 https://github.com/msgpack/msgpack-c.git
```

## Integration

After downloading these libraries, the CMakeLists.txt will automatically detect and include them.
