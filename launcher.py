import os
import platform
import requests
import sentry_sdk
from bot import bot, PRODUCTION, logger


def prepare_cloc() -> None:
    if not os.path.exists('cloc.pl'):
        res: requests.Response = requests.get('https://github.com/AlDanial/cloc/releases/download/v1.90/cloc-1.90.pl')
        with open('cloc.pl', 'wb') as fp:
            fp.write(res.content)


def prepare_sentry() -> None:
    if PRODUCTION and (dsn := os.environ.get('SENTRY_DSN')):
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=0.5
        )


def prepare() -> None:
    logger.info(f'Running on {platform.system()} {platform.release()}')
    if not os.path.exists('./tmp'):
        os.mkdir('tmp')
    prepare_cloc()
    prepare_sentry()


if __name__ == '__main__':
    prepare()
    bot.run(os.getenv('BOT_TOKEN'))
