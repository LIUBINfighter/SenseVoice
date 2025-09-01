#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Copyright FunASR (https://github.com/FunAudioLLM/SenseVoice). All Rights Reserved.
#  MIT License  (https://opensource.org/licenses/MIT)

import os
import glob
import argparse
from tqdm import tqdm
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from mutagen.mp4 import MP4
import datetime

def get_audio_metadata(audio_file):
    """提取音频文件的元数据"""
    metadata = {}
    try:
        audio = MP4(audio_file)
        info = audio.info
        
        # 时长
        metadata['duration'] = f"{info.length:.2f}s"
        
        # 采样率
        metadata['sample_rate'] = f"{info.sample_rate} Hz"
        
        # 通道数
        metadata['channels'] = info.channels
        
        # 比特率（如果可用）
        if hasattr(info, 'bitrate'):
            metadata['bitrate'] = f"{info.bitrate} kbps"
        
        # 文件大小
        file_size = os.path.getsize(audio_file)
        metadata['file_size'] = f"{file_size} bytes"
        
        # 最后修改时间作为 record_time
        mtime = os.path.getmtime(audio_file)
        dt = datetime.datetime.fromtimestamp(mtime)
        metadata['record_time'] = dt.strftime("%Y-%m-%d %H:%M:%S")
        
    except Exception as e:
        print(f"Warning: Could not extract metadata from {audio_file}: {str(e)}")
        # 默认值
        metadata['duration'] = "Unknown"
        metadata['sample_rate'] = "Unknown"
        metadata['channels'] = "Unknown"
        metadata['bitrate'] = "Unknown"
        metadata['file_size'] = "Unknown"
        mtime = os.path.getmtime(audio_file)
        dt = datetime.datetime.fromtimestamp(mtime)
        metadata['record_time'] = dt.strftime("%Y-%m-%d %H:%M:%S")
    
    return metadata

def main():
    parser = argparse.ArgumentParser(description='Batch audio transcription using SenseVoice')
    parser.add_argument('--input_dir', type=str, required=True,
                       help='Input directory containing audio files')
    parser.add_argument('--output_dir', type=str, default='output',
                       help='Output directory to save md files')
    parser.add_argument('--model_dir', type=str, default="iic/SenseVoiceSmall",
                       help='Model directory')
    parser.add_argument('--device', type=str, default="cuda:0",
                       help='Device to run model on')
    parser.add_argument('--language', type=str, default="auto",
                       help='Language: auto, zh, en, yue, ja, ko, nospeech')
    parser.add_argument('--batch_size_s', type=int, default=60,
                       help='Batch size in seconds for long audio processing')

    args = parser.parse_args()

    # Load model
    print("Loading model...")
    model = AutoModel(
        model=args.model_dir,
        trust_remote_code=True,
        remote_code="../model.py",
        vad_model="fsmn-vad",
        vad_kwargs={"max_single_segment_time": 30000},
        device=args.device,
    )

    # Get all audio files
    audio_extensions = ['*.wav', '*.mp3', '*.flac', '*.m4a', '*.ogg']
    audio_files = []
    for ext in audio_extensions:
        pattern = os.path.join(args.input_dir, ext)
        found_files = glob.glob(pattern)
        audio_files.extend(found_files)

    if not audio_files:
        print(f"No audio files found in {args.input_dir}")
        print(f"Searched patterns: {[os.path.join(args.input_dir, ext) for ext in audio_extensions]}")
        return

    print(f"Found {len(audio_files)} audio files: {audio_files}")

    # Convert to absolute paths
    audio_files = [os.path.abspath(f) for f in audio_files]
    args.input_dir = os.path.abspath(args.input_dir)

    success_count = 0
    error_count = 0

    for audio_file in tqdm(audio_files, desc="Processing audio files"):
        try:
            filename = os.path.basename(audio_file)
            name_without_ext = os.path.splitext(filename)[0]

            # 提取元数据
            metadata = get_audio_metadata(audio_file)

            res = model.generate(
                input=audio_file,
                cache={},
                language=args.language,
                use_itn=True,
                batch_size_s=args.batch_size_s,
                merge_vad=True,
                merge_length_s=15,
            )

            text = rich_transcription_postprocess(res[0]["text"])

            # 构建 frontmatter
            frontmatter = f"""---
title: {name_without_ext}
record_time: {metadata['record_time']}
duration: {metadata['duration']}
sample_rate: {metadata['sample_rate']}
channels: {metadata['channels']}
bitrate: {metadata['bitrate']}
file_size: {metadata['file_size']}
---
"""

            # Save to individual md file
            output_file = os.path.join(args.output_dir, f"{name_without_ext}.md")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter)
                f.write("\n")
                f.write(text)

            success_count += 1

        except Exception as e:
            print(f"Error processing {audio_file}: {str(e)}")
            error_count += 1

            # Save error to md file
            filename = os.path.basename(audio_file)
            name_without_ext = os.path.splitext(filename)[0]
            
            # 即使出错也尝试提取元数据
            metadata = get_audio_metadata(audio_file)
            
            frontmatter = f"""---
title: {name_without_ext}
record_time: {metadata['record_time']}
duration: {metadata['duration']}
sample_rate: {metadata['sample_rate']}
channels: {metadata['channels']}
bitrate: {metadata['bitrate']}
file_size: {metadata['file_size']}
---
"""

            output_file = os.path.join(args.output_dir, f"{name_without_ext}.md")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter)
                f.write("\n")
                f.write(f"Error: {str(e)}")

    print("Processing complete!")
    print(f"Successfully processed: {success_count} files")
    print(f"Errors: {error_count} files")
    print(f"Results saved to {args.output_dir} directory")

if __name__ == "__main__":
    main()
