"""Windows native handle primitives for no-reparse, directory-relative file operations.

This module is intentionally a low-level primitive. It does not modify the
backup-first executor policy until its Windows CI and adversarial tests pass.
All mutation helpers require already-open directory handles and single basenames.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Any


class WindowsHandleError(RuntimeError):
    """A native Windows handle operation failed or could not be verified."""


class WindowsDirectoryHandleBackend:
    """Use NtCreateFile RootDirectory handles and handle-relative rename on Windows."""

    OBJ_CASE_INSENSITIVE = 0x00000040

    FILE_LIST_DIRECTORY = 0x0001
    FILE_TRAVERSE = 0x0020
    FILE_READ_ATTRIBUTES = 0x0080
    FILE_READ_DATA = 0x0001
    FILE_WRITE_DATA = 0x0002
    DELETE = 0x00010000
    SYNCHRONIZE = 0x00100000

    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002

    FILE_OPEN = 0x00000001
    FILE_CREATE = 0x00000002

    FILE_DIRECTORY_FILE = 0x00000001
    FILE_NON_DIRECTORY_FILE = 0x00000040
    FILE_OPEN_REPARSE_POINT = 0x00200000
    FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020

    FILE_ATTRIBUTE_NORMAL = 0x00000080
    FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    FILE_ATTRIBUTE_TAG_INFO_CLASS = 9
    FILE_RENAME_INFO_CLASS = 3
    FILE_RENAME_INFO_EX_CLASS = 22
    FILE_RENAME_REPLACE_IF_EXISTS = 0x00000001

    _BASENAME_RE = re.compile(r"^[^\\/:*?\"<>|\x00]+$")

    def __init__(self) -> None:
        if os.name != "nt":
            raise WindowsHandleError("Native Windows handles are available only on Windows.")
        import ctypes
        from ctypes import wintypes

        self.ctypes = ctypes
        self.wintypes = wintypes
        self.ntdll = ctypes.WinDLL("ntdll")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        class UNICODE_STRING(ctypes.Structure):
            _fields_ = [
                ("Length", wintypes.USHORT),
                ("MaximumLength", wintypes.USHORT),
                ("Buffer", wintypes.LPWSTR),
            ]

        class OBJECT_ATTRIBUTES(ctypes.Structure):
            _fields_ = [
                ("Length", wintypes.ULONG),
                ("RootDirectory", wintypes.HANDLE),
                ("ObjectName", ctypes.POINTER(UNICODE_STRING)),
                ("Attributes", wintypes.ULONG),
                ("SecurityDescriptor", wintypes.LPVOID),
                ("SecurityQualityOfService", wintypes.LPVOID),
            ]

        class IO_STATUS_BLOCK(ctypes.Structure):
            _fields_ = [
                ("Status", ctypes.c_void_p),
                ("Information", ctypes.c_size_t),
            ]

        class FILE_ATTRIBUTE_TAG_INFO(ctypes.Structure):
            _fields_ = [
                ("FileAttributes", wintypes.DWORD),
                ("ReparseTag", wintypes.DWORD),
            ]

        class FILE_RENAME_INFO(ctypes.Structure):
            _fields_ = [
                ("ReplaceIfExists", wintypes.BOOLEAN),
                ("RootDirectory", wintypes.HANDLE),
                ("FileNameLength", wintypes.DWORD),
                ("FileName", ctypes.c_wchar * 1),
            ]

        class FILE_RENAME_INFO_EX(ctypes.Structure):
            _fields_ = [
                ("Flags", wintypes.DWORD),
                ("RootDirectory", wintypes.HANDLE),
                ("FileNameLength", wintypes.DWORD),
                ("FileName", ctypes.c_wchar * 1),
            ]

        self.UNICODE_STRING = UNICODE_STRING
        self.OBJECT_ATTRIBUTES = OBJECT_ATTRIBUTES
        self.IO_STATUS_BLOCK = IO_STATUS_BLOCK
        self.FILE_ATTRIBUTE_TAG_INFO = FILE_ATTRIBUTE_TAG_INFO
        self.FILE_RENAME_INFO = FILE_RENAME_INFO
        self.FILE_RENAME_INFO_EX = FILE_RENAME_INFO_EX

        self.ntdll.NtCreateFile.argtypes = [
            ctypes.POINTER(wintypes.HANDLE),
            wintypes.DWORD,
            ctypes.POINTER(OBJECT_ATTRIBUTES),
            ctypes.POINTER(IO_STATUS_BLOCK),
            ctypes.c_void_p,
            wintypes.ULONG,
            wintypes.ULONG,
            wintypes.ULONG,
            wintypes.ULONG,
            ctypes.c_void_p,
            wintypes.ULONG,
        ]
        self.ntdll.NtCreateFile.restype = ctypes.c_long
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        self.kernel32.GetFileInformationByHandleEx.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
        ]
        self.kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
        self.kernel32.ReadFile.argtypes = [
            wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p
        ]
        self.kernel32.ReadFile.restype = wintypes.BOOL
        self.kernel32.WriteFile.argtypes = [
            wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p
        ]
        self.kernel32.WriteFile.restype = wintypes.BOOL
        self.kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
        self.kernel32.FlushFileBuffers.restype = wintypes.BOOL
        self.kernel32.SetFileInformationByHandle.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
        ]
        self.kernel32.SetFileInformationByHandle.restype = wintypes.BOOL
        self.kernel32.GetFileSizeEx.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(ctypes.c_longlong)
        ]
        self.kernel32.GetFileSizeEx.restype = wintypes.BOOL

    def _raise_last_error(self, operation: str) -> None:
        code = self.ctypes.get_last_error()
        raise WindowsHandleError(f"{operation} failed with Win32 error {code}.")

    def _validate_basename(self, name: str) -> str:
        if (
            not isinstance(name, str)
            or not name
            or name in {".", ".."}
            or not self._BASENAME_RE.fullmatch(name)
            or name.endswith((" ", "."))
        ):
            raise WindowsHandleError("A single safe Windows basename is required.")
        return name

    def _nt_open(
        self,
        root_handle: Any,
        name: str,
        *,
        access: int,
        disposition: int,
        options: int,
    ) -> Any:
        ctypes = self.ctypes
        wintypes = self.wintypes
        buffer = ctypes.create_unicode_buffer(name)
        encoded_length = len(name.encode("utf-16-le"))
        unicode_name = self.UNICODE_STRING(
            encoded_length,
            encoded_length + 2,
            ctypes.cast(buffer, wintypes.LPWSTR),
        )
        attributes = self.OBJECT_ATTRIBUTES()
        attributes.Length = ctypes.sizeof(self.OBJECT_ATTRIBUTES)
        attributes.RootDirectory = root_handle if root_handle else None
        attributes.ObjectName = ctypes.pointer(unicode_name)
        attributes.Attributes = self.OBJ_CASE_INSENSITIVE
        io_status = self.IO_STATUS_BLOCK()
        handle = wintypes.HANDLE()
        status = self.ntdll.NtCreateFile(
            ctypes.byref(handle),
            access,
            ctypes.byref(attributes),
            ctypes.byref(io_status),
            None,
            self.FILE_ATTRIBUTE_NORMAL,
            self.FILE_SHARE_READ | self.FILE_SHARE_WRITE,
            disposition,
            options,
            None,
            0,
        )
        if status < 0:
            raise WindowsHandleError(
                f"NtCreateFile failed with NTSTATUS 0x{status & 0xFFFFFFFF:08X}."
            )
        if not handle.value:
            raise WindowsHandleError("NtCreateFile returned an empty handle.")
        try:
            self._assert_not_reparse(handle)
        except Exception:
            self.close(handle)
            raise
        return handle

    def _assert_not_reparse(self, handle: Any) -> None:
        info = self.FILE_ATTRIBUTE_TAG_INFO()
        ok = self.kernel32.GetFileInformationByHandleEx(
            handle,
            self.FILE_ATTRIBUTE_TAG_INFO_CLASS,
            self.ctypes.byref(info),
            self.ctypes.sizeof(info),
        )
        if not ok:
            self._raise_last_error("GetFileInformationByHandleEx(FileAttributeTagInfo)")
        if info.FileAttributes & self.FILE_ATTRIBUTE_REPARSE_POINT:
            raise WindowsHandleError("Reparse-point handles are denied.")

    def open_root(self, root_path: str | Path) -> Any:
        raw_path = Path(root_path).expanduser()
        if ".." in raw_path.parts:
            raise WindowsHandleError("Parent traversal is denied in the repository root path.")
        path = raw_path.absolute()
        if not path.is_dir() or not path.drive or str(path).startswith("\\\\"):
            raise WindowsHandleError("A local absolute directory path is required.")
        access = (
            self.FILE_LIST_DIRECTORY
            | self.FILE_TRAVERSE
            | self.FILE_READ_ATTRIBUTES
            | self.SYNCHRONIZE
        )
        # Start at the drive root and resolve each component relative to the
        # previous handle. FILE_OPEN_REPARSE_POINT opens the entry itself;
        # _assert_not_reparse then rejects it rather than following a junction.
        current = self._nt_open(
            None,
            "\\??\\" + path.anchor,
            access=access,
            disposition=self.FILE_OPEN,
            options=(
                self.FILE_DIRECTORY_FILE
                | self.FILE_SYNCHRONOUS_IO_NONALERT
                | self.FILE_OPEN_REPARSE_POINT
            ),
        )
        try:
            for component in path.parts[1:]:
                child = self.open_child_directory(current, component)
                self.close(current)
                current = child
            return current
        except Exception:
            self.close(current)
            raise

    def open_child_directory(self, parent_handle: Any, name: str) -> Any:
        name = self._validate_basename(name)
        access = (
            self.FILE_LIST_DIRECTORY
            | self.FILE_TRAVERSE
            | self.FILE_READ_ATTRIBUTES
            | self.FILE_WRITE_DATA
            | self.FILE_DELETE_CHILD
            | self.SYNCHRONIZE
        )
        return self._nt_open(
            parent_handle,
            name,
            access=access,
            disposition=self.FILE_OPEN,
            options=self.FILE_DIRECTORY_FILE | self.FILE_SYNCHRONOUS_IO_NONALERT | self.FILE_OPEN_REPARSE_POINT,
        )

    def open_file(self, parent_handle: Any, name: str, *, writable: bool = False) -> Any:
        name = self._validate_basename(name)
        access = self.FILE_READ_ATTRIBUTES | self.SYNCHRONIZE
        if writable:
            access |= self.FILE_READ_DATA | self.FILE_WRITE_DATA | self.DELETE
        else:
            access |= 0x80000000  # GENERIC_READ
        return self._nt_open(
            parent_handle,
            name,
            access=access,
            disposition=self.FILE_OPEN,
            options=self.FILE_NON_DIRECTORY_FILE | self.FILE_SYNCHRONOUS_IO_NONALERT | self.FILE_OPEN_REPARSE_POINT,
        )

    def create_file(self, parent_handle: Any, name: str) -> Any:
        name = self._validate_basename(name)
        access = self.FILE_READ_DATA | self.FILE_WRITE_DATA | self.FILE_READ_ATTRIBUTES | self.DELETE | self.SYNCHRONIZE
        return self._nt_open(
            parent_handle,
            name,
            access=access,
            disposition=self.FILE_CREATE,
            options=self.FILE_NON_DIRECTORY_FILE | self.FILE_SYNCHRONOUS_IO_NONALERT,
        )

    def create_directory(self, parent_handle: Any, name: str) -> Any:
        name = self._validate_basename(name)
        access = (
            self.FILE_LIST_DIRECTORY
            | self.FILE_TRAVERSE
            | self.FILE_READ_ATTRIBUTES
            | self.FILE_WRITE_DATA
            | self.FILE_DELETE_CHILD
            | self.SYNCHRONIZE
        )
        return self._nt_open(
            parent_handle,
            name,
            access=access,
            disposition=self.FILE_CREATE,
            options=self.FILE_DIRECTORY_FILE | self.FILE_SYNCHRONOUS_IO_NONALERT,
        )

    def read_all(self, handle: Any, *, max_bytes: int) -> bytes:
        size = self.ctypes.c_longlong()
        if not self.kernel32.GetFileSizeEx(handle, self.ctypes.byref(size)):
            self._raise_last_error("GetFileSizeEx")
        if size.value < 0 or size.value > max_bytes:
            raise WindowsHandleError("File exceeds the configured size limit.")
        chunks: list[bytes] = []
        total = 0
        while total < size.value:
            amount = min(65536, size.value - total)
            buffer = self.ctypes.create_string_buffer(amount)
            read = self.wintypes.DWORD()
            if not self.kernel32.ReadFile(handle, buffer, amount, self.ctypes.byref(read), None):
                self._raise_last_error("ReadFile")
            if read.value == 0:
                break
            chunks.append(buffer.raw[:read.value])
            total += read.value
        if total != size.value:
            raise WindowsHandleError("File changed or ended during the bounded read.")
        return b"".join(chunks)

    def write_all(self, handle: Any, data: bytes) -> None:
        offset = 0
        while offset < len(data):
            chunk = data[offset : offset + 65536]
            buffer = self.ctypes.create_string_buffer(chunk)
            written = self.wintypes.DWORD()
            if not self.kernel32.WriteFile(
                handle, buffer, len(chunk), self.ctypes.byref(written), None
            ):
                self._raise_last_error("WriteFile")
            if written.value <= 0:
                raise WindowsHandleError("WriteFile returned a zero-length write.")
            offset += written.value
        if not self.kernel32.FlushFileBuffers(handle):
            self._raise_last_error("FlushFileBuffers")

    def rename_relative(
        self,
        source_handle: Any,
        parent_handle: Any,
        target_name: str,
        *,
        replace_existing: bool,
    ) -> None:
        target_name = self._validate_basename(target_name)
        encoded = target_name.encode("utf-16-le")
        header_size = 20 if self.ctypes.sizeof(self.wintypes.HANDLE) == 8 else 12
        buffer_size = header_size + len(encoded)
        buffer = self.ctypes.create_string_buffer(buffer_size)
        info = self.ctypes.cast(
            buffer, self.ctypes.POINTER(self.FILE_RENAME_INFO_EX)
        ).contents
        info.Flags = self.FILE_RENAME_REPLACE_IF_EXISTS if replace_existing else 0
        info.RootDirectory = parent_handle.value
        info.FileNameLength = len(encoded)
        self.ctypes.memmove(
            self.ctypes.addressof(buffer) + header_size, encoded, len(encoded)
        )
        if not self.kernel32.SetFileInformationByHandle(
            source_handle,
            self.FILE_RENAME_INFO_EX_CLASS,
            buffer,
            buffer_size,
        ):
            self._raise_last_error("SetFileInformationByHandle(FileRenameInfoEx)")


    def close(self, handle: Any) -> None:
        if handle and getattr(handle, "value", handle):
            if not self.kernel32.CloseHandle(handle):
                self._raise_last_error("CloseHandle")
