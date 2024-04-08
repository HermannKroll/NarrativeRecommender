import json
import matplotlib.pyplot as plt
import os

from narrec.config import TOPIC_SCORES, SCORE_FREQUENCY, RESOURCE_DIR


def generate_boxplots(data_path):
    for file_name in os.listdir(data_path):
        if file_name.endswith('.json'):
            benchmark = file_name.replace("_topic_scores.json", "")

            output_folder = os.path.join(data_path, f"{benchmark}_plots")
            os.makedirs(output_folder, exist_ok=True)

            with open(os.path.join(data_path, file_name), 'r') as json_file:
                data = json.load(json_file)

            for method, method_data in data.items():
                method_folder = os.path.join(output_folder, f"{method}")
                os.makedirs(method_folder, exist_ok=True)
                for measure, topics in method_data.items():
                    scores = {topic: topic_data['scores'] for topic, topic_data in topics.items()}
                    sorted_topics = sorted(scores.keys(), key=lambda x: int(x))
                    sorted_scores = [scores[topic] for topic in sorted_topics]

                    plt.figure(figsize=(10, 6))
                    plt.boxplot(sorted_scores, labels=sorted_topics)
                    plt.xlabel('Topic')
                    plt.ylabel('Scores')
                    plt.title(f'Boxplot for {benchmark} - {method} - {measure}')

                    output_file = os.path.join(method_folder, f"{benchmark}_{method}_{measure}.png")
                    plt.savefig(output_file)
                    plt.close()

                    print(f"Boxplot for {benchmark} - {method} - {measure} was saved as {output_file}.")


def generate_barplots(data_path):
    max_counts = {}

    for file_name in os.listdir(data_path):
        if file_name.endswith('.json'):
            with open(os.path.join(data_path, file_name), 'r') as json_file:
                data = json.load(json_file)
            for method_data in data.values():
                for measure, scores in method_data.items():
                    max_counts.setdefault(measure, 0)
                    max_counts[measure] = max(max_counts[measure], max(scores.values()))

    for file_name in os.listdir(data_path):
        if file_name.endswith('.json'):
            benchmark = file_name.replace("_score_frequency.json", "")
            output_folder = os.path.join(data_path, f"{benchmark}_barplots")
            os.makedirs(output_folder, exist_ok=True)
            with open(os.path.join(data_path, file_name), 'r') as json_file:
                data = json.load(json_file)
            for method, method_data in data.items():
                method_folder = os.path.join(output_folder, f"{method}")
                os.makedirs(method_folder, exist_ok=True)
                for measure, scores in method_data.items():
                    scores_dict = {float(score): count for score, count in scores.items()}
                    plt.figure(figsize=(10, 6))
                    plt.bar(scores_dict.keys(), scores_dict.values(), width=0.04, align='center')
                    plt.xlabel('Scores')
                    plt.ylabel('Count')
                    plt.title(f'Barplot for {benchmark} - {method} - {measure}')
                    plt.ylim(0, max_counts[measure] + 1)
                    output_file = os.path.join(method_folder, f"{benchmark}_{method}_{measure}.png")
                    plt.savefig(output_file)
                    plt.close()
                    print(f"Barplot for {benchmark} - {method} - {measure} was saved as {output_file}.")



def main():
    # generate_boxplots(TOPIC_SCORES)
    generate_barplots(RESOURCE_DIR)


if __name__ == "__main__":
    main()
