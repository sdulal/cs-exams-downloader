from bs4 import BeautifulSoup
from collections import defaultdict
from threading import Thread
import argparse
import os
import requests
import sys
import urllib.request

__author__ = "Shafqat Dulal"
source_sites = {"HKN": "https://hkn.eecs.berkeley.edu",
                "TBP": "https://tbp.berkeley.edu"}
index_to_exam_type = [-1, -1, "Midterm 1", "Midterm 2", "Midterm 3", "Final"]


def download(source, class_number, semester,
             exam_type, content_type, exam_link):
    if is_valid_download(content_type, exam_link):
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
        verbose_print("{0} ({1}) for {2} is complete!".format(exam_type,
                                                              content_type,
                                                              semester))


def download_files(source, class_number, dict_links):
    for semester in dict_links:
        for exam_type in dict_links[semester]:
            exam, solution = dict_links[semester][exam_type]
            if should_try_download(exam, solution):
                Thread(target=download,
                       args=(source, class_number, semester,
                             exam_type, "Exam", exam)).start()
                Thread(target=download,
                       args=(source, class_number, semester,
                             exam_type, "Solution", solution)).start()


def pull_from_TBP(class_number, super_dict):
    verbose_print("Pulling from TBP.")
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
    verbose_print("Pulling from HKN.")
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
        except Exception as e:
            print("An exception has occurred.")
            with open('error.log', 'a') as error_log:
                error_log.write(str(e))
                error_log.write('\n\n')
            if not os.listdir(folder):
                os.rmdir(folder)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download past computer science exams \
                     that have corresponding solutions available online.")
    parser.add_argument('classes', metavar='class', type=str, nargs="+",
                        help="class to get exam-solution pairs \
                                                        for (ex. 170, 162)")
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="provide more detail on download progress")
    parser.add_argument('-u', '--unpaired', action='store_true', default=False,
                        help="consider unpaired exam/solution files")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-e', '--exams', action='store_const', default='',
                       const='Exam', help="download only exam files")
    group.add_argument('-s', '--solutions', action='store_const', default='',
                       const='Solution', help="download only solution files")
    args = parser.parse_args()

    verbose_print = print if args.verbose else lambda *a, **k: None

    def should_try_download(exam, solution):
        return ((exam and solution) or args.unpaired)

    def is_valid_download(content_type, exam_link):
        if not exam_link:
            return False
        if args.exams:
            return content_type == args.exams
        if args.solutions:
            return content_type == args.solutions
        return True

    main(args.classes)
