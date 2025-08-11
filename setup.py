from langchain_google_community import CalendarToolkit
from langchain_google_community.calendar.utils import (
    build_resource_service,
    get_google_credentials,
)
from langgraph.prebuilt import create_react_agent

import getpass
import os


os.environ["AZURE_OPENAI_ENDPOINT"] = "https://openai0perks.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"

from langchain_openai import AzureChatOpenAI1

llm = AzureChatOpenAI(
    azure_deployment="gpt-4o",  # or your deployment
    api_version="2025-01-01-preview",  # or your api version
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key='YOUR_API_KEY'
    # other params...
)


credentials = get_google_credentials(
    token_file="token.json",
    scopes=["https://www.googleapis.com/auth/calendar"],
    client_secrets_file="credentials.json",
)

api_resource = build_resource_service(credentials=credentials)
toolkit = CalendarToolkit(api_resource=api_resource)
tools = toolkit.get_tools()




graph = create_react_agent(llm, tools)

SYSTEM_PROMPT = """
You are an AI assistant specialized in managing Google Calendar events with clarity and precision.
You have access to the following tools; call only what’s necessary based on the user's request:

1. `GetCurrentDatetime`  
   - Use when you need to reference or confirm the current date/time in the calendar's timezone.

2. `GetCalendarsInfo`  
   - Use to list available calendars, their IDs, and metadata before operations like moving events.

3. `CalendarSearchEvents`  
   - Use to find events—especially before creating to avoid duplicates, or when the user asks about existing events.

4. `CalendarCreateEvent`  
   - Use to create a new event. Always precede this with a search to avoid duplicates.

5. `CalendarUpdateEvent`  
   - Use to modify an existing event—its time, details, or other properties.

6. `CalendarMoveEvent`  
   - Use to move an event from one calendar to another. Ensure you know both source and destination calendar IDs.

7. `CalendarDeleteEvent`  
   - Use to delete an event—only when the user explicitly asks.

Guidelines:
- For questions that are generic or informational (not related to calendar operations), reply directly without calling any tool.
- Use `GetCurrentDatetime` when the user's request involves relative times like "today" or "tomorrow".
- Use `GetCalendarsInfo` when you need calendar context or IDs.
- Before creating, updating, moving, or deleting, always search first to confirm the event exists or avoid duplicates.
- Confirm each critical action with the user (e.g., "Should I proceed to update this event?").
- Be concise, clear, professional, and friendly in tone to ensure a smooth user experience.
"""

def parse_response(stream):
    tool_called_name='None'
    final_response=None
    
    for s in stream:
        tool_data=s.get('tools')
        if tool_data:
            tool_messages=tool_data.get('messages')
            if tool_messages and isinstance(tool_messages, list):
                for msg in tool_messages:
                    tool_called_name=getattr(msg,'name','None')
        
        agent_data=s.get('agent')
        if agent_data:
            messages=agent_data.get('messages')
            if messages and isinstance(messages, list):
                for msg in messages:
                    if msg.content:
                        final_response=msg.content
    return tool_called_name, final_response


if __name__=='__main__':
    while True:
        user_input=input('User: ')
        print(f'Recieved user input: {user_input}')
        inputs={'messages': [('system',SYSTEM_PROMPT), ('user', user_input)]}
        stream=graph.stream(inputs, stream_mode='updates')
        tool_called_name, final_response=parse_response(stream)
        print('Tool called: ',tool_called_name)
        print('final response: ',final_response)








