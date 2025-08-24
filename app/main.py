import logging

from app import Config, DatabaseManager, StockDataFetcher


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    try:
        config = Config()
        fetcher = StockDataFetcher(config)
        db_manager = DatabaseManager(config)

        logger.info(
            f"Starting stock data pipeline with source={config.data_source}, "
            f"fallback={config.fallback_source}"
        )

        stock_data = fetcher.fetch_all_symbols()

        if not stock_data:
            logger.error("No data fetched, exiting")
            return False

        if db_manager.store_stock_data(stock_data):
            logger.info("Pipeline completed successfully")
            return True
        else:
            logger.error("Pipeline failed")
            return False

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
