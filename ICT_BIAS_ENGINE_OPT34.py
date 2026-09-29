# ============================================================
# ICT BIAS ENGINE — OPTIMIZATION 3.4
# SWING → STRUCTURE → LIQUIDITY RELATIONSHIP ENGINE
#
# BASELINE:
# OPT-3.3
#
# IMPORTANT:
# CAUSAL MSS ENGINE IS PRESERVED.
#
# ICT CONCEPTUAL SCOPE:
# Weekly → Daily
# Structure
# Liquidity
# Liquidity lifecycle
# Pre-MSS / Post-MSS liquidity
# Price delivery / displacement
# FVG
# Causal MSS
# Dealing Range
# Premium / Discount
# Liquidity Relevance
# Swing → Structure → Liquidity
# Post-MSS Structure
# Draw Context
#
# NO ENTRY
# NO SL
# NO TP
# NO PROFIT OPTIMIZATION
# NO NUMERIC SCORING
#
# SOURCE CSV IS READ-ONLY
# ============================================================

import os
import json
import math
import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================

SOURCE_FILE = (
    "/storage/emulated/0/xauusd_engine/"
    "XAUUSD_H1_FULL.csv"
)

AUDIT_FILE = (
    "/storage/emulated/0/xauusd_engine/"
    "ICT_BIAS_ENGINE_OPT34_AUDIT.csv"
)

REPORT_FILE = (
    "/storage/emulated/0/xauusd_engine/"
    "ICT_BIAS_ENGINE_OPT34_REPORT.json"
)


# ------------------------------------------------------------
# STRUCTURE
# ------------------------------------------------------------

PIVOT_LEFT = 2
PIVOT_RIGHT = 2

EQUAL_TOLERANCE = 0.05


# ------------------------------------------------------------
# DELIVERY / MSS
# ------------------------------------------------------------

MIN_BODY_FRACTION = 0.55

DELIVERY_MAX_BARS = 8

FVG_MAX_BARS_AFTER_DISPLACEMENT = 2

STRUCTURE_BREAK_MAX_BARS = 8


# ------------------------------------------------------------
# POST-MSS STRUCTURE
# ------------------------------------------------------------

POST_MSS_STRUCTURE_MAX_SWINGS = 20


# ============================================================
# LOAD SOURCE
# ============================================================

print("=" * 78)
print("ICT BIAS ENGINE — OPTIMIZATION 3.4")
print("SWING → STRUCTURE → LIQUIDITY RELATIONSHIP ENGINE")
print("=" * 78)

print()
print("Loading source CSV...")

df = pd.read_csv(
    SOURCE_FILE
)

required_columns = [
    "time",
    "open",
    "high",
    "low",
    "close",
    "volume"
]

missing = [
    c for c in required_columns
    if c not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )


# ============================================================
# TIME CONVERSION
# ============================================================

dt = pd.to_datetime(
    df["time"],
    unit="s",
    errors="coerce"
)

df["datetime"] = (
    dt + pd.Timedelta(hours=7)
)

df = df.dropna(
    subset=[
        "datetime",
        "open",
        "high",
        "low",
        "close"
    ]
).copy()

df = df.sort_values(
    "datetime"
).reset_index(
    drop=True
)


# ============================================================
# BASIC CLEANING
# ============================================================

for col in [
    "open",
    "high",
    "low",
    "close",
    "volume"
]:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


df = df.dropna(
    subset=[
        "open",
        "high",
        "low",
        "close"
    ]
).reset_index(
    drop=True
)


print(
    f"Jumlah H1 : {len(df)}"
)

print(
    f"Awal      : {df['datetime'].iloc[0]}"
)

print(
    f"Akhir     : {df['datetime'].iloc[-1]}"
)


# ============================================================
# PERIOD AGGREGATION
# ============================================================

def aggregate_period(
    df,
    period
):

    x = df.copy()

    x["period"] = (
        x["datetime"]
        .dt.to_period(period)
    )

    result = (
        x.groupby(
            "period",
            sort=True
        )
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum")
        )
        .reset_index()
    )

    result["period_start"] = (
        result["period"]
        .dt.start_time
    )

    result["datetime"] = (
        result["period_start"]
    )

    result = result.drop(
        columns=["period"]
    )

    result = result.sort_values(
        "datetime"
    ).reset_index(
        drop=True
    )

    return result


daily = aggregate_period(
    df,
    "D"
)

weekly = aggregate_period(
    df,
    "W-MON"
)


print()
print(
    f"Daily candles : {len(daily)}"
)

print(
    f"Weekly candles: {len(weekly)}"
)


# ============================================================
# COMPLETED / DEVELOPING
# ============================================================

def split_completed_developing(
    period_df
):

    if len(period_df) == 0:

        return (
            period_df.copy(),
            period_df.copy()
        )

    completed = (
        period_df.iloc[:-1]
        .copy()
    )

    developing = (
        period_df.iloc[-1:]
        .copy()
    )

    return (
        completed,
        developing
    )


daily_completed, daily_developing = (
    split_completed_developing(
        daily
    )
)

weekly_completed, weekly_developing = (
    split_completed_developing(
        weekly
    )
)


print()
print(
    f"Daily completed   : "
    f"{len(daily_completed)}"
)

print(
    f"Daily developing  : "
    f"{len(daily_developing)}"
)

print(
    f"Weekly completed  : "
    f"{len(weekly_completed)}"
)

print(
    f"Weekly developing : "
    f"{len(weekly_developing)}"
)


# ============================================================
# CONFIRMED PIVOTS
# ============================================================

