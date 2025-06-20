from langchain.agents.agent import AgentExecutor
from langgraph.graph import Graph, StateGraph
from typing import Dict, TypedDict, Annotated, Sequence
import operator

from agents.layout_validator import LayoutValidatorAgent
from agents.content_healer import ContentHealerAgent
from agents.fix_generator import FixGeneratorAgent
from agents.code_optimizer import CodeOptimizerAgent
from agents.user_approval import UserApprovalAgent

class AgentState(TypedDict):
    input: str
    layout_issues: Dict
    content_issues: Dict
    fixes: Dict
    optimizations: Dict
    approval: Dict
    final_output: Dict

def create_bug_fixer_graph() -> Graph:
    # Initialize all agents
    layout_validator = LayoutValidatorAgent()
    content_healer = ContentHealerAgent()
    fix_generator = FixGeneratorAgent()
    code_optimizer = CodeOptimizerAgent()
    user_approval = UserApprovalAgent()
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes for each agent
    def validate_layout(state: AgentState) -> AgentState:
        result = layout_validator.run(state["input"])
        print("\n[Layout Validator Agent]")
        print(result)
        state["layout_issues"] = result
        return state

    def heal_content(state: AgentState) -> AgentState:
        result = content_healer.run(state["input"])
        print("\n[Content Healer Agent]")
        print(result)
        state["content_issues"] = result
        return state
    
    def generate_fixes(state: AgentState) -> AgentState:
        result = fix_generator.run({"issues": {"layout": state["layout_issues"], "content": state["content_issues"]}})
        print("\n[Fix Generator Agent]")
        print(result)
        state["fixes"] = result
        return state
    
    def optimize_code(state: AgentState) -> AgentState:
        result = code_optimizer.run({
            "fixes": state["fixes"],
            **state["input"]
        })
        print("\n[Code Optimizer Agent]")
        print(result)
        state["optimizations"] = result
        return state
    
    def get_approval(state: AgentState) -> AgentState:
        result = user_approval.run({
            "changes": {
                "layout": state["fixes"],
                "content": state["fixes"],
                "optimizations": state["optimizations"]
            }
        })
        print("\n[User Approval Agent]")
        print(result)
        state["approval"] = result
        return state
    
    def process_approval(state: AgentState) -> AgentState:
        state["final_output"] = {"status": "pending", "message": "Changes require user approval"}
        print("\n[Final Output]")
        print(state["final_output"]["message"])
        return state

    # Add nodes to the graph
    workflow.add_node("validate_layout", validate_layout)
    workflow.add_node("heal_content", heal_content)
    workflow.add_node("generate_fixes", generate_fixes)
    workflow.add_node("optimize_code", optimize_code)
    workflow.add_node("get_approval", get_approval)
    workflow.add_node("process_approval", process_approval)

    # Define the flow
    workflow.set_entry_point("validate_layout")
    workflow.add_edge("validate_layout", "heal_content")
    workflow.add_edge("heal_content", "generate_fixes")
    workflow.add_edge("generate_fixes", "optimize_code")
    workflow.add_edge("optimize_code", "get_approval")
    workflow.add_edge("get_approval", "process_approval")
    
    # Compile the graph
    app = workflow.compile()
    
    return app

def run_bug_fixer(input_data: Dict) -> Dict:
    """Run the bug fixer workflow"""
    # Create the graph
    graph = create_bug_fixer_graph()
    
    # Initialize the state
    initial_state = AgentState(
        input=input_data,
        layout_issues={},
        content_issues={},
        fixes={},
        optimizations={},
        approval={},
        final_output={}
    )
    
    # Run the workflow
    result = graph.invoke(initial_state)
    
    return result["final_output"]
