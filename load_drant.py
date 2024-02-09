from qdrant_client import models, QdrantClient
import os
from gpt4 import summarize_GPT_4

qdrant_client = QdrantClient(":memory:") 

qdrant_client.recreate_collection(
    collection_name="transcriptions",
    vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
)
print("Create collection reponse:", qdrant_client)



collection_info = qdrant_client.get_collection(collection_name="transcriptions")

print("Collection info:", collection_info)


from openai import OpenAI

client = OpenAI()


def get_embedding(text, model="text-embedding-3-small"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding


from qdrant_client.http.models import PointStruct

files = os.listdir("txt/imang")
for file in files:
    if ".txt" in file:
        fulltext = open("txt/imang/"+ file, "r").read()
        chunks = []
        text = fulltext
        while len(text) > 500:
            last_period_index = text[:500].rfind('.')
            if last_period_index == -1:
                last_period_index = 500
            chunks.append(text[:last_period_index])
            text = text[last_period_index+1:]
        chunks.append(text)
        points = []
        i = 1
        for chunk in chunks:
            i += 1

            print("Embeddings chunk:", chunk)
            embeddings = get_embedding(chunk)
            print("Embeddings:", embeddings)
            points.append(PointStruct(id=i, vector=embeddings, payload={"text": chunk}))


operation_info = qdrant_client.upsert(
    collection_name="transcriptions",
    wait=True,
    points=points
)

print("Operation info:", operation_info)


def create_answer_with_context(query):
    embeddings = get_embedding(query)

    search_result = qdrant_client.search(
        collection_name="transcriptions",
        query_vector=embeddings, 
        limit=15,
    )

    context = "Context:\n"
    for result in search_result:
        context += result.payload['text'] + "\n---\n"

    prompt = "Question: " + query + "\n---\n" + "Answer:"

    print("----PROMPT START----:")
    print(prompt)
    print("----PROMPT END----")

    system_prompt = f"You are Iman Gadzhi's GPT, an AI that is, helpful, creative, clever, and very friendly. Using the same conversation style as the context provided. Please give long well thought answers with the following context in mind:" + context
    completion = summarize_GPT_4(system_prompt, prompt)
    return completion.choices[0].message.content


answer = create_answer_with_context("How to open a social media marketing agency?")
print("Answer:", answer)