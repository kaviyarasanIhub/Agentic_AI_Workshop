from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, AgentType
from gemini_llm import get_llm
from typing import List, Dict, Any
import json

class FixGeneratorAgent:
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
                name="generate_layout_fix",
                func=self._generate_layout_fix,
                description="Generates fixes for layout issues"
            ),
            Tool(
                name="generate_content_fix",
                func=self._generate_content_fix,
                description="Generates fixes for content issues"
            ),
            Tool(
                name="generate_js_fix",
                func=self._generate_js_fix,
                description="Generates fixes for JavaScript issues"
            )
        ]
        return tools

    def _get_prompt(self) -> PromptTemplate:
        return PromptTemplate(
            template="""You are a Fix Generator Agent specialized in creating solutions for web issues.
Your goal is to generate fixes for:
- Layout problems
- Content issues
- JavaScript errors
- CSS conflicts
- Responsive design problems

Input: {input}
Available tools: {tools}
Tool names: {tool_names}

{agent_scratchpad}

Think through this step-by-step:
1. Analyze the reported issues
2. Generate appropriate fixes
3. Ensure compatibility
4. Provide before/after snippets
5. Add implementation notes

Response should be in JSON format with:
- fixes: list of proposed changes
- code_snippets: before/after code
- compatibility_notes: any potential conflicts
- implementation_steps: how to apply fixes

IMPORTANT: Only use the available tools. Do NOT use 'manual fix', 'None', or any unsupported action. If a fix cannot be automated, return a message explaining why.

Let's generate some solutions!""",
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"]
        )

    def _generate_layout_fix(self, issue) -> Dict:
        """Generate fixes for layout issues"""
        fixes = []
        
        # Accept both dict and string
        if isinstance(issue, str):
            # Optionally, you could parse the string for keywords
            return {"fixes": [{"type": "layout_fix", "before": "", "after": "", "explanation": issue}]}
        
        if issue.get("type") == "positioning":
            fixes.append({
                "type": "css_fix",
                "before": "position: absolute;",
                "after": "position: relative;\nz-index: 1;",
                "explanation": "Changed to relative positioning to prevent overlap"
            })
        elif issue.get("type") == "responsive":
            fixes.append({
                "type": "css_fix",
                "before": "width: 300px;",
                "after": "width: 100%;\nmax-width: 300px;",
                "explanation": "Made width responsive with max-width constraint"
            })
            
        return {"fixes": fixes}

    def _generate_content_fix(self, issues) -> Dict:
        """Generate fixes for content issues. Accepts a list of issues or a single issue."""
        fixes = []
        # Accept both a single dict or a list
        if isinstance(issues, dict):
            issues = [issues]
        for issue in issues:
            if not isinstance(issue, dict):
                # Optionally log or skip non-dict issues
                continue
            if issue.get("type") == "placeholder":
                fixes.append({
                    "type": "content_fix",
                    "before": "Lorem ipsum dolor sit amet",
                    "after": "[Add relevant content here]",
                    "explanation": "Remove lorem ipsum placeholder"
                })
            elif issue.get("type") == "missing_image":
                fixes.append({
                    "type": "html_fix",
                    "before": '<img src="#" alt="">',
                    "after": '<img src="path/to/image.jpg" alt="Descriptive text">',
                    "explanation": "Add proper image source and alt text"
                })
        return {"fixes": fixes}

    def _generate_js_fix(self, issue) -> Dict:
        """Generate fixes for JavaScript issues. Accepts a dict or a string."""
        fixes = []
        if not isinstance(issue, dict):
            # Optionally log or skip non-dict issues
            return {"fixes": fixes}
        if issue.get("type") == "syntax_error":
            fixes.append({
                "type": "js_fix",
                "before": "function() { console.log('error'",
                "after": "function() { console.log('error'); }",
                "explanation": "Fixed missing closing bracket and semicolon"
            })
        elif issue.get("type") == "potential_null":
            fixes.append({
                "type": "js_fix",
                "before": "if (obj.property)",
                "after": "if (obj && obj.property)",
                "explanation": "Added null check for obj"
            })
        elif issue.get("type") == "missing_element":
            fixes.append({
                "type": "js_fix",
                "before": "document.getElementById('missing-id').innerText = 'Clicked!';",
                "after": "var el = document.getElementById('missing-id');\nif (el) { el.innerText = 'Clicked!'; }",
                "explanation": "Added check for missing element before accessing innerText"
            })
        return {"fixes": fixes}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fixes for all issues"""
        issues = input_data.get('issues', {})
        summary = f"Layout Issues: {issues.get('layout', [])}\nContent Issues: {issues.get('content', [])}"
        result = self.executor.run(input=summary)
        valid_tools = ["generate_layout_fix", "generate_content_fix", "generate_js_fix"]
        manual_fix_required = []
        # Check if the result is a dict and contains a tool/action name
        if isinstance(result, dict):
            action_name = result.get("tool") or result.get("action")
            if action_name and action_name not in valid_tools:
                # If the agent tried an unsupported action, log as manual fix required
                manual_fix_required.append({
                    "issue": summary,
                    "reason": f"Cannot auto-fix with available tools. Action '{action_name}' is not supported."
                })
                return {"fixes": [], "manual_fix_required": manual_fix_required}
        # If result is just a general suggestion, not a real fix
        if (isinstance(result, dict) and not result.get("fixes")) or (isinstance(result, str) and 'best practice' in result):
            manual_fix_required.append({
                "issue": summary,
                "reason": "No automated fix could be generated. Manual intervention required."
            })
            return {"fixes": [], "manual_fix_required": manual_fix_required}
        return result
