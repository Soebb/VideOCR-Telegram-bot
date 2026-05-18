English | [中文](https://github.com/kiriya55/VideOCRplus/blob/main/README_ch.md)

<p align="center">
<img src="https://github.com/kiriya55/VideOCRplus/blob/master/Pictures/VideOCRplus.png" alt="VideOCRplus Icon" width="128">
  <h1 align="center">VideOCRplus</h1>
  <p align="center">
    Extract hardcoded subtitles from videos!
    <br />
  </p>
</p>


<br>

## ℹ About

**VideOCRplus** is a fork of [VideOCR](https://github.com/timminator/VideOCR) by timminator, extended with a **Vision LLM OCR engine** and a **plugin-based component download system**.

Extract hardcoded (burned-in) subtitles from videos via a simple-to-use GUI. VideOCRplus supports three OCR engines:

- **PaddleOCR** — 100% local text detection and recognition
- **Google Lens** — Hybrid mode: local detection + cloud recognition
- **LLM Vision** — Hybrid mode: local detection + Vision LLM recognition with semantic deduplication

Everything can be easily configured via a few clicks.

This repository also provides a CLI version of VideOCRplus.

### What's New Compared to the Original

| Feature | Original VideOCR | VideOCRplus |
|---------|-----------------|-------------|
| OCR Engines | PaddleOCR, Google Lens | PaddleOCR, Google Lens, **LLM Vision** |
| Component Management | Bundled in release | **Plugin-based download** with progress tracking |
| Download Acceleration | N/A | **gh-proxy.com** support for China users |
| LLM Deduplication | N/A | **Semantic dedup** via Vision LLM (replaces Levenshtein) |
| Concurrent Processing | N/A | **Concurrent LLM API calls** with configurable workers |
| LLM Grid Optimization | N/A | **Auto grid sizing** + text-based cross-grid dedup |
| Source Run Mode | N/A | `install.bat` / `install.sh` create a virtual environment, then launch with app scripts |

## Setup

### From source

VideOCRplus is launched through platform scripts. The install scripts create a local `.venv` virtual environment and install everything listed in `requirements.txt`.

Windows:

```bat
install.bat
VideOCRplus.bat
```

GNU/Linux or macOS:

```bash
chmod +x install.sh VideOCRplus.sh VideOCRplus-cli.sh
./install.sh
./VideOCRplus.sh
```

The CLI helper uses the same virtual environment:

Windows:

```bat
VideOCRplus-cli.bat -h
```

GNU/Linux or macOS:

```
./VideOCRplus-cli.sh -h
```

### Packaged releases

Windows users can also install with the setup installer or download a release folder that includes the executable.

GNU/Linux users can download the tarball archive from the releases page and unzip it. To add VideOCRplus to the application menu, run:

```
./install_videocr.sh
```

Remove the shortcut with `./uninstall_videocr.sh`.

### Plugin Downloads

VideOCRplus uses a plugin-based system for OCR engine components. On first run, the required components can be downloaded directly from the GUI **Settings** tab:

- **PaddleOCR Models** (~250MB) — Required for all engines (text detection)
- **PaddleOCR CPU/GPU** (~140MB–1.2GB) — Required for PaddleOCR engine
- **Google Lens CLI** (~12MB) — Required for Google Lens engine
- LLM Vision engine requires no local components (uses external API)

You can choose between direct GitHub download or **gh-proxy.com** acceleration (recommended for users in China).

## Usage

### Source Run Mode

Run `install.bat` on Windows or `./install.sh` on GNU/Linux/macOS, then start the GUI with `VideOCRplus.bat` or `./VideOCRplus.sh`.

### Using the GUI

Import a video and seek through the video via the timeline. You can also use the right and left arrow keys. Then draw a crop box over the subtitle region. Use click+drag to select. Afterwards start the subtitle extraction process via the "Run" button.

Further options can be configured in the "Advanced Settings" tab. You can find more info about them in the parameters section available in the CLI version.
![image](https://github.com/kiriya55/VideOCRplus/blob/main/Pictures/GUI.png)

## Usage (CLI version)

### From source:
```bash
./VideOCRplus-cli.sh -h
```

### Compiled binary (from releases):

Windows:
```
.\videocr-cli.exe -h
```

Linux:
```
./videocr-cli.bin -h
```

### Example usage:
```bash
./VideOCRplus-cli.sh --video_path "Path/to/your/video/example.mp4" --output "Path/to/your/desired/subtitle/location/example.srt" --lang en --time_start "18:40" --use_gpu true
```

### Example usage with LLM Vision:
```bash
./VideOCRplus-cli.sh --video_path "Path/to/your/video/example.mp4" --output "Path/to/your/desired/subtitle/location/example.srt" --ocr_engine llm_vision --llm_api_key YOUR_KEY --llm_api_base https://api.openai.com/v1 --llm_model gpt-4o
```

More info about the arguments can be found in the parameters section further down.

## Performance

Local OCR processing with PaddleOCR can be slow on a CPU. Using this in combination with a GPU is highly recommended.

Alternatively, using the `google_lens` engine offloads the heaviest part of the pipeline (text recognition) to the cloud. This makes it an excellent and fast choice for users without a powerful GPU, provided they have an active internet connection.

The `llm_vision` engine uses a Vision LLM for both recognition and semantic deduplication. It sends batches of subtitle frames as grids to the LLM API, achieving better deduplication accuracy than traditional Levenshtein distance. Features automatic grid sizing based on video dimensions, text-based cross-grid deduplication, and SSIM-based frame grouping. Supports OpenAI-compatible and Anthropic APIs.

## Tips

When cropping, leave a bit of buffer space above and below the text to ensure accurate readings, but also don't make the box to large.

### Quick Configuration Cheatsheet

|| More Speed | More Accuracy | Notes
-|------------|---------------|--------
Input Video Quality       | Use lower quality           | Use higher quality  | Performance impact of using higher resolution video can be reduced with cropping
`frames_to_skip`          | Higher number               | Lower number        | For perfectly accurate timestamps this parameter needs to be set to 0.
`SSIM threshold`          | Lower threshold             | Higher Threshold    | If the SSIM between consecutive frames exceeds this threshold, the frame is considered similar and skipped for OCR. A lower value can greatly reduce the number of images OCR needs to be performed on.


## Command Line Parameters (CLI version)

- `video_path`

  Path for the video where subtitles should be extracted from.

- `output`

  Path for the desired location where the .srt file should be stored.

- `ocr_engine`

  Select the OCR engine to use for text detection and recognition. Valid values are `paddleocr` (default), `google_lens`, and `llm_vision`.
  `paddleocr` uses 100% local processing for both text detection and recognition.
  `google_lens` uses hybrid processing where PaddleOCR handles the text detection locally and Google Lens handles the text recognition. Note: The `google_lens` mode requires an active internet connection.
  `llm_vision` uses hybrid processing where PaddleOCR handles the text detection locally and a Vision LLM handles text recognition with semantic deduplication. Note: The `llm_vision` mode requires an API key and an active internet connection.

- `lang`

  The language of the subtitles. The supported languages and abbreviations depend on your selected `ocr_engine`.
  - For `paddleocr`: See the [PaddleOCR docs](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.en.md).
  - For `google_lens`: See the [Google Lens docs](https://docs.cloud.google.com/vision/docs/languages).
  - For `llm_vision`: Supports a wide range of languages including `auto` for automatic detection.

- `subtitle_position`

  Specifies the alignment of subtitles in the video and allows for better text recognition.

- `conf_threshold`

  Confidence threshold for word predictions. Words with lower confidence than this value will be discarded. The default value `75` is fine for most cases (PaddleOCR only).

  Make it closer to 0 if you get too few words in each line, or make it closer to 100 if there are too many excess words in each line.

- `sim_threshold`

  Similarity threshold for subtitle lines. Subtitle lines with larger [Levenshtein](https://en.wikipedia.org/wiki/Levenshtein_distance) ratios than this threshold will be merged together. The default value `80` is fine for most cases.

  Make it closer to 0 if you get too many duplicated subtitle lines, or make it closer to 100 if you get too few subtitle lines.

- `ssim_threshold`

  If the SSIM between consecutive frames exceeds this threshold, the frame is considered similar and discarded during initial frame filtering in Step 1. A lower value can greatly reduce the number of images OCR needs to be performed on. On relatively tight crop boxes around the subtitle area good results could be seen with this value all the way lowered to 85.

- `post_processing`

  This parameter adds a post processing step to the subtitle detection. The detected text will be analyzed for missing spaces (as this is a common issue with PaddleOCR) and tries to insert them automatically. Currently only available for English, Spanish, Portuguese, German, Italian and French. For more info check out my [wordninja-enhanced](https://github.com/timminator/wordninja-enhanced) repository.

- `max_merge_gap`

  Maximum allowed time gap (in seconds) between two subtitles to be considered for merging if they are similar. The default value 0.09 (i.e., 90 milliseconds) works well in most scenarios.

  Increase this value if you notice that the output SRT file contains several subtitles with the same text that should be merged into a single one and are wrongly split into multiple ones. This can happen if the PaddleOCR OCR engine is not able to detect any text for a short amount of time while the subtitle is displayed in the selected video.

- `time_start` and `time_end`

  Extract subtitles from only a clip of the video. The subtitle timestamps are still calculated according to the full video length.

- `use_fullframe`

  By default, the specified cropped area is used for OCR or if a crop is not specified, then the bottom third of the frame will be used. By setting this value to `True` the entire frame will be used.

- `crop_x(2)`, `crop_y(2)`, `crop_width(2)`, `crop_height(2)`

  Specifies the bounding area(s) in pixels for the portion of the frame that will be used for OCR. See image below for example:
  ![image](https://github.com/kiriya55/VideOCRplus/blob/main/Pictures/crop_example.png)

- `subtitle_alignment(2)`

  Subtitle alignment. This parameter allows you to control the position of the subtitles within the video frame using ASS (Advanced SubStation Alpha) tags. Valid values are: `bottom-left`, `bottom-center`, `bottom-right`, `middle-left`, `middle-center`, `middle-right`, `top-left`, `top-center`, `top-right`.

- `max_ocr_image_width`

  Downscales the cropped image frame so its width does not exceed this value before passing it to the OCR engine. A lower value shortens the processing time, but setting it too low can reduce OCR accuracy.

- `use_gpu`

  Set to `True` if performing OCR with GPU.

- `use_angle_cls`

  Set to `True` if classification should be enabled (PaddleOCR only).

- `brightness_threshold`
  
  If set, pixels whose brightness are less than the threshold will be blackened out. Valid brightness values range from 0 (black) to 255 (white). This can help improve accuracy when performing OCR on videos with white subtitles.

- `frames_to_skip`

  The number of frames to skip before sampling a frame for OCR. Keep in mind the fps of the input video before increasing.

- `min_subtitle_duration`

  Subtitles shorter than this threshold will be omitted from the final subtitle file.

- `normalize_to_simplified_chinese`

  Traditional Chinese characters will be converted to Simplified Chinese before processing. Only active for \"Chinese & English\". Tries to fix subtitle merging issues caused by the OCR model inconsistently mixing Traditional characters into Simplified text.

- `use_server_model`

  By default the smaller model are used for the OCR process. This parameter enables the usage of the server models for OCR. This can result in better text detection at the cost of more processing power. Should only ever be used in the GPU version.

### LLM Vision Parameters

- `llm_api_key`

  API key for the Vision LLM service. Can also be set via the `LLM_API_KEY` environment variable.

- `llm_api_base`

  Base URL for the LLM API endpoint. Supports OpenAI-compatible APIs (e.g., `https://api.openai.com/v1`) and Anthropic API (`https://api.anthropic.com`). Can also be set via the `LLM_API_BASE` environment variable.

- `llm_model`

  Model name to use for the Vision LLM (e.g., `gpt-4o`, `claude-sonnet-4-20250514`). Can also be set via the `LLM_MODEL` environment variable.

- `llm_concurrency`

  Number of concurrent LLM API requests. Default is `4`. Higher values speed up processing but may hit API rate limits.


## Build and Compile Instructions

### Source Run Mode (no build required)

```bash
git clone https://github.com/kiriya55/VideOCRplus.git
cd VideOCRplus
./install.sh
./VideOCRplus.sh
```

On Windows, run `install.bat` and then `VideOCRplus.bat`.

### Building Compiled Binaries

- Requirements:
    - Python 3.9 or higher

    - Windows:
        - C++ Build Tools (e.g Visual Studio with "Desktop development with C++" kit installed)
        - 7zip (needs to be available from path)
        - Tkinter (comes with the default python installation on Windows)

    - Linux:
        - 7zip
        - Tkinter
        - Working dbus installation is recommended

- Instructions:

    - Clone the repository to your desired location:
      ```bash
      git clone https://github.com/kiriya55/VideOCRplus.git
      ```
    - Navigate into the cloned folder and install all dependencies:
      ```bash
      cd VideOCRplus
      python -m pip install --upgrade pip
      pip install . --group all
      ```
    - Execute the build script to create the desired build:
      ```bash
      python build.py --target cpu
      ```
      More info can be found via:
    ```bash
    python build.py -h
    ```

### Project Structure

```
VideOCRplus/
├── gui.py              # GUI entry point
├── cli.py              # CLI entry point
├── videocr/            # Core library
├── languages/          # UI translations (en/ch/ja)
├── build.py            # Build script
├── requirements.txt    # Python dependencies
└── ...
```

## Credits

- Original project: [VideOCR](https://github.com/timminator/VideOCR) by [timminator](https://github.com/timminator)
- OCR engine: [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- Google Lens CLI: [Chrome-Lens-OCR](https://github.com/timminator/Chrome-Lens-OCR)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
