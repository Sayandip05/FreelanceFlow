"""
Groq AI Service for real-time chat-based worklog generation.
Uses Groq's fast LLM API with LangChain, LangGraph, and LangSmith integration.
"""
import json
from typing import List, Dict, Optional, TypedDict, Literal
from django.conf import settings
from django.utils import timezone

# LangChain and LangGraph imports
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolExecutor
    from langsmith import traceable
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Fallback decorator
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

# Fallback Groq client
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


# LangGraph State Definition for Chat Agent
class ChatAgentState(TypedDict):
    """State for the chat agent graph."""
    messages: List[BaseMessage]
    project_name: str
    contract_details: Optional[Dict]
    report_ready: bool
    report_data: Optional[Dict]
    next_action: Literal["continue", "generate_report", "end"]


class GroqChatService:
    """
    Service for handling AI chat conversations with freelancers using LangGraph.
    Generates structured worklog reports from natural language descriptions.
    """
    
    MODEL = "llama-3.3-70b-versatile"  # Fast, capable model
    MAX_TOKENS = 4096
    TEMPERATURE = 0.7
    
    def __init__(self):
        self.client = None
        self.langchain_client = None
        
        # Initialize direct Groq client (fallback)
        if GROQ_AVAILABLE and hasattr(settings, 'GROQ_API_KEY') and settings.GROQ_API_KEY:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
        
        # Initialize LangChain Groq client for LangGraph
        if LANGCHAIN_AVAILABLE and hasattr(settings, 'GROQ_API_KEY') and settings.GROQ_API_KEY:
            try:
                self.langchain_client = ChatGroq(
                    model=self.MODEL,
                    api_key=settings.GROQ_API_KEY,
                    temperature=self.TEMPERATURE,
                    max_tokens=self.MAX_TOKENS,
                )
            except Exception as e:
                print(f"Failed to initialize LangChain Groq client: {e}")
    
    def is_available(self) -> bool:
        """Check if Groq service is configured and available."""
        return self.client is not None or self.langchain_client is not None
    
    def _get_system_prompt(self, project_name: str, contract_details: Optional[Dict] = None) -> str:
        """Get the system prompt for the AI assistant."""
        return f"""You are an AI worklog assistant for FreelanceFlow, a freelance marketplace platform.

PROJECT: {project_name}

Your role is to help freelancers document their work by:
1. Understanding what they accomplished through natural conversation
2. Asking clarifying questions when needed
3. Generating structured, professional worklog reports
4. Suggesting hours based on the complexity of work described

When the freelancer indicates they're done (e.g., "generate report", "that's all", "submit"), 
you MUST generate a JSON response with this exact structure:

```json
{{
  "report_ready": true,
  "title": "Brief title of the work completed",
  "description": "Detailed description of what was accomplished",
  "hours_worked": 4.5,
  "tasks_completed": [
    "Specific task 1",
    "Specific task 2"
  ],
  "technologies_used": ["Python", "React", "etc"],
  "challenges_faced": "Any challenges overcome (optional)",
  "next_steps": "Suggested next steps (optional)"
}}
```

Guidelines:
- Be professional but conversational
- Ask follow-up questions to get sufficient detail
- Suggest realistic hour estimates based on complexity
- Extract specific technologies/tools mentioned
- Keep the conversation focused on work documentation
- When generating the report, ensure all fields are filled accurately"""
    
    def _create_chat_graph(self, project_name: str) -> StateGraph:
        """
        Create LangGraph workflow for chat agent.
        
        Graph Flow:
        START -> process_message -> check_intent -> [continue_chat | generate_report] -> END
        """
        
        def process_message_node(state: ChatAgentState) -> ChatAgentState:
            """Node: Process user message and generate AI response."""
            if not self.langchain_client:
                state["next_action"] = "end"
                return state
            
            # Get system prompt
            system_prompt = self._get_system_prompt(state["project_name"], state["contract_details"])
            
            # Build messages
            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            
            try:
                # Invoke LLM
                response = self.langchain_client.invoke(messages)
                
                # Add AI response to messages
                state["messages"].append(AIMessage(content=response.content))
                
                # Check if report is ready
                report_data = self._extract_report_json(response.content)
                if report_data:
                    state["report_ready"] = True
                    state["report_data"] = report_data
                    state["next_action"] = "generate_report"
                else:
                    state["report_ready"] = False
                    state["next_action"] = "continue"
                    
            except Exception as e:
                error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try again."
                state["messages"].append(AIMessage(content=error_msg))
                state["next_action"] = "end"
            
            return state
        
        def check_intent_node(state: ChatAgentState) -> ChatAgentState:
            """Node: Check user intent and decide next action."""
            # Already determined in process_message_node
            return state
        
        # Create graph
        workflow = StateGraph(ChatAgentState)
        
        # Add nodes
        workflow.add_node("process_message", process_message_node)
        workflow.add_node("check_intent", check_intent_node)
        
        # Add edges
        workflow.set_entry_point("process_message")
        workflow.add_edge("process_message", "check_intent")
        
        # Conditional edges based on next_action
        workflow.add_conditional_edges(
            "check_intent",
            lambda state: state["next_action"],
            {
                "continue": END,
                "generate_report": END,
                "end": END,
            }
        )
        
        return workflow.compile()
    
    @traceable(
        name="groq_chat_agent",
        tags=["worklog", "groq", "chat", "langgraph"],
        metadata={"model": MODEL}
    )
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        project_name: str,
        contract_details: Optional[Dict] = None
    ) -> Dict:
        """
        Send a chat message to Groq agent and get response using LangGraph.
        Fully traced with LangSmith for monitoring.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            project_name: Name of the project for context
            contract_details: Optional contract information
            
        Returns:
            Dict with 'message', 'report_ready', and optional 'report_data'
        """
        if not self.is_available():
            return self._fallback_response(messages)
        
        # Use LangGraph if available
        if LANGCHAIN_AVAILABLE and self.langchain_client:
            try:
                # Convert messages to LangChain format
                lc_messages = []
                for msg in messages:
                    if msg["role"] == "user":
                        lc_messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        lc_messages.append(AIMessage(content=msg["content"]))
                
                # Create graph
                graph = self._create_chat_graph(project_name)
                
                # Initial state
                initial_state: ChatAgentState = {
                    "messages": lc_messages,
                    "project_name": project_name,
                    "contract_details": contract_details,
                    "report_ready": False,
                    "report_data": None,
                    "next_action": "continue",
                }
                
                # Run graph
                final_state = graph.invoke(initial_state)
                
                # Extract last AI message
                last_message = final_state["messages"][-1].content if final_state["messages"] else ""
                
                return {
                    "message": last_message,
                    "report_ready": final_state["report_ready"],
                    "report_data": final_state["report_data"],
                    "usage": {
                        "model": self.MODEL,
                        "traced": True,
                        "langgraph": True
                    }
                }
                
            except Exception as e:
                print(f"LangGraph error, falling back to direct API: {e}")
        
        # Fallback to direct Groq API
        return self._direct_api_chat(messages, project_name, contract_details)
    
    def _direct_api_chat(
        self,
        messages: List[Dict[str, str]],
        project_name: str,
        contract_details: Optional[Dict] = None
    ) -> Dict:
        """Direct API call fallback when LangGraph is not available."""
        if not self.client:
            return self._fallback_response(messages)
        
        # Prepare messages with system prompt
        system_prompt = self._get_system_prompt(project_name, contract_details)
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=full_messages,
                max_tokens=self.MAX_TOKENS,
                temperature=self.TEMPERATURE,
            )
            
            content = response.choices[0].message.content
            
            # Check if report is ready (contains JSON)
            report_data = self._extract_report_json(content)
            
            return {
                "message": content,
                "report_ready": report_data is not None,
                "report_data": report_data,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            }
            
        except Exception as e:
            return {
                "message": f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                "report_ready": False,
                "report_data": None,
                "error": str(e)
            }
    
    def _extract_report_json(self, content: str) -> Optional[Dict]:
        """Extract report JSON from AI response."""
        import re
        
        # Look for JSON block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Look for raw JSON object
        json_match = re.search(r'\{[\s\S]*"report_ready"[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _fallback_response(self, messages: List[Dict[str, str]]) -> Dict:
        """Fallback response when Groq is not available."""
        last_message = messages[-1]["content"] if messages else ""
        
        # Simple keyword-based response for demo/testing
        if any(word in last_message.lower() for word in ["generate", "report", "done", "submit"]):
            return {
                "message": """I've prepared your worklog report based on our conversation:

```json
{
  "report_ready": true,
  "title": "Development Work Completed",
  "description": "Based on our conversation, work was completed on the project.",
  "hours_worked": 4.0,
  "tasks_completed": ["Development tasks", "Code implementation"],
  "technologies_used": [],
  "challenges_faced": "",
  "next_steps": "Continue with next phase"
}
```

Note: This is a fallback response. Configure GROQ_API_KEY for full AI capabilities.""",
                "report_ready": True,
                "report_data": {
                    "report_ready": True,
                    "title": "Development Work Completed",
                    "description": "Based on our conversation, work was completed on the project.",
                    "hours_worked": 4.0,
                    "tasks_completed": ["Development tasks", "Code implementation"],
                    "technologies_used": [],
                    "challenges_faced": "",
                    "next_steps": "Continue with next phase"
                }
            }
        
        return {
            "message": "I understand. Please tell me more about what you worked on today. When you're ready, say 'generate report' or 'submit' and I'll create your worklog.",
            "report_ready": False,
            "report_data": None
        }
    
    @traceable(
        name="groq_generate_worklog",
        tags=["worklog", "groq", "generation", "langgraph"],
        metadata={"model": MODEL}
    )
    def generate_worklog_from_chat(
        self, 
        chat_transcript: List[Dict[str, str]],
        project_name: str
    ) -> Dict:
        """
        Generate a structured worklog from a complete chat transcript.
        Traced with LangSmith for monitoring.
        
        Args:
            chat_transcript: Full conversation history
            project_name: Name of the project
            
        Returns:
            Dict with structured worklog data
        """
        if not self.is_available():
            return self._fallback_worklog(chat_transcript)
        
        system_prompt = f"""Based on the following conversation about work completed on project "{project_name}", 
generate a structured worklog report. Extract:
1. A clear title
2. Detailed description of work completed
3. Estimated hours worked
4. List of specific tasks completed
5. Technologies/tools used
6. Any challenges faced
7. Next steps

Respond ONLY with a JSON object in this exact format:
{{
  "title": "Brief title",
  "description": "Detailed description",
  "hours_worked": 4.5,
  "tasks_completed": ["task 1", "task 2"],
  "technologies_used": ["tech1", "tech2"],
  "challenges_faced": "description or empty string",
  "next_steps": "description or empty string"
}}"""
        
        # Try LangChain with LangSmith tracing first
        if self.langchain_client and LANGCHAIN_AVAILABLE:
            try:
                transcript_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat_transcript])
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"Conversation transcript:\n{transcript_text}")
                ]
                
                response = self.langchain_client.invoke(messages)
                content = response.content
                
                # Try to parse JSON from response
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code block
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(1))
                    raise
                    
            except Exception as e:
                print(f"LangChain Groq error, falling back to direct API: {e}")
        
        # Fallback to direct Groq API
        if self.client:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Conversation transcript:\n" + 
                 "\n".join([f"{m['role']}: {m['content']}" for m in chat_transcript])}
            ]
            
            try:
                response = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=messages,
                    max_tokens=self.MAX_TOKENS,
                    temperature=0.3,  # Lower temperature for more consistent output
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                return json.loads(content)
                
            except Exception as e:
                print(f"Groq API error: {e}")
                return self._fallback_worklog(chat_transcript)
        
        return self._fallback_worklog(chat_transcript)
    
    def _fallback_worklog(self, chat_transcript: List[Dict[str, str]]) -> Dict:
        """Generate fallback worklog when AI is unavailable."""
        return {
            "title": "Work Completed",
            "description": "Work was completed as discussed in the chat conversation.",
            "hours_worked": 4.0,
            "tasks_completed": ["Development work", "Project tasks"],
            "technologies_used": [],
            "challenges_faced": "",
            "next_steps": "Continue with project development"
        }


# Singleton instance
groq_service = GroqChatService()


def get_groq_service() -> GroqChatService:
    """Get the Groq service singleton."""
    return groq_service
