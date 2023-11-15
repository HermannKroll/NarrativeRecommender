from typing import List

from kgextractiontoolbox.backend.models import Document
from kgextractiontoolbox.backend.retrieve import iterate_over_all_documents_in_collection, \
    retrieve_narrative_documents_from_database
from kgextractiontoolbox.document.document import TaggedEntity
from kgextractiontoolbox.document.narrative_document import NarrativeDocument
from narraint.backend.database import SessionExtended
from narrant.entity.entityresolver import GeneResolver
from narrant.preprocessing.enttypes import GENE
from narrec.document.document import RecommenderDocument


class DocumentRetriever:

    def __init__(self):
        self.__cache = {}
        self.translator = DocumentTranslator()
        self.session = SessionExtended.get()
        self.generesolver = GeneResolver()
        self.generesolver.load_index()

    def retrieve_document_ids_for_collection(self, document_collection: str):
        session = SessionExtended.get()
        q = session.query(Document.id).filter(Document.collection == document_collection)
        doc_ids = set()
        for d in q:
            doc_ids.add(d[0])
        return doc_ids

    def retrieve_documents_text(self, document_ids: [int], document_collection: str):
        session = SessionExtended.get()
        doc_texts = []
        for doc in iterate_over_all_documents_in_collection(session, document_ids=document_ids,
                                                            collection=document_collection,
                                                            consider_sections=True):
            doc_texts.append((doc.id, doc.get_text_content(sections=True)))
        return doc_texts

    def retrieve_narrative_documents_for_collections(self, document_ids: [str], document_collections: [str]):
        for collection in document_collections:
            yield from self.retrieve_narrative_documents(document_ids, collection)

    def retrieve_narrative_documents(self, document_ids: [str], document_collection: str, translate_ids=True) -> List[
        RecommenderDocument]:
        if len(document_ids) == 0:
            return []

        if translate_ids:
            # First translate the document ids
            # Hack: PubMed does not need to be translated
            if document_collection == 'PubMed':
                translated = []
                # Translate all integer pubmed ids
                for did in document_ids:
                    try:
                        translated.append(int(did))
                    except ValueError:
                        pass
                document_ids = translated
            else:
                print(f'Should translate {len(document_ids)} ids...')
                document_ids = self.translator.translate_document_ids_source2art(document_ids, document_collection)
                print(f'{len(document_ids)} document ids translated...')
        else:
            # just make them integers
            document_ids = {int(d) for d in document_ids}

        document_ids = set(document_ids)
        found_ids = set()
        narrative_documents = []

        if document_collection not in self.__cache:
            self.__cache[document_collection] = {}

        # look which documents have been cached
        for did in document_ids:
            if did in self.__cache[document_collection]:
                found_ids.add(did)
                narrative_documents.append(self.__cache[document_collection][did])

        remaining_document_ids = document_ids - found_ids
        if len(remaining_document_ids) == 0:
            return narrative_documents
        narrative_documents_queried = retrieve_narrative_documents_from_database(session=self.session,
                                                                                 document_ids=remaining_document_ids,
                                                                                 document_collection=document_collection)
        # Gene IDs are only present in the Tag table.
        # The rest work with gene symbols
        for doc in narrative_documents_queried:
            self.__translate_gene_ids_to_symbols(doc)

        narrative_documents_queried = [
            RecommenderDocument(document_id=d.id,
                                title=d.title,
                                abstract=d.abstract,
                                metadata=d.metadata,
                                tags=d.tags,
                                sentences=d.sentences,
                                extracted_statements=d.extracted_statements,
                                classification=d.classification)
            for d in narrative_documents_queried]

        # add to cache
        for d in narrative_documents_queried:
            self.__cache[document_collection][d.id] = d

        # add them to list
        narrative_documents.extend(narrative_documents_queried)
        return narrative_documents

    def __translate_gene_ids_to_symbols(self, document: NarrativeDocument):
        translated_gene_ids = []
        for tag in document.tags:
            # Gene IDs need a special handling
            if tag.ent_type == GENE:
                if ';' in tag.ent_id:
                    for g_id in tag.ent_id.split(';'):
                        try:
                            symbol = self.generesolver.gene_id_to_symbol(g_id.strip()).lower()
                            translated_gene_ids.append(TaggedEntity(document=tag.document,
                                                                    start=tag.start,
                                                                    end=tag.end,
                                                                    text=tag.text,
                                                                    ent_id=symbol,
                                                                    ent_type=GENE))
                        except (KeyError, ValueError):
                            continue
                else:
                    try:
                        symbol = self.generesolver.gene_id_to_symbol(tag.ent_id).lower()
                        translated_gene_ids.append(TaggedEntity(document=tag.document,
                                                                start=tag.start,
                                                                end=tag.end,
                                                                text=tag.text,
                                                                ent_id=symbol,
                                                                ent_type=GENE))
                    except (KeyError, ValueError):
                        pass
        document.tags.extend(translated_gene_ids)
