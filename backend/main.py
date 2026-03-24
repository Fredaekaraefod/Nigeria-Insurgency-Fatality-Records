import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# LangChain imports
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit
from langchain_groq import ChatGroq

app = FastAPI(title="Natural Language Investigator API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to our SQLite database
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'incidents.db'))
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

# Request Model
class QueryRequest(BaseModel):
    query: str

def get_agent():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY environment variable not set.")
        
    llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile", groq_api_key=api_key)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    
    # We turn on return_intermediate_steps to capture the 'Thought Process' for the UI
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="zero-shot-react-description",
        verbose=True,
        return_intermediate_steps=True,
        prefix="You are an expert investigative analyst examining the Boko Haram conflict timeline database. Your database contains records of terrorist incidents with columns including date, state, location, attack_type, fatalities, and summary. IMPORTANT: YOU MUST NEVER RETURN RAW SQL TO THE USER. You must physically execute your SQL queries using the provided tools, read the resulting observation data, and synthesize a natural language summary containing the specific facts, names, or counts extracted from the database."
    )
    return agent_executor

@app.post("/api/investigate")
async def investigate(req: QueryRequest):
    try:
        agent = get_agent()
        
        # Run the agent
        response = agent.invoke({"input": req.query})
        
        # The 'intermediate_steps' contains tuples of (AgentAction, Observation/Result)
        # We parse this to send a gorgeous "Thought Process" log back to the frontend
        
        thought_process = []
        sql_query = None
        
        if "intermediate_steps" in response:
            for step in response["intermediate_steps"]:
                action = step[0] # AgentAction
                observation = step[1] # Output of the tool (e.g., SQL execution result)
                
                tool_name = getattr(action, 'tool', 'Unknown Tool')
                tool_input = getattr(action, 'tool_input', '')
                
                # We specifically pull out the exact SQL query written by the LLM
                if tool_name == "sql_db_query":
                    sql_query = tool_input
                
                thought_process.append({
                    "action": f"Using {tool_name}",
                    "input": tool_input,
                    "observation": str(observation)
                })
                
        final_answer_raw = response.get("output", "No clear answer provided.")
        final_answer = ""
        
        if isinstance(final_answer_raw, list):
            final_answer = " ".join([str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in final_answer_raw])
        elif isinstance(final_answer_raw, dict):
            final_answer = str(final_answer_raw.get("text", final_answer_raw))
        else:
            final_answer = str(final_answer_raw)
                
        return {
            "success": True,
            "final_answer": final_answer,
            "thought_process": thought_process,
            "sql_query": sql_query if sql_query else "No SQL query generated."
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/")
def read_root():
    return {"message": "NL Investigator API is running. Point your frontend to /api/investigate"}
