#!/usr/bin/env python3
"""
Utility script to generate bcrypt password hashes for admin users.
Usage: python generate_admin_hash.py
"""

import bcrypt
import getpass

def generate_hash():
    """Generate a bcrypt hash for a password."""
    print("Admin Password Hash Generator")
    print("-" * 40)
    
    password = getpass.getpass("Enter password: ")
    password_confirm = getpass.getpass("Confirm password: ")
    
    if password != password_confirm:
        print("❌ Passwords do not match!")
        return
    
    if len(password) < 8:
        print("❌ Password should be at least 8 characters long!")
        return
    
    # Generate hash with cost factor 12 (good balance of security and performance)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
    hash_string = password_hash.decode('utf-8')
    
    print("\n✅ Hash generated successfully!")
    print("-" * 40)
    print(f"Password hash: {hash_string}")
    print("-" * 40)
    print("\nTo insert this admin into the database, run:")
    print(f"INSERT INTO Admins (username, password_hash) VALUES ('your_username', '{hash_string}');")
    print("\nOr update seed.sql with this hash.")

if __name__ == '__main__':
    generate_hash()
