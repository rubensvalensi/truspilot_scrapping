import requests
from bs4 import BeautifulSoup
import pandas as pd
import argparse
import pymysql.cursors
import json
from config import conf


def check_status():
    """Checks status of webpage"""
    r = requests.get('https://www.trustpilot.com')
    print(r.status_code)
    print(r.status_code == requests.codes.ok)
    print(requests.codes['temporary_redirect'])
    print(requests.codes.teapot)
    print(requests.codes['o/'])


def scrap(company, num_pages):
    """Scrap a company's reviews from their TrustPilot page."""
    names = []
    ratings = []
    titles = []
    contents = []
    rev_wrote = []
    replies = []
    company_names = []
    num_reviews = []
    company_ratings = []
    website = []
    urls = []
    symbols = []

    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
    })

    for p in range(1, int(num_pages)):
        page_url = requests.get('https://www.trustpilot.com/review/' + company + '?page=' + str(p), headers=headers)
        soup = BeautifulSoup(page_url.content, 'html.parser')
        review_card = soup.find_all('div', class_='review-card')
        # find website of the company
        # I do it just one time
        # TODO LOOK AT THIS we need to put
        if p == 1:
            web_tag = soup.find_all('a', class_="badge-card__section badge-card__section--hoverable company_website")
            for a in web_tag:
                website.append(a['href'])
            company_name = soup.find('span', class_='multi-size-header__big').get_text(strip=True)
            company_names.append(company_name)
            num_review = soup.find('h2', class_='header--inline').get_text(strip=True)
            num_review = ''.join(filter(str.isdigit, num_review))
            num_reviews.append(num_review)
            company_rating = soup.find('p', class_='header_trustscore').get_text()
            company_ratings.append(company_rating)
            symbol = yahoo_finance(company_name)
            symbols.append(symbol)
        # get url for each user
        user_url = soup.find_all('a', href=True)
        for a in user_url:
            user_id = a['href']
            if '/users/5' in user_id and user_id not in urls:
                urls.append(user_id)
        for review in review_card:
            # Username
            name = review.find('div', class_='consumer-information__name').get_text(strip=True)
            names.append(name)
            # Rating
            rating = review.find('img').attrs.get('alt')
            ratings.append(rating)
            # Review title
            title = review.find('a', class_='link link--large link--dark').get_text(strip=True)
            titles.append(title)
            # Review content
            if review.find('p', class_='review-content__text'):
                content = review.find('p', class_='review-content__text').get_text(strip=True)
            else:
                content = None
            contents.append(content)
            # Number of reviews wrote by user
            rev_written = review.span.get_text()
            rev_wrote.append(rev_written)
            # Replied received
            reply = review.find('div', class_='review__company-reply')
            if reply:
                replies.append(1)
            else:
                replies.append(0)
            # country and parse another page
    countries = parse_another_page(urls)
    reviews_dict = {'ratings': ratings,
                    'titles': titles,
                    'contents': contents,
                    'replies': replies
                    }
    users_dict = {'names': names,
                  'countries': countries,
                  'rev_wrote': rev_wrote
                  }
    companies_dict = {'company_names': company_names,
                      'company_ratings': company_ratings,
                      'website': website,
                      'num_reviews': num_reviews,
                      'symbols': symbols
                      }
    return reviews_dict, users_dict, companies_dict


def parse_another_page(urls):
    lst = []
    for url in urls:
        page_url = requests.get('https://www.trustpilot.com/' + url)
        soup = BeautifulSoup(page_url.content, 'html.parser')
        countries = soup.find('div', class_='user-summary-location')
        if countries is not None:
            lst.append(countries.text.strip().strip('\n'))
    return lst


def export_csv(company, num_pages):
    """Stores results to pandas df and creates a csv file."""
    reviews_dict, users_dict, companies_dict = scrap(company, num_pages)
    reviews_df = pd.DataFrame(reviews_dict)
    users_df = pd.DataFrame(users_dict)
    companies_df = pd.DataFrame(companies_dict)
    reviews_df.to_csv('reviews.csv')
    users_df.to_csv('users.csv')
    companies_df.to_csv('companies.csv')


