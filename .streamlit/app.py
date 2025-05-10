__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from openai import OpenAI
import streamlit as st
import db, os, time, bs4
from streamlit_js_eval import streamlit_js_eval
import vector_functions as vec
import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader


st.set_page_config(page_title="Stramlit Chat")
st.title=("Chatbot")


def complete():
   st.session_state.complete=True 

def feedback_display():
   st.session_state.feedback_session=True 

def stream_response(response):
    # Split response into words and stream each one
    for word in response.split():
        # Yield the word with a space and pause briefly
        yield word + " "
        time.sleep(0.05)

def chat_page(topic):

    with st.sidebar:

        # Documents Section
        st.subheader("📑 Documents")

        # Get all "document" type sources
        documents = db.list_sources(topic,source_type="document")

        if documents:
            # list the documents
            for doc in documents:
                doc_id = doc[0]
                doc_name = doc[1]
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.write(doc_name)
                with col2:
                    if st.button("❌", key=f"delete_doc_{doc_id}"):
                        db.delete_source(doc_id)
                        st.success(f"Deleted document: {doc_name}")
                        st.rerun()
        else:
            st.write("No documents uploaded.")

        uploaded_file = st.file_uploader("Upload Document", key="file_uploader")

        if uploaded_file:

            # Save document content to database
            with st.spinner("Processing document..."):
                temp_dir = "temp_files"
                os.makedirs(temp_dir, exist_ok=True)
                temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Load document
                document = vec.load_document(temp_file_path)
                
                # Create or update collection
                collection_name = st.session_state["level"]


                if not os.path.exists(f"./persist/{collection_name}"):
                    vectordb = vec.create_collection(collection_name, document)
                else:
                    vectordb = vec.load_collection(collection_name)
                    vectordb = vec.add_documents_to_collection(vectordb, document)

                # Save source to database
                db.create_source(uploaded_file.name, "", st.session_state["level"], source_type="document")

                # Remove temp file
                os.remove(temp_file_path)
                del st.session_state["file_uploader"]

                st.rerun()

    with st.sidebar:
        # rest of the code...

        # Links Section
        st.subheader("🔗 Links")

        # Display list of links
        links = db.list_sources(topic, source_type="link")

        if links:
            for link in links:
                link_id = link[0]
                link_url = link[1]
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.markdown(f"[{link_url}]({link_url})")

                with col2:
                    if st.button("❌    ", key=f"delete_link_{link_id}"):
                        db.delete_source(link_id)
                        st.success(f"Deleted link: {link_url}")
                        st.rerun()
        else:
            st.write("No links added.")

        # Add new link
        new_link = st.text_input("Add a link", key="new_link")
        if st.button("Add Link", key="add_link_btn"):
            if new_link:
                with st.spinner("Processing link..."):
                    # Fetch content from the link
                    try:
                        headers = {

                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"
                        }
                        response = requests.get(new_link, headers=headers)
                        soup = BeautifulSoup(response.text, "html.parser")

                        # Check if the content was successfully retrieved
                        if response.status_code == 200 and soup.text.strip():
                            link_content = soup.get_text(separator="\n")
                        else:
                            st.toast(
                                "Unable to retrieve content from the link. It may be empty or inaccessible.",
                                icon="🚨",
                            )
                            return

                        # Save link content to vector store
                        documents = [
                            Document(
                                page_content=link_content, metadata={"source": new_link}
                            )
                        ]
                        
                        # st.write("check link name---"+ new_link)

                        # documents = WebBaseLoader("https://www.salesforceben.com/salesforce-summer-25-release-date-preview-information/").load()


                        collection_name = st.session_state["level"]
                        
                        if not os.path.exists(f"./persist"):
                            vec.create_collection(collection_name, documents)
                        else:
                            vectordb = vec.load_collection(collection_name)
                            vec.add_documents_to_collection(vectordb, documents)



                        # Save link to database
                        db.create_source(new_link, "", topic, source_type="link")
                        st.success(f"Added link: {new_link}")
                        del st.session_state["add_link_btn"]
                        st.rerun()
                    except Exception as e:
                        st.toast(

                            f"Failed to fetch content from the link: {e}", icon="⚠️"
                        )
            else:
                st.toast("Please enter a link", icon="❗")

def refresh():
    streamlit_js_eval(js_expressions="parent.window.location.reload()")

if "complete" not in st.session_state:
    st.session_state.complete=False

if "messages" not in st.session_state:
    st.session_state["messages"]=[]


if not st.session_state.complete:
    
    if "level" not in st.session_state:
        st.session_state["level"]="Salesforce_Latest_Release"

    
    
    st.subheader('Select the Agent Topic',divider='rainbow')


    st.session_state["level"]= st.radio(
        "Choose Topic",
        options=["Salesforce_Latest_Release","User_Onboarding","Release_Training"] 
    )



    chat_page(st.session_state["level"])
   
    if st.button(label="Start Chat",on_click=complete):
        st.session_state.complete=True

if st.session_state.complete:


    client=OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    collection_name = st.session_state["level"]

    if os.path.exists(f"./persist"):
            retriever = vec.load_retriever(collection_name=collection_name)
    else:
            retriever = None

    # if "openai_model" not in st.session_state:
    #     st.session_state["openai_model"]="gpt-4.1-nano"

    # if "messages" not in st.session_state:
    #     st.session_state["messages"]=[{"role":"system","content":f"You are Salesforce expert and provide guidance on {st.session_state["level"]}"}]

    for message in st.session_state.messages:
        if message["role"]!="system":
            with st.chat_message(message["role"]):
              st.markdown(message["content"])

    if prompt:=st.chat_input("your answer...", max_chars=500):
            st.session_state["messages"].append({"role":"user","content":prompt})

            with st.chat_message("user"):
                st.markdown(prompt) 
            
            with st.chat_message("assistant"):
                output = (
                    vec.generate_answer_from_context(retriever, prompt)
                    if retriever
                    else "I need some context to answer that question."
                )

                response=st.write_stream(stream_response(output))

            st.session_state["messages"].append({"role":"assistant","content":response})

# st.button(label='New Topic?',type="primary",on_click=refresh)


