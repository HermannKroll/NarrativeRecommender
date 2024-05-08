# NarrativeRecommender
This repository belongs to our TPDL2024 submission. Code is still updated and not fully documented.

We cannot share the actual Narrative Service database which is required for the recommendation process (legal and space reasons).
However, we hope that our implementation may shed light on details which are not described in the paper. 

# Implementation Details
- [First Stages](src/narrec/firststage): [FSConcept](src/narrec/firststage/fsconcept.py), [FSNode](src/narrec/firststage/fsnode.py) and [FSCore](src/narrec/firststage/fscore.py)
- [CoreOverlap](src/narrec/recommender/coreoverlap.py) and GraphRec is [coreoverlap + BM25](src/narrec/recommender/graph_base_fallback_bm25.py)
- [BM25 Index Creation](src/narrec/firststage/create_bm25_index.py) and [BM25 First Stage](src/narrec/firststage/bm25abstract.py) and [BM25 ReScoring](src/narrec/scoring/BM25Scorer.py)
- [Edge Scoring](src/narrec/scoring/edge.py) and [Node Scoring](src/narrec/scoring/concept.py)
- [Evaluation](src/narrec/analysis/evaluation.py) and [Analysis Scripts](src/narrec/analysis)
- [Explanation Generation and Recommender App](src/narrec/recommender_app.py)

## Getting Started
This project requires to clone it with sub repositories:
- [KGExtractionToolbox](https://github.com/HermannKroll/KGExtractionToolbox.git)
- [Pharmaceutical Annotation Toolbox](https://github.com/HermannKroll/NarrativeAnnotation.git)
- [Narrative Service](https://github.com/HermannKroll/NarrativeIntelligence.git)

Therefore, please clone the project via:
```
git clone --recurse-submodules https://github.com/HermannKroll/NarrativeRecommender.git
```

Update the repository:
```
git pull --recurse-submodules
```

## Python Setup

Create a virtual python 3.8 environment via, e.g., conda:
```
conda create -n narrec python=3.8
```

Activate the environment
```
conda activate narrec
```


Install all Python requirements:
```
pip install -r requirements.txt
```


## Python Path
Make always be sure that if you run any of our scripts, you activated your conda environment and set the Python Path.
```
conda activate narrec
export PYTHONPATH="/home/USER/NarrativeRecommender/src/:/home/USER/NarrativeRecommender/lib/NarrativeIntelligence/src/:/home/USER/NarrativeRecommender/lib/NarrativeAnnotation/src/:/home/USER/NarrativeRecommender/lib/KGExtractionToolbox/src/"
```

## First Setup
First download required data:
```
cd ~/NarrativeRecommender/lib/NarrativeAnnotation/
bash download_data.sh 
```

Next build required entity translation indexes.
```
pythn ~/NarrativeRecommender/lib/NarrativeAnnotation/src/narrant/build_all_indexes.py
```

## Database connection

The project requires a connection to our database.
Therefore, please bind your local postgres port to the server port via:
```
 ssh -N -f -L localhost:5432:localhost:5432 USER@DB_SERVER_IP
```

## PyCharm:
If you use PyCharm for development purposes, make sure that you mark [src](src) and the src directories of the three modules as "Sources Root". 
Then PyCharm is able to complete and run code. 



# Create Benchmark id lists
execute [extract_tg2005_ids.py](src%2Fnarrec%2Fbenchmark%2Fretrieve_pmids%2Fextract_tg2005_ids.py) and [extract_relish_ids.py](src%2Fnarrec%2Fbenchmark%2Fretrieve_pmids%2Fextract_relish_ids.py).
These scripts will extract document id for Genomics 2005 and relish.
