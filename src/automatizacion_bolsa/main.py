import asyncio
from .config_loader import (
    validate_credentials,
    configure_run_specific_logging,
    logger,
)
from .run_automation import run_automation


async def main():
    validate_credentials()
    configure_run_specific_logging(logger)
    await run_automation(logger)


if __name__ == "__main__":
    asyncio.run(main())
