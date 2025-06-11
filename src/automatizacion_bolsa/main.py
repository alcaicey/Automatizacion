from .config_loader import validate_credentials, configure_run_specific_logging, logger
from .run_automation import run_automation


def main():
    validate_credentials()
    configure_run_specific_logging(logger)
    run_automation(logger)


if __name__ == "__main__":
    main()
