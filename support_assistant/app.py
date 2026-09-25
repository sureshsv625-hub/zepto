import os
import sqlite3
from typing import TypedDict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph.graph import StateGraph, END

# --- 1. STATE DEFINITION ---
class SupportState(TypedDict):
    query: str
    category: str
    response: str

# --- 2. OFFLINE MOCK LLM & CATALOG TOOL ---
def search_zepto_catalog(keyword: str) -> str:
    """Query the SQLite database built in Module 1 to fetch real store data offline."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data_pipeline', 'zepto_catalog.sqlite')
    if not os.path.exists(db_path):
        db_path = 'data_pipeline/zepto_catalog.sqlite'
    
    if not os.path.exists(db_path):
        return "Zepto catalog database not found. Please run Module 1 first."
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, price_inr, rating FROM books WHERE title LIKE ? LIMIT 3", (f"%{keyword}%",))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return f"No items found matching '{keyword}' in the Zepto catalog."
    
    results = [f"- {r[0]} | Price: INR {r[1]:.2f} | Rating: {r[2]}/5" for r in rows]
    return "Here are the matching items from your Zepto store:\n" + "\n".join(results)

def mock_llm_router(state: SupportState) -> SupportState:
    q = state['query'].lower()
    if any(word in q for word in ['price', 'book', 'travel', 'mystery', 'catalog', 'search', 'buy']):
        state['category'] = 'catalog_query'
    elif any(word in q for word in ['hello', 'hi', 'hey', 'help']):
        state['category'] = 'greeting'
    else:
        state['category'] = 'general_support'
    return state

def catalog_node(state: SupportState) -> SupportState:
    query_text = state['query']
    words = query_text.split()
    keyword = words[-1] if words else "book"
    state['response'] = search_zepto_catalog(keyword)
    return state

def greeting_node(state: SupportState) -> SupportState:
    state['response'] = "Hello! Welcome to the Zepto AI Support Assistant. How can I help you explore our catalog today?"
    return state

def general_node(state: SupportState) -> SupportState:
    state['response'] = "I am your offline Zepto support assistant. You can ask me to search for books, check prices, or view categories!"
    return state

# --- 3. LANGGRAPH WORKFLOW ---
workflow = StateGraph(SupportState)

workflow.add_node("router", mock_llm_router)
workflow.add_node("catalog_lookup", catalog_node)
workflow.add_node("greeting_handler", greeting_node)
workflow.add_node("general_handler", general_node)

workflow.set_entry_point("router")

workflow.add_conditional_edges(
    "router",
    lambda state: state['category'],
    {
        "catalog_query": "catalog_lookup",
        "greeting": "greeting_handler",
        "general_support": "general_handler"
    }
)

workflow.add_edge("catalog_lookup", END)
workflow.add_edge("greeting_handler", END)
workflow.add_edge("general_handler", END)

app_graph = workflow.compile()

# --- 4. FASTAPI WEB SERVICE ---
app = FastAPI(title="Zepto GenAI Support Assistant", version="1.0")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    category: str
    response: str

@app.post("/support", response_model=QueryResponse)
def handle_support_query(req: QueryRequest):
    try:
        initial_state = {"query": req.query, "category": "", "response": ""}
        final_state = app_graph.invoke(initial_state)
        return {
            "query": final_state['query'],
            "category": final_state['category'],
            "response": final_state['response']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Zepto GenAI Support Assistant is running offline successfully!"}