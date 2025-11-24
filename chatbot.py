from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import argparse
import requests
import os


load_dotenv()

NVD_API_KEY = os.getenv("NVD_API_KEY")
BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


# Pydantic structured input provides a rigid args schema with descriptions for the model
class NVDInput(BaseModel):
    cve_id: str | None = Field(None, description="Specific CVE ID (i.e CVE-2024-47195)")
    keyword: str | None = Field(None, description="Keyword to search for (i.e. openssl, windows)")
    start_date: str | None = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: str | None = Field(None, description="End date in YYYY-MM-DD format")

def nvd_search(cve_id=None, keyword=None, start_date=None, end_date=None) -> str:
    """
    Search the NVD API for CVEs by ID, keyword, and/or date range. Limits output to the 5 most recent vulnerabilities.
    """
    headers = {"apiKey": NVD_API_KEY} if NVD_API_KEY else {}
    params = {}

    if cve_id:
        params["cveId"] = cve_id
    if keyword:
        params["keywordSearch"] = keyword
    if start_date and end_date:
        params["pubStartDate"] = f"{start_date}T00:00:00.000"
        params["pubEndDate"] = f"{end_date}T23:59:59.000"

    resp = requests.get(BASE_URL, headers=headers, params=params)

    if resp.status_code != 200:
        return f"Error occurred accessing the NVD API {resp.status_code}: {resp.text}"

    data = resp.json()
    vulnerabilities = data.get("vulnerabilities", [])
    vulnerabilities.reverse()           # API by default gives output in chronological order
    
    if not vulnerabilities:
        return "No vulnerabilities found."

    results = []
    
    # Uses the first 5 vulnerabilities for simplicity/to limit input tokens. 
    # This number could be tweaked/removed to allow for more flexibility, or added as an argument where the model can decide how many entries it needs.
    for vuln in vulnerabilities[:5]:
        cve = vuln["cve"]
        desc = cve.get("descriptions", [{}])[0].get("value")
        published = cve.get("published")
        results.append(f"{cve['id']} ({published}): {desc}")

    return "\n".join(results)

nvd_tool = StructuredTool.from_function(
    func=nvd_search,
    name="nvd_search",
    description="Search the NVD for vulnerabilities by CVE ID, keyword, and/or date range.",
    args_schema=NVDInput,
)

# Initializes the agent
memory = MemorySaver()
model = init_chat_model("openai:gpt-4o-mini")
tools = [nvd_tool]
agent_executor = create_react_agent(model, tools, checkpointer=memory)
config = {"configurable": {"thread_id": "test ID"}}




###############################
### CHATBOT USER INPUT LOOP ###
###############################
def main(dev_output=False):

    print("🤓 Hello! I am your NVD chatbot. Ask me about CVEs. (Type 'quit' to exit)")

    while True:
        query = input(">> ")
        if query.lower() in ["quit", "exit"]:
            print("\n🤓: Goodbye!")
            break
        
        try:
            input_message = {"role": "user", "content": query}

            if (dev_output):
                for step in agent_executor.stream({"messages": [input_message]}, config, stream_mode="values"):
                    step["messages"][-1].pretty_print()
            else:
                response = agent_executor.invoke({"messages": [input_message]}, config, stream_mode="values")
                print("\n🤓: ", response["messages"][-1].content)
 
        except Exception as e:
            print(f"\n🤓: Sorry, there was an error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NVD Chatbot CLI")
    parser.add_argument("--dev", action="store_true", help="Enable developer output mode")
    args = parser.parse_args()

    main(dev_output=args.dev)