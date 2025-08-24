import psycopg2
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles database operations"""

    def __init__(self, config):
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
