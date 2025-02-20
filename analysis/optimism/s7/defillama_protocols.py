import requests
import json


targeted_slugs = [
    'aave-v3',
    'acryptos',
    'aera',
    'aerodrome-slipstream',
    'aerodrome-v1',
    'aktionariat',
    'alchemix',
    'alien-base-v2',
    'alien-base-v3',
    'arcadia-v2',
    'aura',
    'avantis',
    'balancer-v2',
    'balancer-v3',
    'baseswap-v2',
    'beefy',
    'compound-v3',
    'contango-v2',
    'curve-dex',
    'derive-v1',
    'derive-v2',
    'dforce',
    'dhedge',
    'exactly',
    'extra-finance-leverage-farming',
    'gains-network',
    'harvest-finance',
    'hop-protocol',
    'infinitypools',
    'intentx',
    'ionic-protocol',
    'kim-exchange-v3',
    'kromatika',
    'lets-get-hai',
    'lombard-vault',
    'moonwell',
    'morpho-blue',
    'mux-perps',
    'okx',
    'overnight-finance',
    'pancakeswap-amm-v3',
    'pendle',
    'perpetual-protocol',
    'polynomial-trade',
    'pooltogether-v5',
    'renzo',
    'reserve-protocol',
    'seamless-protocol',
    'silo-v1',
    'solidly-v3',
    'sommelier',
    'stargate-v1',
    'stargate-v2',
    'sushiswap',
    'sushiswap-v3',
    'synfutures-v3',
    'synthetix',
    'synthetix-v3',
    'tarot',
    'velodrome-v2',
    'woo-x',
    'woofi-earn',
    'yearn-finance',
    'zerolend'
]

def fetch_defllama_protocols(slug):

    base_url = "https://api.llama.fi/protocol/"
    url = base_url + slug
    response = requests.get(url)

    if response.status_code == 200:
        print("Fetching data for", slug)
        data = response.json()
        with open(f"data/protocols/{slug}.json", "w") as f:
            json.dump(data,f,indent=2)
        print("Data saved to", f"data/protocols/{slug}.json")
    else:
        print(f"Request failed with status code {response.status_code}")

def main():
    for slug in targeted_slugs:
        fetch_defllama_protocols(slug)

if __name__ == "__main__":
    main()
