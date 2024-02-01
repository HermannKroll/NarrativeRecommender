import requests
import logging
import ast
import os

from narrec.config import DATA_DIR


class PubMedRecommender:
    def __init__(self):
        self.name = "PubMedRecommender"
        self.cache_path = os.path.join(DATA_DIR, 'pubmed_cache.txt')

    def cache_results(self, pmid, results):
        with open(self.cache_path, 'a') as cache_file:
            cache_file.write(f"{pmid}: {results}\n")

    def get_cached_results(self, pmid):
        try:
            with open(self.cache_path, 'r') as cache_file:
                for line in cache_file:
                    stored_pmid, results_str = line.strip().split(':')
                    if stored_pmid.strip() == pmid:
                        return ast.literal_eval(results_str.strip())
        except FileNotFoundError:
            return None

    def get_similar_article_pmids(self, pmid):
        cached_results = self.get_cached_results(pmid)
        if cached_results is not None:
            logging.info(f"PMID {pmid}: Found in cache.")
            return cached_results

        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
        params = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "linkname": "pubmed_pubmed",
            "id": pmid,
            "cmd": "neighbor",
            "retmode": "json"
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            linksets = data['linksets'][0]
            if 'linksetdbs' in linksets:
                links = linksets['linksetdbs'][0]['links']
                logging.info(f"PMID {pmid}: Found {len(links)} similar articles.")
                # Update the cache with the new result
                self.cache_results(pmid, links)
                return links
            else:
                logging.info(f"PMID {pmid}: No similar articles found.")
                return []
        except requests.RequestException as e:
            logging.info(f"Request error for PMID {pmid}: {e}")
            return []
        except (KeyError, IndexError):
            logging.info(f"Error processing response for PMID {pmid}")
            return []

    def get_similar_articles_for_pmids_list(self, pmids_list):
        logging.info("Retrieving similar articles for a list of PMIDs...\n")
        all_similar_pmids = []
        for pmid in pmids_list:
            similar_pmids = self.get_similar_article_pmids(pmid)
            all_similar_pmids.extend(similar_pmids)
        return all_similar_pmids


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)

    pmids_list = ["36099932", "12345678", "23456789"]
    recommender = PubMedRecommender()
    all_similar_pmids = recommender.get_similar_articles_for_pmids_list(pmids_list)
    print("\nAll Similar PMIDs:", all_similar_pmids)


if __name__ == "__main__":
    main()
