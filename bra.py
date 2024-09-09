from datetime import datetime
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from langchain.memory import VectorStoreRetrieverMemory
from langchain.chains import ConversationChain
from langchain_core.prompts import PromptTemplate

from langchain_chroma import Chroma

embeddings = OllamaEmbeddings(model="tinyllama")


vectorstore = Chroma(
    collection_name="example_collection4",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not neccesary
)

# In actual usage, you would set `k` to be a higher value, but we use k=1 to show that
# the vector lookup still returns the semantically relevant information
retriever = vectorstore.as_retriever(search_kwargs=dict(k=1))
memory = VectorStoreRetrieverMemory(retriever=retriever)

# When added to an agent, the memory object can save pertinent information from conversations or used tools
# memory.save_context({"input": "My favorite food is pizza"}, {"output": "that's good to know"})
# memory.save_context({"input": "My favorite sport is soccer"}, {"output": "..."})
# memory.save_context({"input": "I don't the Celtics"}, {"output": "ok"}) #

#print(memory.load_memory_variables({"prompt": "what sport should i watch?"})["history"])


llm = OllamaLLM(model="tinyllama") # Can be any valid LLM
_DEFAULT_TEMPLATE = """The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know.

Relevant pieces of previous conversation:
{history}

(You do not need to use these pieces of information if not relevant)

Current conversation:
Human: {input}
AI:"""
PROMPT = PromptTemplate(
    input_variables=["history", "input"], template=_DEFAULT_TEMPLATE
)
conversation_with_summary = ConversationChain(
    llm=llm,
    prompt=PROMPT,
    memory=memory,
)


print(conversation_with_summary.predict(input="What's my name?"))

