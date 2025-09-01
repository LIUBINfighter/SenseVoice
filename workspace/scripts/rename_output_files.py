#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
脚本用于重命名 output 文件夹中的所有文件。
命名模式：如果文件名中有 "" 字段，则删除该字段保留其余部分。
如果删除后文件名为空，则赋值为时间戳。
"""

import os
import datetime
from dotenv import load_dotenv

def rename_files_in_output():
    # 加载 .env 文件
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path)
    
    # 从环境变量获取要删除的字符串
    remove_str = os.getenv('REMOVE_STR')
    if not remove_str:
        print("Error: REMOVE_STR not found in .env file. Please set REMOVE_STR in workspace/.env")
        return
    
    # output 文件夹路径（相对于脚本所在目录）
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    
    # 确保 output 目录存在
    if not os.path.exists(output_dir):
        print(f"Output directory {output_dir} does not exist.")
        return
    
    # 遍历 output 目录中的所有文件
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)
        
        # 只处理文件，不处理文件夹
        if not os.path.isfile(filepath):
            continue
        
        # 分离文件名和扩展名
        name, ext = os.path.splitext(filename)
        
        # 检查是否包含要删除的字符串
        if remove_str in name:
            # 删除字符串
            new_name = name.replace(remove_str, '')
            
            # 如果删除后为空，使用时间戳
            if not new_name.strip():
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = timestamp
        else:
            # 如果不包含要删除的字符串，保持原名
            new_name = name
        
        # 构造新文件名
        new_filename = new_name + ext
        new_filepath = os.path.join(output_dir, new_filename)
        
        # 如果新文件名与原文件名不同，则重命名
        if new_filename != filename:
            # 处理文件名冲突
            counter = 1
            while os.path.exists(new_filepath):
                base_name = new_name + f"_{counter}"
                new_filename = base_name + ext
                new_filepath = os.path.join(output_dir, new_filename)
                counter += 1
            
            # 重命名文件
            os.rename(filepath, new_filepath)
            print(f"Renamed: {filename} -> {new_filename}")
        else:
            print(f"No change: {filename}")

if __name__ == "__main__":
    rename_files_in_output()
    print("Renaming complete!")
