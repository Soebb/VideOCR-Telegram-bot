[English](https://github.com/kiriya55/VideOCRplus/blob/main/README.md) | 中文

<p align="center">
<img src="https://github.com/kiriya55/VideOCRplus/blob/master/Pictures/VideOCRplus.png" alt="VideOCRplus 图标" width="128">
  <h1 align="center">VideOCRplus</h1>
  <p align="center">
    从视频中提取硬编码字幕！
    <br />
  </p>
</p>

<br>

## ℹ 关于

**VideOCRplus** 是 [VideOCR](https://github.com/timminator/VideOCR)（作者 timminator）的 fork 版本，新增了 **视觉 LLM OCR 引擎** 和 **插件式组件下载系统**。

通过简单易用的图形界面从视频中提取硬编码（烧录）字幕。VideOCRplus 支持三种 OCR 引擎：

- **PaddleOCR** — 100% 本地文本检测与识别
- **Google Lens** — 混合模式：本地检测 + 云端识别
- **LLM Vision** — 混合模式：本地检测 + 视觉 LLM 识别与语义去重

所有配置均可通过点击轻松完成。

此仓库还提供了可与支持的 OCR 引擎结合使用的命令行版本 VideOCRplus。

### 相比原版的改动

| 功能 | 原版 VideOCR | VideOCRplus |
|------|-------------|-------------|
| OCR 引擎 | PaddleOCR、Google Lens | PaddleOCR、Google Lens、**LLM Vision** |
| 组件管理 | 打包在发布文件中 | **插件式下载**，支持进度追踪 |
| 下载加速 | 无 | 支持 **gh-proxy.com** 加速（中国大陆用户） |
| LLM 去重 | 无 | 通过视觉 LLM 进行**语义去重**（替代 Levenshtein） |
| 并发处理 | 无 | **并发 LLM API 调用**，可配置并发数 |
| LLM 网格优化 | 无 | **自动网格尺寸** + 跨网格文本去重 |
| 源码运行模式 | 无 | `install.bat` / `install.sh` 创建虚拟环境，并通过启动脚本运行 |

## 安装

### 从源码运行

VideOCRplus 现在通过平台脚本启动。安装脚本会创建本地 `.venv` 虚拟环境，并安装 `requirements.txt` 中列出的依赖项。

Windows:

```bat
install.bat
VideOCRplus.bat
```

GNU/Linux 或 macOS:

```bash
chmod +x install.sh VideOCRplus.sh VideOCRplus-cli.sh
./install.sh
./VideOCRplus.sh
```

命令行版本使用同一个虚拟环境：

```bash
./VideOCRplus-cli.sh -h
```

### Windows:
您可以使用安装程序进行安装，也可以直接下载包含所有必需文件（包括可执行文件）的压缩包，解压到目标位置即可。

### Linux:
从发布页面下载压缩包，解压到目标位置。  
如需将 VideOCRplus 添加到应用程序菜单，可在解压后的目录中打开终端并运行以下命令：
```
./install_videocr.sh
```
此命令将创建 VideOCRplus 的快捷方式。如需移除，可运行：  
```
./uninstall_videocr.sh
```

### 插件下载

VideOCRplus 使用插件式系统管理 OCR 引擎组件。首次运行时，可在 GUI 的 **设置** 页面直接下载所需组件：

- **PaddleOCR 模型**（~250MB）— 所有引擎必需（文本检测）
- **PaddleOCR CPU/GPU**（~140MB–1.2GB）— PaddleOCR 引擎必需
- **Google Lens CLI**（~12MB）— Google Lens 引擎必需
- LLM Vision 引擎无需本地组件（使用外部 API）

可选择直接从 GitHub 下载或通过 **gh-proxy.com** 加速下载（推荐中国大陆用户使用）。

## 使用说明

### 从源码运行

运行 `install.bat`（Windows）或 `./install.sh`（GNU/Linux、macOS），然后用 `VideOCRplus.bat` 或 `./VideOCRplus.sh` 启动图形界面。

### 使用 GUI

导入视频后，可通过时间轴或左右方向键浏览视频内容。通过点击拖拽的方式在视频上绘制裁剪框，选择字幕区域。完成后，点击"运行"按钮开始字幕提取。

更多选项可在"高级设置"选项卡中配置，详细信息可参考CLI版本的参数说明。
![image](https://github.com/kiriya55/VideOCRplus/raw/main/Pictures/GUI.png)

## 命令行版本（CLI）使用说明

### 源码运行：
```bash
./VideOCRplus-cli.sh -h
```

### 编译版本（从 releases 下载）：

Windows:
```
.\videocr-cli.exe -h
```

Linux:
```
./videocr-cli.bin -h
```

### 示例用法：
```bash
./VideOCRplus-cli.sh --video_path "视频路径/example.mp4" --output "字幕保存路径/example.srt" --lang en --time_start "18:40" --use_gpu true
```

### LLM Vision 示例用法：
```bash
./VideOCRplus-cli.sh --video_path "视频路径/example.mp4" --output "字幕保存路径/example.srt" --ocr_engine llm_vision --llm_api_key YOUR_KEY --llm_api_base https://api.openai.com/v1 --llm_model gpt-4o
```

更多参数说明请参考下文。

## 性能说明

在 CPU 上运行本地 PaddleOCR 过程可能较慢，建议搭配 GPU 使用。

或者，使用 `google_lens` 引擎可以将流程中最繁重的部分（文本识别）卸载到云端。对于没有强大 GPU 的用户来说，这是一个极佳且快速的选择（需要有效的网络连接）。

`llm_vision` 引擎使用视觉 LLM 进行识别和语义去重。它将字幕帧批量以网格形式发送到 LLM API，比传统的 Levenshtein 距离去重更准确。支持自动网格尺寸调整、基于文本的跨网格去重、SSIM 帧分组。支持 OpenAI 兼容 API 和 Anthropic API。

## 小贴士

裁剪时，在文字上下方留出一定的缓冲空间以提高识别准确率，但不要将裁剪框设置得过大。

### 快速配置参考

|| 更高速度 | 更高准确率 | 备注
-|------------|---------------|--------
输入视频质量       | 使用较低质量           | 使用较高质量  | 高分辨率视频的性能影响可通过裁剪减轻
`frames_to_skip`          | 数值更高               | 数值更低        | 如需完全准确的时间戳，此参数需设为0。
`SSIM阈值`          | 阈值更低             | 阈值更高    | 若连续帧的SSIM超过此阈值，则跳过OCR。较低的值可显著减少OCR处理的帧数。

## 命令行参数说明（CLI版本）

- `video_path`

  待提取字幕的视频路径。

- `output`

  字幕文件（.srt）保存路径。

- `ocr_engine`

  选择用于文本检测和识别的 OCR 引擎。有效值为 `paddleocr`（默认）、`google_lens` 和 `llm_vision`。
  `paddleocr` 在本地执行 100% 的文本检测和识别处理。
  `google_lens` 采用混合处理模式，在本地使用 PaddleOCR 进行文本检测，并使用 Google Lens 进行文本识别。注意：`google_lens` 模式需要有效的网络连接。
  `llm_vision` 采用混合处理模式，在本地使用 PaddleOCR 进行文本检测，并使用视觉 LLM 进行文本识别与语义去重。注意：`llm_vision` 模式需要 API 密钥和有效的网络连接。

- `lang`

  字幕语言。支持的语言及缩写取决于您选择的 `ocr_engine`。
  - 对于 `paddleocr`：请参考 [PaddleOCR文档](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.md)。
  - 对于 `google_lens`：请参考 [Google Lens文档](https://docs.cloud.google.com/vision/docs/languages?hl=zh-cn)。
  - 对于 `llm_vision`：支持多种语言，包括 `auto` 自动检测。

- `subtitle_position`

  指定字幕在视频中的对齐方式，有助于提升识别准确率。

- `conf_threshold`

  文字预测的置信度阈值。低于此值的文字将被忽略。默认值 `75` 适用于大多数场景（仅适用 PaddleOCR）。

  若每行文字过少，可降低此值；若每行文字过多，可提高此值。

- `sim_threshold`

  字幕行的相似度阈值。基于[Levenshtein距离](https://en.wikipedia.org/wiki/Levenshtein_distance)，高于此阈值的字幕行将被合并。默认值`80`适用于大多数场景。

  若字幕行重复过多，可降低此值；若字幕行过少，可提高此值。

- `ssim_threshold`

  若连续帧的SSIM超过此阈值，则该帧在第 1 步的初始过滤中将被视为相似帧并被丢弃。较低的值可显著减少需要进行OCR处理的图像数量。在字幕区域裁剪较精确的情况下，即使将此值降至 85 也能获得良好的效果。

- `post_processing`

  启用后处理步骤，自动分析并修复缺失的空格（PaddleOCR常见问题）。目前仅支持英语、西班牙语、葡萄牙语、德语、意大利语和法语。详情请参考[wordninja-enhanced](https://github.com/timminator/wordninja-enhanced)仓库。

- `max_merge_gap`

  合并相似字幕的最大时间间隔（秒）。默认值0.09（90毫秒）适用于大多数场景。

  若发现相同字幕被错误分割为多条，可增加此值。

- `time_start` 和 `time_end`

  仅提取视频片段中的字幕。时间戳仍以完整视频长度计算。

- `use_fullframe`

  默认使用裁剪区域或底部三分之一帧进行OCR。设为`True`时，将使用完整帧。

- `crop_x(2)`, `crop_y(2)`, `crop_width(2)`, `crop_height(2)`

  指定OCR区域的像素范围。示例见下图：
  ![image](https://github.com/kiriya55/VideOCRplus/raw/main/Pictures/crop_example.png)

- `subtitle_alignment(2)`

  字幕对齐。此参数允许您使用ASS（Advanced SubStation Alpha）标签控制视频帧内字幕的位置。有效值包括：`bottom-left`、`bottom-center`、`bottom-right`、`middle-left`、`middle-center`、`middle-right`、`top-left`、`top-center`、`top-right`。

- `max_ocr_image_width`

  在传递给OCR引擎之前缩小裁剪的图像帧，使其宽度不超过此设定值。较低的数值可缩短处理时间，但设置过低可能会降低OCR识别的准确率。

- `use_gpu`

  设为`True`时，使用GPU进行OCR。

- `use_angle_cls`

  设为 `True` 时，启用分类功能（仅适用 PaddleOCR）。

- `brightness_threshold`
  
  若设置，亮度低于此阈值的像素将被置黑。有效范围为0（黑）至255（白）。适用于白色字幕的视频。

- `frames_to_skip`

  OCR前跳过的帧数。调整时需注意视频的fps。

- `min_subtitle_duration`

  短于此阈值的字幕将被忽略。

- `normalize_to_simplified_chinese`

  在处理前将繁体中文字符转换为简体中文。仅适用于 "Chinese & English" 模式。旨在修复因 OCR 模型在简体文本中不一致地混入繁体字符而导致的字幕合并问题。

- `use_server_model`

  默认使用轻量模型进行OCR。启用后将使用服务器模型，提升检测效果，但会消耗更多资源。建议仅在GPU版本中使用。

### LLM Vision 参数

- `llm_api_key`

  视觉 LLM 服务的 API 密钥。也可通过 `LLM_API_KEY` 环境变量设置。

- `llm_api_base`

  LLM API 端点的基础 URL。支持 OpenAI 兼容 API（如 `https://api.openai.com/v1`）和 Anthropic API（`https://api.anthropic.com`）。也可通过 `LLM_API_BASE` 环境变量设置。

- `llm_model`

  视觉 LLM 的模型名称（如 `gpt-4o`、`claude-sonnet-4-20250514`）。也可通过 `LLM_MODEL` 环境变量设置。

- `llm_concurrency`

  并发 LLM API 请求数。默认为 `4`。数值越大处理越快，但可能触发 API 速率限制。

## 构建与编译说明

### 从源码运行（无需构建）

```bash
git clone https://github.com/kiriya55/VideOCRplus.git
cd VideOCRplus
./install.sh
./VideOCRplus.sh
```

Windows 下运行 `install.bat`，然后运行 `VideOCRplus.bat`。

### 构建编译版本

- 要求：
    - Python 3.9或更高版本
    - Windows:
        - C++构建工具（如Visual Studio的"使用C++的桌面开发"套件）
        - 7zip（需添加到PATH）
        - Tkinter（Windows默认Python安装包含）
    - Linux:
        - 7zip
        - Tkinter
        - 建议安装dbus

- 步骤：
    - 克隆仓库到目标位置：
      ```bash
      git clone https://github.com/kiriya55/VideOCRplus.git
      ```
    - 进入目录并安装依赖：
      ```bash
      cd VideOCRplus
      python -m pip install --upgrade pip
      pip install . --group all
      ```
    - 运行构建脚本：
      ```bash
      python build.py --target cpu
      ```
      更多信息可通过以下命令查看：
    ```bash
    python build.py -h
    ```

### 项目结构

```
VideOCRplus/
├── gui.py              # GUI 入口
├── cli.py              # CLI 入口
├── videocr/            # 核心库
├── languages/          # 界面翻译 (en/ch/ja)
├── build.py            # 构建脚本
├── requirements.txt    # Python 依赖
└── ...
```

## 致谢

- 原始项目：[VideOCR](https://github.com/timminator/VideOCR)，作者 [timminator](https://github.com/timminator)
- OCR 引擎：[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- Google Lens CLI：[Chrome-Lens-OCR](https://github.com/timminator/Chrome-Lens-OCR)

## 许可证

本项目基于 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
