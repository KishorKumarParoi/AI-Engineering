import os
import sys
import pandas as pd
from pathlib import Path

# Ensure the repo root is discoverable
here = Path(__file__).resolve()
# climb up until we find a 'data' folder or hit root
p = here
data_file = None
for _ in range(8):
    candidate = p.joinpath('data', 'Data_With_Images.jsonl')
    if candidate.exists():
        data_file = candidate
        break
    p = p.parent

if not data_file:
    print('Could not find data/Data_With_Images.jsonl in repository search paths.')
    sys.exit(2)

# Add src to path so imports work when running this script directly
repo_root = p
sys.path.insert(0, str(repo_root.joinpath('apps', 'api', 'src')))

from api.api.populate_data import populate_qdrant
from qdrant_client import QdrantClient

# Simple Qdrant client using env vars
qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
qdrant_api_key = os.getenv('QDRANT_API_KEY')
client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, check_compatibility=False)

print('Loading dataset:', data_file)
df = pd.read_json(data_file, lines=True)
print('Dataset shape:', df.shape)

populate_qdrant(df, client)
print('Ingestion finished.')
