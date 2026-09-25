from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import BaseMessage, add_messages, SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from typing import Annotated, List, Dict, Any

class RAGState(BaseModel):
    question: str = Field(..., description="The question to be answered.")
    message:Annotated[List[BaseMessage], add_messages] = Field(default_factory=list, description="The list of messages exchanged during the conversation.")  
    answer: str = Field(None, description="The answer to the question.")
    tool_used: str = Field(None, description="The name of the tool used to answer the question.")
    tool_input: dict = Field(None, description="The input parameters for the tool used.")
    model_name: str = Field("claude-2", description="The name of the LLM model to be used.")

@tool
def calculate_tip(bill_amount: float, tip_percentage: float) -> float:
    """Calculate the tip amount based on the bill amount and tip percentage."""
    return round(bill_amount * (tip_percentage/100), 2)

@tool
def get_order_status(order_id: str) -> str:
    """Retrieve the status of an order based on the order ID."""

    order_statuses = {
        "12345": "Shipped",
        "67890": "Processing",
        "54321": "Delivered"
    } 

    return order_statuses.get(order_id, "Order ID not found")

def create_system_prompt()->Dict[str, Any]:
    system_prompt = """You are a helpful assistant that can answer questions and perform tasks using the available tools. 
            You only have access to the following tools:
            1. calculate_tip: Calculate the tip amount based on the bill amount and tip percentage.
            2. get_order_status: Retrieve the status of an order based on the order ID.
            
            When you receive a question, determine if it can be answered directly or if it requires using one of the tools. 
            If a tool is needed, provide the necessary input parameters for that tool. 
            If the question can be answered directly, provide a concise and accurate response.
            
            Always ensure that your responses are clear and helpful."""
    
    return {"message":[SystemMessage(content=system_prompt())]}

tools=[calculate_tip, get_order_status]

def invoke_llm_with_tools(state) -> Dict[str, Any]:
    llm=ChatAnthropic(model=state.model_name, temperature=0.7)
    llm_with_tools=llm.bind_tools(tools=tools)

    new_message=HumanMessage(content=state.question)
    messages=[
        *state.message,
        new_message
    ]

    response=llm_with_tools.invoke(messages=messages)

    final_response={
        "message": [*messages, AIMessage(content=response.content)],
        "answer": response.content,
        "tool_used": response.tool_used,
        "tool_input": response.tool_input,
    }

    return final_response

state=StateGraph(RAGState)
state.add_node("create_prompt", create_system_prompt)
state.add_node("invoke_llm_with_tools", invoke_llm_with_tools)
state.add_node("tools", ToolNode(tools=tools))

state.add_edge(START, "create_prompt")
state.add_edge("create_prompt", "invoke_llm_with_tools")
state.add_conditional_edge("invoke_llm_with_tools", tools_condition)
state.add_edge("tools", "invoke_llm_with_tools") #go back to llm after tool execution

app=state.compile()

app.invoke({
    "question": "What is the tip for a bill amount of $50 with a tip percentage of 20%?",
    "model_name": "claude-3",
})