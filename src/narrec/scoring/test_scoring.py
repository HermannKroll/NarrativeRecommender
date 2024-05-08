from narrant.entity.entityresolver import EntityResolver
from narrec.backend.retriever import DocumentRetriever
from narrec.document.corpus import DocumentCorpus
from narrec.scoring.edge import score_edge_by_tf_and_concept_idf

retriever = DocumentRetriever()
corpus = DocumentCorpus(["PubMed"])
resolver = EntityResolver.instance()

docs = list(retriever.retrieve_narrative_documents_for_collections([30158249], ["PubMed"]))
doc = docs[0]

for edge in doc.graph:
    t_edge = (resolver.get_name_for_var_ent_id(edge[0], None),
              edge[1],
              resolver.get_name_for_var_ent_id(edge[2], None),)

    score = round(score_edge_by_tf_and_concept_idf(edge, doc, corpus), 2)
    print(f'tfidf+conf+coverage:            {score} <<----  {t_edge}')
    print()
