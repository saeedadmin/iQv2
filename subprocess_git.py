import subprocess
import sys

def execute_git_commands():
    commands = [
        ["git", "add", "public_menu.py"],
        ["git", "commit", "-m", "🔧 FIX: Remove all Markdown to fix entity parsing errors in crypto prices"],
        ["git", "push", "origin", "main"]
    ]
    
    for i, cmd in enumerate(commands, 1):
        try:
            print(f"🔄 Step {i}: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd="/workspace", 
                                  capture_output=True, text=True, 
                                  timeout=30)
            
            if result.returncode == 0:
                print(f"✅ Step {i} successful")
                if result.stdout:
                    print(f"Output: {result.stdout}")
            else:
                print(f"❌ Step {i} failed")
                print(f"Error: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"❌ Step {i} timed out")
            return False
        except Exception as e:
            print(f"❌ Step {i} exception: {str(e)}")
            return False
    
    print("🎉 All git operations completed successfully!")
    return True

if __name__ == "__main__":
    execute_git_commands()