import os
import subprocess
import hashlib

# Define the GitHub repository URL and branch
GITHUB_REPO_URL = 'https://github.com/username/repo_name'
BRANCH = 'main'

newpath = os.path.join(os.path.curdir,"UpdatingRepo") 
if not os.path.exists(newpath):
    os.makedirs(newpath)

# Define the local directory where the repository will be cloned/pulled
REPO_DIR = newpath

# Define the local directory where the files will be checked


LOCAL_DIR = "/"

# Function to calculate the hash of a file
def calculate_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

# Function to compare two files based on their hashes
def compare_files(file1, file2):
    return calculate_file_hash(file1) == calculate_file_hash(file2)

# Function to get a list of ignored files based on .gitignore
def get_ignored_files(repo_dir):
    gitignore_path = os.path.join(repo_dir, '.gitignore')
    ignored_files = set()

    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ignored_files.add(line)
    return ignored_files

# Function to find all files in a directory, excluding ignored files
def find_files_to_check(local_dir, ignored_files):
    files_to_check = []

    for root, _, files in os.walk(local_dir):
        for file in files:
            rel_dir = os.path.relpath(root, local_dir)
            rel_file = os.path.join(rel_dir, file)

            if not any(rel_file.startswith(ignored) for ignored in ignored_files):
                files_to_check.append(rel_file)
    
    return files_to_check

# Clone the repository if it doesn't exist, otherwise pull the latest changes
if not os.path.exists(REPO_DIR):
    subprocess.run(['git', 'clone', GITHUB_REPO_URL, REPO_DIR])
else:
    subprocess.run(['git', '-C', REPO_DIR, 'pull', 'origin', BRANCH])

# Get ignored files from .gitignore
ignored_files = get_ignored_files(REPO_DIR)

# Find all files to check, excluding ignored files
files_to_check = find_files_to_check(LOCAL_DIR, ignored_files)

# Check and update each file
for rel_file in files_to_check:
    local_file = os.path.join(LOCAL_DIR, rel_file)
    github_file = os.path.join(REPO_DIR, rel_file)

    if os.path.exists(local_file) and os.path.exists(github_file) and compare_files(local_file, github_file):
        print(f'{local_file} is up to date.')
    else:
        print(f'{local_file} is outdated or missing. Updating...')
        os.makedirs(os.path.dirname(local_file), exist_ok=True)
        subprocess.run(['cp', github_file, local_file])

print('Update process completed.')
