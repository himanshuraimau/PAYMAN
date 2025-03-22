import os
import json
from typing import List, Tuple, Dict, Any, Optional, Annotated, TypedDict, cast
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent, ToolNode


# Load environment variables
load_dotenv()

# Set your OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
os.environ["OPENAI_API_KEY"] = api_key

# Define custom tools
@tool
def search_wikipedia(query: str) -> str:
    """Search Wikipedia for the given query."""
    from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
    from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
    
    wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    return wikipedia.invoke(query)

@tool
def calculator(expression: str) -> str:
    """Calculate the result of a mathematical expression."""
    import numexpr
    return str(numexpr.evaluate(expression).item())

# Define the state schema as a TypedDict
class AgentState(TypedDict):
    messages: List[BaseMessage]

# Initialize the OpenAI model - using gpt-3.5-turbo for better reliability
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Create the tools and agent
tools = [search_wikipedia, calculator]

# Create the agent
agent = create_react_agent(llm, tools)

# Create the workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent)

# Define when we should end
def should_continue(state: AgentState) -> str:
    if not state["messages"]:
        return "agent"
    
    last_message = state["messages"][-1]
    
    # If the last message is from the AI and doesn't require tool use, we're done
    if isinstance(last_message, AIMessage) and not last_message.tool_calls:
        return END
    
    return "agent"

workflow.add_conditional_edges("agent", should_continue)
workflow.set_entry_point("agent")

# Compile the graph
app = workflow.compile()

# Helper function to run the agent
def run_agent(query: str, verbose: bool = True):
    # Create initial state with the query as the initial message
    state = {"messages": [HumanMessage(content=query)]}
    
    # Store all states for debugging and final response extraction
    all_states = []
    final_response = None
    
    # Run the workflow
    try:
        for current_state in app.stream(state):
            all_states.append(current_state)
            
            if verbose and "messages" in current_state:
                messages = current_state["messages"]
                for message in messages:
                    if not hasattr(message, 'content'):
                        continue
                    
                    content = message.content
                    if isinstance(message, HumanMessage):
                        print(f"\nHuman: {content}")
                    elif isinstance(message, AIMessage):
                        if content:  # Only print non-empty AI messages
                            print(f"\nAI: {content}")
                            # Store the most recent AI message with content as our potential final response
                            final_response = content
    except Exception as e:
        print(f"Error during agent execution: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"
    
    # If we found a final response during streaming, return it
    if final_response:
        return final_response
    
    # Otherwise, try to extract from the final state
    if all_states and "messages" in all_states[-1]:
        messages = all_states[-1]["messages"]
        # Look for the last AI message with content
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content:
                return message.content
    
    return "Sorry, I couldn't generate a response."

# Interactive chat function
def interactive_chat():
    print("Chat with your LangGraph agent (type 'exit' to quit)")
    while True:
        query = input("\nYou: ")
        if query.lower() == "exit":
            break
        result = run_agent(query)
        print(f"\nAgent: {result}")

# Example usage
if __name__ == "__main__":
    # Run a single query
    result = run_agent("What is the capital of France?")
    print("\nFinal Answer:", result)
    
    # Or run the interactive chat
    interactive_chat()