#!/usr/bin/env python3
"""
Test script to verify bcrypt authentication implementation.
"""

import sqlite3
import bcrypt
from app import get_db_connection, DATABASE

def test_admin_table():
    """Test that Admins table exists and has correct structure."""
    print("Testing Admins table structure...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Admins'")
    result = cur.fetchone()
    
    if result:
        print("✅ Admins table exists")
        print(f"   Schema: {result['sql'][:100]}...")
    else:
        print("❌ Admins table not found!")
        return False
    
    conn.close()
    return True

def test_default_admin():
    """Test that default admin user exists."""
    print("\nTesting default admin user...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT username, password_hash FROM Admins WHERE username = 'admin'")
    admin = cur.fetchone()
    
    if admin:
        print(f"✅ Found admin user: {admin['username']}")
        print(f"   Hash preview: {admin['password_hash'][:20]}...")
    else:
        print("❌ Default admin user not found!")
        return False
    
    conn.close()
    return True

def test_password_verification():
    """Test bcrypt password verification."""
    print("\nTesting password verification...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT password_hash FROM Admins WHERE username = 'admin'")
    admin = cur.fetchone()
    
    if not admin:
        print("❌ Admin user not found")
        return False
    
    password_hash = admin['password_hash']
    
    # Test correct password
    correct_password = 'admin123'
    result = bcrypt.checkpw(correct_password.encode('utf-8'), password_hash.encode('utf-8'))
    
    if result:
        print(f"✅ Correct password verification: PASSED")
    else:
        print(f"❌ Correct password verification: FAILED")
        return False
    
    # Test incorrect password
    wrong_password = 'wrongpassword'
    result = bcrypt.checkpw(wrong_password.encode('utf-8'), password_hash.encode('utf-8'))
    
    if not result:
        print(f"✅ Incorrect password rejection: PASSED")
    else:
        print(f"❌ Incorrect password rejection: FAILED (should reject)")
        return False
    
    conn.close()
    return True

def test_unique_username():
    """Test that username uniqueness constraint works."""
    print("\nTesting username uniqueness constraint...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Try to insert duplicate username
        test_hash = bcrypt.hashpw('testpass'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute("INSERT INTO Admins (username, password_hash) VALUES ('admin', ?)", (test_hash,))
        conn.commit()
        print("❌ Duplicate username allowed (constraint not working)")
        return False
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e):
            print("✅ Username uniqueness constraint: WORKING")
            return True
        else:
            print(f"❌ Unexpected error: {e}")
            return False
    finally:
        conn.close()

def test_hash_format():
    """Test that hash is in correct bcrypt format."""
    print("\nTesting bcrypt hash format...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT password_hash FROM Admins WHERE username = 'admin'")
    admin = cur.fetchone()
    
    if not admin:
        print("❌ Admin user not found")
        return False
    
    password_hash = admin['password_hash']
    
    # Bcrypt hash format: $2b$12$...
    if password_hash.startswith('$2b$') and len(password_hash) == 60:
        print(f"✅ Hash format: VALID")
        print(f"   Format: {password_hash[:7]}...")
        print(f"   Length: {len(password_hash)} chars (expected 60)")
        return True
    else:
        print(f"❌ Hash format: INVALID")
        print(f"   Got: {password_hash[:20]}...")
        return False
    
    conn.close()

def main():
    print("=" * 60)
    print("Building Reservation System - Auth Tests")
    print("=" * 60)
    print(f"Database: {DATABASE}\n")
    
    tests = [
        test_admin_table,
        test_default_admin,
        test_hash_format,
        test_password_verification,
        test_unique_username,
    ]
    
    results = []
    for test_func in tests:
        try:
            results.append(test_func())
        except Exception as e:
            print(f"❌ Test {test_func.__name__} raised exception: {e}")
            results.append(False)
        print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Authentication system is working!")
    else:
        print("❌ SOME TESTS FAILED - Review errors above")
    
    print("=" * 60)
    
    return passed == total

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
