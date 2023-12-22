import gzip
import glob
import tqdm
import re


if __name__ == "__main__":
    files = glob.glob("tmp/*")
    pattern = re.compile("<PMID Version=\"1\">([0-9]*)</PMID>")
    pmids = set()
    for gz_file in tqdm.tqdm(files):
        if not gz_file.endswith(".gz"):
            continue

        with gzip.open(gz_file, "rt", encoding="latin") as file:
            text = file.read()
            for m in pattern.finditer(text):
                pmids.add(int(m.group(1)))

    with open("pubmed_baseline_pm19.txt", "w") as out:
        out.write("\n".join([str(x) for x in pmids]))
    print("finished. retrieved", len(pmids), "doc ids.")
        