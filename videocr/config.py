"""Configuration dataclasses for VideOCR processing pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OcrConfig:
    """OCR engine selection and language settings."""
    ocr_engine: str = "paddleocr"
    lang: str = "en"
    use_gpu: bool = False
    use_angle_cls: bool = False
    use_server_model: bool = False


@dataclass
class TimeRange:
    """Time window for processing."""
    time_start: str = "0:00"
    time_end: str = ""


@dataclass
class DetectionConfig:
    """Thresholds for frame detection and filtering."""
    conf_threshold: int = 75
    ssim_threshold: int = 92
    brightness_threshold: int | None = None


@dataclass
class FrameConfig:
    """Frame extraction and cropping settings."""
    use_fullframe: bool = False
    frames_to_skip: int = 1
    ocr_image_max_width: int = 720
    crop_zones: list[dict[str, int]] = field(default_factory=list)
    subtitle_position: str = "center"


@dataclass
class LlmConfig:
    """LLM Vision API settings."""
    api_key: str = ""
    api_base: str = ""
    model: str = ""
    concurrency: int = 4
    disable_inference: bool = False
    max_frames_per_grid: int = 0
    image_quality: int = 75


@dataclass
class PostProcessConfig:
    """Subtitle post-processing settings."""
    sim_threshold: int = 80
    max_merge_gap_sec: float = 0.1
    post_processing: bool = False
    min_subtitle_duration_sec: float = 0.2
    subtitle_alignments: list[str | None] = field(default_factory=lambda: [None, None])
    normalize_to_simplified_chinese: bool = True
