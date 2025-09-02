import os
import subprocess
from mutagen import File
import tiktoken

def count_text_tokens(text):
    """
    计算文本的 token 数量（使用 tiktoken，更精确）
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")  # GPT-3.5/4 编码
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Error encoding text: {e}")
        return len(text.split())  # 回退到简单分词

def get_audio_duration_ffprobe(file_path):
    """
    使用 ffprobe 获取音频文件的时长（备用方法）
    """
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration
        else:
            print(f"ffprobe failed for {file_path}: {result.stderr}")
            return 0
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error with ffprobe for {file_path}: {e}")
        return 0

def get_audio_duration(file_path):
    """
    获取音频文件的时长（秒），优先使用 mutagen，失败则用 ffprobe
    """
    try:
        audio = File(file_path)
        if audio is not None and hasattr(audio, 'info') and hasattr(audio.info, 'length') and audio.info.length > 0:
            return audio.info.length
        else:
            print(f"mutagen failed or returned 0 for {file_path}, trying ffprobe...")
            return get_audio_duration_ffprobe(file_path)
    except Exception as e:
        print(f"Error with mutagen for {file_path}: {e}, trying ffprobe...")
        return get_audio_duration_ffprobe(file_path)

def calculate_total_duration(directory):
    """
    计算指定目录下所有音频文件的总时长
    """
    if not os.path.exists(directory):
        print(f"Warning: Directory {directory} does not exist.")
        return 0.0
    
    total_duration = 0.0
    supported_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac']

    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in supported_extensions):
                file_path = os.path.join(root, file)
                duration = get_audio_duration(file_path)
                total_duration += duration
                print(f"{file_path}: {duration:.2f} seconds")

    return total_duration

def calculate_total_tokens(directory):
    """
    计算指定目录下所有文本文件的总token数
    """
    if not os.path.exists(directory):
        print(f"Warning: Directory {directory} does not exist.")
        return 0
    
    total_tokens = 0
    supported_extensions = ['.txt', '.md']

    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in supported_extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        tokens = count_text_tokens(content)
                        total_tokens += tokens
                        print(f"{file_path}: {tokens} tokens")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return total_tokens

def main():
    # 定义目录路径（相对于脚本所在目录）
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # workspace
    input_dir1 = os.path.join(base_dir, 'input')
    input_dir2 = os.path.join(base_dir, 'runs', 'input')
    output_dir = os.path.join(base_dir, 'output')
    output_dir2 = os.path.join(base_dir, 'runs', 'output')

    print("Calculating total duration for workspace/input...")
    total1 = calculate_total_duration(input_dir1)

    print("\nCalculating total duration for workspace/runs/input...")
    total2 = calculate_total_duration(input_dir2)

    total_duration = total1 + total2

    print("\nCalculating total tokens for workspace/output...")
    total_tokens = calculate_total_tokens(output_dir)

    print("\nCalculating total tokens for workspace/runs/output...")
    total_tokens2 = calculate_total_tokens(output_dir2)

    print("\n" + "="*50)
    print("SUMMARY:")
    print("="*50)
    print("Total duration in workspace/input: {:.2f} seconds ({:.2f} minutes)".format(total1, total1 / 60))
    print("Total duration in workspace/runs/input: {:.2f} seconds ({:.2f} minutes)".format(total2, total2 / 60))
    print("Overall total duration: {:.2f} seconds ({:.2f} minutes)".format(total_duration, total_duration / 60))
    print("Total tokens in workspace/output: {}".format(total_tokens))
    print("Total tokens in workspace/runs/output: {}".format(total_tokens2))
    print("="*50)

if __name__ == "__main__":
    main()