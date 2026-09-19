import logging


def get_logger(name):
    # ----------------- logging --------------------------
    # logging.DEBUG / logging.INFO / logging.WARNING / logging.ERROR / logging.CRITICAL
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # ---------------- logging :check handlers -----------------
    if logger.handlers:
        return logger  # اگه قبلاً تنظیم شده، دوباره handler اضافه نکن

    # ---------------- logging :formatter -----------------
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # ---------------- logging :handlers -----------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(f"{name}.log", encoding="utf-8", mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
