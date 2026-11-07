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

    FILE_PERSISTENT_ACLS = 0x00000008

    READ_CONTROL = 0x00020000
    SE_FILE_OBJECT = 1
    OWNER_SECURITY_INFORMATION = 0x00000001
    DACL_SECURITY_INFORMATION = 0x00000004
    TOKEN_QUERY = 0x0008
    TOKEN_USER_CLASS = 1
    ACL_SIZE_INFORMATION_CLASS = 2
    ACCESS_ALLOWED_ACE_TYPE = 0
    ACCESS_DENIED_ACE_TYPE = 1
    ACE_OBJECT_INHERIT = 0x01
    ACE_CONTAINER_INHERIT = 0x02
    GENERIC_ALL = 0x10000000
    FILE_ALL_ACCESS = 0x001F01FF
    WELL_KNOWN_BUILTIN_ADMINISTRATORS = 26
    WELL_KNOWN_LOCAL_SYSTEM = 22

    FILE_OPEN = 0x00000001
    FILE_CREATE = 0x00000002

    FILE_DIRECTORY_FILE = 0x00000001
    FILE_NON_DIRECTORY_FILE = 0x00000040
    FILE_OPEN_REPARSE_POINT = 0x00200000
    FILE_WRITE_THROUGH = 0x00000002
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

        class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("dwFileAttributes", wintypes.DWORD),
                ("ftCreationTime", wintypes.FILETIME),
                ("ftLastAccessTime", wintypes.FILETIME),
                ("ftLastWriteTime", wintypes.FILETIME),
                ("dwVolumeSerialNumber", wintypes.DWORD),
                ("nFileSizeHigh", wintypes.DWORD),
                ("nFileSizeLow", wintypes.DWORD),
                ("nNumberOfLinks", wintypes.DWORD),
                ("nFileIndexHigh", wintypes.DWORD),
                ("nFileIndexLow", wintypes.DWORD),
            ]

        class FILE_DISPOSITION_INFO(ctypes.Structure):
            _fields_ = [("DeleteFile", wintypes.BOOLEAN)]

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

        class ACL_SIZE_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("AceCount", wintypes.DWORD),
                ("AclBytesInUse", wintypes.DWORD),
                ("AclBytesFree", wintypes.DWORD),
            ]

        class ACE_HEADER(ctypes.Structure):
            _fields_ = [
                ("AceType", wintypes.BYTE),
                ("AceFlags", wintypes.BYTE),
                ("AceSize", wintypes.WORD),
            ]

        class SID_AND_ATTRIBUTES(ctypes.Structure):
            _fields_ = [
                ("Sid", ctypes.c_void_p),
                ("Attributes", wintypes.DWORD),
            ]

        class TOKEN_USER(ctypes.Structure):
            _fields_ = [("User", SID_AND_ATTRIBUTES)]

        self.ACL_SIZE_INFORMATION = ACL_SIZE_INFORMATION
        self.ACE_HEADER = ACE_HEADER
        self.TOKEN_USER = TOKEN_USER
        self.UNICODE_STRING = UNICODE_STRING
        self.OBJECT_ATTRIBUTES = OBJECT_ATTRIBUTES
        self.IO_STATUS_BLOCK = IO_STATUS_BLOCK
        self.FILE_ATTRIBUTE_TAG_INFO = FILE_ATTRIBUTE_TAG_INFO
        self.BY_HANDLE_FILE_INFORMATION = BY_HANDLE_FILE_INFORMATION
        self.FILE_DISPOSITION_INFO = FILE_DISPOSITION_INFO
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
        self.ntdll.NtSetInformationFile.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(IO_STATUS_BLOCK),
            ctypes.c_void_p,
            wintypes.ULONG,
            wintypes.ULONG,
        ]
        self.ntdll.NtSetInformationFile.restype = ctypes.c_long
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        self.kernel32.GetCurrentProcess.argtypes = []
        self.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        self.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        self.kernel32.LocalFree.restype = ctypes.c_void_p

        self.advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        self.advapi32.GetSecurityInfo.argtypes = [
            wintypes.HANDLE, ctypes.c_int, wintypes.DWORD,
            ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self.advapi32.GetSecurityInfo.restype = wintypes.DWORD
        self.advapi32.GetSecurityDescriptorDacl.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(wintypes.BOOL),
            ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.BOOL),
        ]
        self.advapi32.GetSecurityDescriptorDacl.restype = wintypes.BOOL
        self.advapi32.GetAclInformation.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.c_int
        ]
        self.advapi32.GetAclInformation.restype = wintypes.BOOL
        self.advapi32.GetAce.argtypes = [
            ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p)
        ]
        self.advapi32.GetAce.restype = wintypes.BOOL
        self.advapi32.OpenProcessToken.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)
        ]
        self.advapi32.OpenProcessToken.restype = wintypes.BOOL
        self.advapi32.GetTokenInformation.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
            wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
        ]
        self.advapi32.GetTokenInformation.restype = wintypes.BOOL
        self.advapi32.EqualSid.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self.advapi32.EqualSid.restype = wintypes.BOOL
        self.advapi32.CreateWellKnownSid.argtypes = [
            ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.POINTER(wintypes.DWORD)
        ]
        self.advapi32.CreateWellKnownSid.restype = wintypes.BOOL

        self.kernel32.GetVolumeInformationByHandleW.argtypes = [
            wintypes.HANDLE,
            wintypes.LPWSTR,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPWSTR,
            wintypes.DWORD,
        ]
        self.kernel32.GetVolumeInformationByHandleW.restype = wintypes.BOOL
        self.kernel32.GetFileInformationByHandleEx.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
        ]
        self.kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
        self.kernel32.GetFileInformationByHandle.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(BY_HANDLE_FILE_INFORMATION)
        ]
        self.kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
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
        self.kernel32.SetFilePointerEx.argtypes = [
            wintypes.HANDLE, ctypes.c_longlong, ctypes.POINTER(ctypes.c_longlong), wintypes.DWORD
        ]
        self.kernel32.SetFilePointerEx.restype = wintypes.BOOL
        self.kernel32.SetEndOfFile.argtypes = [wintypes.HANDLE]
        self.kernel32.SetEndOfFile.restype = wintypes.BOOL

    def _raise_last_error(self, operation: str) -> None:
        code = self.ctypes.get_last_error()
        raise WindowsHandleError(f"{operation} failed with Win32 error {code}.")

    def volume_information(self, handle: Any) -> dict[str, Any]:
        """Read filesystem capabilities from the already-pinned volume handle."""
        serial = self.wintypes.DWORD()
        flags = self.wintypes.DWORD()
        max_component = self.wintypes.DWORD()
        filesystem = self.ctypes.create_unicode_buffer(64)
        ok = self.kernel32.GetVolumeInformationByHandleW(
            handle,
            None,
            0,
            self.ctypes.byref(serial),
            self.ctypes.byref(max_component),
            self.ctypes.byref(flags),
            filesystem,
            len(filesystem),
        )
        if not ok:
            self._raise_last_error("GetVolumeInformationByHandleW")
        return {
            "filesystem": filesystem.value,
            "serial": int(serial.value),
            "flags": int(flags.value),
        }

    def _assert_supported_volume(self, handle: Any) -> None:
        info = self.volume_information(handle)
        if info["filesystem"].casefold() != "ntfs":
            raise WindowsHandleError(
                "Backup-first mutation requires NTFS write-through metadata semantics."
            )
        if not (info["flags"] & self.FILE_PERSISTENT_ACLS):
            raise WindowsHandleError(
                "Backup-first mutation requires a filesystem with persistent ACL enforcement."
            )
        if info["serial"] != self.file_identity(handle)[0]:
            raise WindowsHandleError("Volume identity changed while inspecting filesystem capabilities.")

    def assert_private_directory_acl(self, handle: Any) -> dict[str, int | bool]:
        """Require a backup directory ACL limited to the current user, SYSTEM and Administrators.

        This audits the effective DACL on the already-pinned directory handle.
        It deliberately rejects unsupported ACE forms, explicit deny ACEs,
        non-inheritable grants and grants to any other SID.
        """
        ctypes = self.ctypes
        wintypes = self.wintypes
        owner_sid = ctypes.c_void_p()
        dacl = ctypes.c_void_p()
        security_descriptor = ctypes.c_void_p()
        status = self.advapi32.GetSecurityInfo(
            handle,
            self.SE_FILE_OBJECT,
            self.OWNER_SECURITY_INFORMATION | self.DACL_SECURITY_INFORMATION,
            ctypes.byref(owner_sid),
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(security_descriptor),
        )
        if status != 0:
            raise WindowsHandleError(
                f"GetSecurityInfo(backup root) failed with Win32 error {status}."
            )

        token = wintypes.HANDLE()
        try:
            if not self.advapi32.OpenProcessToken(
                self.kernel32.GetCurrentProcess(),
                self.TOKEN_QUERY,
                ctypes.byref(token),
            ):
                self._raise_last_error("OpenProcessToken")
            token_buffer = ctypes.create_string_buffer(1024)
            returned = wintypes.DWORD()
            if not self.advapi32.GetTokenInformation(
                token,
                self.TOKEN_USER_CLASS,
                token_buffer,
                len(token_buffer),
                ctypes.byref(returned),
            ):
                self._raise_last_error("GetTokenInformation(TokenUser)")
            current_user_sid = self.ctypes.cast(
                token_buffer, ctypes.POINTER(self.TOKEN_USER)
            ).contents.User.Sid
            if not current_user_sid:
                raise WindowsHandleError("The current process token has no user SID.")

            well_known_buffers = []
            approved_sids = [current_user_sid]
            for sid_type in (
                self.WELL_KNOWN_BUILTIN_ADMINISTRATORS,
                self.WELL_KNOWN_LOCAL_SYSTEM,
            ):
                sid_buffer = ctypes.create_string_buffer(68)
                sid_size = wintypes.DWORD(len(sid_buffer))
                if not self.advapi32.CreateWellKnownSid(
                    sid_type,
                    None,
                    sid_buffer,
                    ctypes.byref(sid_size),
                ):
                    self._raise_last_error("CreateWellKnownSid")
                well_known_buffers.append(sid_buffer)
                approved_sids.append(ctypes.cast(sid_buffer, ctypes.c_void_p))

            if not owner_sid or not any(
                self.advapi32.EqualSid(owner_sid, approved)
                for approved in approved_sids
            ):
                raise WindowsHandleError(
                    "Backup root owner must be the current user, SYSTEM or Administrators."
                )

            dacl_present = wintypes.BOOL()
            dacl_defaulted = wintypes.BOOL()
            dacl_pointer = ctypes.c_void_p()
            if not self.advapi32.GetSecurityDescriptorDacl(
                security_descriptor,
                ctypes.byref(dacl_present),
                ctypes.byref(dacl_pointer),
                ctypes.byref(dacl_defaulted),
            ):
                self._raise_last_error("GetSecurityDescriptorDacl")
            if not dacl_present.value or not dacl_pointer:
                raise WindowsHandleError(
                    "Backup root has a null or absent DACL; refusing to store patch backups."
                )

            acl_info = self.ACL_SIZE_INFORMATION()
            if not self.advapi32.GetAclInformation(
                dacl_pointer,
                ctypes.byref(acl_info),
                ctypes.sizeof(acl_info),
                self.ACL_SIZE_INFORMATION_CLASS,
            ):
                self._raise_last_error("GetAclInformation")
            if acl_info.AceCount == 0 or acl_info.AceCount > 4096:
                raise WindowsHandleError(
                    "Backup root DACL is empty or exceeds the supported ACE inspection bound."
                )

            user_grant_verified = False
            for index in range(acl_info.AceCount):
                ace_pointer = ctypes.c_void_p()
                if not self.advapi32.GetAce(
                    dacl_pointer, index, ctypes.byref(ace_pointer)
                ):
                    self._raise_last_error("GetAce")
                header = ctypes.cast(
                    ace_pointer, ctypes.POINTER(self.ACE_HEADER)
                ).contents
                if header.AceType != self.ACCESS_ALLOWED_ACE_TYPE:
                    raise WindowsHandleError(
                        "Backup root DACL contains an unsupported or explicit-deny ACE; refusing mutation."
                    )
                if header.AceSize < 16:
                    raise WindowsHandleError("Backup root DACL contains a malformed access ACE.")
                sid_pointer = ctypes.c_void_p(ace_pointer.value + 8)
                if not any(
                    self.advapi32.EqualSid(sid_pointer, approved)
                    for approved in approved_sids
                ):
                    raise WindowsHandleError(
                        "Backup root DACL grants access to a SID other than the current user, SYSTEM or Administrators."
                    )
                inheritance = self.ACE_OBJECT_INHERIT | self.ACE_CONTAINER_INHERIT
                if (header.AceFlags & inheritance) != inheritance:
                    raise WindowsHandleError(
                        "Backup root access ACEs must inherit to files and child directories."
                    )
                mask = ctypes.c_uint32.from_address(ace_pointer.value + 4).value
                if not (mask & self.GENERIC_ALL) and (
                    mask & self.FILE_ALL_ACCESS
                ) != self.FILE_ALL_ACCESS:
                    raise WindowsHandleError(
                        "Backup root approved principals require full control for safe backup and recovery."
                    )
                if self.advapi32.EqualSid(sid_pointer, current_user_sid):
                    user_grant_verified = True

            if not user_grant_verified:
                raise WindowsHandleError(
                    "Backup root DACL has no inheritable full-control grant for the current user."
                )
            return {
                "ace_count": int(acl_info.AceCount),
                "allowed_ace_count": int(acl_info.AceCount),
                "owner_verified": True,
                "current_user_inheritable_full_control": True,
            }
        finally:
            if token:
                self.close(token)
            if security_descriptor:
                self.kernel32.LocalFree(security_descriptor)

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
        share_mode: int | None = None,
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
            (self.FILE_SHARE_READ | self.FILE_SHARE_WRITE) if share_mode is None else share_mode,
            disposition,
            options,
            None,
            0,
        )
        if status < 0:
            error = WindowsHandleError(
                f"NtCreateFile failed with NTSTATUS 0x{status & 0xFFFFFFFF:08X}."
            )
            error.ntstatus = status & 0xFFFFFFFF
            raise error
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

    def open_root(self, root_path: str | Path, *, read_control: bool = True) -> Any:
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
            | (self.READ_CONTROL if read_control else 0)
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
            self._assert_supported_volume(current)
            for component in path.parts[1:]:
                child = self.open_child_directory(current, component, read_control=read_control)
                self.close(current)
                current = child
            return current
        except Exception:
            self.close(current)
            raise

    def ensure_directory(self, directory_path: str | Path, *, read_control: bool = True) -> Any:
        """Create missing local directory components relative to pinned handles."""
        raw_path = Path(directory_path).expanduser()
        if ".." in raw_path.parts:
            raise WindowsHandleError("Parent traversal is denied in backup directory paths.")
        path = raw_path.absolute()
        if not path.drive or str(path).startswith("\\\\"):
            raise WindowsHandleError("A local absolute backup directory path is required.")
        access = (
            self.FILE_LIST_DIRECTORY
            | self.FILE_TRAVERSE
            | self.FILE_READ_ATTRIBUTES
            | (self.READ_CONTROL if read_control else 0)
            | self.SYNCHRONIZE
        )
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
            self._assert_supported_volume(current)
            for component in path.parts[1:]:
                try:
                    child = self.open_child_directory(current, component, read_control=read_control)
                except WindowsHandleError as exc:
                    if getattr(exc, "ntstatus", None) not in {0xC0000034, 0xC000003A}:
                        raise
                    try:
                        child = self.create_directory(current, component, read_control=read_control)
                    except WindowsHandleError as create_exc:
                        if getattr(create_exc, "ntstatus", None) != 0xC0000035:
                            raise
                        # A concurrent creator won; reopen no-follow and verify.
                        child = self.open_child_directory(current, component, read_control=read_control)
                self.close(current)
                current = child
            return current
        except Exception:
            self.close(current)
            raise

    def open_child_directory(self, parent_handle: Any, name: str, *, read_control: bool = True) -> Any:
        name = self._validate_basename(name)
        access = (
            self.FILE_LIST_DIRECTORY
            | self.FILE_TRAVERSE
            | self.FILE_READ_ATTRIBUTES
            | (self.READ_CONTROL if read_control else 0)
            | self.SYNCHRONIZE
        )
        return self._nt_open(
            parent_handle,
            name,
            access=access,
            disposition=self.FILE_OPEN,
            options=self.FILE_DIRECTORY_FILE | self.FILE_SYNCHRONOUS_IO_NONALERT | self.FILE_OPEN_REPARSE_POINT,
        )

    def open_file(
        self,
        parent_handle: Any,
        name: str,
        *,
        writable: bool = False,
        exclusive: bool = False,
    ) -> Any:
        name = self._validate_basename(name)
        access = self.FILE_READ_ATTRIBUTES | self.SYNCHRONIZE
        if writable:
            access |= self.FILE_READ_DATA | self.FILE_WRITE_DATA | self.DELETE
        elif exclusive:
            access |= self.FILE_READ_DATA | self.FILE_WRITE_DATA
        else:
            access |= 0x80000000  # GENERIC_READ
        # Exclusive target handles deny new write/delete opens for their lifetime.
        share_mode = self.FILE_SHARE_READ if exclusive else None
        options = (
            self.FILE_NON_DIRECTORY_FILE
            | self.FILE_SYNCHRONOUS_IO_NONALERT
            | self.FILE_OPEN_REPARSE_POINT
        )
        if writable or exclusive:
            options |= self.FILE_WRITE_THROUGH
        return self._nt_open(
            parent_handle,
            name,
            access=access,
            disposition=self.FILE_OPEN,
            options=options,
            share_mode=share_mode,
        )

    def open_file_optional(
        self,
        parent_handle: Any,
        name: str,
        *,
        writable: bool = False,
        exclusive: bool = False,
    ) -> Any | None:
        try:
            return self.open_file(parent_handle, name, writable=writable, exclusive=exclusive)
        except WindowsHandleError as exc:
            if getattr(exc, "ntstatus", None) in {0xC0000034, 0xC000003A}:
                return None
            raise

    def create_file(self, parent_handle: Any, name: str, *, exclusive: bool = False) -> Any:
        name = self._validate_basename(name)
        access = self.FILE_READ_DATA | self.FILE_WRITE_DATA | self.FILE_READ_ATTRIBUTES | self.DELETE | self.SYNCHRONIZE
        return self._nt_open(
            parent_handle,
            name,
            access=access,
            disposition=self.FILE_CREATE,
            options=self.FILE_NON_DIRECTORY_FILE | self.FILE_SYNCHRONOUS_IO_NONALERT | self.FILE_WRITE_THROUGH,
            share_mode=self.FILE_SHARE_READ if exclusive else None,
        )

    def create_directory(self, parent_handle: Any, name: str, *, read_control: bool = True) -> Any:
        name = self._validate_basename(name)
        access = (
            self.FILE_LIST_DIRECTORY
            | self.FILE_TRAVERSE
            | self.FILE_READ_ATTRIBUTES
            | (self.READ_CONTROL if read_control else 0)
            | self.DELETE
            | self.SYNCHRONIZE
        )
        return self._nt_open(
            parent_handle,
            name,
            access=access,
            disposition=self.FILE_CREATE,
            options=self.FILE_DIRECTORY_FILE | self.FILE_SYNCHRONOUS_IO_NONALERT | self.FILE_WRITE_THROUGH,
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

    def reset_file_pointer(self, handle: Any) -> None:
        if not self.kernel32.SetFilePointerEx(handle, 0, None, 0):
            self._raise_last_error("SetFilePointerEx(FILE_BEGIN)")

    def truncate_file(self, handle: Any) -> None:
        self.reset_file_pointer(handle)
        if not self.kernel32.SetEndOfFile(handle):
            self._raise_last_error("SetEndOfFile")

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
        parent_handle: Any | None,
        target_name: str,
        *,
        replace_existing: bool,
    ) -> None:
        target_name = self._validate_basename(target_name)
        encoded = target_name.encode("utf-16-le")
        header_size = self.FILE_RENAME_INFO.FileName.offset
        buffer_size = self.ctypes.sizeof(self.FILE_RENAME_INFO) + len(encoded)
        buffer = self.ctypes.create_string_buffer(buffer_size)
        info = self.ctypes.cast(
            buffer, self.ctypes.POINTER(self.FILE_RENAME_INFO)
        ).contents
        info.ReplaceIfExists = 1 if replace_existing else 0
        info.RootDirectory = parent_handle.value if parent_handle else None
        info.FileNameLength = len(encoded)
        self.ctypes.memmove(
            self.ctypes.addressof(buffer) + header_size, encoded, len(encoded)
        )
        io_status = self.IO_STATUS_BLOCK()
        status = self.ntdll.NtSetInformationFile(
            source_handle,
            self.ctypes.byref(io_status),
            buffer,
            buffer_size,
            10,  # FileRenameInformation
        )
        if status < 0:
            raise WindowsHandleError(
                f"NtSetInformationFile(FileRenameInformation) failed with NTSTATUS 0x{status & 0xFFFFFFFF:08X}."
            )
    def file_identity(self, handle: Any) -> tuple[int, int]:
        info = self.BY_HANDLE_FILE_INFORMATION()
        if not self.kernel32.GetFileInformationByHandle(handle, self.ctypes.byref(info)):
            self._raise_last_error("GetFileInformationByHandle")
        file_index = (int(info.nFileIndexHigh) << 32) | int(info.nFileIndexLow)
        return int(info.dwVolumeSerialNumber), file_index

    def file_link_count(self, handle: Any) -> int:
        info = self.BY_HANDLE_FILE_INFORMATION()
        if not self.kernel32.GetFileInformationByHandle(handle, self.ctypes.byref(info)):
            self._raise_last_error("GetFileInformationByHandle")
        return int(info.nNumberOfLinks)

    def delete_handle(self, handle: Any) -> None:
        info = self.FILE_DISPOSITION_INFO()
        info.DeleteFile = 1
        io_status = self.IO_STATUS_BLOCK()
        status = self.ntdll.NtSetInformationFile(
            handle,
            self.ctypes.byref(io_status),
            self.ctypes.byref(info),
            self.ctypes.sizeof(info),
            13,  # FileDispositionInformation
        )
        if status < 0:
            raise WindowsHandleError(
                f"NtSetInformationFile(FileDispositionInformation) failed with NTSTATUS 0x{status & 0xFFFFFFFF:08X}."
            )

    def close(self, handle: Any) -> None:
        if handle and getattr(handle, "value", handle):
            if not self.kernel32.CloseHandle(handle):
                self._raise_last_error("CloseHandle")