def export_sql(company, num_pages):
    """Stores results to pandas df and creates a csv file."""
    reviews_dict, users_dict, companies_dict = scrap(company, num_pages)
    try:
        connection = pymysql.connect(host='localhost',
                                     user=conf.user,
                                     password=conf.password,
                                     database='trustpilot',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        print(f'Database exists. Succesfully connected')
        c = connection.cursor()
    except:
        connection = pymysql.connect(host='localhost',
                                     user=conf.user,
                                     password=conf.password,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        c = connection.cursor()
        c.execute('CREATE DATABASE trustpilot')
        c.execute('USE trustpilot')
        users_table = """ CREATE TABLE Users (
                    user_id int NOT NULL UNIQUE AUTO_INCREMENT,
                    user_name varchar(255),
                    country varchar(255),
                    rev_wrote int,
                    PRIMARY KEY (user_id));
                """
        companies_table = """
                        CREATE TABLE Companies (
                            company_id int NOT NULL UNIQUE AUTO_INCREMENT,
                            company_names varchar(255),
                            company_ratings varchar(255),
                            website varchar(255),
                            num_reviews int,
                            symbols varchar(255),
                            PRIMARY KEY (company_id)
                            );
                            """
        reviews_table = """
                        CREATE TABLE Reviews (
                            review_id int NOT NULL UNIQUE AUTO_INCREMENT,
                            rating int,
                            title varchar(255),
                            content varchar(255),
                            replies int,
                            user_id int,
                            company_id int,
                            PRIMARY KEY (review_id),
                            FOREIGN KEY (user_id) REFERENCES Users (user_id),
                            FOREIGN KEY (company_id) REFERENCES Companies (company_id)
                            );
                            """
        # with connection.cursor() as cursor:
        c.execute(users_table)
        c.execute(companies_table)
        c.execute(reviews_table)
    c.execute("SET GLOBAL sql_mode='';")
    companies_insert_query = 'INSERT INTO Companies(company_names,company_ratings,website,num_reviews) VALUES (%s,%s,%s,%s) '
    c.execute(companies_insert_query, (companies_dict['company_names'][0], companies_dict['company_ratings'][0],
                                       companies_dict['website'][0], companies_dict['num_reviews'][0]))
    company_id = c.lastrowid
    for i in range(len(reviews_dict['ratings']) - 1):
        # print(reviews_dict['ratings'][i])
        users_insert_query = 'INSERT INTO Users(user_name,country,rev_wrote) VALUES (%s,%s,%s)'
        c.execute(users_insert_query,
                  (users_dict['names'][i], users_dict['countries'][i], users_dict['rev_wrote'][i]))
        # get user id foreign key
        user_id = c.lastrowid
        reviews_insert_query = 'INSERT INTO Reviews(rating,title,content,replies, user_id, company_id) VALUES (%s,%s,%s,%s,%s,%s)'
        c.execute(reviews_insert_query,
                  (reviews_dict['ratings'][i], reviews_dict['titles'][i], reviews_dict['contents'][i],
                   reviews_dict['replies'][i], user_id, company_id))
    # c.commit()
    # insert foreign key company
    c.close()
    connection.commit()


def yahoo_finance(company_name):
    """Gets the company's stock symbol if it is publicly traded"""
    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/auto-complete"
    querystring = {"q": company_name, "region": "US"}
    headers = {
        'x-rapidapi-key': conf.api_key,
        'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    resp_str = response.text
    resp_dict = json.loads(resp_str)
    try:
        quote = resp_dict['quotes'][0]
        symbol = quote['symbol']
    except IndexError:
        symbol = ''
    return symbol


def main():
    """Runs commands above"""
    # CLI
    parser = argparse.ArgumentParser()
    parser.add_argument('company', help='company_name')
    parser.add_argument('num_pages', help='page limit')
    args = parser.parse_args()
    company = args.company
    num_pages = args.num_pages
    print('Scrapping data from ' + company)
    # export_csv(company, num_pages)
    export_sql(company, num_pages)


if __name__ == '__main__':
    main()
