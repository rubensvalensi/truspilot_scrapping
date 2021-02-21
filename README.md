# Trustpilot.com web scrapping
Scraps reviews from Trustpilot.

## Table of contents
* [Introduction](#introduction)
* [Language](#language)
* [Requirements](#requirements)
* [Setup](#setup)
* [Usage](#usage)
* [ERD](#erd)

## Introduction
We are scrapping the reviews of companies on Trustpilot.com.  For each review we get information such as rating, username, review title, review content, numbers of reviews written by the user and whether the user recieved a reply by the company. 

## Language

`python 3.7.4`


## Requirements
```
beautifulsoup4 == 4.9.3
pandas == 1.1.3
requests == 2.24.0
```

## Setup
```
$ pip install -r requirements.txt
```

## Usage
- Run and choose your company to scrap from and the number of pages (20 reviews per pages).
 If you would like to scrap all pages enter 'all': 
```
$ python scrapper.py --company --pages
```
Example:
```
$ python scrapper.py www.monday.com 20
```

## ERD
![ERD](erd_trustpilot.png)
