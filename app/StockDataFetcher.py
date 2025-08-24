import logging
import time
import requests
import yfinance as yf

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StockDataFetcher:
    """Handles stock data fetching and processing"""

    def __init__(self, config):
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
