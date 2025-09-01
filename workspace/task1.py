#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Copyright FunASR (https://github.com/FunAudioLLM/SenseVoice). All Rights Reserved.
#  MIT License  (https://opensource.org/licenses/MIT)

import os
import glob
import json
import argparse
from tqdm import tqdm
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

def main():
    parser = argparse.ArgumentParser(description='Batch audio transcription using SenseVoice')
    parser.add_argument('--input_dir', type=str, required=True,
                       help='Input directory containing audio files')
    parser.add_argument('--output_dir', type=str, default='output',
                       help='Output directory to save txt files')
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

            # Save to individual txt file
            output_file = os.path.join(args.output_dir, f"{name_without_ext}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)

            success_count += 1

        except Exception as e:
            print(f"Error processing {audio_file}: {str(e)}")
            error_count += 1

            # Save error to txt file
            filename = os.path.basename(audio_file)
            name_without_ext = os.path.splitext(filename)[0]
            output_file = os.path.join(args.output_dir, f"{name_without_ext}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Error: {str(e)}")

    print("Processing complete!")
    print(f"Successfully processed: {success_count} files")
    print(f"Errors: {error_count} files")
    print(f"Results saved to {args.output_dir} directory")

if __name__ == "__main__":
    main()
