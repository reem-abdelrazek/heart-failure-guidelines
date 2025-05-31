import os
import yaml

with open(os.path.join(os.path.dirname(__file__), 'config.yaml'), 'r') as file:
    config = yaml.safe_load(file)

# Load configuration values
EMBEDDING_MODEL = config['embedding_model']
MILVUS = config['milvus']
MILVUS_HOST = MILVUS['host']
MILVUS_PORT = MILVUS['port']
VECTOR_DIM = MILVUS['embedding_dimension']
COLLECTION_NAME = MILVUS['collection_name']
INDEX_TYPE = MILVUS['index_type']
METRIC_TYPE = MILVUS['metric_type']

CHATBOT_MODEL = config['chatbot_model']
CHATBOT_MODEL_NAME = CHATBOT_MODEL['model_name']
