"""
File Operations Tool - Safe file system operations.

Provides controlled file access with security constraints.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import mimetypes


# Security: Define allowed directories
ALLOWED_DIRECTORIES = [
    "./workspace",
    "./data",
    "./output",
]


def _is_path_allowed(path: str) -> bool:
    """
    Check if path is within allowed directories.
    
    Security measure to prevent directory traversal attacks.
    """
    abs_path = Path(path).resolve()
    
    for allowed_dir in ALLOWED_DIRECTORIES:
        allowed_abs = Path(allowed_dir).resolve()
        try:
            abs_path.relative_to(allowed_abs)
            return True
        except ValueError:
            continue
    
    return False


def read_file(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Read file contents.
    
    Args:
        file_path: Path to file
        encoding: File encoding
        
    Returns:
        Dictionary with file contents or error
        
    Security: Only allows reading from whitelisted directories
    """
    try:
        if not _is_path_allowed(file_path):
            return {
                "success": False,
                "error": "Access denied: Path not in allowed directories",
                "file_path": file_path,
            }
        
        path = Path(file_path)
        
        if not path.exists():
            return {
                "success": False,
                "error": "File not found",
                "file_path": file_path,
            }
        
        if not path.is_file():
            return {
                "success": False,
                "error": "Path is not a file",
                "file_path": file_path,
            }
        
        content = path.read_text(encoding=encoding)
        
        return {
            "success": True,
            "file_path": file_path,
            "content": content,
            "size_bytes": len(content.encode(encoding)),
            "line_count": content.count('\n') + 1,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
        }


def write_file(
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    overwrite: bool = False,
) -> Dict[str, Any]:
    """
    Write content to file.
    
    Args:
        file_path: Path to file
        content: Content to write
        encoding: File encoding
        overwrite: Allow overwriting existing files
        
    Returns:
        Dictionary with operation result
        
    Security: Only allows writing to whitelisted directories
    """
    try:
        if not _is_path_allowed(file_path):
            return {
                "success": False,
                "error": "Access denied: Path not in allowed directories",
                "file_path": file_path,
            }
        
        path = Path(file_path)
        
        if path.exists() and not overwrite:
            return {
                "success": False,
                "error": "File exists and overwrite=False",
                "file_path": file_path,
            }
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        path.write_text(content, encoding=encoding)
        
        return {
            "success": True,
            "file_path": str(path),
            "bytes_written": len(content.encode(encoding)),
            "line_count": content.count('\n') + 1,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
        }


def list_directory(directory_path: str, pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    List files in a directory.
    
    Args:
        directory_path: Path to directory
        pattern: Optional glob pattern (e.g., "*.txt")
        
    Returns:
        Dictionary with file listing
    """
    try:
        if not _is_path_allowed(directory_path):
            return {
                "success": False,
                "error": "Access denied: Path not in allowed directories",
                "directory_path": directory_path,
            }
        
        path = Path(directory_path)
        
        if not path.exists():
            return {
                "success": False,
                "error": "Directory not found",
                "directory_path": directory_path,
            }
        
        if not path.is_dir():
            return {
                "success": False,
                "error": "Path is not a directory",
                "directory_path": directory_path,
            }
        
        # List files
        if pattern:
            items = list(path.glob(pattern))
        else:
            items = list(path.iterdir())
        
        files = []
        directories = []
        
        for item in sorted(items):
            info = {
                "name": item.name,
                "path": str(item),
                "size_bytes": item.stat().st_size if item.is_file() else 0,
            }
            
            if item.is_file():
                files.append(info)
            elif item.is_dir():
                directories.append(info)
        
        return {
            "success": True,
            "directory_path": directory_path,
            "file_count": len(files),
            "directory_count": len(directories),
            "files": files,
            "directories": directories,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "directory_path": directory_path,
        }


def delete_file(file_path: str) -> Dict[str, Any]:
    """
    Delete a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with operation result
        
    Security: Only allows deleting from whitelisted directories
    """
    try:
        if not _is_path_allowed(file_path):
            return {
                "success": False,
                "error": "Access denied: Path not in allowed directories",
                "file_path": file_path,
            }
        
        path = Path(file_path)
        
        if not path.exists():
            return {
                "success": False,
                "error": "File not found",
                "file_path": file_path,
            }
        
        if not path.is_file():
            return {
                "success": False,
                "error": "Path is not a file",
                "file_path": file_path,
            }
        
        path.unlink()
        
        return {
            "success": True,
            "file_path": file_path,
            "message": "File deleted successfully",
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
        }


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get information about a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    try:
        if not _is_path_allowed(file_path):
            return {
                "success": False,
                "error": "Access denied: Path not in allowed directories",
                "file_path": file_path,
            }
        
        path = Path(file_path)
        
        if not path.exists():
            return {
                "success": False,
                "error": "File not found",
                "file_path": file_path,
            }
        
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))
        
        return {
            "success": True,
            "file_path": str(path),
            "name": path.name,
            "extension": path.suffix,
            "size_bytes": stat.st_size,
            "mime_type": mime_type,
            "is_file": path.is_file(),
            "is_directory": path.is_dir(),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
        }
