import subprocess
import os
import sys

def git_operations():
    try:
        os.chdir('/workspace')
        
        print("🔄 Adding file to git...")
        result = subprocess.run(['git', 'add', 'public_menu.py'], 
                              capture_output=True, text=True, check=True)
        print("✅ File added successfully")
        
        print("🔄 Committing changes...")
        result = subprocess.run(['git', 'commit', '-m', 
                               '🔧 FIX: Remove all Markdown to fix entity parsing errors in crypto prices'], 
                              capture_output=True, text=True, check=True)
        print("✅ Commit completed successfully")
        print(f"Commit message: {result.stdout}")
        
        print("🔄 Pushing to GitHub...")
        result = subprocess.run(['git', 'push', 'origin', 'main'], 
                              capture_output=True, text=True, check=True)
        print("✅ Pushed to GitHub successfully!")
        print(f"Push output: {result.stdout}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed:")
        print(f"Error: {e}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        return False
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    git_operations()