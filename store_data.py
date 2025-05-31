from utils import extract_text_from_pdf, extract_tables_from_pdf, clean_text
from configuration.config import EMBEDDING_MODEL, MILVUS_HOST, MILVUS_PORT, COLLECTION_NAME, METRIC_TYPE, VECTOR_DIM, INDEX_TYPE
from nltk.tokenize import sent_tokenize
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import sys
import os

# Get the absolute path of the project's root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)


# Create collection if it doesn't exist
def create_collection():
    if utility.has_collection(COLLECTION_NAME):
        utility.drop_collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR,
                    is_primary=True, max_length=100),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="embedding",
                    dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM)
    ]

    schema = CollectionSchema(fields, description="ESC Guidelines Collection")
    collection = Collection(name=COLLECTION_NAME, schema=schema)

    # Create IVF_FLAT index for vector field
    index_params = {'metric_type': METRIC_TYPE,
                    'index_type': INDEX_TYPE, 'params': {"nlist": 64}}
    collection.create_index(field_name="embedding", index_params=index_params)
    return collection


# Embed and store in Milvus
def store_embeddings(sections, collection):
    """Embeds and stores extracted sections in Milvus"""
    collection.load()

    entities = []
    ids = []

    for i, section in tqdm(enumerate(sections), total=len(sections)):
        section_id = f"chunk-{i}"
        embedding = embedder.encode(section).tolist()

        # Clean and truncate text if needed (Milvus has VARCHAR limits)
        clean_section = clean_text(section)
        if len(clean_section) > 65000:  # Leave some margin from 65535
            clean_section = clean_section[:65000]

        ids.append(section_id)
        entities.append([section_id, clean_section, embedding])

    # Insert in batches if needed
    batch_size = 50
    for i in range(0, len(entities), batch_size):
        batch = entities[i:i + batch_size]

        ids_batch = [item[0] for item in batch]
        texts_batch = [item[1] for item in batch]
        embeddings_batch = [item[2] for item in batch]

        collection.insert([ids_batch, texts_batch, embeddings_batch])

    # Flush to ensure data is committed
    collection.flush()
    print(f"✅ Inserted {len(entities)} sections into Milvus")


# Chunk long text into manageable pieces
def chunk_text(text, max_chunk_size=200):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def process_and_store_tables(tables, collection):
    """Convert extracted tables to text, embed them, and store in Milvus."""
    collection.load()

    table_entities = []
    table_ids = []

    for idx, table_text in enumerate(tables):
        table_id = f"table-{idx}"
        clean_table_text = clean_text(table_text)

        # Embed table text
        embedding = embedder.encode(clean_table_text).tolist()

        # Handle VARCHAR length limit
        if len(clean_table_text) > 65000:
            clean_table_text = clean_table_text[:65000]

        table_ids.append(table_id)
        table_entities.append([table_id, clean_table_text, embedding])

    # Insert in batches
    batch_size = 50
    for i in range(0, len(table_entities), batch_size):
        batch = table_entities[i:i + batch_size]
        ids_batch = [item[0] for item in batch]
        texts_batch = [item[1] for item in batch]
        embeddings_batch = [item[2] for item in batch]

        collection.insert([ids_batch, texts_batch, embeddings_batch])

    collection.flush()
    print(f"✅ Inserted {len(table_entities)} tables into Milvus")


if __name__ == "__main__":
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)

    # PDF File Path
    PDF_PATH = r"C:\Users\reema\OneDrive\Desktop\thesis\heart-failure-guidelines\esc_guidelines1.pdf"

    # Create or get the collection
    collection = create_collection()

    # --- Extract Tables ---
    tables_data = extract_tables_from_pdf(
        PDF_PATH, difference_between_each_row=100)
    # with open("tables.json", "w", encoding="utf-8") as f:
    #     json.dump(tables_data, f, indent=4)
    #     print("✅ Tables extracted and saved to tables.json!")

    # --- Store Tables in Milvus ---
    process_and_store_tables(tables_data, collection)

    # # --- Extract Text Sections ---
    raw_text = extract_text_from_pdf(PDF_PATH)
    raw_text = clean_text(raw_text)
    sections = chunk_text(raw_text)
    store_embeddings(sections, collection)

    print("✅ All content stored successfully with vector embeddings in Milvus!")
