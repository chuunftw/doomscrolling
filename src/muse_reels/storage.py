"""Local request records and Windows user-bound encrypted credential storage."""
import ctypes
import json
import os
import re
import secrets
from pathlib import Path
from ctypes import wintypes


def beneath(root, name):
    root = Path(root).expanduser().resolve()
    target = (root / name).resolve()
    if target == root or root not in target.parents:
        raise ValueError('path escapes the selected local folder')
    return target


def atomic_write(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = beneath(path.parent, '.stage-' + secrets.token_hex(16))
    try:
        with temporary.open('xb') as output:
            output.write(payload)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path, value):
    atomic_write(path, json.dumps(value, indent=2, ensure_ascii=False).encode('utf-8'))


def validate_cookie(value):
    # Only the required Muse cookie is accepted, never a general browser jar.
    if not isinstance(value, str) or not re.fullmatch(r'[!-:<-~]{16,16384}', value) or ';' in value or ',' in value:
        raise ValueError('enter only the hatch_sess value, with no cookie name, whitespace or additional cookies')
    return value


class Blob(ctypes.Structure):
    _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_ubyte))]


def dpapi(value, decrypt=False):
    if os.name != 'nt':
        raise RuntimeError('Windows DPAPI is required; no plaintext credential fallback is provided')
    buffer = ctypes.create_string_buffer(value, len(value))
    source = Blob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    if decrypt:
        fn = crypt.CryptUnprotectData
        fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                       ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        arguments = (ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output))
    else:
        fn = crypt.CryptProtectData
        fn.argtypes = [ctypes.POINTER(Blob), wintypes.LPCWSTR, ctypes.c_void_p, ctypes.c_void_p,
                       ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        arguments = (ctypes.byref(source), 'Muse Reels session', None, None, None, 1, ctypes.byref(output))
    fn.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    try:
        if not fn(*arguments):
            raise RuntimeError('Windows credential encryption failed; no plaintext file was written')
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        if output.pbData:
            kernel.LocalFree(output.pbData)
        ctypes.memset(buffer, 0, len(value))


def save_cookie(path, value, overwrite=False):
    value = validate_cookie(value)
    path = Path(path)
    if path.suffix.lower() != '.dpapi' or path.is_symlink():
        raise ValueError('choose a regular .dpapi encrypted credential file')
    if path.exists() and not overwrite:
        raise FileExistsError('encrypted credential already exists; explicit --replace is required')
    encrypted = dpapi(value.encode('utf-8'))
    atomic_write(path, encrypted)  # No plaintext cookie, .bak, or secret in argv/logs.


def load_cookie(path):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > 100_000:
        raise ValueError('invalid encrypted credential file')
    return 'hatch_sess=' + validate_cookie(dpapi(path.read_bytes(), decrypt=True).decode('utf-8'))
