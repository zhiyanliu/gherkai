# 演示制作与媒体工具

这些工具负责生图、按页配音和更新成片。最终交付不依赖旧版 PPT 构建脚本。需要 Python 3.10+；视频操作还需 FFmpeg 与 FFprobe。网页字幕版另需 Pillow 和覆盖中文的字体文件。密钥及声音 ID 不在仓库内。

## 制作资料

| 内容 | 入口 |
|---|---|
| 正式 PPT、视频、字幕、讲稿与素材包 | [演示成果](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/presentations/README.md) |
| 定位、视觉、口播与交付约定 | [制作规范](https://github.com/zhiyanliu/gherkai/blob/HEAD/tools/presentations/production.md) |
| 共用图标及许可 | [图标源文件](https://github.com/zhiyanliu/gherkai/blob/HEAD/tools/presentations/assets/icons/) |
| 配套示例的需求、用例与实际操作 | [示例仓库](https://github.com/zhiyanliu/gherkai-webapp-demo/blob/HEAD/README.md) |
| 真实运行材料与使用边界 | [演示证据](https://github.com/zhiyanliu/gherkai-webapp-demo/blob/HEAD/internal/presentations/demo/evidence.md) |

最终 PPT 是页面编辑源，素材包保留逐页画面、配音和主视觉。v12 的字幕经人工修订，文件整理与媒体更新不得改写其文字或时间轴；仅更新画面时复用现有成片音轨。

已确认材料按版本号维护，仓库只保留当前交付，历史由 Git 记录。示例仓库维护后续 demo 的准备计划和运行证据。此目录随公开仓库分发，不保存密钥、凭证或机器连接配置。

工作数据放仓库忽略的 `tools/presentations/work/`，从仓库根目录运行以下命令。

## 生图

`gemini_image.py` 支持提示词、参考图编辑、输出尺寸和预检。密钥从本机 `~/.config/gherkai-presentation/gemini-api-key` 读取，不通过命令行传入。

```bash
python3 tools/presentations/gemini_image.py \
  --model "$GEMINI_IMAGE_MODEL" \
  --prompt-file tools/presentations/work/image-prompt.md \
  --out tools/presentations/work/image.png --dry-run
```

去掉 `--dry-run` 才调用生成服务。生成结果与模型记录保存在指定输出位置，不自动重试付费请求，不覆盖已有素材。

## 按页配音

`minimax_narration.py` 合并 API 调用与批量制作逻辑；密钥读取 `MINIMAX_API_KEY` 或终端隐藏输入，声音 ID 读取 `MINIMAX_VOICE_ID`。

输入 JSON 结构：

```json
{
  "style": {
    "model": "speech-2.8-hd",
    "region": "china",
    "speed": 1.02,
    "emotion": "happy"
  },
  "pronunciation_dict": {"tone": ["gherkai/格儿凯"]},
  "pages": [
    {
      "page": 1,
      "text": "已审阅的口播正文",
      "text_sha256": "正文 UTF-8 字节的 SHA-256",
      "audio_file": "audio/01.mp3"
    }
  ]
}
```

```bash
python3 tools/presentations/minimax_narration.py \
  tools/presentations/work/narration.json --dry-run
```

默认选择全部页面，也可用 `--pages 1,3-5`。去掉预检选项才发送请求；已有完整且正文相同的配音会复用。失败或不完整请求不自动付费重试。此工具生成的原始时间戳不能覆盖人工定稿 SRT。

## 视频画面与字幕更新

`video.py` 合并画面更新、字幕替换及必要的章节/校验逻辑。它要求新输出位置，保留输入文件，复用已认可的音轨。先将最终素材包解压到 `work/materials/`；包内 `manifest.json` 是时间线，`slides/01.png` 等是逐页画面。

只更新画面、保持已认可讲稿和每页时长：

```bash
python3 tools/presentations/video.py refresh \
  --source-video docs/presentations/value-method/gherkai-value-method-v12.mp4 \
  --timeline tools/presentations/work/materials/manifest.json \
  --slides-dir tools/presentations/work/materials/slides \
  --protected-srt docs/presentations/value-method/gherkai-value-method-v12.srt \
  --output tools/presentations/work/updated.mp4 \
  --stage tools/presentations/work/video-refresh
```

替换人工修订字幕，复制画面与音频：

```bash
python3 tools/presentations/video.py subtitles \
  --source-video docs/presentations/value-method/gherkai-value-method-v12.mp4 \
  --subtitles docs/presentations/value-method/gherkai-value-method-v12.srt \
  --output tools/presentations/work/captioned.mp4 \
  --stage tools/presentations/work/subtitle-update
```

画面更新检查第 0 帧为完整首页、逐页画面、直切、结尾淡出与完整解码；字幕替换核对文字、时间轴和视频/音频媒体包不变。两者均检查字幕源未被改写。输出日志仅供当次验收，交付后删除。

新讲稿、新语速或新页数需要重新生成时间线和合成音轨，不能用此画面更新工具代替。素材包的逐页原始配音和正文供后续制作复用；第一份视频无需重新配音。

## 网页字幕版

GitHub 首页使用字幕直接写入画面的播放版，默认静音时也可阅读。字幕位于原幻灯片下方的独立区域，不遮挡页面；源视频和人工修订的 SRT 保持不变。输出为 1920×1200，原幻灯片保持 1920×1080，底部字幕栏高 120 像素。此版本的字幕固定显示，下载版仍保留独立字幕轨。

安装 Pillow 后运行；字体路径按本机配置填写：

```bash
python3 tools/presentations/video.py web-captions \
  --source-video docs/presentations/value-method/gherkai-value-method-v12.mp4 \
  --subtitles docs/presentations/value-method/gherkai-value-method-v12.srt \
  --font "/System/Library/Fonts/Hiragino Sans GB.ttc" \
  --output tools/presentations/work/github-captioned.mp4 \
  --stage tools/presentations/work/github-captions
```

工具复用原音轨和章节，检查每条字幕的起止画面及源文件校验值。字幕时刻按 60 fps 对齐，显示误差小于一帧。上传验收后的播放版，更新首页视频附件地址及交付 manifest 中的 `readme_video` 校验记录。播放版托管在 GitHub 附件服务，仓库保留源视频、字幕和生成工具。
