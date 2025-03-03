import os
import json
from datetime import datetime, timezone
import re
import polars as pl


def oso_id(*args):
    # Placeholder for the oso_id function
    return "_".join(str(arg).lower() for arg in args)


def load_protocol_data(directory="data/protocols"):
    protocols = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            path = os.path.join(directory, filename)
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    if not data.get("slug"):
                        data["slug"] = filename.replace(".json", "").lower()
                    protocols.append(data)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return protocols


def extract_chain_tvl_events(protocol):
    """
    Extract aggregated TVL events from the chainTvls field.
    For each chain, each event is expected to have a date and a totalLiquidityUSD value.
    """
    events = []
    chain_tvls = protocol.get("chainTvls", {})
    for chain_name, tvl_data in chain_tvls.items():
        tvl_list = tvl_data.get("tvl", [])
        if not tvl_list:
            continue
        
        for entry in tvl_list:
            if isinstance(entry, dict):
                date = entry.get("date")
                if date is None:
                    continue
                readable_time = datetime.fromtimestamp(date, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                amount = float(entry.get("totalLiquidityUSD", 0))
                event = {
                    "time": readable_time,
                    "chain": chain_name.lower(),
                    "slug": protocol.get("slug", "").lower(),
                    "token": "usd",
                    "amount": amount,
                    "event_type": "TVL"
                }
                events.append(event)
            else:            
                continue
    return events


def extract_tokens_in_usd_events(protocol):
    """
    Extract aggregated TVL events from the tokensInUsd field.
    For each record, all token values are summed to produce a single event.
    """
    events = []
    tokens_in_usd = protocol.get("tokensInUsd", [])
    default_chain = protocol.get("chain", "").lower()
    for record in tokens_in_usd:
        dt = record.get("date")
        if dt is None:
            continue
        readable_time = datetime.fromtimestamp(dt, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        tokens = record.get("tokens", {})
        total = sum(float(value) for value in tokens.values())
        event = {
            "time": readable_time,
            "chain": default_chain,
            "slug": protocol.get("slug", "").lower(),
            "token": "usd",
            "amount": total,
            "event_type": "TOKENS_IN_USD"
        }
        events.append(event)
    return events


def build_enriched_events_dataframe(events):
    """
    Given a list of events with fields:
    time, chain, slug, token, amount, event_type,
    compute the enriched fields:
      - event_source_id (using concatenation of time, chain, slug, token)
      - event_source (constant "DEFILLAAMA")
      - to_artifact_ fields (based on protocol slug and chain)
      - from_artifact_ fields (based on token and chain)
      - amount (the TVL value)
    """
    df = pl.DataFrame(events)

    df = df.with_columns([
        pl.col("event_type"),
        pl.concat_str([
            pl.col("time"),
            pl.col("chain"),
            pl.col("slug"),
            pl.col("token")
        ], separator="_").alias("event_source_id"),
        pl.lit("defillama").str.to_uppercase().alias("event_source"),
        pl.col("slug").alias("to_artifact_name"),
        pl.col("chain").alias("to_artifact_namespace"),
        pl.lit("protocol").str.to_uppercase().alias("to_artifact_type"),
        pl.concat_str([
            pl.col("chain"),
            pl.col("slug")
        ], separator="_").alias("to_artifact_id"),
        pl.concat_str([
            pl.col("chain"),
            pl.col("slug")
        ], separator="_").alias("to_artifact_source_id"),
        pl.col("token").alias("from_artifact_name"),
        pl.col("chain").alias("from_artifact_namespace"),
        pl.lit("token").str.to_uppercase().alias("from_artifact_type"),
        pl.concat_str([
            pl.col("chain"),
            pl.col("token")
        ], separator="_").alias("from_artifact_id"),
        pl.concat_str([
            pl.col("chain"),
            pl.col("token")
        ], separator="_").alias("from_artifact_source_id"),
    ])

    final_cols = [
        "time", "event_type", "event_source_id", "event_source",
        "to_artifact_name", "to_artifact_namespace", "to_artifact_type",
        "to_artifact_id", "to_artifact_source_id",
        "from_artifact_name", "from_artifact_namespace", "from_artifact_type",
        "from_artifact_id", "from_artifact_source_id",
        "amount"
    ]
    return df.select(final_cols)


def main():
    # Load all protocol JSON files (stored locally for testing purposes)
    protocols = load_protocol_data(directory="data/protocols")
    all_events = []

    for protocol in protocols:
        # Extract aggregated TVL events from chainTvls
        events_chain = extract_chain_tvl_events(protocol)
        # Extract aggregated tokensInUsd events
        events_tokens = extract_tokens_in_usd_events(protocol)
        all_events.extend(events_chain)
        all_events.extend(events_tokens)

    if not all_events:
        print("No TVL events found.")
        return

    enriched_df = build_enriched_events_dataframe(all_events)

    # --- Apply OP Labs filtering ---
    ENDING_PATTERNS_TO_FILTER = ["-borrowed", "-vesting", "-staking", "-pool2", "-treasury", "-cex"]
    EXACT_PATTERNS_TO_FILTER = ["treasury", "borrowed", "staking", "pool2", "polygon-bridge-&-staking"]

    endings_pattern = "|".join(re.escape(e) for e in ENDING_PATTERNS_TO_FILTER)
    namespace_ending_mask = pl.col("to_artifact_namespace").str.to_lowercase().str.contains(rf"({endings_pattern})$")
    namespace_exact_mask = pl.col("to_artifact_namespace").str.to_lowercase().is_in(
        pl.Series(EXACT_PATTERNS_TO_FILTER).str.to_lowercase()
    )

    polygon_bridge_mask = pl.col("to_artifact_name") == "polygon-bridge-&-staking"
    cex_mask = pl.col("to_artifact_name").str.ends_with("-cex")

    filter_mask = namespace_ending_mask | namespace_exact_mask | polygon_bridge_mask | cex_mask
    filtered_enriched_df = enriched_df.filter(~filter_mask)

    os.makedirs("data", exist_ok=True)

    output_path = "data/enriched_tvl_events.parquet"
    filtered_enriched_df.write_parquet(output_path)
    print(f"Enriched TVL events saved to {output_path}")


if __name__ == "__main__":
    main()