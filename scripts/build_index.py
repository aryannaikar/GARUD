import os


import sys


sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

import chromadb


from sentence_transformers import SentenceTransformer

from tools.system_paths import get_search_paths

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="chroma/file_index")

collection = client.get_or_create_collection(
    name="files"
)


indexed = 0

for folder in get_search_paths():

    print(f"Scanning: {folder}")

    for root, dirs, files in os.walk(folder):

        for file in files:

            try:
                full_path = os.path.join(root, file)

                embedding = model.encode(file).tolist()

                collection.add(
                    ids=[full_path],
                    embeddings=[embedding],
                    documents=[file],
                    metadatas=[
                        {
                            "path": full_path
                        }
                    ]
                )

                indexed += 1

            except Exception as e:
                print(e)


print(f"\nIndexed {indexed} files.")