from prefect import flow, task
from typing import Dict, List
import logging
import random
import time
from scraper import scrape_with_selenium


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@task(retries=5)
def scrape_website(url: str, wait=None) -> Dict:
    logger.info(f'Scraping {url}')
    time.sleep(random.randint(2,5) if wait is None else wait)
    assert 1 == random.randint(1,10)
    return {'url': url, 'data': f'content from {url}'}


@task(retries=2)
def scrape_avito(url):
    logger.info(f'Starting Avito scraping for {url}')
    try:
        scrape_with_selenium(url)
        logger.info(f'Successfully scraped Avito URL: {url}')
    except Exception as e:
        logger.error(f'Failed to scrape Avito: {str(e)}')
        raise


@flow(name="Avito Scraping Flow")
async def avito_scraping_flow(sites: Dict[str, List[str]] = None) -> None:
    if sites is None:
        sites = {
            'avito': [
                'https://www.avito.ru/moskva/avtomobili/hyundai/solaris-ASgBAgICAkTgtg2imzHitg3kmzE?cd=1&radius=0&searchRadius=0'
            ]
        }

    for category, urls in sites.items():
        if category == 'avito':
            for url in urls:
                scrape_avito(url)
        else:
            for url in urls:
                scrape_website(url)


if __name__ == '__main__':
    avito_scraping_flow.serve(
        name='avito-scraper-deployment',
        cron='0 * * * *',
        parameters={
            'sites': {
                'avito': [
                    'https://www.avito.ru/moskva/avtomobili/hyundai/solaris-ASgBAgICAkTgtg2imzHitg3kmzE?cd=1&radius=0&searchRadius=0'
                ]
            }
        },
        tags=['production', 'avito', 'cars'],
    )
