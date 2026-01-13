#!/usr/bin/env python3
"""
生成密码哈希值脚本
用于更新初始化数据脚本中的密码哈希值
"""
import bcrypt
import sys

def generate_password_hash(password: str) -> str:
    """生成bcrypt密码哈希"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password_hash(password: str, password_hash: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python generate_password_hash.py <password>")
        print("示例: python generate_password_hash.py password123")
        sys.exit(1)
    
    password = sys.argv[1]
    password_hash = generate_password_hash(password)
    
    print(f"密码: {password}")
    print(f"哈希值: {password_hash}")
    print()
    print("验证:")
    if verify_password_hash(password, password_hash):
        print("✓ 密码哈希验证成功")
    else:
        print("✗ 密码哈希验证失败")
