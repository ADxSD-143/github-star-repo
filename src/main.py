import argparse
import sys
from agent import RepoInsightAgent
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="RepoInsight: Safely explore and summarize authenticated GitHub repositories."
    )
    
    parser.add_argument(
        "repo_url",
        type=str,
        help="The GitHub repository URL or name (e.g., 'facebook/react' or 'https://github.com/facebook/react'). "
             "Ensure you are already authenticated in your browser to access this repository."
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*50)
    print(f"Initializing RepoInsight for: {args.repo_url}")
    print("="*50 + "\n")
    
    agent = RepoInsightAgent(args.repo_url)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\nAgent stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
