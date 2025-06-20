from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, AgentType
from gemini_llm import get_llm
from typing import List, Dict, Any
import json

class UserApprovalAgent:
    def __init__(self):
        self.llm = get_llm()
        self.tools = self._get_tools()
        self.executor = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            agent_kwargs={"prompt": self._get_prompt()},
            verbose=True,
            handle_parsing_errors=True,
            iterations=1
        )

    def _get_tools(self) -> List[Tool]:
        tools = [
            Tool(
                name="generate_summary",
                func=self._generate_summary,
                description="Generates summary of proposed changes"
            ),
            Tool(
                name="create_diff_view",
                func=self._create_diff_view,
                description="Creates side-by-side diff view of changes"
            ),
            Tool(
                name="save_approval_log",
                func=self._save_approval_log,
                description="Saves approval decisions to audit log"
            )
        ]
        return tools

    def _get_prompt(self) -> PromptTemplate:
        return PromptTemplate(
            template="""You are a User Approval Agent managing the change approval process.
Your goal is to:
- Summarize proposed changes
- Present clear before/after comparisons
- Track approval decisions
- Maintain audit logs
- Ensure transparency

Input: {input}
Available tools: {tools}
Tool names: {tool_names}

{agent_scratchpad}

Think through this step-by-step:
1. Collect all proposed changes
2. Generate clear summaries
3. Create visual comparisons
4. Record decisions
5. Update audit logs

Response should be in JSON format with:
- changes: list of proposed changes
- comparisons: before/after views
- approval_status: pending/approved/rejected
- audit_trail: decision log

Let's manage these changes!""",
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"]
        )

    def _generate_summary(self, changes) -> Dict:
        """Generate a summary of proposed changes. Handles both dict and string input."""
        summary = {
            "layout_changes": [],
            "content_changes": [],
            "optimizations": []
        }
        if not isinstance(changes, dict):
            # If changes is a string, just return it as a summary
            return {"summary": {"note": str(changes)}}
        # Summarize layout changes
        for change in changes.get("layout", []):
            if not isinstance(change, dict):
                continue
            summary["layout_changes"].append({
                "type": change.get("type"),
                "description": change.get("explanation"),
                "impact": "medium"  # Could be determined based on change scope
            })
        # Summarize content changes
        for change in changes.get("content", []):
            if not isinstance(change, dict):
                continue
            summary["content_changes"].append({
                "type": change.get("type"),
                "description": change.get("explanation"),
                "impact": "low"
            })
        # Summarize optimizations
        for change in changes.get("optimizations", []):
            if not isinstance(change, dict):
                continue
            summary["optimizations"].append({
                "type": change.get("type"),
                "description": change.get("suggestion"),
                "impact": "high"
            })
        return {"summary": summary}

    def _create_diff_view(self, changes) -> Dict:
        """Create side-by-side diff view. Handles both dict and string input."""
        diff_views = []
        if not isinstance(changes, dict):
            # If changes is a string, return a note
            return {"diff_views": [{"note": str(changes)}]}
        for change_type, changes_list in changes.items():
            for change in changes_list:
                if not isinstance(change, dict):
                    continue
                diff_views.append({
                    "type": change_type,
                    "before": change.get("before", ""),
                    "after": change.get("after", ""),
                    "explanation": change.get("explanation", ""),
                    "line_numbers": {
                        "before": change.get("before_line", 0),
                        "after": change.get("after_line", 0)
                    }
                })
        return {"diff_views": diff_views}

    def _save_approval_log(self, decision) -> Dict:
        """Save approval decision to audit log. Handles both dict and string input."""
        if not isinstance(decision, dict):
            # If decision is a string, log it as a comment
            log_entry = {
                "timestamp": None,
                "change_id": None,
                "status": None,
                "approver": None,
                "comments": str(decision)
            }
        else:
            log_entry = {
                "timestamp": decision.get("timestamp"),
                "change_id": decision.get("change_id"),
                "status": decision.get("status"),
                "approver": decision.get("approver"),
                "comments": decision.get("comments")
            }
        # In a real implementation, this would save to a database
        return {"log_entry": log_entry}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        changes = input_data.get('changes', {})
        manual_fixes = input_data.get('manual_fix_required', [])
        summary = f"Proposed Changes: {changes}"
        result = self.executor.run(input=summary)
        # Attach manual fixes to the result for the approval dashboard
        if manual_fixes:
            result['manual_fix_required'] = manual_fixes
        return result
