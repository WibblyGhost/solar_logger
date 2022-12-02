"""
Backup reader program which reads 'xz' backups and uploads the decoded
rows into an InfluxDB server
"""
import logging
import time

from src.classes.backup_classes import BackupReader
from src.helpers.consts import BACKUP_READER_CONFIG_TITLE
from src.helpers.multithreading import ThreadedRunner


class BackupRunner(ThreadedRunner):
    """
    Class which handles reading the 'xz' backups, decoding and uploads
    """
    def __init__(self) -> None:
        self.sleep_time = 15
        # TODO: Move this backup name to the config.ini
        self.file_path = "backups/clearwater.backup.xz"
        super().__init__(BACKUP_READER_CONFIG_TITLE)

    def start(self):
        """
        Calls both the Influx database connector and the Backup connector
        and runs the Influx connector in a separate threads
        """
        self.run_threaded_influx_writer()
        time.sleep(self.sleep_time)
        self.run_data_importer()

    def run_data_importer(self) -> None:
        """
        Main process which runs the backup connector
        Reads a compressed 'xz' file and decodes and passes the packets
        onto InfluxDB
        """
        logging.info("Creating Backup Reader service")
        backup_reader = BackupReader()
        logging.info(f"Starting restoration process on file {self.file_path}")
        backup_reader.read_compressed_xz(file_path=self.file_path)


def main():
    """
    Main runtime for Backup Reader, called from start_restore.py
    """
    thread_runner = BackupRunner()
    thread_runner.start()
