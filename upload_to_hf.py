from huggingface_hub import HfApi
import os

# Initialize API with token
api = HfApi(token="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")

# Upload files
repo_id = "Saeedm777/stt"
repo_type = "space"

files_to_upload = [
    ("app.py", "/workspace/hf_space_api/app.py"),
    ("requirements.txt", "/workspace/hf_space_api/requirements.txt"),
    ("Dockerfile", "/workspace/hf_space_api/Dockerfile"),
    ("README.md", "/workspace/hf_space_api/README.md"),
    (".gitignore", "/workspace/hf_space_api/.gitignore"),
]

for path_in_repo, local_path in files_to_upload:
    try:
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=path_in_repo,
            repo_id=repo_id,
            repo_type=repo_type,
            commit_message=f"Add {path_in_repo}"
        )
        print(f"✅ Uploaded: {path_in_repo}")
    except Exception as e:
        print(f"❌ Failed to upload {path_in_repo}: {e}")

print("\n🎉 All files uploaded successfully!")
