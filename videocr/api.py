from __future__ import annotations

import sys
from .plugin_manager import PLUGIN_REGISTRY, get_missing_plugins, check_plugin_status, PluginDownloadTask
from . import utils
from .config import DetectionConfig, FrameConfig, LlmConfig, OcrConfig, PostProcessConfig, TimeRange
from .video import Video


def save_subtitles_to_file(
        video_path: str, file_path: str = 'subtitle.srt', ocr_engine: str = 'google_lens', lang: str = 'en',
        time_start: str = '0:00', time_end: str = '', conf_threshold: int = 75, sim_threshold: int = 80, max_merge_gap_sec: float = 0.1,
        use_fullframe: bool = False, use_gpu: bool = False, use_angle_cls: bool = False, use_server_model: bool = False,
        brightness_threshold: int | None = None, ssim_threshold: int = 92, subtitle_position: str = "center", frames_to_skip: int = 1,
        crop_zones: list[dict[str, int]] | None = None, ocr_image_max_width: int = 720, post_processing: bool = False, min_subtitle_duration_sec: float = 0.2,
        normalize_to_simplified_chinese: bool = True, subtitle_alignments: list[str | None] | None = None,
        llm_api_key: str = '', llm_api_base: str = '', llm_model: str = '', llm_concurrency: int = 4,
        llm_disable_inference: bool = False, llm_max_frames_per_grid: int = 0, llm_image_quality: int = 75) -> None:

    if crop_zones is None:
        crop_zones = []

    if subtitle_alignments is None:
        subtitle_alignments = [None, None]
    elif len(subtitle_alignments) == 1:
        subtitle_alignments.append(None)

# Check required components for the selected engine
    engine_key = ocr_engine
    missing = get_missing_plugins(engine_key)
    if missing:
        plugin_keys = [k for k, v in PLUGIN_REGISTRY.items() if engine_key in v["required_for"]]
        plugin_keys = [k for k in plugin_keys if not check_plugin_status(k)["installed"]]
        for key in plugin_keys:
            task = PluginDownloadTask(key, use_proxy=False)
            task.run()

    # All engines need PaddleOCR executable for Phase 2 text detection
    paddleocr_path = utils.find_executable("paddleocr")
    try:
        utils.perform_hardware_check(paddleocr_path, use_gpu)
    except SystemExit as e:
        print(e, flush=True)
        sys.exit(1)

    if ocr_engine == 'paddleocr':
        det_model_dir, rec_model_dir, cls_model_dir = utils.resolve_model_dirs(lang, use_server_model)
    else:
        det_model_dir, rec_model_dir, cls_model_dir = utils.resolve_model_dirs('en', use_server_model)

    google_lens_path = ""
    if ocr_engine == "google_lens":
        google_lens_path = utils.find_executable("chrome-lens")

    ocr = OcrConfig(ocr_engine=ocr_engine, lang=lang, use_gpu=use_gpu, use_angle_cls=use_angle_cls, use_server_model=use_server_model)
    time_range = TimeRange(time_start=time_start, time_end=time_end)
    detection = DetectionConfig(conf_threshold=conf_threshold, ssim_threshold=ssim_threshold, brightness_threshold=brightness_threshold)
    frame = FrameConfig(use_fullframe=use_fullframe, frames_to_skip=frames_to_skip, ocr_image_max_width=ocr_image_max_width, crop_zones=crop_zones, subtitle_position=subtitle_position)
    llm = LlmConfig(api_key=llm_api_key, api_base=llm_api_base, model=llm_model, concurrency=llm_concurrency, disable_inference=llm_disable_inference, max_frames_per_grid=llm_max_frames_per_grid, image_quality=llm_image_quality)
    post = PostProcessConfig(sim_threshold=sim_threshold, max_merge_gap_sec=max_merge_gap_sec, post_processing=post_processing, min_subtitle_duration_sec=min_subtitle_duration_sec, subtitle_alignments=subtitle_alignments, normalize_to_simplified_chinese=normalize_to_simplified_chinese)

    v = Video(video_path, paddleocr_path, det_model_dir, rec_model_dir, cls_model_dir, google_lens_path)
    try:
        v.run_ocr(ocr, time_range, detection, frame, llm, post)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        sys.exit(1)
    subtitles = v.get_subtitles(post.sim_threshold, post.max_merge_gap_sec, ocr.lang, post.post_processing, post.min_subtitle_duration_sec, post.subtitle_alignments)

    with open(file_path, 'w+', encoding='utf-8') as f:
        f.write(subtitles)
