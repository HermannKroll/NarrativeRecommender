import requests
import logging


def get_similar_article_pmids(pmid):
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
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        linksets = data['linksets'][0]
        if 'linksetdbs' in linksets:
            links = linksets['linksetdbs'][0]['links']
            logging.info(f"PMID {pmid}: Found {len(links)} similar articles.")
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


def get_similar_articles_for_pmids_list(pmids_list):
    logging.info("Retrieving similar articles for a list of PMIDs...\n")
    all_similar_pmids = []
    for pmid in pmids_list:
        similar_pmids = get_similar_article_pmids(pmid)
        all_similar_pmids.extend(similar_pmids)
    return all_similar_pmids


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)
    pmids_list = ["36099932"]#, "12345678", "23456789"]

    all_similar_pmids = get_similar_articles_for_pmids_list(pmids_list)
    print("\nAll Similar PMIDs:", all_similar_pmids)


if __name__ == "__main__":
    main()
