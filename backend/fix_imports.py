"""
Script to fix all imports from 'backend.app' to 'app' for standalone backend deployment.
"""
import os
import re

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace 'from backend.app' with 'from app'
        content = re.sub(r'from backend\.app\.', 'from app.', content)
        
        # Replace 'import backend.app' with 'import app'
        content = re.sub(r'import backend\.app\.', 'import app.', content)
        
        # Replace 'from backend.config' with 'from config'
        content = re.sub(r'from backend\.config', 'from config', content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def fix_all_imports(root_dir):
    """Fix imports in all Python files."""
    fixed_count = 0
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip venv and __pycache__ directories
        dirnames[:] = [d for d in dirnames if d not in ['venv', '__pycache__', '.git']]
        
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(dirpath, filename)
                if fix_imports_in_file(filepath):
                    fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    # Fix imports in app directory
    print("Fixing imports in app directory...")
    fix_all_imports("app")
    
    # Fix imports in tests directory
    print("\nFixing imports in tests directory...")
    fix_all_imports("tests")
    
    print("\nDone! All imports have been fixed.")
