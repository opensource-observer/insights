import requests
import json


DEFILLAMA_PROTOCOLS = [
    "aave",
    "aave-v1",
    "aave-v2",
    "aave-v3",
    "across",
    "acryptos",
    "aera",
    "aerodrome-slipstream",
    "aerodrome-v1",
    "aktionariat",
    "alchemix",
    "alien-base-v2",
    "alien-base-v3",
    "amped-finance",
    "arcadia-v2",
    "aura",
    "avantis",
    "bakerfi",
    "balancer-v2",
    "balancer-v3",
    "baseswap",
    "baseswap-v2",
    "bedrock",
    "beefy",
    "blueshift",
    "bmx",
    "bsx-exchange",
    "clusters",
    "compound-v3",
    "contango-v2",
    "curve-dex",
    "dackieswap",
    "derive-v1",
    "derive-v2",
    "dforce",
    "dhedge",
    "exactly",
    "extra-finance-leverage-farming",
    "gains-network",
    "harvest-finance",
    "hermes-v2",
    "hop-protocol",
    "idle",
    "infinitypools",
    "intentx",
    "ionic-protocol",
    "javsphere",
    "jumper-exchange",
    "kelp",
    "kim-exchange-v3",
    "kromatika",
    "krystal",
    "lets-get-hai",
    "lombard-vault",
    "meme-wallet",
    "meson",
    "mint-club",
    "mintswap-finance",
    "moonwell",
    "morpho",
    "morpho-blue",
    "mux-perps",
    "okx",
    "optimism-bridge",
    "origin-protocol",
    "overnight-finance",
    "pancakeswap-amm-v3",
    "pendle",
    "perpetual-protocol",
    "pinto",
    "polynomial-trade",
    "pooltogether-v5",
    "pyth-network",
    "rainbow",
    "renzo",
    "reserve-protocol",
    "sablier",
    "seamless-protocol",
    "silo-v1",
    "solidly-v3",
    "sommelier",
    "sonus-exchange",
    "sonus-exchange-amm",
    "sonus-exchange-clmm",
    "stargate-v1",
    "stargate-v2",
    "superswap-ink",
    "sushi",
    "sushiswap",
    "sushiswap-v3",
    "swapbased",
    "swapbased-amm",
    "swapbased-concentrated-liquidity",
    "swapbased-perp",
    "swapmode",
    "synapse",
    "synfutures-v3",
    "synthetix",
    "synthetix-v3",
    "tarot",
    "team-finance",
    "tlx-finance",
    "toros",
    "velodrome-v2",
    "woo-x",
    "woofi",
    "woofi-earn",
    "yearn-finance",
    "zerolend"
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
    for slug in DEFILLAMA_PROTOCOLS:
        fetch_defllama_protocols(slug)

if __name__ == "__main__":
    main()
