import os

import faiss
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

os.environ["CUDA_VISIBLE_DEVICES"] = "5"

from narrec.citation.graph import CitationGraph
from narrec.document.document import RecommenderDocument
from narrec.recommender.graph_base import GraphBase
from narrec.scoring.BM25Scorer import BM25Scorer


class SpladeRecommender(GraphBase):
    def __init__(self, bm25scorer: BM25Scorer):
        super().__init__(name="SpladeRecommender")
        self.bm25_scorer = bm25scorer

        model_id = 'naver/splade-cocondenser-ensembledistil'  # OR 'naver/efficient-splade-V-large-query'
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = AutoModel.from_pretrained(model_id).to(self.device)
        print(f'Splade will use device: {self.device}')

    # Encode text using SPLADE
    # Encode text using SPLADE
    def encode_text(self, texts, aggregation, batch_size=256):
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            inputs = self.tokenizer(batch_texts, padding=True, truncation=True, return_tensors="pt", max_length=512).to(
                self.device)  # Move inputs to GPU
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use the last hidden state as the representation
                token_embeddings = outputs.last_hidden_state

                # Aggregate token embeddings
                if aggregation == 'mean':
                    embeddings = token_embeddings.mean(dim=1)  # Mean pooling
                else:
                    embeddings = token_embeddings.max(dim=1).values  # Max pooling

                all_embeddings.append(embeddings.cpu().numpy())  # Move embeddings to CPU before returning

            # Clear cache after each batch
            torch.cuda.empty_cache()

        return np.vstack(all_embeddings)

    def recommend_documents(self, doc: RecommenderDocument, docs_from: [RecommenderDocument],
                            citation_graph: CitationGraph) -> [RecommenderDocument]:
        queries = list([doc.get_text_content()])
        document_ids = list([doc.id for doc in docs_from])
        document_texts = list([document.get_text_content() for document in docs_from])
        k = len(document_texts)  # we need to score k things (all documents)
        aggregation = 'max'  # OR 'mean'

        # Encode the documents and queries
        doc_embeddings = self.encode_text(document_texts, aggregation)
        query_embeddings = self.encode_text(queries, aggregation)

        # Faiss for efficient similarity search
        dimension = query_embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)

        if faiss.get_num_gpus() > 0:
            gpu_or_cpu_index = faiss.index_cpu_to_all_gpus(index)
        else:
            gpu_or_cpu_index = index

        gpu_or_cpu_index.add(doc_embeddings)

        # Retrieval with KNN
        distances, indices = gpu_or_cpu_index.search(query_embeddings, k)

        # Output the results
        document_ids_scored = dict()
        max_score = 0
        for i, query in enumerate(queries):
            # print(f"Query: {query}")
            for j in range(k):
                score = distances[i, j]
                doc_id = document_ids[indices[i, j]]
                document_ids_scored[doc_id] = score
                max_score = max(max_score, score)
                # print(f"Rank {j + 1}: Document {indices[i, j]} with score {distances[i, j]}")
                #  print(f"Content: {documents[indices[i, j]]}\n")

        # Sort by score and then doc desc
        document_ids_scored = sorted([(k, v / max_score)
                                      for k, v in document_ids_scored.items()],
                                     key=lambda x: (x[1], x[0]), reverse=False)  # Higher Scores = Worse Results

        # our pipeline expects the first score to be the highest. After normaliziation, we can just rescale the
        # scores by new_score = 1.0 - old_score
        document_ids_scored = list([(k, 1.0 - v) for k, v in document_ids_scored])  # Higher Scores = Worse Results
        # Ensure cutoff
        return document_ids_scored
