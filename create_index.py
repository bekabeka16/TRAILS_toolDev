import os
from dotenv import load_dotenv
load_dotenv()
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchField, SearchFieldDataType,
    VectorSearch, VectorSearchProfile, HnswAlgorithmConfiguration
)

SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
SEARCH_ADMIN_KEY = os.environ["AZURE_SEARCH_ADMIN_KEY"]
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX", "reading-index")

# Choose embedding dimensions based on your embeddings model.
# Common: 1536 (text-embedding-3-small), 3072 (text-embedding-3-large)
EMBED_DIM = int(os.environ.get("EMBEDDING_DIM", "1536"))

client = SearchIndexClient(SEARCH_ENDPOINT, AzureKeyCredential(SEARCH_ADMIN_KEY))

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
    SimpleField(name="source", type=SearchFieldDataType.String, filterable=True, facetable=True),
    SimpleField(name="page", type=SearchFieldDataType.String, filterable=True),
    SearchField(
        name="embedding",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=EMBED_DIM,
        vector_search_profile_name="vprofile"
    )
]

index = SearchIndex(
    name=INDEX_NAME,
    fields=fields,
    vector_search=VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="vprofile", algorithm_configuration_name="hnsw")]
    )
)

# Create or replace
try:
    client.delete_index(INDEX_NAME)
except Exception:
    pass

client.create_index(index)
print(f"Created index: {INDEX_NAME} (dim={EMBED_DIM})")
