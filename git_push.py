import subprocess
import os
import sys

def git_push():
    try:
        # Change to workspace
        os.chdir('/workspace')
        
        # Add file
        print("🔄 Adding file...")
        result = subprocess.run(['git', 'add', 'public_menu.py'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Add failed: {result.stderr}")
            return False
        
        # Commit
        print("🔄 Committing...")
        result = subprocess.run(['git', 'commit', '-m', 
                               '🔧 FIX: Remove all Markdown to fix entity parsing errors in crypto prices'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Commit failed: {result.stderr}")
            return False
        
        # Push
        print("🔄 Pushing to GitHub...")
        result = subprocess.run(['git', 'push', 'origin', 'main'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Push failed: {result.stderr}")
            return False
        
        print("✅ Successfully pushed to GitHub!")
        return True
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    git_push()