import logging

def log():
  logger = logging.getLogger(__name__)
  logging.basicConfig(
    filename='producer.log', 
    level=logging.INFO, 
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s"
  )
  return logger
