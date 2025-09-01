# SenseVoice 批量音频转文字处理工具集

## 概述
本工具集基于 SenseVoice 模型，提供多种音频处理脚本：
- `task1.py`: 批量音频转录，输出 JSON 格式结果
- `task2.py`: 批量音频转录，输出 Markdown 格式结果（含元数据）
- `rename_output_files.py`: 批量重命名输出文件工具

## 功能特性
- 支持批量处理多个音频文件（wav, mp3, flac, m4a, ogg）
- 自动检测语言（支持中文、英文、粤语、日语、韩语）
- 支持长音频处理（通过VAD自动分割）
- 多种输出格式：JSON、Markdown、纯文本
- 进度显示和错误处理
- 音频元数据提取（task2）
- 文件批量重命名（去除敏感信息）

## 安装依赖
```bash
# 激活 conda 环境
conda activate sensevoice_env

# 安装项目依赖
pip install -r ../requirements.txt

# 安装额外工具依赖
pip install python-dotenv mutagen
```

## 准备工作
1. 将音频文件放入 `input/` 文件夹
2. 配置 `.env` 文件（用于重命名脚本）
3. 确保输出目录 `output/` 存在

## 脚本使用方法

### 1. task1.py - 批量转录（JSON输出）
```bash
python task1.py --input_dir input --output_dir output --device cpu --language zh
```

**参数说明：**
- `--input_dir`: 音频文件所在文件夹路径（必需）
- `--output_dir`: 输出目录（默认: output）
- `--model_dir`: 模型路径（默认: iic/SenseVoiceSmall）
- `--device`: 运行设备（默认: cuda:0，可改为 cpu）
- `--language`: 语言设置（默认: auto）
- `--batch_size_s`: 长音频批处理大小（默认: 60秒）

**输出格式：**
每个音频文件生成对应的 `.txt` 文件，包含转录文本。

### 2. task2.py - 批量转录（Markdown输出）
```bash
python task2.py --input_dir input --output_dir output --device cpu --language zh
```

**参数说明：** 同 task1.py

**输出格式：**
每个音频文件生成对应的 `.md` 文件，包含：
- Frontmatter 元数据（标题、录制时间、时长、采样率等）
- 转录文本内容

**Frontmatter 示例：**
```yaml
---
title: audio_file_name
record_time: 2024-09-29 16:49:42
duration: 120.50s
sample_rate: 44100 Hz
channels: 2
bitrate: 128 kbps
file_size: 2048576 bytes
---
转录文本内容...
```

### 3. rename_output_files.py - 批量重命名
```bash
cd ../scripts
python rename_output_files.py
```

**功能：**
- 从 `.env` 文件读取要删除的字符串
- 重命名 `output/` 文件夹中的文件
- 删除指定字符串，保留其余部分
- 如果文件名为空，使用时间戳

**配置 .env 文件：**
```env
REMOVE_STR=
```

## 示例

### 处理中文音频文件
```bash
# 使用 task1 生成 JSON 结果
python task1.py --input_dir ./input --language zh --device cpu

# 使用 task2 生成 Markdown 结果
python task2.py --input_dir ./input --language zh --device cpu

# 重命名输出文件
cd ../scripts && python rename_output_files.py
```

### 处理多语言音频
```bash
python task1.py --input_dir ./input --language auto --device cuda:0
```

## 输出文件结构
```
workspace/
├── input/
│   ├── audio1.m4a
│   └── audio2.wav
├── output/
│   ├── audio1.txt          # task1 输出
│   ├── audio1.md           # task2 输出
│   └── audio2.txt
├── .env                    # 重命名配置
└── README.md
```

## 注意事项
1. 首次运行会自动下载模型（约2GB），需要网络连接
2. 长音频会自动通过VAD分割处理，无需担心文件大小
3. task2 需要安装 `mutagen` 库来提取音频元数据
4. 重命名脚本使用 `.env` 文件避免硬编码敏感信息
5. 输出文本包含情感标签（😊😔😡等）和事件标签（🎼👏等）

## 性能优化
- **GPU推荐**：使用 `cuda:0` 可显著提高处理速度
- **批量大小**：长音频使用默认60秒，短音频可增加batch_size
- **并发处理**：如需更高效率，可考虑使用API方式（../api.py）

## 故障排除
- 如果遇到模型加载错误，检查网络连接
- 如果CUDA不可用，使用 `--device cpu`
- 如果内存不足，减少 `batch_size_s` 参数
- 如果音频文件无法读取，检查文件格式和完整性
- 如果重命名脚本出错，检查 `.env` 文件格式
