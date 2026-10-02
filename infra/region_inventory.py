"""Read-only Linear v1 header/slot validation; no conversion or world writes."""
import ctypes
import ctypes.util
import struct
import zlib

SIGNATURE = 0xc3ff13183cca9d9a
MAX_BODY = 512 * 1024 * 1024


def linear_header(path):
    with path.open('rb') as stream:
        header = stream.read(32)
    if len(header) != 32:
        raise ValueError(f'Short Linear header: {path}')
    magic, version, timestamp, level, count, length, checksum = struct.unpack('>QBQBHIQ', header)
    if magic != SIGNATURE or version != 1 or count > 1024 or length > MAX_BODY:
        raise ValueError(f'Unsupported/invalid Linear header: {path}')
    if path.stat().st_size != length + 40:
        raise ValueError(f'Incomplete Linear region: {path}')
    return count, length, checksum


def _read_linear(path, include_payloads):
    count, length, checksum = linear_header(path)
    with path.open('rb') as stream:
        stream.seek(32)
        compressed = stream.read(length)
        footer = stream.read(8)
    if footer != SIGNATURE.to_bytes(8, 'big') or (checksum and zlib.crc32(compressed) != checksum):
        raise ValueError(f'Linear checksum/footer mismatch: {path}')
    library = ctypes.util.find_library('zstd')
    if not library:
        raise RuntimeError('Linear inventory requires libzstd')
    native = ctypes.CDLL(library)
    native.ZSTD_getFrameContentSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    native.ZSTD_getFrameContentSize.restype = ctypes.c_ulonglong
    native.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
    native.ZSTD_decompress.restype = ctypes.c_size_t
    native.ZSTD_isError.argtypes = [ctypes.c_size_t]
    native.ZSTD_isError.restype = ctypes.c_uint
    source = ctypes.create_string_buffer(compressed)
    size = native.ZSTD_getFrameContentSize(source, len(compressed))
    if size < 8192 or size > MAX_BODY:
        raise ValueError(f'Invalid/oversized Linear body: {path}')
    target = ctypes.create_string_buffer(size)
    decoded = native.ZSTD_decompress(target, size, source, len(compressed))
    if native.ZSTD_isError(decoded) or decoded != size:
        raise ValueError(f'Linear decompression failed: {path}')
    directory = ctypes.string_at(target, 8192)
    sizes = [struct.unpack_from('>I', directory, slot*8)[0] for slot in range(1024)]
    slots = [slot for slot, size in enumerate(sizes) if size]
    if len(slots) != count or sum(sizes) + 8192 != decoded:
        raise ValueError(f'Linear chunk directory mismatch: {path}')
    if not include_payloads:
        return slots
    body = ctypes.string_at(target, decoded)
    offset = 8192
    payloads = {}
    for slot, size in enumerate(sizes):
        if size:
            payloads[slot] = body[offset:offset + size]
            offset += size
    return payloads


def linear_payloads(path):
    return _read_linear(path, True)


def linear_slots(path):
    return _read_linear(path, False)
