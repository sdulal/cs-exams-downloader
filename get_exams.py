"""
This program can be used to get posted exams for UC Berkeley's CS courses.
Given one or more courses, this downloader will search HKN and TBP's databases
and pull out available exam-solution files. See --help to view some options.

This program requires Python 3, as well as a few additional modules that are
listed in the requirements file.
"""

from bs4 import BeautifulSoup
from collections import defaultdict
from threading import Thread
import argparse
import os
import requests
import sys
import urllib.request

"""Setup for parsing arguments."""
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
g_one = parser.add_mutually_exclusive_group()
g_one.add_argument('-e', '--exams', action='store_const', default='',
                   const='Exam', help="download only exam files")
g_one.add_argument('-s', '--solutions', action='store_const', default='',
                   const='Solution', help="download only solution files")
g_two = parser.add_mutually_exclusive_group()
g_two.add_argument('-k', '--hkn', action='store_true', default=False,
                   help="search only on HKN's database")
g_two.add_argument('-t', '--tbp', action='store_true', default=False,
                   help="search only on TBP's database")

__author__ = "Shafqat Dulal"

"""Sources from which to find previous exams."""
source_sites = {"HKN": "https://hkn.eecs.berkeley.edu",
                "TBP": "https://tbp.berkeley.edu"}

"""An array used to deal with the row-data format of HKN's exam database."""
index_to_exam_type = [-1, -1, "Midterm 1", "Midterm 2", "Midterm 3", "Final"]

"""Special constants."""
_EXAM = "Exam"
_SOLUTION = "Solution"


def download(source, class_number, semester,
             exam_type, content_type, exam_link):
    """
    Downloads the exam/solution file specified by the exam_link. Note that
    the naming of the file is determined by most of the function's arguments.

    Without any flags or options used for the program, this function will
    consider any download that has an existing exam_link.
    """
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
    """
    Scans the semester-exam-link mappings found by searching a source and
    attempts to download the files corresponding to the links found.

    Without any flags or options used for the program, this function will
    consider downloads only when both an exam and its solution is available.
    """
    for semester in dict_links:
        for exam_type in dict_links[semester]:
            exam, solution = dict_links[semester][exam_type]
            if should_try_download(exam, solution):
                Thread(target=download,
                       args=(source, class_number, semester,
                             exam_type, _EXAM, exam)).start()
                Thread(target=download,
                       args=(source, class_number, semester,
                             exam_type, _SOLUTION, solution)).start()


def pull_from_TBP(class_number, super_dict):
    """
    Searches TBP's database of previous exams for the course corresponding to
    the class_number.
    """
    if not args.tbp:
        return
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
        semester = data[2].text
        for anchor in row.find_all("a", class_="exam-download-link"):
            index = 0 if anchor.text.strip() == _EXAM else 1
            super_dict[semester][exam_type][index] = anchor.get("href")

    download_files("TBP", class_number, super_dict)


def pull_from_HKN(class_number, super_dict):
    """
    Searches HKN's database of previous exams for the course corresponding to
    the class_number.
    """
    if not args.hkn:
        return
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
    """
    Runs the main download operation. Looks through HKN's and TBP's websites
    for exams for each class specified and downloads the exam/solution files.
    The -k/-t flags may limit searches to one of the two sites.
    """
    for class_number in class_numbers:
        folder = "CS {0}".format(class_number)
        verbose_print("Starting searches for {0}.".format(folder))
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
                error_log.write('\n')
            if not os.listdir(folder):
                os.rmdir(folder)

"""
Parses arguments, then calls the main function
to start the program. Exits upon completion.
"""
if __name__ == "__main__":
    args = parser.parse_args()

    """A print function that is active only when the -v flag is used."""
    verbose_print = print if args.verbose else lambda *a, **k: None

    def should_try_download(exam, solution):
        """
        Considers whether or not a particular exam-solution pair warrants a
        download attempt. Usually, the exam-solution pair must be complete
        (can be overriden with the -u flag).
        """
        return ((exam and solution) or args.unpaired)

    def is_valid_download(content_type, exam_link):
        """
        Checks that it is valid to download a certain exam. Non-existent exam
        links will always fail. The -e/-s flags may limit downloads to only
        exams or only solutions.
        """
        if not exam_link:
            return False
        if args.exams:
            return content_type == args.exams
        if args.solutions:
            return content_type == args.solutions
        return True

    if (not args.hkn) and (not args.tbp):
        args.hkn = args.tbp = True

    main(args.classes)
