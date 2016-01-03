from bs4 import BeautifulSoup
from collections import defaultdict
import urllib.request
import requests
import os
import sys

__author__ = "Shafqat Dulal"

source_sites = {"HKN": "https://hkn.eecs.berkeley.edu",
                "TBP": "https://tbp.berkeley.edu"}
index_to_exam_type = [-1, -1, "Midterm 1", "Midterm 2", "Midterm 3", "Final"]


def download(source, class_number, semester,
             exam_type, content_type, exam_link):
    if exam_link:
        extension = "pdf"
        if source == "HKN":
            extension = exam_link[-3:]
        file_name = "CS {0}/{1} {2} {3}.{4}".format(
            class_number, exam_type, semester, content_type, extension)
        file_link = "{0}{1}".format(source_sites[source], exam_link)
        if not os.path.exists(file_name):
            with open(file_name, 'wb') as exam:
                a = requests.get(file_link, stream=True)
                for block in a.iter_content(512):
                    if not block:
                        break
                    exam.write(block)


def download_files(source, class_number, dict_links):
    for semester in dict_links:
        for exam_type in dict_links[semester]:
            exam, solution = dict_links[semester][exam_type]
            if exam and solution:
                download(
                    source, class_number, semester, exam_type, "Exam", exam)
                download(
                    source, class_number, semester,
                    exam_type, "Solution", solution)
                print(
                    "{0} for semester {1} is complete!"
                    .format(exam_type, semester))


def pull_from_TBP(class_number, super_dict):
    print("Pulling from TBP.")
    site = "https://tbp.berkeley.edu/courses/cs/{0}".format(class_number)
    resp = urllib.request.urlopen(site)
    soup = BeautifulSoup(resp, "html.parser",
                         from_encoding=resp.info().get_param('charset'))

    for row in soup.find_all("tr"):
        if row.find("th"):
            continue

        data = row.find_all("td")
        exam_type = data[1].text
        content_type = data[2].text
        semester = data[3].text
        try:
            link = row.find("a", class_="exam-download-link").get('href')
        except AttributeError:
            continue

        index = 0 if content_type == 'Exam' else 1
        super_dict[semester][exam_type][index] = link

    download_files("TBP", class_number, super_dict)


def pull_from_HKN(class_number, super_dict):
    print("Pulling from HKN.")
    site = "https://hkn.eecs.berkeley.edu/exams/course/cs/{0}".format(
        class_number)
    resp = urllib.request.urlopen(site)
    soup = BeautifulSoup(resp, "html.parser",
                         from_encoding=resp.info().get_param('charset'))

    for row in soup.find_all("tr"):
        if row.find("th"):
            continue

        data = row.find_all("td")
        semester = data[0].text.strip()
        for index, datum in enumerate(data):
            if index >= 2:
                exam_type = index_to_exam_type[index]
                for link in datum.find_all("a"):
                    index = 0 if link.text == '[pdf]' else 1
                    super_dict[semester][exam_type][index] = link.get('href')

    download_files("HKN", class_number, super_dict)


def main(class_numbers):
    for class_number in class_numbers:
        folder = "CS {0}".format(class_number)
        try:
            os.makedirs(folder, exist_ok=True)
            pull_from_TBP(
                class_number,
                defaultdict(lambda: defaultdict(lambda: [None, None])))
            pull_from_HKN(
                class_number,
                defaultdict(lambda: defaultdict(lambda: [None, None])))
        except:
            print("An exception has occurred.")
            if not os.listdir(folder):
                os.rmdir(folder)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please input valid class numbers (ex. 186 for CS 186).")
    else:
        sys.argv.pop(0)
        main(sys.argv)
