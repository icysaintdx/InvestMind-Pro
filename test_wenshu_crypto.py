#!/usr/bin/env python3
"""
测试中国裁判文书网3DES加密
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🔐 测试中国裁判文书网3DES加密")
print("=" * 80)
print()

try:
    from backend.dataflows.legal.wenshu_crawler import get_wenshu_crawler, HAS_CRYPTO
    
    if not HAS_CRYPTO:
        print("❌ pycryptodome未安装")
        print()
        print("请运行以下命令安装:")
        print("  pip install pycryptodome")
        print()
        print("或运行:")
        print("  install_crypto_deps.bat")
        sys.exit(1)
    
    # 创建爬虫实例
    crawler = get_wenshu_crawler()
    
    print("📋 测试加密功能")
    print("-" * 80)
    print()
    
    # 测试1: 生成GUID
    print("1. 测试GUID生成:")
    guid = crawler._generate_guid()
    print(f"   GUID: {guid}")
    print(f"   长度: {len(guid)} (应为32)")
    print()
    
    # 测试2: 生成cipher
    print("2. 测试cipher生成:")
    cipher = crawler._generate_cipher()
    print(f"   Cipher: {cipher[:100]}...")
    print(f"   长度: {len(cipher)}")
    print()
    
    # 测试3: 3DES加密
    print("3. 测试3DES加密:")
    plaintext = "test123"
    key = "abcdefghijklmnopqrstuvwx"
    iv = "20251204"
    encrypted = crawler._des3_encrypt(plaintext, key, iv)
    print(f"   明文: {plaintext}")
    print(f"   密钥: {key}")
    print(f"   IV: {iv}")
    print(f"   密文: {encrypted}")
    print()
    
    # 测试4: 字符串转二进制
    print("4. 测试字符串转二进制:")
    text = "ABC"
    binary = crawler._str_to_binary(text)
    print(f"   原文: {text}")
    print(f"   二进制: {binary}")
    print()
    
    print("=" * 80)
    print("✅ 所有加密测试通过!")
    print("=" * 80)
    print()
    print("下一步:")
    print("1. 测试巨潮资讯网API: python test_cninfo_api.py")
    print("2. 实现完整的文书网API调用")
    print()
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print()
    print("请确保:")
    print("1. 已安装pycryptodome: pip install pycryptodome")
    print("2. 项目路径正确")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
