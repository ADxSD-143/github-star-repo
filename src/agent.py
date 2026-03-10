import time
import json
from pathlib import Path
from browser_utils import BrowserManager
from screencapture import capture_screen
from ocr_engine import extract_text_from_image
from llm_client import LLMClient

# Prompts for the various phases
PROMPTS = {
    "auth_verify": (
        "The user has provided the following GitHub repository name: {repo_name}. "
        "Confirm you have received this repository name. Verify that you are authenticated "
        "to access this repository via the developer's GitHub account by looking at the profile/header. "
        "Report the authenticated username."
    ),
    "code_summary": (
        "Navigate to the root directory of the {repo_name} repository. List the top directories/files "
        "and their contents visible on the screen. Briefly describe their apparent purpose. "
    ),
    "ocr_analysis_subprompt": (
        "You are verifying a web automation action. You will receive OCR text extracted from a screenshot "
        "of the browser window after an action was taken. Analyze this text to determine if the action "
        "was successful according to the current goal: {current_goal}\n\n"
        "Provide your analysis as a strict JSON object with the following keys:\n"
        "1. \"success\": boolean (true if action appears successful, false otherwise)\n"
        "2. \"reasoning\": string (explanation of your conclusion based on the OCR text)\n"
        "3. \"extracted_data\": object (any specific data requested by the goal, e.g., username, directories)\n\n"
        "Do not include any text outside the JSON object."
    ),
    "doc_review": (
        "Navigate to the README.md file within the {repo_name} repository and view its contents. "
        "Extract the project description, installation instructions, and usage examples. "
        "Summarize the key features and functionality of the project."
    ),
    "dependency_analysis": (
        "Identify the primary dependencies listed in the project's dependency file (e.g., requirements.txt, package.json). "
        "Click into that file if visible. List the dependency name, version, and a brief description of its purpose."
    )
}

class RepoInsightAgent:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.repo_name = repo_url.split("github.com/")[-1] if "github.com/" in repo_url else repo_url
        
        self.browser_manager = BrowserManager()
        self.llm_client = LLMClient()
        self.max_retries = 3

    def run_analysis_loop(self, goal_description: str) -> dict:
        """
        Executes the feedback loop: Capture -> OCR -> LLM Analysis.
        Returns the parsed JSON response from the LLM.
        """
        print(f"\n--- Running Analysis Loop ---")
        print(f"Goal: {goal_description}")
        
        for attempt in range(self.max_retries):
            print(f"Attempt {attempt + 1}/{self.max_retries}...")
            
            # 1. Capture screen
            screenshot_path = capture_screen("temp_capture.png")
            print("Screenshot captured.")
            
            # 2. Extract OCR
            ocr_text = extract_text_from_image(screenshot_path)
            # print(f"OCR Extracted: {len(ocr_text)} characters.")
            
            # 3. Analyze via LLM
            system_prompt = PROMPTS["ocr_analysis_subprompt"].format(current_goal=goal_description)
            llm_response = self.llm_client.analyze_action(system_prompt, ocr_text)
            
            # Parse JSON
            
            try:
                import re

                cleaned_response = llm_response.replace('```json', '').replace('```', '').strip()
  

                # Extract JSON safely
                match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)

                if match:
                    json_block = match.group()

                    # Fix missing closing brace if model forgot it
                    if json_block.count("{") > json_block.count("}"):
                        json_block += "}"

                    result = json.loads(json_block)

                    if result.get("success"):
                        print("Action Successful!")
                        print(f"Reasoning: {result.get('reasoning')}")
                        return result
                    else:
                        print(f"Action failed. LLM Reasoning: {result.get('reasoning')}")
                        time.sleep(2)

                else:
                    raise ValueError("No JSON object found in LLM response")

            except Exception as e:
                print(f"Failed to parse LLM response as JSON: {e}")
                print(f"Raw Response: {llm_response}")
                
        print("Max retries reached for this action.")
        return {"success": False, "reasoning": "Max retries exceeded."}

    def execute_phase_1(self):
        """Phase 1: Verification & Repo Navigation"""
        print("\n--- Phase 1: Authentication & Navigation ---")
        target_url = f"https://github.com/{self.repo_name}"
        self.browser_manager.navigate(target_url)
        
        goal = PROMPTS["auth_verify"].format(repo_name=self.repo_name)
        result = self.run_analysis_loop(goal)
        return result

    def execute_phase_2(self):
        """Phase 2: Code Summary"""
        print("\n--- Phase 2: Code Summary ---")
        goal = PROMPTS["code_summary"].format(repo_name=self.repo_name)
        result = self.run_analysis_loop(goal)
        return result

    def execute_phase_3(self):
        """Phase 3: Documentation Review"""
        print("\n--- Phase 3: Documentation Review ---")
        # Direct navigation to typical README paths could save robust clicking logic for this PoC
        target_url = f"https://github.com/{self.repo_name}/blob/main/README.md"
        self.browser_manager.navigate(target_url)
        
        goal = PROMPTS["doc_review"].format(repo_name=self.repo_name)
        result = self.run_analysis_loop(goal)
        
        # Fallback to master if main doesn't exist (basic handling)
        if not result.get("success") and "404" in result.get("reasoning", ""):
           print("README not found on main branch. Trying master...")
           self.browser_manager.navigate(f"https://github.com/{self.repo_name}/blob/master/README.md")
           result = self.run_analysis_loop(goal)

        return result

    def execute_phase_4(self):
        """Phase 4: Dependency Analysis"""
        print("\n--- Phase 4: Dependency Analysis ---")
        print("Checking common dependency files...")
        
        # Test a few common paths for Python/JS. A robust agent would click through the UI found in Phase 2.
        common_paths = [
            f"https://github.com/{self.repo_name}/blob/main/requirements.txt",
            f"https://github.com/{self.repo_name}/blob/main/package.json"
        ]
        
        goal = PROMPTS["dependency_analysis"]
        result = {"success": False}
        
        for path in common_paths:
            self.browser_manager.navigate(path)
            # Give it a small pause to check if the page is a 404 visually before capturing
            time.sleep(2)
            result = self.run_analysis_loop(goal)
            if result.get("success"):
                break
                
        return result

    def run(self):
        try:
            self.browser_manager.start()
            
            # Execute Phases
            res1 = self.execute_phase_1()
            if not res1.get("success"):
                print("Failed at Phase 1. Aborting.")
                return

            res2 = self.execute_phase_2()
            print(f"\nPhase 2 Extracted Data: {json.dumps(res2.get('extracted_data'), indent=2)}")
            
            res3 = self.execute_phase_3()
            print(f"\nPhase 3 Extracted Data: {json.dumps(res3.get('extracted_data'), indent=2)}")

            res4 = self.execute_phase_4()
            print(f"\nPhase 4 Extracted Data: {json.dumps(res4.get('extracted_data'), indent=2)}")
            
            print("\n" + "="*50)
            print("RepoInsight Analysis Complete!")
            print("="*50)
            
        finally:
            self.browser_manager.stop()

if __name__ == "__main__":
    # Test execution
    test_repo = "microsoft/playwright-python" # Public repo for testing navigation
    agent = RepoInsightAgent(test_repo)
    agent.run()
