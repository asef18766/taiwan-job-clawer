import logging
def create_logger_to_file(fname:str):
    logging.basicConfig(filename=fname, level=logging.INFO)