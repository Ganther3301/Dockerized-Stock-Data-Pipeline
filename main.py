import logging
import os
import time

import psycopg2
import requests
import yfinance as yf
from dotenv import load_dotenv


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration management with validation"""

    def __init__(self):
        load_dotenv()

        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASS")

        self.alpha_api_key = os.getenv("ALPHA_API_KEY")
        self.data_source = os.getenv("DATA_SOURCE", "yf").lower()  # main source
        self.fallback_source = os.getenv("FALLBACK_SOURCE", "yf").lower()  # <-- NEW

        self.symbols = ["GOOGL", "NVDA", "MSFT"]
        self.api_timeout = 30


class StockDataFetcher:
    """Handles stock data fetching and processing"""

    def __init__(self, config: Config):
        self.config = config

    def fetch_stock_data(self, symbol: str):
        """Fetch stock data from primary source, fallback if fails"""
        logger.info(f"Fetching {symbol} using {self.config.data_source}")

        data = self._fetch(symbol, self.config.data_source)

        if (
            not data
            and self.config.fallback_source
            and self.config.fallback_source != self.config.data_source
        ):
            logger.warning(
                f"Primary source '{self.config.data_source}' failed for {symbol}. "
                f"Falling back to '{self.config.fallback_source}'"
            )
            data = self._fetch(symbol, self.config.fallback_source)

        return data

    def _fetch(self, symbol: str, source: str):
        """Internal: fetch from a specific source"""
        if source == "alpha_vantage":
            return self._fetch_from_alpha(symbol)
        elif source == "yf":
            return self._fetch_from_yfinance(symbol)
        else:
            logger.error(f"Unknown data source: {source}")
            return None

    def _fetch_from_alpha(self, symbol: str):
        url = (
            f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
            f"&symbol={symbol}&apikey={self.config.alpha_api_key}"
        )

        try:
            logger.info(f"[Alpha Vantage] Fetching data for {symbol}")
            response = requests.get(url, timeout=self.config.api_timeout)
            response.raise_for_status()

            data = response.json()

            if "Error Message" in data:
                logger.error(f"API Error for {symbol}: {data['Error Message']}")
                return None
            if "Note" in data:
                logger.warning(f"Rate limit exceeded: {data['Note']}")
                return None
            if "Time Series (Daily)" not in data:
                logger.warning(f"No time series data for {symbol} \n{data}")
                return None

            return self._parse_time_series(data["Time Series (Daily)"], symbol)

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching data for {symbol}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error for {symbol}: {e}")
        except ValueError as e:
            logger.error(f"JSON parsing error for {symbol}: {e}")
        return None

    def _fetch_from_yfinance(self, symbol: str):
        try:
            logger.info(f"[Yahoo Finance] Fetching data for {symbol}")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d", interval="1d")

            if hist.empty:
                logger.warning(f"No yfinance data for {symbol}")
                return None

            records = []
            for date, row in hist.iterrows():
                records.append(
                    {
                        "symbol": symbol,
                        "date": date.date().isoformat(),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]),
                    }
                )
            return records
        except Exception as e:
            logger.error(f"Error fetching {symbol} from yfinance: {e}")
            return None

    def _parse_time_series(self, time_series, symbol):
        """Parse Alpha Vantage time series data"""
        parsed_records = []

        for date_str, values in time_series.items():
            try:
                record = {
                    "symbol": symbol,
                    "date": date_str,
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(float(values["5. volume"])),
                }
                parsed_records.append(record)
            except (KeyError, ValueError) as e:
                logger.warning(
                    f"Skipping invalid record for {symbol} on {date_str}: {e}"
                )

        logger.info(f"Parsed {len(parsed_records)} records for {symbol}")
        return parsed_records

    def fetch_all_symbols(self):
        """Fetch data for all configured symbols"""
        all_data = {}
        for i, symbol in enumerate(self.config.symbols):
            data = self.fetch_stock_data(symbol)
            if data:
                all_data[symbol] = data

            if (
                self.config.data_source == "alpha_vantage"
                and i < len(self.config.symbols) - 1
            ):
                logger.info("Waiting to respect API rate limits...")
                time.sleep(12)

        return all_data


class DatabaseManager:
    """Handles database operations"""

    def __init__(self, config: Config):
        self.config = config

    def get_connection(self):
        try:
            return psycopg2.connect(
                host=self.config.db_host,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                connect_timeout=10,
            )
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def store_stock_data(self, stock_data):
        if not stock_data:
            logger.warning("No data to store")
            return False

        upsert_query = """
            INSERT INTO stock_data (symbol, date, open_price, high_price, low_price, close_price, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s) 
            ON CONFLICT (symbol, date) 
            DO UPDATE SET 
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume,
                updated_at = CURRENT_TIMESTAMP;
        """

        conn = None
        total_records = 0

        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                for symbol, records in stock_data.items():
                    for record in records:
                        cursor.execute(
                            upsert_query,
                            (
                                record["symbol"],
                                record["date"],
                                record["open"],
                                record["high"],
                                record["low"],
                                record["close"],
                                record["volume"],
                            ),
                        )
                        total_records += 1

            conn.commit()
            logger.info(f"Successfully stored {total_records} records")
            return True

        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            return False

        finally:
            if conn:
                conn.close()


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
