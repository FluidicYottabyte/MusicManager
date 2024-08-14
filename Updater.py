import os
import subprocess

class GitUpdater:
    def __init__(self, repo_dir=None):
        """
        Initializes the GitUpdater class.

        Parameters:
        repo_dir (str): The directory of the git repository. Defaults to the current directory.
        """
        self.repo_dir = repo_dir if repo_dir else os.getcwd()

    def run_git_command(self, command):
        """
        Runs a git command and returns the output.

        Parameters:
        command (list): The git command to run.

        Returns:
        tuple: stdout and stderr output from the git command.
        """
        result = subprocess.run(command, cwd=self.repo_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip(), result.stderr.strip()

    def fetch_updates(self):
        """
        Fetches the latest changes from the remote repository.
        """
        print("Fetching the latest changes...")
        stdout, stderr = self.run_git_command(['git', 'fetch'])
        
        if stderr:
            print(f"Error during fetch: {stderr}")
        else:
            print(stdout)

    def check_for_updates(self):
        """
        Checks if the local branch is behind the remote branch.

        Returns:
        bool: True if updates are available, False otherwise.
        """
        print("Checking for differences...")
        stdout, stderr = self.run_git_command(['git', 'status', '-uno'])
        
        if "Your branch is behind" in stdout:
            return False
        elif stderr:
            print(f"Error during status check: {stderr}")
        return True

    def pull_updates(self):
        """
        Pulls the latest changes from the remote repository if updates are available.
        """
        if not self.check_for_updates():
            print("Updates are available. Pulling the latest changes...")
            stdout, stderr = self.run_git_command(['git', 'pull'])
            
            if stderr:
                print(f"Error during pull: {stderr}")
            else:
                print(stdout)
        else:
            print("The local repository is up to date.")

    def update(self):
        """
        Executes the full update process: fetch, check, and pull updates if necessary.
        """
        self.fetch_updates()
        self.pull_updates()
        print('Update process completed.')

# Example usage (from another script in the same directory):
# from git_updater import GitUpdater
# updater = GitUpdater()
# updater.update()
