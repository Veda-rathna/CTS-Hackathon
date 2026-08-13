import csv
from collections import Counter

def check_file(path):
    print(f"\n--- {path} ---")
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        print("Headers:", headers)
        row_count = 0
        samples = []
        for row in reader:
            row_count += 1
            if len(samples) < 3:
                samples.append(row)
        print(f"Total Rows: {row_count}")
        print("Sample Rows:")
        for s in samples:
            print("  ", s)

check_file("../Filtered_Data/Contractor.csv")
check_file("../Filtered_Data/Jurisdiction_With_States.csv")
check_file("../Filtered_Data/Related_Documents.csv")
check_file("../Filtered_Data/Related_NCD.csv")
