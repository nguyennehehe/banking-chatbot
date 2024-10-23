import streamlit as st
from openai import OpenAI
from openai.types.beta.assistant_stream_event import ThreadMessageDelta
from openai.types.beta.threads.text_delta_block import TextDeltaBlock
import re

def clean_response(text):
    # Remove citation-like markers such as  
    cleaned_text = re.sub(r'【\d+:\d+†source】', '', text)
    return cleaned_text

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ASSISTANT_ID = st.secrets["ASSISTANT_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)
assistant = client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)

st.set_page_config(
    page_title='Banking Chatbot',
    page_icon='💬',
    layout='centered'
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{
        "role": "assistant",
        "content": "How may I assist you today?"
    }]

st.title("🏦 The Byte Squad - Chatbot")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_query := st.chat_input("Input a prompt..."):

    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    with st.chat_message("user"):
        st.markdown(user_query)

    st.session_state.chat_history.append({"role": "user", "content": user_query})

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id, role="user", content=user_query
    )

    with st.chat_message("assistant"):
        stream = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id, assistant_id=ASSISTANT_ID, stream=True
        )

        assistant_reply_box = st.empty()

        assistant_reply = ""

        for event in stream:
            if isinstance(event, ThreadMessageDelta):
                if isinstance(event.data.delta.content[0], TextDeltaBlock):
                    assistant_reply_box.empty()
                    assistant_reply += clean_response(event.data.delta.content[0].text.value)
                    assistant_reply_box.markdown(assistant_reply)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": assistant_reply}
        )
