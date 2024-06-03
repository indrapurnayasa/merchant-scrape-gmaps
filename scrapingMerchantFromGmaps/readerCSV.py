import csv

class CSVReader:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_and_print(self):
        with open(self.file_path, 'r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                for column in row:
                    print(column)

# Usage example
csv_file_path = 'merchant_name.csv'
csv_reader = CSVReader(csv_file_path)
csv_reader.read_and_print()
