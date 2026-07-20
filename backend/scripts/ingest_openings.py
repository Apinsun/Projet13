"""
Script d'ingestion : charge les articles d'ouvertures dans Milvus.

Usage :
    cd backend && poetry run python scripts/ingest_openings.py
"""

import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)

# ── Configuration ─────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "openings"
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
COLLECTION_NAME = "chess_openings"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
CHUNK_SIZE = 2000  # caractères par chunk (assez grand pour contenir un article entier)


def load_documents(data_dir: Path) -> list[dict]:
    """Charge tous les fichiers .txt et retourne une liste de {name, text}."""
    docs = []
    for filepath in sorted(data_dir.glob("*.txt")):
        name = filepath.stem  # ex: "sicilienne"
        text = filepath.read_text(encoding="utf-8")
        docs.append({"name": name, "text": text})
        print(f"  ✓ Chargé : {name} ({len(text)} car.)")
    return docs


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Découpe un texte en chunks de ~chunk_size caractères aux sauts de ligne."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) < chunk_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks


def create_collection() -> Collection:
    """Crée la collection Milvus (si elle n'existe pas déjà)."""
    if utility.has_collection(COLLECTION_NAME):
        print(f"  Collection '{COLLECTION_NAME}' existe déjà, suppression...")
        utility.drop_collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2048),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
    ]
    schema = CollectionSchema(fields, description="Articles d'ouvertures d'échecs")
    collection = Collection(name=COLLECTION_NAME, schema=schema)
    return collection


def main():
    # 1. Connexion Milvus
    print(f"🔌 Connexion Milvus ({MILVUS_HOST}:{MILVUS_PORT})...")
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    print("  Connecté ✓")

    # 2. Chargement des documents
    print(f"\n📂 Chargement des documents depuis {DATA_DIR}...")
    docs = load_documents(DATA_DIR)
    print(f"  {len(docs)} documents chargés")

    # 3. Chunking
    print("\n✂️  Découpage en chunks...")
    chunks = []
    for doc in docs:
        for chunk_text_item in chunk_text(doc["text"]):
            chunks.append({"name": doc["name"], "text": chunk_text_item})
    print(f"  {len(chunks)} chunks créés")

    # 4. Embedding
    print(f"\n🧠 Chargement du modèle {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    print("  Modèle chargé ✓")

    print("  Vectorisation des chunks...")
    texts = [f"passage: {c['text']}" for c in chunks]  # préfixe requis par E5
    embeddings = model.encode(texts, normalize_embeddings=True)
    print(f"  {len(embeddings)} vecteurs générés (dim={embeddings.shape[1]})")

    # 5. Indexation Milvus
    print("\n📥 Indexation dans Milvus...")
    collection = create_collection()

    entities = [
        [c["name"] for c in chunks],
        [c["text"] for c in chunks],
        embeddings.tolist(),
    ]

    collection.insert(entities)
    collection.flush()

    # 6. Création de l'index
    print("  Création de l'index vectoriel...")
    index_params = {
        "metric_type": "IP",  # Inner Product (cosine avec vecteurs normalisés)
        "index_type": "IVF_FLAT",
        "params": {"nlist": 4},
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    collection.load()

    print(f"\n✅ Terminé ! {len(chunks)} chunks indexés dans '{COLLECTION_NAME}'")


if __name__ == "__main__":
    main()
