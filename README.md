CS Exams Downloader
===================

The CS Exams Downloader can be used to download past exams for UC Berkeley's 
CS courses. It makes use of HKN and TBP's databases. As of this writing, the
program downloads only those exams that also have their solutions available
on those databases.

## Setup

Simply clone this repo to get started. Note that the application makes use of
the following extra modules:
- [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/)
- [Requests](http://docs.python-requests.org/en/latest/)

Users of ``pip`` can install these modules using 
``pip install -r requirements.txt.``

## Usage

Run the code with a valid class to download exam-solution pairs!

```python
python3 get_exams.py 61A
```

You can also get files for multiple classes in one run.

```python
python3 get_exams.py 162 186 188
```

## License

This code is released under the [Apache License, Version 2.0.](LICENSE.md)

> Copyright 2016 Shafqat Dulal
>
> Licensed under the Apache License, Version 2.0 (the "License");
> you may not use this file except in compliance with the License.
> You may obtain a copy of the License at
>
>  http://www.apache.org/licenses/LICENSE-2.0
>
> Unless required by applicable law or agreed to in writing, software
> distributed under the License is distributed on an "AS IS" BASIS,
> WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
> See the License for the specific language governing permissions and
> limitations under the License.
