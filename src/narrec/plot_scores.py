import json
import matplotlib.pyplot as plt
import os

from narrec.run_config import TOPIC_SCORES


def generate_boxplots(data_path):
    for file_name in os.listdir(data_path):
        if file_name.endswith('.json'):
            benchmark = os.path.splitext(file_name)[0].split('_')[0]

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


def main():
    data_path = TOPIC_SCORES
    generate_boxplots(data_path)


if __name__ == "__main__":
    main()