def detect_pivots(
    data,
    left=PIVOT_LEFT,
    right=PIVOT_RIGHT
):

    rows = []

    highs = data["high"].values
    lows = data["low"].values
    times = data["datetime"].values

    n = len(data)

    for i in range(
        left,
        n - right
    ):

        current_high = highs[i]
        current_low = lows[i]

        left_highs = highs[
            i - left:i
        ]

        right_highs = highs[
            i + 1:i + right + 1
        ]

        left_lows = lows[
            i - left:i
        ]

        right_lows = lows[
            i + 1:i + right + 1
        ]

        is_high = (
            current_high
            >
            left_highs.max()
            and
            current_high
            >=
            right_highs.max()
        )

        is_low = (
            current_low
            <
            left_lows.min()
            and
            current_low
            <=
            right_lows.min()
        )

        confirmation_time = (
            times[i + right]
        )

        if is_high:

            rows.append({

                "index": i,

                "datetime":
                    pd.Timestamp(
                        times[i]
                    ),

                "price":
                    float(
                        current_high
                    ),

                "type":
                    "HIGH",

                "confirmed_time":
                    pd.Timestamp(
                        confirmation_time
                    )
            })


        if is_low:

            rows.append({

                "index": i,

                "datetime":
                    pd.Timestamp(
                        times[i]
                    ),

                "price":
                    float(
                        current_low
                    ),

                "type":
                    "LOW",

                "confirmed_time":
                    pd.Timestamp(
                        confirmation_time
                    )
            })


    if not rows:

        return pd.DataFrame(
            columns=[
                "index",
                "datetime",
                "price",
                "type",
                "confirmed_time",
                "label"
            ]
        )


    swings = pd.DataFrame(
        rows
    )

    swings = (
        swings
        .sort_values(
            [
                "index",
                "type"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return swings


# ============================================================
# SWING LABELING
# ============================================================

def label_swings(
    swings
):

    swings = swings.copy()

    swings["label"] = None

    last_high = None
    last_low = None

    for i in range(
        len(swings)
    ):

        row_type = swings.at[
            i,
            "type"
        ]

        price = float(
            swings.at[
                i,
                "price"
            ]
        )


        if row_type == "HIGH":

            if last_high is None:

                swings.at[
                    i,
                    "label"
                ] = "HIGH"

            elif price > last_high:

                swings.at[
                    i,
                    "label"
                ] = "HH"

            elif price < last_high:

                swings.at[
                    i,
                    "label"
                ] = "LH"

            else:

                swings.at[
                    i,
                    "label"
                ] = "EQH"

            last_high = price


        elif row_type == "LOW":

            if last_low is None:

                swings.at[
                    i,
                    "label"
                ] = "LOW"

            elif price > last_low:

                swings.at[
                    i,
                    "label"
                ] = "HL"

            elif price < last_low:

                swings.at[
                    i,
                    "label"
                ] = "LL"

            else:

                swings.at[
                    i,
                    "label"
                ] = "EQL"

            last_low = price


    return swings


# ============================================================
# LIQUIDITY POOLS
# ============================================================

def build_liquidity_pools(
    swings
):

    pools = []


    # --------------------------------------------------------
    # SWING LIQUIDITY
    # --------------------------------------------------------

    for _, row in swings.iterrows():

        if row["type"] == "HIGH":

            pools.append({

                "kind":
                    "SWING",

                "side":
                    "BSL",

                "level":
                    float(
                        row["price"]
                    ),

                "created_time":
                    row["datetime"],

                "source_time":
                    row["datetime"],

                "source_confirmed_time":
                    row["confirmed_time"],

                "source_label":
                    row["label"],

                "source_index":
                    int(
                        row["index"]
                    )
            })


        elif row["type"] == "LOW":

            pools.append({

                "kind":
                    "SWING",

                "side":
                    "SSL",

                "level":
                    float(
                        row["price"]
                    ),

                "created_time":
                    row["datetime"],

                "source_time":
                    row["datetime"],

                "source_confirmed_time":
                    row["confirmed_time"],

                "source_label":
                    row["label"],

                "source_index":
                    int(
                        row["index"]
                    )
            })


    # --------------------------------------------------------
    # EQUAL HIGH / LOW
    # --------------------------------------------------------

    highs = (
        swings[
            swings["type"] == "HIGH"
        ]
        .sort_values(
            "datetime"
        )
    )

    lows = (
        swings[
            swings["type"] == "LOW"
        ]
        .sort_values(
            "datetime"
        )
    )


    for i in range(
        1,
        len(highs)
    ):

        a = highs.iloc[
            i - 1
        ]

        b = highs.iloc[
            i
        ]

        if abs(
            float(a["price"])
            -
            float(b["price"])
        ) <= EQUAL_TOLERANCE:

            pools.append({

                "kind":
                    "EQUAL",

                "side":
                    "BSL",

                "level":
                    float(
                        (
                            a["price"]
                            +
                            b["price"]
                        ) / 2
                    ),

                "created_time":
                    b["datetime"],

                "source_time":
                    b["datetime"],

                "source_confirmed_time":
                    b["confirmed_time"],

                "source_label":
                    "EQH",

                "source_index":
                    int(
                        b["index"]
                    )
            })


    for i in range(
        1,
        len(lows)
    ):

        a = lows.iloc[
            i - 1
        ]

        b = lows.iloc[
            i
        ]

        if abs(
            float(a["price"])
            -
            float(b["price"])
        ) <= EQUAL_TOLERANCE:

            pools.append({

                "kind":
                    "EQUAL",

                "side":
                    "SSL",

                "level":
                    float(
                        (
                            a["price"]
                            +
                            b["price"]
                        ) / 2
                    ),

                "created_time":
                    b["datetime"],

                "source_time":
                    b["datetime"],

                "source_confirmed_time":
                    b["confirmed_time"],

                "source_label":
                    "EQL",

                "source_index":
                    int(
                        b["index"]
                    )
            })


    if not pools:

        return pd.DataFrame()


    pools = pd.DataFrame(
        pools
    )

    pools = (
        pools
        .sort_values(
            [
                "created_time",
                "source_index"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    pools["pool_id"] = np.arange(
        len(pools)
    )

    return pools


# ============================================================
# LIQUIDITY LIFECYCLE
# ============================================================

def detect_liquidity_lifecycle(
    data,
    pools
):

    events = []

    if pools.empty:

        return pd.DataFrame()


    for _, pool in pools.iterrows():

        level = float(
            pool["level"]
        )

        side = pool["side"]

        created_time = (
            pool["created_time"]
        )

        future = data[
            data["datetime"]
            >
            created_time
        ]


        for _, candle in future.iterrows():

            high = float(
                candle["high"]
            )

            low = float(
                candle["low"]
            )

            close = float(
                candle["close"]
            )

            event_time = (
                candle["datetime"]
            )


            if side == "BSL":

                if (
                    high >= level
                    and
                    close < level
                ):

                    events.append({

                        "pool_id":
                            int(
                                pool["pool_id"]
                            ),

                        "side":
                            side,

                        "kind":
                            pool["kind"],

                        "level":
                            level,

                        "created_time":
                            created_time,

                        "event_time":
                            event_time,

                        "event":
                            "RAIDED"
                    })

                    break


                elif (
                    high >= level
                    and
                    close >= level
                ):

                    events.append({

                        "pool_id":
                            int(
                                pool["pool_id"]
                            ),

                        "side":
                            side,

                        "kind":
                            pool["kind"],

                        "level":
                            level,

                        "created_time":
                            created_time,

                        "event_time":
                            event_time,

                        "event":
                            "TAKEN"
                    })

                    break


            elif side == "SSL":

                if (
                    low <= level
                    and
                    close > level
                ):

                    events.append({

                        "pool_id":
                            int(
                                pool["pool_id"]
                            ),

                        "side":
                            side,

                        "kind":
                            pool["kind"],

                        "level":
                            level,

                        "created_time":
                            created_time,

                        "event_time":
                            event_time,

                        "event":
                            "RAIDED"
                    })

                    break


                elif (
                    low <= level
                    and
                    close <= level
                ):

                    events.append({

                        "pool_id":
                            int(
                                pool["pool_id"]
                            ),

                        "side":
                            side,

                        "kind":
                            pool["kind"],

                        "level":
                            level,

                        "created_time":
                            created_time,

                        "event_time":
                            event_time,

                        "event":
                            "TAKEN"
                    })

                    break


    if not events:

        return pd.DataFrame()

    return pd.DataFrame(
        events
    )


# ============================================================
# FVG
# ============================================================

def detect_fvgs(
    data
):

    rows = []

    for i in range(
        2,
        len(data)
    ):

        c1 = data.iloc[
            i - 2
        ]

        c3 = data.iloc[
            i
        ]


        if (
            float(c1["high"])
            <
            float(c3["low"])
        ):

            rows.append({

                "index":
                    i,

                "datetime":
                    c3["datetime"],

                "direction":
                    "BULLISH",

                "lower":
                    float(
                        c1["high"]
                    ),

                "upper":
                    float(
                        c3["low"]
                    )
            })


        if (
            float(c1["low"])
            >
            float(c3["high"])
        ):

            rows.append({

                "index":
                    i,

                "datetime":
                    c3["datetime"],

                "direction":
                    "BEARISH",

                "lower":
                    float(
                        c3["high"]
                    ),

                "upper":
                    float(
                        c1["low"]
                    )
            })


    if not rows:

        return pd.DataFrame(
            columns=[
                "index",
                "datetime",
                "direction",
                "lower",
                "upper"
            ]
        )

    return pd.DataFrame(
        rows
    )


# ============================================================
# DISPLACEMENT
# ============================================================

def detect_displacement(
    data,
    start_index,
    direction,
    max_bars=DELIVERY_MAX_BARS
):

    end_index = min(
        len(data) - 1,
        start_index + max_bars
    )

    for i in range(
        start_index,
        end_index + 1
    ):

        candle = data.iloc[
            i
        ]

        o = float(
            candle["open"]
        )

        h = float(
            candle["high"]
        )

        l = float(
            candle["low"]
        )

        c = float(
            candle["close"]
        )

        candle_range = (
            h - l
        )

        if candle_range <= 0:
            continue

        body = abs(
            c - o
        )

        body_fraction = (
            body
            /
            candle_range
        )

        if (
            body_fraction
            <
            MIN_BODY_FRACTION
        ):
            continue

        if direction == "BULLISH":

            if c <= o:
                continue

        elif direction == "BEARISH":

            if c >= o:
                continue

        else:

            continue

        return {

            "index":
                i,

            "time":
                candle["datetime"],

            "body_fraction":
                body_fraction
        }

    return None


# ============================================================
# FVG AFTER DISPLACEMENT
# ============================================================

def find_fvg_after_displacement(
    data,
    displacement_index,
    direction
):

    start = displacement_index

    end = min(
        len(data) - 1,
        displacement_index
        + FVG_MAX_BARS_AFTER_DISPLACEMENT
    )

    if end < start:
        return None

    for i in range(
        start,
        end + 1
    ):

        if i < 2:
            continue

        c1 = data.iloc[
            i - 2
        ]

        c3 = data.iloc[
            i
        ]

        if direction == "BULLISH":

            if (
                float(c1["high"])
                <
                float(c3["low"])
            ):

                return {

                    "index":
                        i,

                    "time":
                        c3["datetime"],

                    "lower":
                        float(
                            c1["high"]
                        ),

                    "upper":
                        float(
                            c3["low"]
                        )
                }

        elif direction == "BEARISH":

            if (
                float(c1["low"])
                >
                float(c3["high"])
            ):

                return {

                    "index":
                        i,

                    "time":
                        c3["datetime"],

                    "lower":
                        float(
                            c3["high"]
                        ),

                    "upper":
                        float(
                            c1["low"]
                        )
                }

    return None


# ============================================================
# CAUSAL MSS ENGINE
# ============================================================
#
# IMPORTANT:
# THIS FUNCTION IS PRESERVED FROM OPT-3.3.
#
# NO OPT-3.4 CHANGE HERE.
#
# RAID
#   ↓
# DIRECTION
#   ↓
# PRE-EXISTING REFERENCE
#   ↓
# DISPLACEMENT
#   ↓
# STRUCTURE BREAK
#   ↓
# MSS
# ============================================================

def detect_causal_mss(
    data,
    swings,
    lifecycle
):

    if lifecycle.empty:
        return []

    chains = []

    raids = (
        lifecycle[
            lifecycle["event"]
            ==
            "RAIDED"
        ]
        .sort_values(
            "event_time"
        )
    )


    for _, raid in raids.iterrows():

        raid_time = raid[
            "event_time"
        ]

        raid_level = float(
            raid["level"]
        )

        liquidity_side = raid[
            "side"
        ]


        if liquidity_side == "SSL":

            direction = "BULLISH"

        elif liquidity_side == "BSL":

            direction = "BEARISH"

        else:

            continue


        # ----------------------------------------------------
        # FREEZE REFERENCE
        # ----------------------------------------------------

        if direction == "BULLISH":

            candidates = swings[
                (swings["type"] == "HIGH")
                &
                (
                    swings["confirmed_time"]
                    <= raid_time
                )
                &
                (
                    swings["datetime"]
                    < raid_time
                )
            ].copy()

        else:

            candidates = swings[
                (swings["type"] == "LOW")
                &
                (
                    swings["confirmed_time"]
                    <= raid_time
                )
                &
                (
                    swings["datetime"]
                    < raid_time
                )
            ].copy()


        if candidates.empty:
            continue


        candidates = (
            candidates
            .sort_values(
                [
                    "confirmed_time",
                    "datetime"
                ]
            )
        )

        reference = candidates.iloc[-1]

        reference_price = float(
            reference["price"]
        )

        reference_time = (
            reference["datetime"]
        )

        reference_confirmed_time = (
            reference["confirmed_time"]
        )


        # ----------------------------------------------------
        # DISPLACEMENT
        # ----------------------------------------------------

        raid_indices = data.index[
            data["datetime"]
            >
            raid_time
        ]

        if len(raid_indices) == 0:
            continue

        start_index = int(
            raid_indices[0]
        )

        displacement = (
            detect_displacement(
                data,
                start_index,
                direction
            )
        )

        if displacement is None:
            continue


        displacement_index = (
            displacement["index"]
        )


        # ----------------------------------------------------
        # FVG
        # ----------------------------------------------------

        fvg = (
            find_fvg_after_displacement(
                data,
                displacement_index,
                direction
            )
        )


        # ----------------------------------------------------
        # STRUCTURE BREAK
        # ----------------------------------------------------

        break_start = (
            displacement_index + 1
        )

        break_end = min(
            len(data) - 1,
            displacement_index
            + STRUCTURE_BREAK_MAX_BARS
        )

        mss = None

        for i in range(
            break_start,
            break_end + 1
        ):

            candle = data.iloc[
                i
            ]

            close = float(
                candle["close"]
            )

            if direction == "BULLISH":

                if close > reference_price:

                    mss = {

                        "index":
                            i,

                        "time":
                            candle[
                                "datetime"
                            ]
                    }

                    break

            else:

                if close < reference_price:

                    mss = {

                        "index":
                            i,

                        "time":
                            candle[
                                "datetime"
                            ]
                    }

                    break


        if mss is None:
            continue


        bars_raid_to_disp = (
            displacement_index
            -
            start_index
        )

        bars_disp_to_mss = (
            mss["index"]
            -
            displacement_index
        )

        bars_raid_to_mss = (
            mss["index"]
            -
            start_index
        )


        chains.append({

            "direction":
                direction,

            "liquidity":
                liquidity_side,

            "liquidity_kind":
                raid["kind"],

            "liquidity_level":
                raid_level,

            "raid_time":
                raid_time,

            "reference_price":
                reference_price,

            "reference_time":
                reference_time,

            "reference_confirmed_time":
                reference_confirmed_time,

            "displacement_time":
                displacement["time"],

            "displacement_body_fraction":
                displacement[
                    "body_fraction"
                ],

            "bars_raid_to_displacement":
                bars_raid_to_disp,

            "fvg_found":
                fvg is not None,

            "fvg_time":
                None
                if fvg is None
                else fvg["time"],

            "fvg_lower":
                None
                if fvg is None
                else fvg["lower"],

            "fvg_upper":
                None
                if fvg is None
                else fvg["upper"],

            "mss_time":
                mss["time"],

            "bars_displacement_to_mss":
                bars_disp_to_mss,

            "bars_raid_to_mss":
                bars_raid_to_mss,

            "status":
                "VALID"
        })


    # --------------------------------------------------------
    # SAME RAID → ONE CHAIN
    # --------------------------------------------------------

    unique = {}

    for chain in chains:

        key = (
            chain["liquidity"],
            chain["raid_time"]
        )

        if key not in unique:

            unique[key] = chain

        else:

            old = unique[key]

            if (
                chain["mss_time"]
                <
                old["mss_time"]
            ):

                unique[key] = chain


    chains = list(
        unique.values()
    )

    chains.sort(
        key=lambda x:
            x["mss_time"]
    )


    # --------------------------------------------------------
    # OPPOSING MSS INVALIDATION
    # --------------------------------------------------------

    current_direction = None

    for chain in chains:

        if current_direction is None:

            current_direction = (
                chain["direction"]
            )

            continue


        if (
            chain["direction"]
            !=
            current_direction
        ):

            for previous in chains:

                if (
                    previous["mss_time"]
                    <
                    chain["mss_time"]
                ):

                    if (
                        previous["direction"]
                        !=
                        chain["direction"]
                    ):

                        previous[
                            "status"
                        ] = (
                            "INVALIDATED_BY_OPPOSING_MSS"
                        )


            current_direction = (
                chain["direction"]
            )


    valid = [
        c
        for c in chains
        if c["status"] == "VALID"
    ]

    return valid


# ============================================================
# ORDER FLOW
# ============================================================

def determine_order_flow(
    swings
):

    if swings.empty:
        return "NO DATA"

    highs = (
        swings[
            swings["type"] == "HIGH"
        ]
        .sort_values(
            "datetime"
        )
    )

    lows = (
        swings[
            swings["type"] == "LOW"
        ]
        .sort_values(
            "datetime"
        )
    )

    bullish = False
    bearish = False


    if len(highs) >= 2:

        h1 = float(
            highs.iloc[-2]["price"]
        )

        h2 = float(
            highs.iloc[-1]["price"]
        )

        if h2 > h1:
            bullish = True

        elif h2 < h1:
            bearish = True


    if len(lows) >= 2:

        l1 = float(
            lows.iloc[-2]["price"]
        )

        l2 = float(
            lows.iloc[-1]["price"]
        )

        if l2 > l1:
            bullish = True

        elif l2 < l1:
            bearish = True


    if bullish and not bearish:
        return "BULLISH"

    if bearish and not bullish:
        return "BEARISH"

    return "MIXED"


# ============================================================
# CURRENT DEALING RANGE
# ============================================================

def build_dealing_range(
    data,
    current_mss,
    swings
):

    if current_mss is None:
        return None

    reference_time = (
        current_mss["reference_time"]
    )

    reference_price = float(
        current_mss["reference_price"]
    )

    direction = (
        current_mss["direction"]
    )


    prior_swings = swings[
        (
            swings["confirmed_time"]
            <= reference_time
        )
        &
        (
            swings["datetime"]
            < reference_time
        )
    ].copy()


    if prior_swings.empty:
        return None


    if direction == "BULLISH":

        lows = prior_swings[
            prior_swings["type"] == "LOW"
        ].copy()

        if lows.empty:
            return None

        lows = (
            lows
            .sort_values(
                [
                    "confirmed_time",
                    "datetime"
                ]
            )
        )

        anchor = lows.iloc[-1]

        range_low = float(
            anchor["price"]
        )

        range_low_time = (
            anchor["datetime"]
        )

        range_high = reference_price
        range_high_time = reference_time


    elif direction == "BEARISH":

        highs = prior_swings[
            prior_swings["type"] == "HIGH"
        ].copy()

        if highs.empty:
            return None

        highs = (
            highs
            .sort_values(
                [
                    "confirmed_time",
                    "datetime"
                ]
            )
        )

        anchor = highs.iloc[-1]

        range_high = float(
            anchor["price"]
        )

        range_high_time = (
            anchor["datetime"]
        )

        range_low = reference_price
        range_low_time = reference_time


    else:

        return None


    if range_high <= range_low:
        return None


    equilibrium = (
        range_high
        +
        range_low
    ) / 2


    return {

        "range_high":
            range_high,

        "range_low":
            range_low,

        "range_high_time":
            range_high_time,

        "range_low_time":
            range_low_time,

        "equilibrium":
            equilibrium,

        "direction":
            direction
    }


# ============================================================
# PREMIUM / DISCOUNT
# ============================================================

def determine_premium_discount(
    current_price,
    dealing_range
):

    if dealing_range is None:
        return None

    eq = float(
        dealing_range["equilibrium"]
    )

    if current_price > eq:
        zone = "PREMIUM"

    elif current_price < eq:
        zone = "DISCOUNT"

    else:
        zone = "EQUILIBRIUM"

    return {

        "current_price":
            float(current_price),

        "equilibrium":
            eq,

        "zone":
            zone
    }


# ============================================================
# LIQUIDITY STATE
# ============================================================

def attach_liquidity_state(
    pools,
    lifecycle
):

    pools = pools.copy()

    pools["state"] = "UNTOUCHED"

    if lifecycle.empty:
        return pools


    for i in range(
        len(pools)
    ):

        pool_id = int(
            pools.at[
                i,
                "pool_id"
            ]
        )

        events = lifecycle[
            lifecycle["pool_id"]
            ==
            pool_id
        ]

        if not events.empty:

            event = events.iloc[0]

            pools.at[
                i,
                "state"
            ] = event["event"]


    return pools


# ============================================================
# OPT-3.4
# SWING → STRUCTURE RELATIONSHIP
# ============================================================
#
# This is the main new layer.
#
# A liquidity pool is now explicitly connected to:
#
# SOURCE SWING
#      ↓
# STRUCTURE ROLE
#      ↓
# LIQUIDITY ROLE
#      ↓
# TEMPORAL ROLE
#      ↓
# DELIVERY ROLE
#
# Examples:
#
# 4773.575
# HH / BSL / PRE-MSS / EXTERNAL
#
# 4399.670
# LH / BSL / POST-MSS / EXTERNAL
# ============================================================

def classify_swing_structure_relationship(
    pools,
    swings,
    current_mss,
    post_mss_structure,
    dealing_range
):

    pools = pools.copy()

    if pools.empty:

        return pools


    # --------------------------------------------------------
    # Default columns
    # --------------------------------------------------------

    pools["structure_role"] = (
        pools["source_label"]
    )

    pools["liquidity_role"] = (
        pools["side"]
    )

    pools["location"] = (
        "UNKNOWN"
    )

    pools["temporal_role"] = (
        "UNKNOWN"
    )

    pools["availability_at_mss"] = (
        "UNKNOWN"
    )

    pools["delivery_role"] = (
        "UNCLASSIFIED"
    )

    pools["structural_family"] = (
        "UNCLASSIFIED"
    )

    pools["post_mss_sequence_role"] = (
        "NONE"
    )


    # --------------------------------------------------------
    # Current MSS time
    # --------------------------------------------------------

    mss_time = None

    if current_mss is not None:

        mss_time = (
            current_mss["mss_time"]
        )


    # --------------------------------------------------------
    # Range boundaries
    # --------------------------------------------------------

    range_high = None
    range_low = None

    if dealing_range is not None:

        range_high = float(
            dealing_range["range_high"]
        )

        range_low = float(
            dealing_range["range_low"]
        )


    # --------------------------------------------------------
    # Post-MSS high/low sequences
    # --------------------------------------------------------

    post_highs = []

    post_lows = []

    if post_mss_structure:

        post_highs = (
            post_mss_structure.get(
                "high_sequence",
                []
            )
        )

        post_lows = (
            post_mss_structure.get(
                "low_sequence",
                []
            )
        )


    # --------------------------------------------------------
    # Process every liquidity pool
    # --------------------------------------------------------

    for i in range(
        len(pools)
    ):

        pool = pools.iloc[i]

        pool_id = (
            pool["pool_id"]
        )

        source_time = (
            pool["source_time"]
        )

        source_label = (
            pool["source_label"]
        )

        side = (
            pool["side"]
        )

        level = float(
            pool["level"]
        )


        # ----------------------------------------------------
        # Structure role
        # ----------------------------------------------------

        if source_label in [
            "HH",
            "LH",
            "HL",
            "LL",
            "EQH",
            "EQL",
            "HIGH",
            "LOW"
        ]:

            structure_role = (
                source_label
            )

        else:

            structure_role = (
                "STRUCTURAL_SWING"
            )


        pools.at[
            i,
            "structure_role"
        ] = structure_role


        # ----------------------------------------------------
        # Location
        # ----------------------------------------------------

        if (
            range_high is not None
            and
            range_low is not None
        ):

            if (
                range_low
                <=
                level
                <=
                range_high
            ):

                location = "INTERNAL"

            else:

                location = "EXTERNAL"

        else:

            location = "UNKNOWN"


        pools.at[
            i,
            "location"
        ] = location


        # ----------------------------------------------------
        # Temporal role
        # ----------------------------------------------------

        if mss_time is None:

            temporal_role = (
                "NO_CURRENT_MSS"
            )

            availability = (
                "NO_CURRENT_MSS"
            )

        else:

            if source_time < mss_time:

                temporal_role = (
                    "PRE_MSS"
                )

                confirmed_time = (
                    pool[
                        "source_confirmed_time"
                    ]
                )

                if (
                    confirmed_time
                    <=
                    mss_time
                ):

                    availability = (
                        "CONFIRMED_BEFORE_MSS"
                    )

                else:

                    availability = (
                        "FORMED_BEFORE_MSS_"
                        "CONFIRMED_AFTER"
                    )


            elif source_time > mss_time:

                temporal_role = (
                    "POST_MSS"
                )

                availability = (
                    "FORMED_AFTER_MSS"
                )


            else:

                temporal_role = (
                    "MSS_TIME"
                )

                confirmed_time = (
                    pool[
                        "source_confirmed_time"
                    ]
                )

                if (
                    confirmed_time
                    <=
                    mss_time
                ):

                    availability = (
                        "CONFIRMED_AT_MSS"
                    )

                else:

                    availability = (
                        "FORMED_AT_MSS_"
                        "CONFIRMED_AFTER"
                    )


        pools.at[
            i,
            "temporal_role"
        ] = temporal_role

        pools.at[
            i,
            "availability_at_mss"
        ] = availability


        # ----------------------------------------------------
        # Liquidity role
        # ----------------------------------------------------

        pools.at[
            i,
            "liquidity_role"
        ] = side


        # ----------------------------------------------------
        # Delivery role
        # ----------------------------------------------------
        #
        # This is intentionally descriptive.
        #
        # HH / HL after bullish MSS:
        # continuation structure
        #
        # LH / LL after bullish MSS:
        # corrective structure
        #
        # Reverse for bearish MSS.
        # ----------------------------------------------------

        delivery_role = (
            "HISTORICAL"
        )


        if temporal_role == "POST_MSS":

            if current_mss is not None:

                direction = (
                    current_mss["direction"]
                )


                if direction == "BULLISH":

                    if structure_role in [
                        "HH",
                        "HL"
                    ]:

                        delivery_role = (
                            "POST_MSS_CONTINUATION"
                        )

                    elif structure_role in [
                        "LH",
                        "LL"
                    ]:

                        delivery_role = (
                            "POST_MSS_CORRECTION"
                        )

                    else:

                        delivery_role = (
                            "POST_MSS_DEVELOPING"
                        )


                elif direction == "BEARISH":

                    if structure_role in [
                        "LL",
                        "LH"
                    ]:

                        delivery_role = (
                            "POST_MSS_CONTINUATION"
                        )

                    elif structure_role in [
                        "HH",
                        "HL"
                    ]:

                        delivery_role = (
                            "POST_MSS_CORRECTION"
                        )

                    else:

                        delivery_role = (
                            "POST_MSS_DEVELOPING"
                        )


        elif temporal_role == "PRE_MSS":

            delivery_role = (
                "PRE_MSS_STRUCTURE"
            )


        pools.at[
            i,
            "delivery_role"
        ] = delivery_role


        # ----------------------------------------------------
        # Structural family
        # ----------------------------------------------------

        if temporal_role == "PRE_MSS":

            if structure_role in [
                "HH",
                "EQH",
                "HIGH"
            ]:

                family = (
                    "PRE_MSS_HIGH_STRUCTURE"
                )

            elif structure_role in [
                "LH"
            ]:

                family = (
                    "PRE_MSS_LOWER_HIGH"
                )

            elif structure_role in [
                "HL",
                "EQL",
                "LOW"
            ]:

                family = (
                    "PRE_MSS_LOW_STRUCTURE"
                )

            elif structure_role in [
                "LL"
            ]:

                family = (
                    "PRE_MSS_LOWER_LOW"
                )

            else:

                family = (
                    "PRE_MSS_STRUCTURE"
                )


        elif temporal_role == "POST_MSS":

            if structure_role in [
                "HH"
            ]:

                family = (
                    "POST_MSS_HIGHER_HIGH"
                )

            elif structure_role in [
                "LH"
            ]:

                family = (
                    "POST_MSS_LOWER_HIGH"
                )

            elif structure_role in [
                "HL"
            ]:

                family = (
                    "POST_MSS_HIGHER_LOW"
                )

            elif structure_role in [
                "LL"
            ]:

                family = (
                    "POST_MSS_LOWER_LOW"
                )

            elif structure_role in [
                "EQH"
            ]:

                family = (
                    "POST_MSS_EQUAL_HIGH"
                )

            elif structure_role in [
                "EQL"
            ]:

                family = (
                    "POST_MSS_EQUAL_LOW"
                )

            else:

                family = (
                    "POST_MSS_STRUCTURE"
                )

        else:

            family = (
                "UNCLASSIFIED"
            )


        pools.at[
            i,
            "structural_family"
        ] = family


        # ----------------------------------------------------
        # Post-MSS sequence role
        # ----------------------------------------------------

        if (
            temporal_role
            ==
            "POST_MSS"
        ):

            if structure_role == "LH":

                pools.at[
                    i,
                    "post_mss_sequence_role"
                ] = (
                    "LOWER_HIGH_SEQUENCE"
                )

            elif structure_role == "HH":

                pools.at[
                    i,
                    "post_mss_sequence_role"
                ] = (
                    "HIGHER_HIGH_SEQUENCE"
                )

            elif structure_role == "HL":

                pools.at[
                    i,
                    "post_mss_sequence_role"
                ] = (
                    "HIGHER_LOW_SEQUENCE"
                )

            elif structure_role == "LL":

                pools.at[
                    i,
                    "post_mss_sequence_role"
                ] = (
                    "LOWER_LOW_SEQUENCE"
                )


    return pools


# ============================================================
# POST-MSS STRUCTURE ENGINE
# ============================================================

def analyze_post_mss_structure(
    swings,
    current_mss
):

    result = {

        "available":
            False,

        "mss_time":
            None,

        "direction":
            None,

        "post_mss_swings":
            [],

        "high_sequence":
            [],

        "low_sequence":
            [],

        "structure_state":
            "NO_POST_MSS_STRUCTURE",

        "high_structure":
            "NONE",

        "low_structure":
            "NONE",

        "narrative":
            ""
    }


    if current_mss is None:

        result["narrative"] = (
            "No current MSS."
        )

        return result


    mss_time = (
        current_mss["mss_time"]
    )

    direction = (
        current_mss["direction"]
    )


    result["available"] = True
    result["mss_time"] = mss_time
    result["direction"] = direction


    post = swings[
        swings["datetime"]
        >
        mss_time
    ].copy()


    if post.empty:

        result["narrative"] = (
            "No confirmed swing has formed "
            "after the current MSS."
        )

        return result


    post = (
        post
        .sort_values(
            "datetime"
        )
        .tail(
            POST_MSS_STRUCTURE_MAX_SWINGS
        )
        .reset_index(
            drop=True
        )
    )


    highs = post[
        post["type"] == "HIGH"
    ].copy()

    lows = post[
        post["type"] == "LOW"
    ].copy()


    for _, row in highs.iterrows():

        result[
            "high_sequence"
        ].append({

            "time":
                row["datetime"],

            "price":
                float(
                    row["price"]
                ),

            "label":
                row["label"]
        })


    for _, row in lows.iterrows():

        result[
            "low_sequence"
        ].append({

            "time":
                row["datetime"],

            "price":
                float(
                    row["price"]
                ),

            "label":
                row["label"]
        })


    result[
        "post_mss_swings"
    ] = [

        {

            "time":
                row["datetime"],

            "price":
                float(
                    row["price"]
                ),

            "type":
                row["type"],

            "label":
                row["label"]
        }

        for _, row in post.iterrows()
    ]


    # --------------------------------------------------------
    # HIGH STRUCTURE
    # --------------------------------------------------------

    high_labels = [
        x["label"]
        for x in result[
            "high_sequence"
        ]
    ]


    if len(high_labels) >= 2:

        last_two = high_labels[-2:]

        if all(
            x == "LH"
            for x in last_two
        ):

            high_structure = (
                "LOWER_HIGH_SEQUENCE"
            )

        elif all(
            x == "HH"
            for x in last_two
        ):

            high_structure = (
                "HIGHER_HIGH_SEQUENCE"
            )

        elif last_two[-1] == "LH":

            high_structure = (
                "RECENT_LOWER_HIGH"
            )

        elif last_two[-1] == "HH":

            high_structure = (
                "RECENT_HIGHER_HIGH"
            )

        else:

            high_structure = (
                "MIXED_HIGH_STRUCTURE"
            )


    elif len(high_labels) == 1:

        if high_labels[-1] == "LH":

            high_structure = (
                "LOWER_HIGH"
            )

        elif high_labels[-1] == "HH":

            high_structure = (
                "HIGHER_HIGH"
            )

        else:

            high_structure = (
                "INITIAL_HIGH"
            )

    else:

        high_structure = (
            "NO_HIGH_STRUCTURE"
        )


    # --------------------------------------------------------
    # LOW STRUCTURE
    # --------------------------------------------------------

    low_labels = [
        x["label"]
        for x in result[
            "low_sequence"
        ]
    ]


    if len(low_labels) >= 2:

        last_two = low_labels[-2:]

        if all(
            x == "LL"
            for x in last_two
        ):

            low_structure = (
                "LOWER_LOW_SEQUENCE"
            )

        elif all(
            x == "HL"
            for x in last_two
        ):

            low_structure = (
                "HIGHER_LOW_SEQUENCE"
            )

        elif last_two[-1] == "LL":

            low_structure = (
                "RECENT_LOWER_LOW"
            )

        elif last_two[-1] == "HL":

            low_structure = (
                "RECENT_HIGHER_LOW"
            )

        else:

            low_structure = (
                "MIXED_LOW_STRUCTURE"
            )


    elif len(low_labels) == 1:

        if low_labels[-1] == "LL":

            low_structure = (
                "LOWER_LOW"
            )

        elif low_labels[-1] == "HL":

            low_structure = (
                "HIGHER_LOW"
            )

        else:

            low_structure = (
                "INITIAL_LOW"
            )

    else:

        low_structure = (
            "NO_LOW_STRUCTURE"
        )


    result[
        "high_structure"
    ] = high_structure

    result[
        "low_structure"
    ] = low_structure


    # ========================================================
    # STRUCTURE STATE
    # ========================================================

    if direction == "BULLISH":

        if (
            "LOWER_HIGH"
            in high_structure
            or
            high_structure
            in [
                "RECENT_LOWER_HIGH",
                "LOWER_HIGH_SEQUENCE"
            ]
        ):

            if (
                "LOWER_LOW"
                in low_structure
                or
                low_structure
                in [
                    "RECENT_LOWER_LOW",
                    "LOWER_LOW_SEQUENCE"
                ]
            ):

                state = (
                    "BEARISH_CORRECTION_STRUCTURE"
                )

            else:

                state = (
                    "BULLISH_BIAS_WITH_LOWER_HIGH_CORRECTION"
                )


        elif (
            "HIGHER_HIGH"
            in high_structure
            or
            high_structure
            in [
                "RECENT_HIGHER_HIGH",
                "HIGHER_HIGH_SEQUENCE"
            ]
        ):

            if (
                "HIGHER_LOW"
                in low_structure
                or
                low_structure
                in [
                    "RECENT_HIGHER_LOW",
                    "HIGHER_LOW_SEQUENCE"
                ]
            ):

                state = (
                    "BULLISH_CONTINUATION_STRUCTURE"
                )

            else:

                state = (
                    "BULLISH_STRUCTURE_DEVELOPING"
                )

        else:

            state = (
                "MIXED_POST_MSS_STRUCTURE"
            )


    elif direction == "BEARISH":

        if (
            "HIGHER_LOW"
            in low_structure
            or
            low_structure
            in [
                "RECENT_HIGHER_LOW",
                "HIGHER_LOW_SEQUENCE"
            ]
        ):

            if (
                "HIGHER_HIGH"
                in high_structure
                or
                high_structure
                in [
                    "RECENT_HIGHER_HIGH",
                    "HIGHER_HIGH_SEQUENCE"
                ]
            ):

                state = (
                    "BULLISH_CORRECTION_STRUCTURE"
                )

            else:

                state = (
                    "BEARISH_BIAS_WITH_HIGHER_LOW_CORRECTION"
                )


        elif (
            "LOWER_LOW"
            in low_structure
            or
            low_structure
            in [
                "RECENT_LOWER_LOW",
                "LOWER_LOW_SEQUENCE"
            ]
        ):

            if (
                "LOWER_HIGH"
                in high_structure
                or
                low_structure
                in [
                    "RECENT_LOWER_HIGH",
                    "LOWER_HIGH_SEQUENCE"
                ]
            ):

                state = (
                    "BEARISH_CONTINUATION_STRUCTURE"
                )

            else:

                state = (
                    "BEARISH_STRUCTURE_DEVELOPING"
                )

        else:

            state = (
                "MIXED_POST_MSS_STRUCTURE"
            )


    else:

        state = (
            "MIXED_POST_MSS_STRUCTURE"
        )


    result[
        "structure_state"
    ] = state


    if (
        state
        ==
        "BULLISH_CONTINUATION_STRUCTURE"
    ):

        narrative = (
            "Post-MSS price delivery is "
            "developing higher-high / "
            "higher-low structure."
        )


    elif (
        state
        ==
        "BULLISH_BIAS_WITH_LOWER_HIGH_CORRECTION"
    ):

        narrative = (
            "Bullish MSS remains the active "
            "structural event, but post-MSS "
            "delivery has produced lower-high "
            "structure."
        )


    elif (
        state
        ==
        "BEARISH_CORRECTION_STRUCTURE"
    ):

        narrative = (
            "Post-MSS delivery is corrective "
            "and currently shows lower-high / "
            "lower-low characteristics."
        )


    elif (
        state
        ==
        "BEARISH_CONTINUATION_STRUCTURE"
    ):

        narrative = (
            "Post-MSS price delivery is "
            "developing lower-low / "
            "lower-high structure."
        )


    elif (
        state
        ==
        "BEARISH_BIAS_WITH_HIGHER_LOW_CORRECTION"
    ):

        narrative = (
            "Bearish MSS remains the active "
            "structural event, but post-MSS "
            "delivery has produced higher-low "
            "structure."
        )


    elif (
        state
        ==
        "BULLISH_STRUCTURE_DEVELOPING"
    ):

        narrative = (
            "Post-MSS delivery shows bullish "
            "structural development, but the "
            "sequence is incomplete."
        )


    elif (
        state
        ==
        "BEARISH_STRUCTURE_DEVELOPING"
    ):

        narrative = (
            "Post-MSS delivery shows bearish "
            "structural development, but the "
            "sequence is incomplete."
        )


    else:

        narrative = (
            "Post-MSS structure is mixed or "
            "not yet sufficiently developed."
        )


    result[
        "narrative"
    ] = narrative

    return result


# ============================================================
# OPT-3.4 LIQUIDITY CONTEXT
# ============================================================
#
# IMPORTANT CHANGE:
#
# We do NOT immediately choose a draw.
#
# First classify every untouched liquidity pool.
#
# Then determine its structural context.
#
# PRE-MSS and POST-MSS remain visible.
#
# HH / LH / HL / LL remain visible.
#
# ============================================================

def classify_liquidity_context(
    pools,
    dealing_range,
    current_price,
    current_mss,
    post_mss_structure
):

    output = {

        "internal": [],

        "external": [],

        "relevant_external": [],

        "pre_mss_external": [],

        "post_mss_external": [],

        "pre_mss_relevant": [],

        "post_mss_relevant": [],

        "post_mss_correction": [],

        "post_mss_continuation": [],

        "pre_mss_structural": [],

        "draw_context_candidates": []
    }


    if (
        pools.empty
        or
        dealing_range is None
    ):

        return output


    range_high = float(
        dealing_range["range_high"]
    )

    range_low = float(
        dealing_range["range_low"]
    )

    direction = (
        dealing_range["direction"]
    )


    # ========================================================
    # BUILD RAW CONTEXT
    # ========================================================

    for _, pool in pools.iterrows():

        if (
            pool["state"]
            !=
            "UNTOUCHED"
        ):
            continue


        level = float(
            pool["level"]
        )


        if (
            range_low
            <=
            level
            <=
            range_high
        ):

            location = "INTERNAL"

        else:

            location = "EXTERNAL"


        item = {

            "pool_id":
                int(pool["pool_id"]),

            "side":
                pool["side"],

            "kind":
                pool["kind"],

            "level":
                level,

            "created_time":
                pool["created_time"],

            "source_time":
                pool["source_time"],

            "source_confirmed_time":
                pool[
                    "source_confirmed_time"
                ],

            "source_label":
                pool["source_label"],

            "structure_role":
                pool.get(
                    "structure_role",
                    pool["source_label"]
                ),

            "liquidity_role":
                pool.get(
                    "liquidity_role",
                    pool["side"]
                ),

            "state":
                pool["state"],

            "location":
                location,

            "temporal_role":
                pool.get(
                    "temporal_role",
                    "UNKNOWN"
                ),

            "availability_at_mss":
                pool.get(
                    "availability_at_mss",
                    "UNKNOWN"
                ),

            "delivery_role":
                pool.get(
                    "delivery_role",
                    "UNCLASSIFIED"
                ),

            "structural_family":
                pool.get(
                    "structural_family",
                    "UNCLASSIFIED"
                ),

            "post_mss_sequence_role":
                pool.get(
                    "post_mss_sequence_role",
                    "NONE"
                )
        }


        if location == "INTERNAL":

            output[
                "internal"
            ].append(item)

        else:

            output[
                "external"
            ].append(item)


            if (
                item["temporal_role"]
                ==
                "PRE_MSS"
            ):

                output[
                    "pre_mss_external"
                ].append(item)

            elif (
                item["temporal_role"]
                ==
                "POST_MSS"
            ):

                output[
                    "post_mss_external"
                ].append(item)


    # ========================================================
    # STRUCTURAL GATE
    # ========================================================

    if direction == "BULLISH":

        structural_gate = range_high

        # ----------------------------------------------------
        # PRE-MSS
        # ----------------------------------------------------

        for item in output[
            "pre_mss_external"
        ]:

            if item["side"] != "BSL":
                continue

            if item["level"] <= structural_gate:
                continue

            item = item.copy()

            item["relevance"] = (
                "PRE_MSS_STRUCTURAL_LIQUIDITY"
            )

            item["structural_gate"] = (
                structural_gate
            )

            item["relation"] = (
                "ABOVE_CURRENT_RANGE_HIGH"
            )

            output[
                "pre_mss_relevant"
            ].append(item)

            output[
                "pre_mss_structural"
            ].append(item)


        # ----------------------------------------------------
        # POST-MSS
        # ----------------------------------------------------

        for item in output[
            "post_mss_external"
        ]:

            if item["side"] != "BSL":
                continue

            if item["level"] <= structural_gate:
                continue

            item = item.copy()

            item["structural_gate"] = (
                structural_gate
            )

            item["relation"] = (
                "ABOVE_CURRENT_RANGE_HIGH"
            )

            # ------------------------------------------------
            # IMPORTANT:
            #
            # LH is not called continuation liquidity.
            #
            # It is part of corrective delivery.
            # ------------------------------------------------

            if (
                item["structure_role"]
                ==
                "LH"
            ):

                item["relevance"] = (
                    "POST_MSS_CORRECTIVE_LIQUIDITY"
                )

                output[
                    "post_mss_correction"
                ].append(item)

            elif (
                item["structure_role"]
                ==
                "HH"
            ):

                item["relevance"] = (
                    "POST_MSS_CONTINUATION_LIQUIDITY"
                )

                output[
                    "post_mss_continuation"
                ].append(item)

            else:

                item["relevance"] = (
                    "POST_MSS_DEVELOPING_LIQUIDITY"
                )


            output[
                "post_mss_relevant"
            ].append(item)


    elif direction == "BEARISH":

        structural_gate = range_low

        # ----------------------------------------------------
        # PRE-MSS
        # ----------------------------------------------------

        for item in output[
            "pre_mss_external"
        ]:

            if item["side"] != "SSL":
                continue

            if item["level"] >= structural_gate:
                continue

            item = item.copy()

            item["relevance"] = (
                "PRE_MSS_STRUCTURAL_LIQUIDITY"
            )

            item["structural_gate"] = (
                structural_gate
            )

            item["relation"] = (
                "BELOW_CURRENT_RANGE_LOW"
            )

            output[
                "pre_mss_relevant"
            ].append(item)

            output[
                "pre_mss_structural"
            ].append(item)


        # ----------------------------------------------------
        # POST-MSS
        # ----------------------------------------------------

        for item in output[
            "post_mss_external"
        ]:

            if item["side"] != "SSL":
                continue

            if item["level"] >= structural_gate:
                continue

            item = item.copy()

            item["structural_gate"] = (
                structural_gate
            )

            item["relation"] = (
                "BELOW_CURRENT_RANGE_LOW"
            )

            if (
                item["structure_role"]
                ==
                "LH"
            ):

                item["relevance"] = (
                    "POST_MSS_CONTINUATION_LIQUIDITY"
                )

                output[
                    "post_mss_continuation"
                ].append(item)

            elif (
                item["structure_role"]
                ==
                "HL"
            ):

                item["relevance"] = (
                    "POST_MSS_CORRECTIVE_LIQUIDITY"
                )

                output[
                    "post_mss_correction"
                ].append(item)

            else:

                item["relevance"] = (
                    "POST_MSS_DEVELOPING_LIQUIDITY"
                )


            output[
                "post_mss_relevant"
            ].append(item)


    # ========================================================
    # COMBINE
    # ========================================================

    output[
        "relevant_external"
    ] = (
        output["pre_mss_relevant"]
        +
        output["post_mss_relevant"]
    )


    # ========================================================
    # SORT
    # ========================================================

    if direction == "BULLISH":

        for key in [
            "pre_mss_relevant",
            "post_mss_relevant",
            "pre_mss_structural",
            "post_mss_correction",
            "post_mss_continuation"
        ]:

            output[key] = sorted(
                output[key],
                key=lambda x: (
                    x["level"],
                    x["created_time"]
                )
            )


    elif direction == "BEARISH":

        for key in [
            "pre_mss_relevant",
            "post_mss_relevant",
            "pre_mss_structural",
            "post_mss_correction",
            "post_mss_continuation"
        ]:

            output[key] = sorted(
                output[key],
                key=lambda x: (
                    -x["level"],
                    x["created_time"]
                )
            )


    # ========================================================
    # DRAW CONTEXT CANDIDATES
    # ========================================================
    #
    # NO WINNER.
    #
    # We expose the structurally different candidates.
    # ========================================================

    candidates = []

    for item in output[
        "pre_mss_relevant"
    ]:

        x = item.copy()

        x["draw_context"] = (
            "PRE_MSS_STRUCTURAL"
        )

        candidates.append(x)


    for item in output[
        "post_mss_correction"
    ]:

        x = item.copy()

        x["draw_context"] = (
            "POST_MSS_CORRECTIVE"
        )

        candidates.append(x)


    for item in output[
        "post_mss_continuation"
    ]:

        x = item.copy()

        x["draw_context"] = (
            "POST_MSS_CONTINUATION"
        )

        candidates.append(x)


    output[
        "draw_context_candidates"
    ] = candidates


    return output


# ============================================================
# OPT-3.4 DRAW CONTEXT
# ============================================================
#
# IMPORTANT:
#
# This function does NOT pretend that one level is automatically
# the draw.
#
# It returns a narrative/context object.
#
# PRE-MSS ≠ automatic draw.
# POST-MSS ≠ automatic draw.
# NEAREST ≠ automatic draw.
#
# ============================================================

def determine_draw_on_liquidity(
    context,
    current_mss,
    post_mss_structure
):

    result = {

        "available":
            False,

        "mode":
            "NO_DRAW_CONTEXT",

        "primary_context":
            None,

        "candidates":
            [],

        "narrative":
            ""
    }


    candidates = context.get(
        "draw_context_candidates",
        []
    )


    if not candidates:

        result[
            "narrative"
        ] = (
            "No structurally relevant external "
            "liquidity is currently available "
            "beyond the dealing-range boundary."
        )

        return result


    result[
        "available"
    ] = True


    # --------------------------------------------------------
    # Preserve all candidates.
    # --------------------------------------------------------

    result[
        "candidates"
    ] = candidates


    # --------------------------------------------------------
    # Determine current delivery state.
    # --------------------------------------------------------

    structure_state = None

    if post_mss_structure:

        structure_state = (
            post_mss_structure.get(
                "structure_state"
            )
        )


    # --------------------------------------------------------
    # Contextual interpretation
    # --------------------------------------------------------

    pre = context.get(
        "pre_mss_relevant",
        []
    )

    corrective = context.get(
        "post_mss_correction",
        []
    )

    continuation = context.get(
        "post_mss_continuation",
        []
    )


    # --------------------------------------------------------
    # PRE-MSS + corrective post-MSS
    # --------------------------------------------------------
    #
    # We do NOT select one level.
    #
    # We identify two different structural layers.
    # --------------------------------------------------------

    if (
        pre
        and
        corrective
    ):

        result[
            "mode"
        ] = (
            "PRE_MSS_AND_POST_MSS_CORRECTION"
        )

        result[
            "primary_context"
        ] = (
            "POST_MSS_CORRECTIVE_DELIVERY"
        )

        result[
            "narrative"
        ] = (
            "Both pre-MSS structural liquidity "
            "and post-MSS corrective liquidity "
            "remain externally available. "
            "Current delivery context is "
            "corrective; therefore liquidity "
            "cannot be reduced to a single "
            "undifferentiated draw."
        )

        return result


    # --------------------------------------------------------
    # PRE-MSS only
    # --------------------------------------------------------

    if pre and not corrective:

        result[
            "mode"
        ] = (
            "PRE_MSS_STRUCTURAL_CONTEXT"
        )

        result[
            "primary_context"
        ] = (
            "PRE_MSS_STRUCTURAL"
        )

        result[
            "narrative"
        ] = (
            "Pre-MSS structural liquidity remains "
            "externally available. It belongs to "
            "the structural environment that "
            "preceded the current MSS."
        )

        return result


    # --------------------------------------------------------
    # Corrective POST-MSS only
    # --------------------------------------------------------

    if corrective and not pre:

        result[
            "mode"
        ] = (
            "POST_MSS_CORRECTIVE_CONTEXT"
        )

        result[
            "primary_context"
        ] = (
            "POST_MSS_CORRECTIVE"
        )

        result[
            "narrative"
        ] = (
            "External liquidity has been created "
            "by post-MSS corrective structure. "
            "These levels belong to the current "
            "lower-high / corrective delivery "
            "sequence."
        )

        return result


    # --------------------------------------------------------
    # Continuation only
    # --------------------------------------------------------

    if continuation:

        result[
            "mode"
        ] = (
            "POST_MSS_CONTINUATION_CONTEXT"
        )

        result[
            "primary_context"
        ] = (
            "POST_MSS_CONTINUATION"
        )

        result[
            "narrative"
        ] = (
            "External liquidity has been created "
            "by post-MSS continuation structure."
        )

        return result


    # --------------------------------------------------------
    # Generic
    # --------------------------------------------------------

    result[
        "mode"
    ] = (
        "MULTIPLE_EXTERNAL_CONTEXTS"
    )

    result[
        "primary_context"
    ] = (
        "MULTIPLE"
    )

    result[
        "narrative"
    ] = (
        "Multiple structurally distinct "
        "external liquidity contexts remain "
        "available."
    )

    return result


# ============================================================
# TIMEFRAME ENGINE
# ============================================================

def run_engine(
    period_df,
    timeframe_name
):

    result = {

        "timeframe":
            timeframe_name,

        "bias":
            "NO CLEAR BIAS",

        "order_flow":
            "NO DATA",

        "reason":
            "",

        "swings":
            pd.DataFrame(),

        "pools":
            pd.DataFrame(),

        "lifecycle":
            pd.DataFrame(),

        "fvgs":
            pd.DataFrame(),

        "mss":
            [],

        "current_mss":
            None,

        "dealing_range":
            None,

        "premium_discount":
            None,

        "post_mss_structure":
            {},

        "liquidity_context":
            {},

        "draw":
            None
    }


    if period_df.empty:

        result[
            "reason"
        ] = "No data."

        return result


    # ========================================================
    # SWINGS
    # ========================================================

    swings = detect_pivots(
        period_df
    )

    swings = label_swings(
        swings
    )

    result[
        "swings"
    ] = swings


    # ========================================================
    # LIQUIDITY
    # ========================================================

    pools = build_liquidity_pools(
        swings
    )

    result[
        "pools"
    ] = pools


    if pools.empty:

        lifecycle = pd.DataFrame()

    else:

        lifecycle = (
            detect_liquidity_lifecycle(
                period_df,
                pools
            )
        )


    pools = attach_liquidity_state(
        pools,
        lifecycle
    )

    result[
        "pools"
    ] = pools

    result[
        "lifecycle"
    ] = lifecycle


    # ========================================================
    # FVG
    # ========================================================

    fvgs = detect_fvgs(
        period_df
    )

    result[
        "fvgs"
    ] = fvgs


    # ========================================================
    # MSS
    # ========================================================

    mss_chains = (
        detect_causal_mss(
            period_df,
            swings,
            lifecycle
        )
    )

    result[
        "mss"
    ] = mss_chains


    if mss_chains:

        current_mss = (
            mss_chains[-1]
        )

    else:

        current_mss = None


    result[
        "current_mss"
    ] = current_mss


    # ========================================================
    # ORDER FLOW
    # ========================================================

    result[
        "order_flow"
    ] = determine_order_flow(
        swings
    )


    # ========================================================
    # BIAS
    # ========================================================

    if current_mss is not None:

        result[
            "bias"
        ] = current_mss[
            "direction"
        ]

        if (
            current_mss["direction"]
            ==
            "BULLISH"
        ):

            result[
                "reason"
            ] = (
                "Sell-side liquidity was raided, "
                "followed by bullish delivery and "
                "a causal break of pre-existing "
                "structure."
            )

        else:

            result[
                "reason"
            ] = (
                "Buy-side liquidity was raided, "
                "followed by bearish delivery and "
                "a causal break of pre-existing "
                "structure."
            )

    else:

        result[
            "bias"
        ] = "NO CLEAR BIAS"

        result[
            "reason"
        ] = (
            "No confirmed chronological "
            "liquidity -> delivery -> "
            "structure break chain."
        )


    # ========================================================
    # DEALING RANGE
    # ========================================================

    dealing_range = (
        build_dealing_range(
            period_df,
            current_mss,
            swings
        )
    )

    result[
        "dealing_range"
    ] = dealing_range


    # ========================================================
    # CURRENT PRICE
    # ========================================================

    current_price = float(
        period_df.iloc[-1]["close"]
    )


    # ========================================================
    # PREMIUM / DISCOUNT
    # ========================================================

    result[
        "premium_discount"
    ] = (
        determine_premium_discount(
            current_price,
            dealing_range
        )
    )


    # ========================================================
    # POST-MSS STRUCTURE
    # ========================================================

    post_mss_structure = (
        analyze_post_mss_structure(
            swings,
            current_mss
        )
    )

    result[
        "post_mss_structure"
    ] = post_mss_structure


    # ========================================================
    # OPT-3.4
    #
    # SWING → STRUCTURE → LIQUIDITY
    # ========================================================

    pools = (
        classify_swing_structure_relationship(
            pools,
            swings,
            current_mss,
            post_mss_structure,
            dealing_range
        )
    )

    result[
        "pools"
    ] = pools


    # ========================================================
    # LIQUIDITY CONTEXT
    # ========================================================

    liquidity_context = (
        classify_liquidity_context(
            pools,
            dealing_range,
            current_price,
            current_mss,
            post_mss_structure
        )
    )

    result[
        "liquidity_context"
    ] = liquidity_context


    # ========================================================
    # DRAW CONTEXT
    # ========================================================

    draw = (
        determine_draw_on_liquidity(
            liquidity_context,
            current_mss,
            post_mss_structure
        )
    )

    result[
        "draw"
    ] = draw


    # ========================================================
    # CONTEXTUAL REASON
    # ========================================================

    if draw.get("available"):

        result[
            "reason"
        ] += (
            " Liquidity has been linked to its "
            "source swing and separated by "
            "structural and temporal role."
        )

        result[
            "reason"
        ] += (
            " "
            +
            draw.get(
                "narrative",
                ""
            )
        )

    else:

        result[
            "reason"
        ] += (
            " No structurally relevant "
            "external liquidity was identified "
            "beyond the current dealing-range "
            "boundary."
        )


    if post_mss_structure:

        result[
            "reason"
        ] += (
            " "
            +
            post_mss_structure.get(
                "narrative",
                ""
            )
        )


    return result


# ============================================================
# RUN
# ============================================================

daily_report = run_engine(
    daily_completed,
    "DAILY"
)

weekly_report = run_engine(
    weekly_completed,
    "WEEKLY"
)


# ============================================================
# HELPERS
# ============================================================

def count_events(
    lifecycle,
    event_name
):

    if lifecycle.empty:
        return 0

    return int(
        (
            lifecycle["event"]
            ==
            event_name
        ).sum()
    )


# ============================================================
# PRINT POST-MSS STRUCTURE
# ============================================================

def print_post_mss_structure(
    structure
):

    print()
    print("=" * 78)
    print("POST-MSS STRUCTURE")
    print("=" * 78)


    if not structure:

        print("None")
        return


    print(
        f"Available        : "
        f"{structure.get('available')}"
    )

    print(
        f"MSS time         : "
        f"{structure.get('mss_time')}"
    )

    print(
        f"Direction        : "
        f"{structure.get('direction')}"
    )

    print(
        f"Structure state  : "
        f"{structure.get('structure_state')}"
    )

    print(
        f"High structure   : "
        f"{structure.get('high_structure')}"
    )

    print(
        f"Low structure    : "
        f"{structure.get('low_structure')}"
    )

    print()
    print(
        f"Narrative:\n"
        f"{structure.get('narrative')}"
    )


    highs = structure.get(
        "high_sequence",
        []
    )

    if highs:

        print()
        print(
            "POST-MSS HIGH SEQUENCE"
        )

        for item in highs[-10:]:

            print(
                f"{item['time']} | "
                f"{item['price']:.3f} | "
                f"{item['label']}"
            )


    lows = structure.get(
        "low_sequence",
        []
    )

    if lows:

        print()
        print(
            "POST-MSS LOW SEQUENCE"
        )

        for item in lows[-10:]:

            print(
                f"{item['time']} | "
                f"{item['price']:.3f} | "
                f"{item['label']}"
            )


# ============================================================
# PRINT LIQUIDITY FAMILY
# ============================================================

def print_liquidity_family(
    context
):

    print()
    print("=" * 78)
    print(
        "STRUCTURE → LIQUIDITY RELATIONSHIP — OPT 3.4"
    )
    print("=" * 78)


    print(
        f"Internal untouched       : "
        f"{len(context.get('internal', []))}"
    )

    print(
        f"External untouched       : "
        f"{len(context.get('external', []))}"
    )

    print(
        f"Pre-MSS external         : "
        f"{len(context.get('pre_mss_external', []))}"
    )

    print(
        f"Post-MSS external        : "
        f"{len(context.get('post_mss_external', []))}"
    )

    print(
        f"Pre-MSS relevant         : "
        f"{len(context.get('pre_mss_relevant', []))}"
    )

    print(
        f"Post-MSS relevant        : "
        f"{len(context.get('post_mss_relevant', []))}"
    )

    print(
        f"Post-MSS corrective      : "
        f"{len(context.get('post_mss_correction', []))}"
    )

    print(
        f"Post-MSS continuation    : "
        f"{len(context.get('post_mss_continuation', []))}"
    )


    # --------------------------------------------------------
    # PRE-MSS
    # --------------------------------------------------------

    pre = context.get(
        "pre_mss_relevant",
        []
    )

    if pre:

        print()
        print(
            "PRE-MSS STRUCTURAL LIQUIDITY"
        )

        for item in pre[:10]:

            print(
                f"{item['level']:.3f} | "
                f"{item['structure_role']} | "
                f"{item['side']} | "
                f"{item['temporal_role']} | "
                f"{item['location']} | "
                f"{item['created_time']}"
            )


    # --------------------------------------------------------
    # POST-MSS CORRECTIVE
    # --------------------------------------------------------

    corrective = context.get(
        "post_mss_correction",
        []
    )

    if corrective:

        print()
        print(
            "POST-MSS CORRECTIVE LIQUIDITY"
        )

        for item in corrective[:10]:

            print(
                f"{item['level']:.3f} | "
                f"{item['structure_role']} | "
                f"{item['side']} | "
                f"{item['delivery_role']} | "
                f"{item['structural_family']} | "
                f"{item['created_time']}"
            )


    # --------------------------------------------------------
    # POST-MSS CONTINUATION
    # --------------------------------------------------------

    continuation = context.get(
        "post_mss_continuation",
        []
    )

    if continuation:

        print()
        print(
            "POST-MSS CONTINUATION LIQUIDITY"
        )

        for item in continuation[:10]:

            print(
                f"{item['level']:.3f} | "
                f"{item['structure_role']} | "
                f"{item['side']} | "
                f"{item['delivery_role']} | "
                f"{item['structural_family']} | "
                f"{item['created_time']}"
            )


# ============================================================
# PRINT DRAW CONTEXT
# ============================================================

def print_draw_context(
    draw
):

    print()
    print("=" * 78)
    print(
        "DRAW CONTEXT — OPT 3.4"
    )
    print("=" * 78)


    if not draw:

        print("None")
        return


    print(
        f"Available        : "
        f"{draw.get('available')}"
    )

    print(
        f"Mode             : "
        f"{draw.get('mode')}"
    )

    print(
        f"Primary context  : "
        f"{draw.get('primary_context')}"
    )

    print()
    print(
        "Narrative:"
    )

    print(
        draw.get(
            "narrative",
            ""
        )
    )


    candidates = draw.get(
        "candidates",
        []
    )


    if not candidates:

        return


    print()
    print(
        "DRAW CONTEXT CANDIDATES"
    )


    for item in candidates[:20]:

        print(
            f"{item['level']:.3f} | "
            f"{item['structure_role']} | "
            f"{item['side']} | "
            f"{item['temporal_role']} | "
            f"{item['draw_context']} | "
            f"{item['created_time']}"
        )


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(
    report
):

    print()
    print("=" * 78)
    print(
        report["timeframe"]
    )
    print("=" * 78)


    period_df = (
        daily_completed
        if report["timeframe"] == "DAILY"
        else weekly_completed
    )


    print(
        f"Last candle      : "
        f"{period_df.iloc[-1]['datetime']}"
    )

    print(
        f"Bias             : "
        f"{report['bias']}"
    )

    print(
        f"Order Flow       : "
        f"{report['order_flow']}"
    )

    print(
        f"Reason           : "
        f"{report['reason']}"
    )


    print()

    print(
        f"Confirmed swings : "
        f"{len(report['swings'])}"
    )

    print(
        f"Liquidity pools  : "
        f"{len(report['pools'])}"
    )

    print(
        f"Liquidity events : "
        f"{len(report['lifecycle'])}"
    )

    print(
        f"Liquidity raids  : "
        f"{count_events(report['lifecycle'], 'RAIDED')}"
    )

    print(
        f"Liquidity taken  : "
        f"{count_events(report['lifecycle'], 'TAKEN')}"
    )

    print(
        f"FVG              : "
        f"{len(report['fvgs'])}"
    )

    print(
        f"MSS chains       : "
        f"{len(report['mss'])}"
    )


    # ========================================================
    # MSS
    # ========================================================

    print()
    print("LATEST VALID MSS")

    chain = report[
        "current_mss"
    ]


    if chain is None:

        print("None")

    else:

        print(
            f"Direction       : "
            f"{chain['direction']}"
        )

        print(
            f"Liquidity       : "
            f"{chain['liquidity']}"
        )

        print(
            f"Liquidity kind  : "
            f"{chain['liquidity_kind']}"
        )

        print(
            f"Liquidity level : "
            f"{chain['liquidity_level']:.3f}"
        )

        print(
            f"Liquidity time  : "
            f"{chain['raid_time']}"
        )

        print(
            f"Reference swing : "
            f"{chain['reference_price']:.3f}"
        )

        print(
            f"Swing time      : "
            f"{chain['reference_time']}"
        )

        print(
            f"Swing confirmed : "
            f"{chain['reference_confirmed_time']}"
        )

        print(
            f"Displacement    : "
            f"{chain['displacement_time']}"
        )

        print(
            f"Body fraction   : "
            f"{chain['displacement_body_fraction']:.4f}"
        )

        print(
            f"Raid → Disp     : "
            f"{chain['bars_raid_to_displacement']} bars"
        )

        print(
            f"FVG found       : "
            f"{chain['fvg_found']}"
        )

        if chain["fvg_found"]:

            print(
                f"FVG time        : "
                f"{chain['fvg_time']}"
            )

            print(
                f"FVG lower       : "
                f"{chain['fvg_lower']:.3f}"
            )

            print(
                f"FVG upper       : "
                f"{chain['fvg_upper']:.3f}"
            )

        print(
            f"MSS time        : "
            f"{chain['mss_time']}"
        )

        print(
            f"Disp → MSS      : "
            f"{chain['bars_displacement_to_mss']} bars"
        )

        print(
            f"Raid → MSS      : "
            f"{chain['bars_raid_to_mss']} bars"
        )

        print(
            f"Status          : "
            f"{chain['status']}"
        )


    # ========================================================
    # DEALING RANGE
    # ========================================================

    print()
    print("=" * 78)
    print(
        "CURRENT DEALING RANGE"
    )
    print("=" * 78)


    dr = report[
        "dealing_range"
    ]


    if dr is None:

        print("None")

    else:

        print(
            f"High          : "
            f"{dr['range_high']:.3f}"
        )

        print(
            f"High time     : "
            f"{dr['range_high_time']}"
        )

        print(
            f"Low           : "
            f"{dr['range_low']:.3f}"
        )

        print(
            f"Low time      : "
            f"{dr['range_low_time']}"
        )

        print(
            f"Equilibrium   : "
            f"{dr['equilibrium']:.3f}"
        )


    # ========================================================
    # PREMIUM / DISCOUNT
    # ========================================================

    print()
    print("=" * 78)
    print(
        "PREMIUM / DISCOUNT"
    )
    print("=" * 78)


    pd_zone = report[
        "premium_discount"
    ]


    if pd_zone is None:

        print("None")

    else:

        print(
            f"Current price : "
            f"{pd_zone['current_price']:.3f}"
        )

        print(
            f"Equilibrium   : "
            f"{pd_zone['equilibrium']:.3f}"
        )

        print(
            f"Zone          : "
            f"{pd_zone['zone']}"
        )


    # ========================================================
    # POST MSS
    # ========================================================

    print_post_mss_structure(
        report[
            "post_mss_structure"
        ]
    )


    # ========================================================
    # LIQUIDITY
    # ========================================================

    print_liquidity_family(
        report[
            "liquidity_context"
        ]
    )


    # ========================================================
    # DRAW
    # ========================================================

    print_draw_context(
        report[
            "draw"
        ]
    )


# ============================================================
# PRINT REPORTS
# ============================================================

print_report(
    weekly_report
)

print_report(
    daily_report
)


# ============================================================
# MULTI-TIMEFRAME NARRATIVE
# ============================================================

print()
print("=" * 78)
print(
    "MULTI-TIMEFRAME NARRATIVE"
)
print("=" * 78)


weekly_bias = (
    weekly_report["bias"]
)

daily_bias = (
    daily_report["bias"]
)


print(
    f"WEEKLY BIAS : "
    f"{weekly_bias}"
)

print(
    f"DAILY BIAS  : "
    f"{daily_bias}"
)


if (
    weekly_bias == "BULLISH"
    and
    daily_bias == "BULLISH"
):

    mtf_narrative = (
        "Weekly and Daily narratives are "
        "directionally aligned bullish."
    )


elif (
    weekly_bias == "BEARISH"
    and
    daily_bias == "BEARISH"
):

    mtf_narrative = (
        "Weekly and Daily narratives are "
        "directionally aligned bearish."
    )


elif (
    daily_bias in [
        "BULLISH",
        "BEARISH"
    ]
    and
    weekly_bias == "NO CLEAR BIAS"
):

    mtf_narrative = (
        "Daily has a directional narrative, "
        "but the higher-timeframe Weekly "
        "narrative is incomplete."
    )


else:

    mtf_narrative = (
        "Higher-timeframe and Daily narratives "
        "are not directionally aligned."
    )


print()
print(
    f"NARRATIVE:\n"
    f"{mtf_narrative}"
)


# ============================================================
# AUDIT
# ============================================================

audit_rows = []


for report in [
    weekly_report,
    daily_report
]:

    chain = report[
        "current_mss"
    ]

    draw = report[
        "draw"
    ]

    dr = report[
        "dealing_range"
    ]

    pd_zone = report[
        "premium_discount"
    ]

    context = report[
        "liquidity_context"
    ]

    post_structure = report[
        "post_mss_structure"
    ]


    audit_rows.append({

        "timeframe":
            report["timeframe"],

        "bias":
            report["bias"],

        "order_flow":
            report["order_flow"],

        "reason":
            report["reason"],

        "confirmed_swings":
            len(report["swings"]),

        "liquidity_pools":
            len(report["pools"]),

        "liquidity_events":
            len(report["lifecycle"]),

        "liquidity_raids":
            count_events(
                report["lifecycle"],
                "RAIDED"
            ),

        "liquidity_taken":
            count_events(
                report["lifecycle"],
                "TAKEN"
            ),

        "fvg_count":
            len(report["fvgs"]),

        "mss_count":
            len(report["mss"]),


        # ----------------------------------------------------
        # MSS
        # ----------------------------------------------------

        "mss_direction":
            None
            if chain is None
            else chain["direction"],

        "mss_liquidity":
            None
            if chain is None
            else chain["liquidity"],

        "mss_liquidity_level":
            None
            if chain is None
            else chain["liquidity_level"],

        "raid_time":
            None
            if chain is None
            else chain["raid_time"],

        "reference_price":
            None
            if chain is None
            else chain["reference_price"],

        "reference_time":
            None
            if chain is None
            else chain["reference_time"],

        "reference_confirmed_time":
            None
            if chain is None
            else chain[
                "reference_confirmed_time"
            ],

        "displacement_time":
            None
            if chain is None
            else chain["displacement_time"],

        "displacement_body_fraction":
            None
            if chain is None
            else chain[
                "displacement_body_fraction"
            ],

        "bars_raid_to_displacement":
            None
            if chain is None
            else chain[
                "bars_raid_to_displacement"
            ],

        "fvg_found":
            None
            if chain is None
            else chain["fvg_found"],

        "fvg_time":
            None
            if chain is None
            else chain["fvg_time"],

        "mss_time":
            None
            if chain is None
            else chain["mss_time"],

        "bars_displacement_to_mss":
            None
            if chain is None
            else chain[
                "bars_displacement_to_mss"
            ],

        "bars_raid_to_mss":
            None
            if chain is None
            else chain[
                "bars_raid_to_mss"
            ],


        # ----------------------------------------------------
        # DEALING RANGE
        # ----------------------------------------------------

        "dealing_range_high":
            None
            if dr is None
            else dr["range_high"],

        "dealing_range_low":
            None
            if dr is None
            else dr["range_low"],

        "equilibrium":
            None
            if dr is None
            else dr["equilibrium"],

        "current_price":
            None
            if pd_zone is None
            else pd_zone["current_price"],

        "premium_discount":
            None
            if pd_zone is None
            else pd_zone["zone"],


        # ----------------------------------------------------
        # POST MSS
        # ----------------------------------------------------

        "post_mss_structure_state":
            post_structure.get(
                "structure_state"
            )
            if post_structure
            else None,

        "post_mss_high_structure":
            post_structure.get(
                "high_structure"
            )
            if post_structure
            else None,

        "post_mss_low_structure":
            post_structure.get(
                "low_structure"
            )
            if post_structure
            else None,

        "post_mss_narrative":
            post_structure.get(
                "narrative"
            )
            if post_structure
            else None,

        "post_mss_swing_count":
            len(
                post_structure.get(
                    "post_mss_swings",
                    []
                )
            )
            if post_structure
            else 0,


        # ----------------------------------------------------
        # LIQUIDITY CONTEXT
        # ----------------------------------------------------

        "internal_untouched":
            len(
                context.get(
                    "internal",
                    []
                )
            ),

        "external_untouched":
            len(
                context.get(
                    "external",
                    []
                )
            ),

        "pre_mss_external":
            len(
                context.get(
                    "pre_mss_external",
                    []
                )
            ),

        "post_mss_external":
            len(
                context.get(
                    "post_mss_external",
                    []
                )
            ),

        "pre_mss_relevant":
            len(
                context.get(
                    "pre_mss_relevant",
                    []
                )
            ),

        "post_mss_relevant":
            len(
                context.get(
                    "post_mss_relevant",
                    []
                )
            ),

        "post_mss_correction":
            len(
                context.get(
                    "post_mss_correction",
                    []
                )
            ),

        "post_mss_continuation":
            len(
                context.get(
                    "post_mss_continuation",
                    []
                )
            ),

        "relevant_external":
            len(
                context.get(
                    "relevant_external",
                    []
                )
            ),


        # ----------------------------------------------------
        # DRAW CONTEXT
        # ----------------------------------------------------

        "draw_available":
            None
            if not draw
            else draw.get(
                "available"
            ),

        "draw_mode":
            None
            if not draw
            else draw.get(
                "mode"
            ),

        "draw_primary_context":
            None
            if not draw
            else draw.get(
                "primary_context"
            ),

        "draw_candidate_count":
            0
            if not draw
            else len(
                draw.get(
                    "candidates",
                    []
                )
            ),

        "draw_narrative":
            None
            if not draw
            else draw.get(
                "narrative"
            )
    })


audit_df = pd.DataFrame(
    audit_rows
)


# ============================================================
# SAVE AUDIT
# ============================================================

audit_df.to_csv(
    AUDIT_FILE,
    index=False
)


# ============================================================
# JSON SERIALIZATION
# ============================================================

def json_safe(
    value
):

    if isinstance(
        value,
        (
            pd.Timestamp,
            np.datetime64
        )
    ):

        return str(
            value
        )


    if isinstance(
        value,
        (
            np.integer,
        )
    ):

        return int(
            value
        )


    if isinstance(
        value,
        (
            np.floating,
        )
    ):

        return float(
            value
        )


    if value is None:

        return None


    try:

        if pd.isna(value):

            return None

    except Exception:

        pass


    return value


# ============================================================
# DATAFRAME → RECORDS
# ============================================================

def dataframe_to_records(
    data
):

    if data is None:
        return []

    if data.empty:
        return []

    records = (
        data
        .replace(
            {
                np.nan:
                    None
            }
        )
        .to_dict(
            orient="records"
        )
    )

    return records


# ============================================================
# SERIALIZE REPORT
# ============================================================

def serialize_report(
    report
):

    output = {

        "timeframe":
            report["timeframe"],

        "bias":
            report["bias"],

        "order_flow":
            report["order_flow"],

        "reason":
            report["reason"],

        "confirmed_swings":
            len(report["swings"]),

        "liquidity_pools":
            len(report["pools"]),

        "liquidity_events":
            len(report["lifecycle"]),

        "liquidity_raids":
            count_events(
                report["lifecycle"],
                "RAIDED"
            ),

        "liquidity_taken":
            count_events(
                report["lifecycle"],
                "TAKEN"
            ),

        "fvg_count":
            len(report["fvgs"]),

        "mss_count":
            len(report["mss"]),

        "current_mss":
            report["current_mss"],

        "dealing_range":
            report["dealing_range"],

        "premium_discount":
            report["premium_discount"],

        "post_mss_structure":
            report["post_mss_structure"],

        "liquidity_context":
            report["liquidity_context"],

        "draw_context":
            report["draw"]
    }


    return output


# ============================================================
# JSON REPORT
# ============================================================

json_report = {

    "engine":
        "ICT_BIAS_ENGINE_OPT34",

    "engine_version":
        "OPT-3.4",

    "source":
        SOURCE_FILE,

    "source_read_only":
        True,

    "time_conversion":
        "UTC epoch + 7 hours WIB",

    "scope": [

        "Weekly",

        "Daily",

        "Structure",

        "Liquidity",

        "Liquidity lifecycle",

        "Pre-MSS liquidity",

        "Post-MSS liquidity",

        "Swing structure role",

        "HH LH HL LL",

        "BSL SSL",

        "Structural liquidity family",

        "Price delivery",

        "Displacement",

        "FVG",

        "Causal MSS",

        "Dealing Range",

        "Premium Discount",

        "Liquidity Relevance",

        "Post-MSS Structure",

        "Draw Context"
    ],

    "excluded": [

        "Entry",

        "Stop Loss",

        "Take Profit",

        "Profit Optimization",

        "Numeric Scoring",

        "CRT",

        "Finex Session Rules",

        "18:00 Setup",

        "19:00 Entry",

        "21:00 Exit"
    ],

    "weekly":
        serialize_report(
            weekly_report
        ),

    "daily":
        serialize_report(
            daily_report
        ),

    "multi_timeframe": {

        "weekly_bias":
            weekly_bias,

        "daily_bias":
            daily_bias,

        "narrative":
            mtf_narrative
    }
}


with open(
    REPORT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        json_report,
        f,
        indent=2,
        ensure_ascii=False,
        default=json_safe
    )


# ============================================================
# FILE OUTPUT
# ============================================================

print()
print("=" * 78)
print("FILES")
print("=" * 78)

print(
    f"Audit  : "
    f"{AUDIT_FILE}"
)

print(
    f"Report : "
    f"{REPORT_FILE}"
)

print()
print(
    "SOURCE CSV TIDAK DIUBAH."
)

print()
print("=" * 78)
print(
    "OPTIMIZATION 3.4 SELESAI"
)
print("=" * 78)