# NVD CHATBOT

This is a simple command-line chatbot that can answer basic questions about 
software vulnerabilities by querying the National Vulnerability Database (NVD).
I used LangGraph's reasoning and acting (ReAct) agent to augment the gpt-4o-mini
model with a custom tool used to make api calls to the NVD.

You can run the chatbot with 'python chatbot.py', or 'python chatbot.py --dev' to get extended model output

** To actually run, you'll need to supply your OpenAI API key in a .env file which has the line OPENAI_API_KEY=[your-api-key]

The nvd_search tool takes several optional inputs: a cve_id, a keyword to search by,
and start/end dates to use in the query. The tool uses the input to build the query,
selects the relevant vulnerability data to return, and limits the results. 
I used Pydantic to create structured input, as in my past experience models can sometimes 
ignore requests to format data in a specific way.

This would be the first iteration of the chatbot so here are a couple improvements that could be made:
- Giving the model a system message which gives it more context about the types of questions it will be asked, telling it to provide answers in some standard format, or telling it to ignore irrelevant questions.
- Improving the search tool/adding more tools. Right now the tool only gives the 5 most recent vulnerabilities returned by the api response in order to limit input tokens. If input tokens weren't a problem, one could remove this limit and just feed the model all of the data. Or, we could add another argument to the search tool and the model can decide how much data it wants.
- I could have the tool to return more data points and add arguments to cover more of what is exposed by the API. This includes severity scores, metrics, US-CERT alerts, etc.
