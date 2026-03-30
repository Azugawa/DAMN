#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Whisper 模型下载脚本 - 使用国内镜像
支持自定义下载路径
"""
import os
import sys

# 设置国内镜像源
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

def download_model(model_size: str = "base", save_path: str = None):
    """
    下载 Whisper 模型
    
    Args:
        model_size: 模型大小 (tiny, base, small, medium, large)
        save_path: 自定义保存路径 (可选)
    """
    print(f"🔄 开始下载 faster-whisper-{model_size} 模型...")
    print(f"📡 使用镜像源：hf-mirror.com")
    
    try:
        from huggingface_hub import snapshot_download
        
        # 模型 ID
        model_id = f"guillaumekln/faster-whisper-{model_size}"
        
        # 确定保存路径
        if save_path:
            # 使用自定义路径
            local_dir = os.path.abspath(save_path)
            os.makedirs(local_dir, exist_ok=True)
            print(f"📂 保存到自定义路径：{local_dir}")
            
            # 下载到自定义路径
            model_path = snapshot_download(
                repo_id=model_id,
                local_dir=local_dir,
                local_dir_use_symlinks=False,
            )
        else:
            # 使用默认缓存目录
            cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
            os.makedirs(cache_dir, exist_ok=True)
            
            print(f"📂 使用默认缓存目录：{cache_dir}")
            
            # 下载模型
            model_path = snapshot_download(
                repo_id=model_id,
                cache_dir=cache_dir,
                local_dir=None,
            )
        
        print(f"\n✅ 模型下载完成！")
        print(f"📁 模型路径：{model_path}")
        
        return model_path
    
    except ImportError:
        print("\n❌ 未安装 huggingface_hub")
        print("请运行：pip install huggingface_hub")
        return None
    
    except Exception as e:
        print(f"\n❌ 下载失败：{e}")
        print("\n💡 建议:")
        print("   1. 检查网络连接")
        print("   2. 尝试使用更小的模型 (tiny 或 base)")
        print("   3. 手动下载模型文件")
        return None


def main():
    print("=" * 60)
    print("Whisper 模型下载工具")
    print("=" * 60)
    print()
    
    # 询问是否使用自定义路径
    print("是否使用自定义下载路径？")
    print("  [1] 否 - 使用默认缓存目录")
    print("  [2] 是 - 指定保存路径")
    print()
    
    path_choice = input("→ 选择 (1/2): ").strip()
    
    save_path = None
    if path_choice == "2":
        save_path = input("→ 请输入保存路径 (例如 D:\\models\\whisper): ").strip()
        # 处理路径分隔符
        save_path = save_path.replace("/", "\\")
    
    # 模型选择
    print("\n选择模型大小:")
    print("  [1] tiny  - 最快，准确度一般 (~78MB)")
    print("  [2] base  - 平衡速度和准确度 (~148MB) ⭐推荐")
    print("  [3] small - 更准确，稍慢 (~244MB)")
    print("  [4] medium- 很准确，较慢 (~769MB)")
    print("  [5] large - 最准确，最慢 (~1550MB)")
    print()
    
    choice = input("→ 选择 (1-5): ").strip()
    
    models = {
        "1": "tiny",
        "2": "base",
        "3": "small",
        "4": "medium",
        "5": "large",
    }
    
    model_size = models.get(choice, "base")
    
    # 下载
    model_path = download_model(model_size, save_path)
    
    if model_path:
        print("\n✅ 下载完成！")
        print(f"\n💡 使用方法:")
        print(f"   在 config.py 中设置模型路径:")
        print(f"   WHISPER_CONFIG = {{")
        print(f"       \"model\": \"{model_path}\",")
        print(f"       \"device\": \"auto\",")
        print(f"       \"compute_type\": \"float16\",")
        print(f"   }}")
    else:
        print("\n❌ 下载失败，请检查网络或尝试手动下载")
        print("\n手动下载地址:")
        print(f"  https://hf-mirror.com/guillaumekln/faster-whisper-{model_size}/resolve/main/model.bin")


if __name__ == "__main__":
    main()
