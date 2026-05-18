"""Plugin manager for downloading and managing OCR engine dependencies."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

from .utils import get_base_dir

GITHUB_API = "https://api.github.com"
GH_PROXY = "https://gh-proxy.com"


def get_cache_dir() -> str:
    """Return the directory where downloaded plugin archives are cached."""
    cache_dir = os.path.join(get_base_dir(), ".plugin_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def clear_cache() -> int:
    """Clear all cached plugin archives. Returns number of files removed."""
    cache_dir = get_cache_dir()
    count = 0
    for f in os.listdir(cache_dir):
        fpath = os.path.join(cache_dir, f)
        if os.path.isfile(fpath):
            os.remove(fpath)
            count += 1
    return count


def get_cache_size() -> int:
    """Return total size of cached archives in bytes."""
    cache_dir = get_cache_dir()
    total = 0
    for f in os.listdir(cache_dir):
        fpath = os.path.join(cache_dir, f)
        if os.path.isfile(fpath):
            total += os.path.getsize(fpath)
    return total

IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

# ─── Plugin Registry ────────────────────────────────────────────────────────

def _get_asset_patterns(plugin_key: str) -> list[str]:
    """Return platform-specific asset filename patterns for a plugin.
    Patterns are ordered by preference (archives first, then installers)."""
    patterns: dict[str, dict[str, list[str]]] = {
        "paddleocr_models": {
            "win32": ["PaddleOCR.PP-OCRv5.support.files.VideOCR.7z"],
            "linux": ["PaddleOCR.PP-OCRv5.support.files.VideOCR.tar.xz"],
        },
        "paddleocr_cpu": {
            # Prefer .7z archives over .exe installers
            "win32": ["PaddleOCR-CPU-*.7z", "PaddleOCR-CPU-*-setup-x64.exe"],
            "linux": ["PaddleOCR-CPU-*-Linux.7z", "PaddleOCR-CPU-*-Linux.tar.xz"],
        },
        "paddleocr_gpu_cuda11": {
            # Prefer .7z archives over .exe installers
            "win32": ["PaddleOCR-GPU-*-CUDA-11.8.7z", "PaddleOCR-GPU-*-CUDA-11.8-setup-x64.exe"],
            "linux": ["PaddleOCR-GPU-*-CUDA-11.8-Linux.7z"],
        },
        "paddleocr_gpu_cuda12": {
            "win32": ["PaddleOCR-GPU-*-CUDA-12.9.7z"],
            "linux": ["PaddleOCR-GPU-*-CUDA-12.9-Linux.7z.*"],
        },
        "chrome_lens": {
            "win32": ["Chrome-Lens-OCR-v*.7z"],
            "linux": ["Chrome-Lens-OCR-*-Linux.7z"],
        },
    }
    plat = "win32" if IS_WINDOWS else "linux"
    return patterns.get(plugin_key, {}).get(plat, [])


PLUGIN_REGISTRY: dict[str, dict[str, Any]] = {
    "paddleocr_models": {
        "repo": "timminator/PaddleOCR-Standalone",
        "display_name": "PaddleOCR Detection + Recognition Models",
        "description": "PP-OCRv5 text detection and recognition models. Required for all engines (Phase 2 detection).",
        "extract_to": ".",
        "required_for": ["paddleocr", "google_lens", "llm_vision"],
        "check_path": "PaddleOCR.PP-OCRv5.support.files",
        "estimated_size_mb": 250,
    },
    "paddleocr_cpu": {
        "repo": "timminator/PaddleOCR-Standalone",
        "display_name": "PaddleOCR Executable (CPU)",
        "description": "Standalone PaddleOCR CLI for text detection and recognition on CPU.",
        "extract_to": ".",
        "required_for": ["paddleocr", "google_lens", "llm_vision"],  # All engines need text detection
        "check_path_exec": "paddleocr",
        "estimated_size_mb": 140,
    },
    "paddleocr_gpu_cuda11": {
        "repo": "timminator/PaddleOCR-Standalone",
        "display_name": "PaddleOCR Executable (GPU, CUDA 11.8)",
        "description": "Standalone PaddleOCR CLI with CUDA 11.8 GPU acceleration.",
        "extract_to": ".",
        "required_for": [],
        "check_path_exec": "paddleocr",
        "estimated_size_mb": 900,
    },
    "paddleocr_gpu_cuda12": {
        "repo": "timminator/PaddleOCR-Standalone",
        "display_name": "PaddleOCR Executable (GPU, CUDA 12.9)",
        "description": "Standalone PaddleOCR CLI with CUDA 12.9 GPU acceleration.",
        "extract_to": ".",
        "required_for": [],
        "check_path_exec": "paddleocr",
        "estimated_size_mb": 1200,
    },
    "chrome_lens": {
        "repo": "timminator/Chrome-Lens-OCR",
        "display_name": "Google Lens CLI",
        "description": "CLI tool for Google Lens OCR. Only needed for Google Lens engine.",
        "extract_to": ".",
        "required_for": ["google_lens"],
        "check_path_exec": "chrome-lens",
        "estimated_size_mb": 12,
    },
}

# ─── Status Checking ────────────────────────────────────────────────────────

def get_install_dir() -> str:
    """Return the directory where plugins should be installed."""
    return get_base_dir()


def check_plugin_status(plugin_key: str) -> dict[str, Any]:
    """Check if a plugin is installed. Returns {installed, path, version}."""
    info = PLUGIN_REGISTRY[plugin_key]
    install_dir = get_install_dir()

    # Check by directory existence
    check_path = info.get("check_path")
    if check_path:
        full_path = os.path.join(install_dir, check_path)
        if os.path.isdir(full_path):
            return {"installed": True, "path": full_path, "version": "installed"}

    # Check by executable existence
    check_exec = info.get("check_path_exec")
    if check_exec:
        ext = ".exe" if IS_WINDOWS else ".bin"
        exec_name = f"{check_exec}{ext}"
        for entry in os.listdir(install_dir):
            if entry.lower().startswith(f"{check_exec.lower()}-"):
                path = os.path.join(install_dir, entry, exec_name)
                if os.path.isfile(path):
                    return {"installed": True, "path": path, "version": entry}

    return {"installed": False, "path": "", "version": ""}


def get_missing_plugins(ocr_engine: str) -> list[str]:
    """Return list of plugin keys missing for the given engine."""
    missing = []
    for key, info in PLUGIN_REGISTRY.items():
        if ocr_engine in info["required_for"]:
            status = check_plugin_status(key)
            if not status["installed"]:
                missing.append(key)
    return missing


# ─── GitHub API ─────────────────────────────────────────────────────────────

def _github_api(url: str) -> Any:
    """Make a GitHub API request."""
    req = urllib.request.Request(url, headers={"User-Agent": "VideOCR-PluginManager"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_latest_release(repo: str) -> dict[str, Any]:
    """Get the latest release info for a GitHub repo."""
    url = f"{GITHUB_API}/repos/{repo}/releases/latest"
    return _github_api(url)


def find_asset(release: dict[str, Any], patterns: list[str]) -> dict[str, Any] | None:
    """Find the best matching asset from a release, filtering by current platform."""
    assets = release.get("assets", [])
    import fnmatch

    # Platform keywords to exclude (wrong-platform assets)
    if IS_WINDOWS:
        exclude_keywords = ["-Linux", "-linux"]
    else:
        exclude_keywords = ["-setup-x64", "-setup-x86"]

    for pattern in patterns:
        for asset in assets:
            name = asset["name"]
            if not fnmatch.fnmatch(name.lower(), pattern.lower()):
                continue
            # Skip wrong-platform assets
            if any(kw.lower() in name.lower() for kw in exclude_keywords):
                continue
            return asset

    return None


# ─── Download ───────────────────────────────────────────────────────────────

def download_file(
    url: str,
    dest_path: str,
    use_proxy: bool = False,
    progress_callback: Callable[[int, int], None] | None = None,
    cancel_event: threading.Event | None = None,
    max_retries: int = 3,
) -> bool:
    """Download a file with optional gh-proxy, progress reporting, and retry.

    Args:
        url: Direct download URL
        dest_path: Where to save the file
        use_proxy: Whether to prepend gh-proxy.com
        progress_callback: (downloaded_bytes, total_bytes) callback
        cancel_event: Threading event to signal cancellation
        max_retries: Number of retry attempts on failure

    Returns:
        True if download succeeded, False if cancelled
    """
    if use_proxy:
        url = f"{GH_PROXY}/{url}"

    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)

    for attempt in range(max_retries):
        if cancel_event and cancel_event.is_set():
            return False

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "VideOCR-PluginManager"})

            # Longer timeout for initial connection, no timeout for data transfer
            with urllib.request.urlopen(req, timeout=30) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                block_size = 1024 * 256  # 256KB for faster downloads

                with open(dest_path, "wb") as f:
                    while True:
                        if cancel_event and cancel_event.is_set():
                            f.close()
                            os.remove(dest_path)
                            return False

                        try:
                            chunk = resp.read(block_size)
                        except Exception:
                            # If we have partial data, retry from where we left off
                            break

                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback:
                            progress_callback(downloaded, total)

                # Verify download completeness
                if total > 0 and downloaded < total:
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retry
                        continue
                    raise RuntimeError(f"Download incomplete: {downloaded}/{total} bytes")

                return True

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retry
                continue
            # Final attempt failed
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise

    return False


# ─── Extraction ─────────────────────────────────────────────────────────────

def extract_archive(archive_path: str, dest_dir: str) -> None:
    """Extract a .7z, .tar.xz, .zip archive, or handle .exe installer."""
    lower = archive_path.lower()

    try:
        if lower.endswith(".7z"):
            _extract_7z(archive_path, dest_dir)
        elif lower.endswith(".tar.xz") or lower.endswith(".tar.gz"):
            with tarfile.open(archive_path) as tf:
                tf.extractall(dest_dir, filter="data")
        elif lower.endswith(".zip"):
            import zipfile
            with zipfile.ZipFile(archive_path) as zf:
                zf.extractall(dest_dir)
        elif lower.endswith(".exe"):
            # For .exe installers, just copy to destination
            # User may need to run it manually or it might be a portable exe
            import shutil as _shutil
            dest_path = os.path.join(dest_dir, os.path.basename(archive_path))
            _shutil.copy2(archive_path, dest_path)
            return
        else:
            raise ValueError(f"Unsupported archive format: {archive_path}")
    except Exception as e:
        # Re-raise with more context
        raise RuntimeError(f"Failed to extract '{os.path.basename(archive_path)}': {e}") from e


def is_7z_available() -> bool:
    """Check if 7z or 7za is available in PATH."""
    import shutil as _shutil
    return _shutil.which("7z") is not None or _shutil.which("7za") is not None


def _extract_7z(archive_path: str, dest_dir: str) -> None:
    """Extract a .7z file using 7z, 7za, or py7zr (pure Python fallback)."""
    import shutil as _shutil

    # Try 7z first, then 7za
    last_error = ""
    found_cmd = False
    for cmd in ["7z", "7za"]:
        if _shutil.which(cmd) is None:
            last_error = f"'{cmd}' not found in PATH"
            continue
        found_cmd = True
        try:
            result = subprocess.run(
                [cmd, "x", "-y", f"-o{dest_dir}", archive_path],
                capture_output=True, text=True, check=True,
            )
            return
        except subprocess.CalledProcessError as e:
            last_error = f"'{cmd}' failed with exit code {e.returncode}"
            if e.stderr:
                last_error += f": {e.stderr.strip()[:200]}"
            elif e.stdout:
                last_error += f": {e.stdout.strip()[:200]}"
            continue

    # Fallback: try py7zr (pure Python)
    try:
        import py7zr
        os.makedirs(dest_dir, exist_ok=True)
        with py7zr.SevenZipFile(archive_path, mode='r') as z:
            z.extractall(dest_dir)
        return
    except ImportError as e:
        import sys
        last_error = f"py7zr not available ({e}). Python: {sys.executable}"
    except Exception as e:
        last_error = f"py7zr extraction failed: {e}"

    if not found_cmd:
        import sys
        raise RuntimeError(
            f"7-Zip not found and py7zr not available.\n"
            f"Python executable: {sys.executable}\n"
            f"Install 7-Zip (https://7-zip.org) or run:\n"
            f"\"{sys.executable}\" -m pip install py7zr"
        )
    raise RuntimeError(f"Extraction failed: {last_error}")


# ─── High-level Operations ──────────────────────────────────────────────────

class PluginDownloadTask:
    """Represents a download task with progress tracking."""

    def __init__(self, plugin_key: str, use_proxy: bool = False):
        self.plugin_key = plugin_key
        self.info = PLUGIN_REGISTRY[plugin_key]
        self.use_proxy = use_proxy
        self.status = "pending"  # pending, downloading, extracting, done, error
        self.progress = 0.0  # 0.0 - 1.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.error_message = ""
        self.cancel_event = threading.Event()

    def run(self, progress_callback: Callable[[str, float, str], None] | None = None) -> None:
        """Execute the download and extraction.

        Args:
            progress_callback: (plugin_key, progress, status) callback
        """
        def _update(status: str, prog: float, msg: str = ""):
            self.status = status
            self.progress = prog
            if progress_callback:
                progress_callback(self.plugin_key, prog, status)

        try:
            _update("querying", 0.0)

            # Find the asset
            release = get_latest_release(self.info["repo"])
            patterns = _get_asset_patterns(self.plugin_key)
            asset = find_asset(release, patterns)

            if not asset:
                _update("error", 0.0)
                self.error_message = f"No matching asset found for {self.plugin_key} on this platform."
                return

            self.total_bytes = asset["size"]
            asset_name = asset["name"]

            # Check cache first
            cache_dir = get_cache_dir()
            cached_path = os.path.join(cache_dir, asset_name)
            use_cache = False

            if os.path.isfile(cached_path) and os.path.getsize(cached_path) == asset["size"]:
                use_cache = True
                _update("downloading", 1.0)
            else:
                download_url = asset["browser_download_url"]

                # Download to cache
                _update("downloading", 0.0)
                os.makedirs(cache_dir, exist_ok=True)
                tmp_path = os.path.join(cache_dir, f".tmp_{asset_name}")

                def _progress(downloaded: int, total: int) -> None:
                    self.downloaded_bytes = downloaded
                    if total > 0:
                        prog = downloaded / total
                        _update("downloading", prog)

                success = download_file(
                    download_url, tmp_path,
                    use_proxy=self.use_proxy,
                    progress_callback=_progress,
                    cancel_event=self.cancel_event,
                )

                if not success:
                    _update("cancelled", 0.0)
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    return

                # Move temp file to cache
                if os.path.exists(cached_path):
                    os.remove(cached_path)
                os.rename(tmp_path, cached_path)

            # Extract from cache
            _update("extracting", 0.9)
            install_dir = get_install_dir()
            extract_to = os.path.join(install_dir, self.info["extract_to"])
            try:
                extract_archive(cached_path, extract_to)
            except Exception as extract_err:
                # Clean up partial extraction so status check doesn't
                # report a broken install as "installed"
                check_path = self.info.get("check_path")
                if check_path:
                    partial_dir = os.path.join(install_dir, check_path)
                    if os.path.isdir(partial_dir):
                        shutil.rmtree(partial_dir, ignore_errors=True)
                raise extract_err

            _update("done", 1.0)

        except Exception as e:
            _update("error", 0.0)
            self.error_message = str(e)

    def cancel(self) -> None:
        """Cancel the download."""
        self.cancel_event.set()


def check_extraction_capability() -> tuple[bool, str]:
    """Check if we can extract .7z archives. Returns (can_extract, message)."""
    import shutil as _shutil
    if _shutil.which("7z") is not None or _shutil.which("7za") is not None:
        return True, "7-Zip found"
    try:
        import py7zr
        return True, "py7zr available"
    except ImportError as e:
        import sys
        return False, (
            f"py7zr import failed: {e}\n"
            f"Python: {sys.executable}\n"
            f"Install with: \"{sys.executable}\" -m pip install py7zr"
        )
    except Exception as e:
        return False, f"py7zr error: {e}"


def get_all_plugins_status(ocr_engine: str = "") -> list[dict[str, Any]]:
    """Get status of all plugins, optionally filtered by engine requirement."""
    result = []
    for key, info in PLUGIN_REGISTRY.items():
        status = check_plugin_status(key)
        needed = ocr_engine in info["required_for"] if ocr_engine else False
        result.append({
            "key": key,
            "display_name": info["display_name"],
            "description": info["description"],
            "estimated_size_mb": info["estimated_size_mb"],
            "installed": status["installed"],
            "version": status.get("version", ""),
            "path": status.get("path", ""),
            "needed_for_engine": needed,
        })
    return result
