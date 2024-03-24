import platform
import aiohttp
import asyncio
import datetime
import sys


class RateProvider:
    async def get_rates(self, currency, days, session):
        raise NotImplementedError("Subclasses must implement this method.")


class NBPRateProvider(RateProvider):
    async def get_rates(self, currency, days, session):
        base_url = "http://api.nbp.pl/api/exchangerates/rates/c"
        rate = []

        days_to_fetch = min(int(days), 10)
        if int(days) > 10:
            print(f"Fetching more than 10 days is not supported for currency {currency}. Only fetching data for the last 10 days.")

        for day_offset in range(days_to_fetch):
            date = datetime.date.today() - datetime.timedelta(days=day_offset)
            formatted_date = date.strftime("%d.%m.%Y")

            url = f"{base_url}/{currency}/last/{day_offset + 1}/?format=json"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = {
                        formatted_date: {
                            currency: {
                                'selling': data['rates'][0]['ask'],
                                'buying': data['rates'][0]['bid']
                            }
                        }
                    }
                    rate.append(rates)
                else:
                    print(f"Error fetching data for {formatted_date}. Status: {response.status}")

        return rate


class RateCollector:
    def __init__(self, providers):
        self.providers = providers

    async def collect_rates(self, currencies, days, session):
        rate = []
        for currency in currencies:
            for provider in self.providers:
                try:
                    rates = await provider.get_rates(currency, days, session)
                    rate.extend(rates)
                except Exception as e:
                    print(f"Error fetching rates for {currency}: {e}")
        return rate


async def main(days):
    async with aiohttp.ClientSession() as session:
        nbp_provider = NBPRateProvider()
        collector = RateCollector([nbp_provider])

        currencies = ["EUR", "USD"]
        result = await collector.collect_rates(currencies, days, session)
        print(result)


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if len(sys.argv) != 2:
        print("Usage: python main.py <number_of_days>")
        sys.exit(1)

    try:
        days = int(sys.argv[1])
    except ValueError:
        print("Invalid input. Please provide a valid number of days.")
        sys.exit(1)

    if days <= 0:
        print("Number of days must be greater than zero.")
        sys.exit(1)

    asyncio.run(main(days))
