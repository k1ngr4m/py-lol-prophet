import ctypes
from ctypes import wintypes
import psutil  # 需要安装psutil库

class Process:
    @staticmethod
    def get_process_command(target_name):
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == target_name:
                    return ' '.join(proc.info['cmdline'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        raise ProcessNotFound()

class ProcessNotFound(Exception):
    pass

# Windows API常量
TH32CS_SNAPPROCESS = 0x00000002
MAX_PATH = 260

# 原生API实现（如需完整实现可继续扩展）
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize',              wintypes.DWORD),
        ('cntUsage',            wintypes.DWORD),
        ('th32ProcessID',       wintypes.DWORD),
        ('th32DefaultHeapID',   wintypes.ULONG),
        ('th32ModuleID',       wintypes.DWORD),
        ('cntThreads',          wintypes.DWORD),
        ('th32ParentProcessID', wintypes.DWORD),
        ('pcPriClassBase',      wintypes.LONG),
        ('dwFlags',             wintypes.DWORD),
        ('szExeFile',           wintypes.WCHAR * MAX_PATH)
    ]

# 注意：以下为底层API调用示例，实际使用建议结合psutil
CreateToolhelp32Snapshot = kernel32.CreateToolhelp32Snapshot
CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
CreateToolhelp32Snapshot.restype = wintypes.HANDLE

Process32First = kernel32.Process32FirstW
Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
Process32First.restype = wintypes.BOOL

Process32Next = kernel32.Process32NextW
Process32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
Process32Next.restype = wintypes.BOOL