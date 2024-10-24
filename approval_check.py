# approval_check.py
import os
import sys
import yaml
from github import Github
from pathlib import Path

class PullRequestApprovalChecker:
    def __init__(self, repo_token: str, repository: str, pull_request_number: int):
        """
        Initialize the checker with GitHub credentials and PR info.
        
        Args:
            repo_token: GitHub personal access token
            repository: Repository in format 'owner/repo'
            pull_request_number: PR number to check
        """
        self.github = Github(repo_token)
        self.repo = self.github.get_repo(repository)
        self.pull_request = self.repo.get_pull(pull_request_number)
        
    def load_required_approvers(self) -> list:
        """Load the list of required approvers from the configuration file."""
        config_path = Path('.github/mandatory-approvers.yml')
        
        if not config_path.exists():
            raise FileNotFoundError(
                "Could not find mandatory-approvers.yml in .github directory"
            )
            
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        return config.get('required_approvers', [])
        
    def get_current_approvals(self) -> set:
        """Get the set of usernames who have approved the PR."""
        reviews = self.pull_request.get_reviews()
        approvals = set()
        
        # Track the latest review state for each user
        user_latest_review = {}
        for review in reviews:
            user_latest_review[review.user.login] = review.state
            
        # Only count users whose latest review was APPROVED
        for username, state in user_latest_review.items():
            if state == 'APPROVED':
                approvals.add(username)
                
        return approvals
        
    def check_approvals(self) -> tuple[bool, list]:
        """
        Check if all required approvers have approved the PR.
        
        Returns:
            tuple: (success, list of missing approvers)
        """
        required_approvers = self.load_required_approvers()
        current_approvals = self.get_current_approvals()
        
        missing_approvers = [
            username for username in required_approvers 
            if username not in current_approvals
        ]
        
        return len(missing_approvers) == 0, missing_approvers

def main():
    # These would typically come from GitHub Actions environment variables
    token = os.environ.get('GITHUB_TOKEN')
    repository = os.environ.get('GITHUB_REPOSITORY')
    pr_number = int(os.environ.get('PR_NUMBER'))
    
    if not all([token, repository, pr_number]):
        print("Error: Missing required environment variables")
        sys.exit(1)
    
    checker = PullRequestApprovalChecker(token, repository, pr_number)
    
    try:
        success, missing_approvers = checker.check_approvals()
        
        if not success:
            print(f"❌ Missing required approvals from: {', '.join(missing_approvers)}")
            sys.exit(1)
        else:
            print("✅ All required approvals have been obtained")
            sys.exit(0)
            
    except Exception as e:
        print(f"Error checking approvals: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
