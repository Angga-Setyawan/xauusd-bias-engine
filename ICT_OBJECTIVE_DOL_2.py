# =============================================================================
# ICT_OBJECTIVE_DOL_2.py
# =============================================================================
#
# ICT OBJECTIVE / DOL ENGINE — PHASE 2
# FINAL CONCEPTUAL IMPLEMENTATION
#
# PURPOSE
# -------
# 1. Consume Phase 1 context.
# 2. Build objective map.
# 3. Process objective states chronologically.
# 4. Separate liquidity state from inefficiency state.
# 5. Interpret DOL from contextual delivery evidence.
# 6. Never force a DOL merely because an objective is nearby.
#
# ICT CONCEPTUAL GUARDRAILS
# -------------------------
# - DOL = draw / objective of price delivery.
# - Liquidity raid != automatically DOL.
# - PD Array / FVG != automatically DOL.
# - NDOG / NWOG may function as DOL in context.
# - Current leg != automatically macro bias.
# - Macro bullish + bearish correction must remain a two-layer context.
# - No nearest-objective rule.
# - No numerical DOL score.
#
# OUR FORMALIZATIONS
# ------------------
# The following are computational representations, NOT claimed as
# universal ICT rules:
# - 2-left / 2-right swing detector
# - numerical equal-high/equal-low tolerance
# - candle/zone touch detection
# - liquidity penetration detection
# - FVG fill definition
# - objective grouping
# - contextual DOL classification
#
# SOURCE CSV
# ----------
# READ ONLY.
# All calculations use DataFrame copies.
#
# TIME
# ----
# Epoch source is interpreted explicitly as UTC and then +7 hours for WIB.
#
# IMPORTANT
# ---------
# datetime.fromtimestamp() MUST receive timezone=timezone.utc.
# Otherwise Android/Pydroid3 local WIB timezone can cause +7 hours twice.
# =============================================================================


import os
import json
import glob
from datetime import datetime, timedelta, timezone

import pandas as pd


# =============================================================================
# CONFIG
# =============================================================================

BASE_DIR = "/storage/emulated/0/xauusd_engine"

SOURCE_CANDIDATES = [
    os.path.join(
        BASE_DIR,
        "XAUUSD_H1_FULL.csv"
    ),
    os.path.join(
        BASE_DIR,
        "XAUUSD_H1_2026.csv"
    ),
]

PARENT_CANDIDATES = [
    os.path.join(
        BASE_DIR,
        "ICT_BIAS_ENGINE_OPT35_REPORT.json"
    ),
    os.path.join(
        BASE_DIR,
        "ICT_BIAS_ENGINE_1.json"
    ),
]

OUTPUT_JSON = os.path.join(
    BASE_DIR,
    "ICT_OBJECTIVE_DOL_PHASE2_REPORT.json"
)

OUTPUT_OBJECTIVES = os.path.join(
    BASE_DIR,
    "ICT_OBJECTIVE_DOL_PHASE2_OBJECTIVES.csv"
)

OUTPUT_EVENTS = os.path.join(
    BASE_DIR,
    "ICT_OBJECTIVE_DOL_PHASE2_EVENTS.csv"
)


# =============================================================================
# TIME
# =============================================================================

def epoch_to_wib(value):
    """
    DATASET TIME CONVENTION

    Source:
        epoch timestamp interpreted as UTC

    Conversion:
        UTC + 7 hours = WIB

    IMPORTANT:
        Explicit timezone.utc is required.

        datetime.fromtimestamp(value)
        without timezone can use the Android device timezone.
        Since the device is WIB, adding another +7 would create:

            UTC -> WIB -> +7 again

        which was the cause of the previous 13:00 / 14:00 output.

    The final datetime is returned timezone-naive intentionally so the rest
    of this engine can continue using the same datetime comparisons.
    """

    utc_dt = datetime.fromtimestamp(
        float(value),
        tz=timezone.utc
    )

    wib_dt = (
        utc_dt
        + timedelta(hours=7)
    )

    return wib_dt.replace(
        tzinfo=None
    )


# =============================================================================
# FILE DISCOVERY
# =============================================================================

def find_existing(paths):

    for path in paths:

        if os.path.exists(path):
            return path

    return None


def find_parent_json():

    found = find_existing(
        PARENT_CANDIDATES
    )

    if found:
        return found

    candidates = []

    patterns = [
        os.path.join(
            BASE_DIR,
            "*OPT35*.json"
        ),
        os.path.join(
            BASE_DIR,
            "*BIAS*.json"
        ),
    ]

    for pattern in patterns:

        candidates.extend(
            glob.glob(pattern)
        )

    seen = set()

    for path in candidates:

        if path in seen:
            continue

        seen.add(path)

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            daily = data.get(
                "daily",
                {}
            )

            if (
                "current_structural_leg"
                in daily
            ):
                return path

        except Exception:
            pass

    return None


# =============================================================================
# PARENT CONTEXT
# =============================================================================

def load_parent_context(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    weekly = data.get(
        "weekly",
        {}
    )

    daily = data.get(
        "daily",
        {}
    )

    # IMPORTANT:
    # Phase 1 valid current structural leg
    # is under daily.current_structural_leg.

    leg = daily.get(
        "current_structural_leg",
        {}
    )

    context = {

        "weekly_bias":
            weekly.get(
                "bias"
            ),

        "daily_bias":
            daily.get(
                "bias"
            ),

        "macro_bias":
            leg.get(
                "macro_bias"
            )
            or
            daily.get(
                "bias"
            ),

        "current_leg":
            leg.get(
                "leg_direction"
            ),

        "leg_type":
            leg.get(
                "leg_type"
            ),

        "delivery_state":
            leg.get(
                "delivery_state"
            ),

        "leg_origin":
            leg.get(
                "origin"
            ),

        "leg_endpoint":
            leg.get(
                "endpoint"
            ),
    }

    return data, context


# =============================================================================
# SOURCE
# =============================================================================

def load_source(path):

    df = pd.read_csv(
        path
    )

    required = [
        "time",
        "open",
        "high",
        "low",
        "close",
    ]

    for column in required:

        if column not in df.columns:

            raise ValueError(
                "CSV missing required column: "
                + column
            )

    # IMPORTANT:
    # Never modify the original source DataFrame.
    df = df.copy()

    df["wib_time"] = (
        df["time"]
        .apply(
            epoch_to_wib
        )
    )

    for column in [
        "open",
        "high",
        "low",
        "close",
    ]:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(
        subset=[
            "wib_time",
            "open",
            "high",
            "low",
            "close",
        ]
    )

    df = df.sort_values(
        "wib_time"
    ).reset_index(
        drop=True
    )

    return df


# =============================================================================
# SWING DETECTION
# =============================================================================

def detect_swings(df):
    """
    OUR FORMALIZATION ONLY.

    A swing high/low requires:
        2 candles left
        2 candles right

    This is a computational definition for the engine,
    not claimed as ICT's universal swing definition.
    """

    records = []

    for i in range(
        2,
        len(df) - 2
    ):

        row = df.iloc[i]

        left = df.iloc[
            i - 2:i
        ]

        right = df.iloc[
            i + 1:i + 3
        ]

        high = float(
            row["high"]
        )

        low = float(
            row["low"]
        )

        is_high = (
            high > left["high"].max()
            and
            high > right["high"].max()
        )

        is_low = (
            low < left["low"].min()
            and
            low < right["low"].min()
        )

        if is_high:

            records.append({
                "time":
                    row["wib_time"],

                "price":
                    high,

                "type":
                    "HIGH",

                "label":
                    "SWING_HIGH",
            })

        if is_low:

            records.append({
                "time":
                    row["wib_time"],

                "price":
                    low,

                "type":
                    "LOW",

                "label":
                    "SWING_LOW",
            })

    return records


# =============================================================================
# EQUAL HIGH / LOW
# =============================================================================

def build_equal_objectives(swings):
    """
    OUR FORMALIZATION.

    Numerical tolerance is only used to mechanically represent
    relative equal levels.

    It is NOT claimed to be an ICT universal numerical tolerance.
    """

    tolerance = 1.0

    highs = [
        x
        for x in swings
        if x["type"] == "HIGH"
    ]

    lows = [
        x
        for x in swings
        if x["type"] == "LOW"
    ]

    eqh = []
    eql = []

    for i in range(
        len(highs)
    ):

        for j in range(
            i + 1,
            len(highs)
        ):

            a = highs[i]
            b = highs[j]

            if (
                abs(
                    a["price"]
                    -
                    b["price"]
                )
                <= tolerance
            ):

                eqh.append(
                    make_objective(
                        obj_type="EQH",
                        obj_class="LIQUIDITY",
                        low=min(
                            a["price"],
                            b["price"]
                        ),
                        high=max(
                            a["price"],
                            b["price"]
                        ),
                        formation_time=max(
                            a["time"],
                            b["time"]
                        ),
                    )
                )

    for i in range(
        len(lows)
    ):

        for j in range(
            i + 1,
            len(lows)
        ):

            a = lows[i]
            b = lows[j]

            if (
                abs(
                    a["price"]
                    -
                    b["price"]
                )
                <= tolerance
            ):

                eql.append(
                    make_objective(
                        obj_type="EQL",
                        obj_class="LIQUIDITY",
                        low=min(
                            a["price"],
                            b["price"]
                        ),
                        high=max(
                            a["price"],
                            b["price"]
                        ),
                        formation_time=max(
                            a["time"],
                            b["time"]
                        ),
                    )
                )

    return eqh, eql


# =============================================================================
# OBJECTIVE CONSTRUCTOR
# =============================================================================

def make_objective(
    obj_type,
    obj_class,
    low,
    high,
    formation_time,
    direction=None
):

    return {

        "id":
            None,

        "type":
            obj_type,

        "class":
            obj_class,

        "low":
            float(
                low
            ),

        "high":
            float(
                high
            ),

        "midpoint":
            (
                float(low)
                +
                float(high)
            ) / 2.0,

        "formation_time":
            formation_time,

        "direction":
            direction,

        # ---------------------------------------------------------------------
        # STATE
        # ---------------------------------------------------------------------

        "state":
            "UNTOUCHED",

        "first_touch_time":
            None,

        "raid_time":
            None,

        "raid_price":
            None,

        "fill_time":
            None,

        "completion_time":
            None,

        "completion_reason":
            None,
    }


# =============================================================================
# FVG
# =============================================================================

def build_fvg_objectives(df):

    records = []

    for i in range(
        2,
        len(df)
    ):

        first = df.iloc[
            i - 2
        ]

        third = df.iloc[
            i
        ]

        # ---------------------------------------------------------------------
        # BULLISH FVG
        # ---------------------------------------------------------------------

        if (
            float(third["low"])
            >
            float(first["high"])
        ):

            records.append(
                make_objective(
                    obj_type="FVG",
                    obj_class="INEFFICIENCY",
                    low=float(
                        first["high"]
                    ),
                    high=float(
                        third["low"]
                    ),
                    formation_time=
                        third["wib_time"],
                    direction="BULLISH",
                )
            )

        # ---------------------------------------------------------------------
        # BEARISH FVG
        # ---------------------------------------------------------------------

        elif (
            float(third["high"])
            <
            float(first["low"])
        ):

            records.append(
                make_objective(
                    obj_type="FVG",
                    obj_class="INEFFICIENCY",
                    low=float(
                        third["high"]
                    ),
                    high=float(
                        first["low"]
                    ),
                    formation_time=
                        third["wib_time"],
                    direction="BEARISH",
                )
            )

    return records


# =============================================================================
# PDH / PDL
# =============================================================================

def build_previous_day_objectives(df):

    temp = df.copy()

    temp["date"] = (
        temp["wib_time"]
        .dt.date
    )

    daily = (
        temp
        .groupby("date")
        .agg(
            high=("high", "max"),
            low=("low", "min")
        )
        .reset_index()
    )

    records = []

    for i in range(
        1,
        len(daily)
    ):

        previous = daily.iloc[
            i - 1
        ]

        current = daily.iloc[
            i
        ]

        formation_time = (
            datetime.combine(
                current["date"],
                datetime.min.time()
            )
        )

        records.append(
            make_objective(
                obj_type="PDH",
                obj_class="LIQUIDITY",
                low=float(
                    previous["high"]
                ),
                high=float(
                    previous["high"]
                ),
                formation_time=
                    formation_time,
            )
        )

        records.append(
            make_objective(
                obj_type="PDL",
                obj_class="LIQUIDITY",
                low=float(
                    previous["low"]
                ),
                high=float(
                    previous["low"]
                ),
                formation_time=
                    formation_time,
            )
        )

    return records


# =============================================================================
# SWING OBJECTIVES
# =============================================================================

def build_swing_objectives(swings):

    records = []

    for swing in swings:

        if swing["type"] == "HIGH":

            obj_type = "SWING_HIGH"

        else:

            obj_type = "SWING_LOW"

        records.append(
            make_objective(
                obj_type=obj_type,
                obj_class="LIQUIDITY",
                low=swing["price"],
                high=swing["price"],
                formation_time=
                    swing["time"],
            )
        )

    return records


# =============================================================================
# OBJECTIVE MAP
# =============================================================================

def build_objective_map(df):

    print()
    print(
        "BUILDING OBJECTIVE MAP"
    )

    swings = detect_swings(
        df
    )

    print(
        f"Swing records    : "
        f"{len(swings)}"
    )

    eqh, eql = (
        build_equal_objectives(
            swings
        )
    )

    fvg = build_fvg_objectives(
        df
    )

    pdhl = build_previous_day_objectives(
        df
    )

    swing_objects = (
        build_swing_objectives(
            swings
        )
    )

    objectives = (
        eqh
        +
        eql
        +
        fvg
        +
        pdhl
        +
        swing_objects
    )

    objectives.sort(
        key=lambda x: (
            x["formation_time"],
            x["type"],
            x["low"],
            x["high"],
        )
    )

    for index, obj in enumerate(
        objectives,
        start=1
    ):

        obj["id"] = index

    counts = {}

    for obj in objectives:

        counts[obj["type"]] = (
            counts.get(
                obj["type"],
                0
            )
            +
            1
        )

    print()
    print(
        "RAW OBJECTIVE COUNTS"
    )

    for key in sorted(
        counts
    ):

        print(
            f"{key:<14}: "
            f"{counts[key]}"
        )

    print(
        f"{'TOTAL':<14}: "
        f"{len(objectives)}"
    )

    return objectives


# =============================================================================
# GEOMETRY
# =============================================================================

def candle_touches(
    row,
    obj
):

    H = float(
        row["high"]
    )

    L = float(
        row["low"]
    )

    return (
        H >= obj["low"]
        and
        L <= obj["high"]
    )


def liquidity_raided(
    row,
    obj
):

    H = float(
        row["high"]
    )

    L = float(
        row["low"]
    )

    if obj["type"] in (
        "EQH",
        "PDH",
        "SWING_HIGH",
    ):

        return (
            H > obj["high"]
        )

    if obj["type"] in (
        "EQL",
        "PDL",
        "SWING_LOW",
    ):

        return (
            L < obj["low"]
        )

    return False


def fvg_fully_filled(
    row,
    obj
):

    H = float(
        row["high"]
    )

    L = float(
        row["low"]
    )

    return (
        L <= obj["low"]
        and
        H >= obj["high"]
    )


# =============================================================================
# STATE ENGINE
# =============================================================================

def process_objective_states(
    df,
    objectives
):

    print()
    print(
        "PROCESSING OBJECTIVE STATES"
    )

    print(
        "Chronological engine : ACTIVE"
    )

    print(
        "Look-ahead guard     : ACTIVE"
    )

    # -------------------------------------------------------------------------
    # PERFORMANCE
    #
    # Objectives are activated once.
    #
    # We do NOT build:
    #
    #     candle × all-objectives
    #
    # historical DOL timeline.
    # -------------------------------------------------------------------------

    ordered = sorted(
        objectives,
        key=lambda x:
            x["formation_time"]
    )

    pointer = 0
    active = []

    events = []

    for _, row in df.iterrows():

        current_time = (
            row["wib_time"]
        )

        # ---------------------------------------------------------------------
        # ACTIVATE ONLY OBJECTIVES FORMED BEFORE CURRENT CANDLE
        # ---------------------------------------------------------------------

        while (
            pointer < len(ordered)
            and
            ordered[pointer][
                "formation_time"
            ]
            <
            current_time
        ):

            active.append(
                ordered[pointer]
            )

            pointer += 1

        # ---------------------------------------------------------------------
        # PROCESS ACTIVE OBJECTIVES
        # ---------------------------------------------------------------------

        for obj in active:

            # Completed objective does not need repeated processing.
            if (
                obj["completion_time"]
                is not None
            ):
                continue

            if not candle_touches(
                row,
                obj
            ):
                continue

            # -----------------------------------------------------------------
            # FIRST TOUCH
            # -----------------------------------------------------------------

            if (
                obj["first_touch_time"]
                is None
            ):

                obj["first_touch_time"] = (
                    current_time
                )

                if (
                    obj["state"]
                    ==
                    "UNTOUCHED"
                ):

                    obj["state"] = (
                        "TOUCHED"
                    )

                events.append({
                    "time":
                        current_time,

                    "objective_id":
                        obj["id"],

                    "objective_type":
                        obj["type"],

                    "class":
                        obj["class"],

                    "event":
                        "TOUCH",
                })

            # -----------------------------------------------------------------
            # LIQUIDITY
            # -----------------------------------------------------------------

            if (
                obj["class"]
                ==
                "LIQUIDITY"
            ):

                if liquidity_raided(
                    row,
                    obj
                ):

                    obj["raid_time"] = (
                        current_time
                    )

                    obj["completion_time"] = (
                        current_time
                    )

                    obj["completion_reason"] = (
                        "LIQUIDITY_RAID"
                    )

                    if obj["type"] in (
                        "EQH",
                        "PDH",
                        "SWING_HIGH",
                    ):

                        obj["raid_price"] = (
                            float(
                                row["high"]
                            )
                        )

                    else:

                        obj["raid_price"] = (
                            float(
                                row["low"]
                            )
                        )

                    obj["state"] = (
                        "RAIDED"
                    )

                    events.append({
                        "time":
                            current_time,

                        "objective_id":
                            obj["id"],

                        "objective_type":
                            obj["type"],

                        "class":
                            obj["class"],

                        "event":
                            "RAID",

                        "price":
                            obj["raid_price"],
                    })

            # -----------------------------------------------------------------
            # INEFFICIENCY / FVG
            # -----------------------------------------------------------------

            elif (
                obj["class"]
                ==
                "INEFFICIENCY"
            ):

                if fvg_fully_filled(
                    row,
                    obj
                ):

                    obj["fill_time"] = (
                        current_time
                    )

                    obj["completion_time"] = (
                        current_time
                    )

                    obj["completion_reason"] = (
                        "FULL_ZONE_FILL"
                    )

                    obj["state"] = (
                        "FILLED"
                    )

                    events.append({
                        "time":
                            current_time,

                        "objective_id":
                            obj["id"],

                        "objective_type":
                            obj["type"],

                        "class":
                            obj["class"],

                        "event":
                            "FILL",

                        "price":
                            obj["midpoint"],
                    })

    return objectives, events


# =============================================================================
# STATE SUMMARY
# =============================================================================

def summarize_states(
    objectives
):

    summary = {}

    for obj in objectives:

        key = (
            obj["class"],
            obj["state"]
        )

        summary[key] = (
            summary.get(
                key,
                0
            )
            +
            1
        )

    return summary


def print_state_summary(
    objectives
):

    summary = summarize_states(
        objectives
    )

    print()
    print(
        "OBJECTIVE STATES"
    )

    print()
    print(
        "LIQUIDITY"
    )

    for state in [
        "UNTOUCHED",
        "TOUCHED",
        "RAIDED",
    ]:

        count = summary.get(
            (
                "LIQUIDITY",
                state
            ),
            0
        )

        print(
            f"{state:<12}: "
            f"{count}"
        )

    print()
    print(
        "INEFFICIENCY"
    )

    for state in [
        "UNTOUCHED",
        "TOUCHED",
        "FILLED",
    ]:

        count = summary.get(
            (
                "INEFFICIENCY",
                state
            ),
            0
        )

        print(
            f"{state:<12}: "
            f"{count}"
        )


# =============================================================================
# CURRENT SNAPSHOT
# =============================================================================

def current_snapshot(
    df
):

    row = df.iloc[-1]

    return {

        "time":
            row["wib_time"],

        "price":
            float(
                row["close"]
            ),

        "open":
            float(
                row["open"]
            ),

        "high":
            float(
                row["high"]
            ),

        "low":
            float(
                row["low"]
            ),
    }


# =============================================================================
# POSITION
# =============================================================================

def objective_position(
    obj,
    price
):

    if obj["low"] > price:

        return "ABOVE"

    if obj["high"] < price:

        return "BELOW"

    return "AT_PRICE"


# =============================================================================
# AVAILABLE OBJECTIVES
# =============================================================================

def available_objectives(
    objectives,
    snapshot
):

    result = []

    now = snapshot["time"]
    price = snapshot["price"]

    for obj in objectives:

        # ---------------------------------------------------------------------
        # LOOK-AHEAD GUARD
        # ---------------------------------------------------------------------

        if (
            obj["formation_time"]
            >=
            now
        ):

            continue

        # ---------------------------------------------------------------------
        # ALREADY COMPLETED
        # ---------------------------------------------------------------------

        if (
            obj["completion_time"]
            is not None
        ):

            continue

        position = objective_position(
            obj,
            price
        )

        if position == "AT_PRICE":

            continue

        item = {

            "id":
                obj["id"],

            "type":
                obj["type"],

            "class":
                obj["class"],

            "low":
                obj["low"],

            "high":
                obj["high"],

            "midpoint":
                obj["midpoint"],

            "formation_time":
                obj["formation_time"],

            "state":
                obj["state"],

            "position":
                position,

            "direction":
                obj.get(
                    "direction"
                ),
        }

        result.append(
            item
        )

    return result


# =============================================================================
# DIRECTIONAL RELATION
# =============================================================================

def direction_relation(
    direction,
    position
):

    if direction == "BULLISH":

        if position == "ABOVE":

            return "WITH_DIRECTION"

        if position == "BELOW":

            return "OPPOSITE_DIRECTION"

    if direction == "BEARISH":

        if position == "BELOW":

            return "WITH_DIRECTION"

        if position == "ABOVE":

            return "OPPOSITE_DIRECTION"

    return "NEUTRAL"


# =============================================================================
# OBJECTIVE FAMILY
# =============================================================================

def objective_family(
    obj
):

    if obj["type"] in (
        "EQH",
        "PDH",
        "SWING_HIGH",
    ):

        return "BUY_SIDE_LIQUIDITY"

    if obj["type"] in (
        "EQL",
        "PDL",
        "SWING_LOW",
    ):

        return "SELL_SIDE_LIQUIDITY"

    if obj["type"] == "FVG":

        return "INEFFICIENCY"

    return "OTHER"


# =============================================================================
# DOL INTERPRETER
# =============================================================================

def interpret_dol(
    objectives,
    events,
    snapshot,
    context
):
    """
    IMPORTANT:

    This is a contextual interpreter.

    It does NOT claim to reproduce ICT discretionary judgement
    mathematically.

    It deliberately refuses to manufacture a DOL when the available
    Phase 1 context does not provide sufficient directional evidence.
    """

    available = available_objectives(
        objectives,
        snapshot
    )

    macro = context[
        "macro_bias"
    ]

    leg = context[
        "current_leg"
    ]

    leg_type = context[
        "leg_type"
    ]

    delivery = context[
        "delivery_state"
    ]

    result = {

        "status":
            "NOT_DETERMINED",

        "initial_dol":
            None,

        "current_dol":
            None,

        "next_dol":
            None,

        "macro_draws":
            [],

        "leg_draws":
            [],

        "opposing_liquidity_events":
            [],

        "reason":
            None,

        "available_objective_count":
            len(available),
    }

    # -------------------------------------------------------------------------
    # CLASSIFY AVAILABLE OBJECTIVES
    # -------------------------------------------------------------------------

    for obj in available:

        family = objective_family(
            obj
        )

        obj["family"] = family

        # ---------------------------------------------------------------------
        # MACRO RELATION
        # ---------------------------------------------------------------------

        if macro in (
            "BULLISH",
            "BEARISH"
        ):

            obj[
                "macro_relation"
            ] = direction_relation(
                macro,
                obj["position"]
            )

        else:

            obj[
                "macro_relation"
            ] = (
                "NO_MACRO_DIRECTION"
            )

        # ---------------------------------------------------------------------
        # LEG RELATION
        # ---------------------------------------------------------------------

        if leg in (
            "BULLISH",
            "BEARISH"
        ):

            obj[
                "leg_relation"
            ] = direction_relation(
                leg,
                obj["position"]
            )

        else:

            obj[
                "leg_relation"
            ] = (
                "NO_LEG_DIRECTION"
            )

        # ---------------------------------------------------------------------
        # MACRO-ALIGNED LIQUIDITY
        # ---------------------------------------------------------------------

        if (
            obj["class"]
            ==
            "LIQUIDITY"
            and
            obj["macro_relation"]
            ==
            "WITH_DIRECTION"
        ):

            result[
                "macro_draws"
            ].append(
                obj
            )

        # ---------------------------------------------------------------------
        # CURRENT-LEG-ALIGNED LIQUIDITY
        # ---------------------------------------------------------------------

        if (
            obj["class"]
            ==
            "LIQUIDITY"
            and
            obj["leg_relation"]
            ==
            "WITH_DIRECTION"
        ):

            result[
                "leg_draws"
            ].append(
                obj
            )

    # -------------------------------------------------------------------------
    # RECORDED LIQUIDITY EVENTS
    #
    # Only already-recorded events are used.
    # No future scanning.
    # -------------------------------------------------------------------------

    current_time = snapshot[
        "time"
    ]

    for event in events:

        if (
            event["time"]
            >
            current_time
        ):

            continue

        if (
            event["event"]
            !=
            "RAID"
        ):

            continue

        result[
            "opposing_liquidity_events"
        ].append(
            event
        )

    # -------------------------------------------------------------------------
    # RECENT AUDIT WINDOW
    #
    # This is NOT an ICT timing rule.
    #
    # It is only an implementation/audit window preventing very old events
    # from being described as current delivery evidence.
    # -------------------------------------------------------------------------

    recent_cutoff = (
        current_time
        -
        timedelta(days=5)
    )

    result[
        "opposing_liquidity_events"
    ] = [

        x
        for x in
        result[
            "opposing_liquidity_events"
        ]

        if x["time"]
        >=
        recent_cutoff
    ]

    # -------------------------------------------------------------------------
    # CASE 1
    #
    # Macro and current leg point in the SAME direction.
    # -------------------------------------------------------------------------

    same_direction = (

        macro in (
            "BULLISH",
            "BEARISH"
        )

        and

        leg == macro
    )

    if same_direction:

        candidates = (
            result[
                "macro_draws"
            ]
        )

        if len(candidates) == 1:

            # A unique directionally aligned candidate is still NOT
            # automatically accepted.
            #
            # Active delivery evidence is required.
            #
            # For this H1 engine, Phase 1 delivery state is the available
            # contextual evidence.

            active_delivery = (
                delivery
                not in (
                    None,
                    "UNDEFINED",
                    "UNKNOWN"
                )
            )

            if active_delivery:

                result[
                    "status"
                ] = (
                    "CONTEXTUALLY_DETERMINED"
                )

                result[
                    "current_dol"
                ] = candidates[0]

                result[
                    "reason"
                ] = (
                    "A single unresolved liquidity objective "
                    "is aligned with the active macro/current-leg "
                    "direction and Phase 1 reports an active "
                    "delivery state."
                )

                return result

        result[
            "reason"
        ] = (
            "Macro and current structural leg are aligned, "
            "but the available objective set does not establish "
            "one unique DOL without introducing a nearest-objective "
            "or numerical-ranking rule."
        )

        return result

    # -------------------------------------------------------------------------
    # CASE 2
    #
    # Macro bullish + bearish correction.
    #
    # Macro draw and current-leg draw may point in opposite directions.
    # -------------------------------------------------------------------------

    correction_conflict = (

        macro == "BULLISH"

        and

        leg == "BEARISH"

        and

        leg_type == "CORRECTION"
    )

    if correction_conflict:

        result[
            "reason"
        ] = (
            "The active macro context is bullish while the "
            "current structural leg is a bearish correction. "
            "Therefore a buy-side macro draw and a sell-side "
            "current-leg objective must not be collapsed into "
            "one direction. The available Phase 1 context does "
            "not contain a new causal delivery event that resolves "
            "which objective is the active DOL."
        )

        return result

    # -------------------------------------------------------------------------
    # CASE 3
    #
    # Macro bearish + bullish correction.
    # -------------------------------------------------------------------------

    correction_conflict = (

        macro == "BEARISH"

        and

        leg == "BULLISH"

        and

        leg_type == "CORRECTION"
    )

    if correction_conflict:

        result[
            "reason"
        ] = (
            "The active macro context is bearish while the "
            "current structural leg is a bullish correction. "
            "Therefore a sell-side macro draw and a buy-side "
            "current-leg objective must not be collapsed into "
            "one direction. The available Phase 1 context does "
            "not contain a new causal delivery event that resolves "
            "which objective is the active DOL."
        )

        return result

    # -------------------------------------------------------------------------
    # CASE 4
    #
    # Unknown / neutral macro.
    # -------------------------------------------------------------------------

    result[
        "reason"
    ] = (
        "The parent context does not establish a sufficiently "
        "defined directional delivery state for a mechanical DOL "
        "interpretation."
    )

    return result


# =============================================================================
# EVENT TIMELINE
# =============================================================================

def build_event_timeline(
    events
):

    events = sorted(
        events,
        key=lambda x: (
            x["time"],
            x["objective_id"],
            x["event"],
        )
    )

    return events


# =============================================================================
# SERIALIZATION
# =============================================================================

def serialize(value):
    """
    Convert Python objects into JSON-safe objects.

    IMPORTANT:
    summarize_states() internally uses tuple keys:

        ("LIQUIDITY", "RAIDED")

    Python dictionaries allow tuple keys.
    JSON dictionaries do not.

    Therefore tuple keys are converted to a readable string:

        LIQUIDITY|RAIDED
    """

    if isinstance(
        value,
        datetime
    ):

        return value.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    if isinstance(
        value,
        dict
    ):

        result = {}

        for key, val in value.items():

            if isinstance(
                key,
                tuple
            ):

                safe_key = "|".join(
                    str(x)
                    for x in key
                )

            else:

                safe_key = str(
                    key
                )

            result[
                safe_key
            ] = serialize(
                val
            )

        return result

    if isinstance(
        value,
        (list, tuple)
    ):

        return [
            serialize(x)
            for x in value
        ]

    return value


# =============================================================================
# SAVE JSON
# =============================================================================

def save_json(
    path,
    report
):

    safe_report = serialize(
        report
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            safe_report,
            f,
            indent=2,
            ensure_ascii=False
        )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print(
        "=" * 78
    )

    print(
        "ICT OBJECTIVE / DOL ENGINE — PHASE 2 FINAL"
    )

    print(
        "=" * 78
    )

    # =========================================================================
    # PARENT
    # =========================================================================

    parent_path = (
        find_parent_json()
    )

    if parent_path is None:

        raise FileNotFoundError(
            "Phase 1 parent JSON not found."
        )

    print()
    print(
        "PARENT FIELD DISCOVERY"
    )

    print(
        f"Parent JSON       : "
        f"{parent_path}"
    )

    _, context = (
        load_parent_context(
            parent_path
        )
    )

    print(
        f"Weekly Bias      : "
        f"{context['weekly_bias']}"
    )

    print(
        f"Daily Bias       : "
        f"{context['daily_bias']}"
    )

    print(
        f"Macro Bias       : "
        f"{context['macro_bias']}"
    )

    print(
        f"Current Leg      : "
        f"{context['current_leg']}"
    )

    print(
        f"Leg Type         : "
        f"{context['leg_type']}"
    )

    print(
        f"Delivery State   : "
        f"{context['delivery_state']}"
    )

    print(
        f"Leg Origin       : "
        f"{context['leg_origin']}"
    )

    print(
        f"Leg Endpoint     : "
        f"{context['leg_endpoint']}"
    )

    # =========================================================================
    # SOURCE
    # =========================================================================

    source_path = (
        find_existing(
            SOURCE_CANDIDATES
        )
    )

    if source_path is None:

        raise FileNotFoundError(
            "XAUUSD H1 source CSV not found."
        )

    print()
    print(
        "LOADING SOURCE CSV"
    )

    df = load_source(
        source_path
    )

    print(
        f"Rows             : "
        f"{len(df)}"
    )

    print(
        f"Start WIB        : "
        f"{df['wib_time'].iloc[0]}"
    )

    print(
        f"End WIB          : "
        f"{df['wib_time'].iloc[-1]}"
    )

    print()
    print(
        "CSV STATUS       : READ ONLY"
    )

    print(
        "Working copy     : YES"
    )

    # =========================================================================
    # OBJECTIVE MAP
    # =========================================================================

    objectives = (
        build_objective_map(
            df
        )
    )

    # =========================================================================
    # CHRONOLOGICAL STATE ENGINE
    # =========================================================================

    objectives, events = (
        process_objective_states(
            df,
            objectives
        )
    )

    print_state_summary(
        objectives
    )

    # =========================================================================
    # CURRENT SNAPSHOT
    # =========================================================================

    snapshot = (
        current_snapshot(
            df
        )
    )

    print()
    print(
        "CURRENT SNAPSHOT"
    )

    print(
        f"Time             : "
        f"{snapshot['time']}"
    )

    print(
        f"Price            : "
        f"{snapshot['price']:.3f}"
    )

    # =========================================================================
    # DOL
    # =========================================================================

    dol = interpret_dol(
        objectives,
        events,
        snapshot,
        context
    )

    # =========================================================================
    # EVENT TIMELINE
    # =========================================================================

    event_timeline = (
        build_event_timeline(
            events
        )
    )

    # =========================================================================
    # FINAL DOL OUTPUT
    # =========================================================================

    print()
    print(
        "=" * 78
    )

    print(
        "DOL INTERPRETATION"
    )

    print(
        "=" * 78
    )

    print(
        f"Status           : "
        f"{dol['status']}"
    )

    if dol["current_dol"]:

        obj = dol[
            "current_dol"
        ]

        print(
            f"CURRENT DOL      : "
            f"{obj['type']} "
            f"{obj['low']:.3f} - "
            f"{obj['high']:.3f}"
        )

        print(
            f"Position         : "
            f"{obj['position']}"
        )

        print(
            f"Macro Relation   : "
            f"{obj.get('macro_relation')}"
        )

        print(
            f"Leg Relation     : "
            f"{obj.get('leg_relation')}"
        )

    else:

        print(
            "CURRENT DOL      : "
            "NOT DETERMINED"
        )

    print()
    print(
        f"Available objs   : "
        f"{dol['available_objective_count']}"
    )

    print()
    print(
        "Reason:"
    )

    print(
        dol["reason"]
    )

    # =========================================================================
    # REPORT
    # =========================================================================

    state_summary = (
        summarize_states(
            objectives
        )
    )

    report = {

        "engine": {

            "name":
                "ICT OBJECTIVE / DOL ENGINE",

            "phase":
                2,

            "version":
                "FINAL",

            "status":
                "CONCEPTUAL_FINAL",
        },

        "source": {

            "csv":
                source_path,

            "read_only":
                True,

            "working_copy":
                True,

            "time_conversion":
                "UTC epoch + 7 hours = WIB",
        },

        "parent": {

            "file":
                parent_path,

            "context":
                context,
        },

        "current_snapshot":
            snapshot,

        "objective_map": {

            "total":
                len(objectives),

            "state_summary":
                state_summary,
        },

        "dol_interpretation":
            dol,

        "objective_event_timeline": {

            "type":
                "OBJECTIVE_EVENT_TIMELINE",

            "not_historical_dol":
                True,

            "events":
                event_timeline,
        },

        "integrity": {

            "phase_1_recalculated":
                False,

            "objective_map":
                True,

            "chronological_state":
                True,

            "lookahead_guard":
                True,

            "current_candle_objectives_excluded":
                True,

            "liquidity_raid_separate_from_fvg_fill":
                True,

            "nearest_objective_rule":
                False,

            "numeric_dol_score":
                False,

            "bruteforce_candle_x_objective":
                False,

            "source_csv_modified":
                False,

            "historical_dol_claim":
                False,

            "mechanical_formalizations": [

                "2-left / 2-right swing detection",

                "1.0 price equal-level tolerance",

                "candle-zone intersection",

                "liquidity penetration",

                "FVG full-zone fill",

                "macro/leg directional relation",

                "contextual DOL interpretation",
            ],
        },
    }

    # =========================================================================
    # SAVE JSON
    # =========================================================================

    save_json(
        OUTPUT_JSON,
        report
    )

    # =========================================================================
    # OBJECTIVE CSV
    # =========================================================================

    rows = []

    for obj in objectives:

        row = obj.copy()

        for key, value in list(
            row.items()
        ):

            if isinstance(
                value,
                datetime
            ):

                row[key] = (
                    value.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

        rows.append(
            row
        )

    pd.DataFrame(
        rows
    ).to_csv(
        OUTPUT_OBJECTIVES,
        index=False
    )

    # =========================================================================
    # EVENT CSV
    # =========================================================================

    event_rows = []

    for event in event_timeline:

        row = event.copy()

        if isinstance(
            row.get("time"),
            datetime
        ):

            row["time"] = (
                row["time"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        event_rows.append(
            row
        )

    pd.DataFrame(
        event_rows
    ).to_csv(
        OUTPUT_EVENTS,
        index=False
    )

    # =========================================================================
    # INTEGRITY
    # =========================================================================

    print()
    print(
        "=" * 78
    )

    print(
        "ENGINE INTEGRITY"
    )

    print(
        "=" * 78
    )

    print(
        "Phase 1 parent         : YES"
    )

    print(
        "Phase 1 recalculated   : NO"
    )

    print(
        "Objective Map          : YES"
    )

    print(
        "Chronological State    : YES"
    )

    print(
        "Look-ahead guard       : YES"
    )

    print(
        "Liquidity/FVG states   : SEPARATED"
    )

    print(
        "DOL interpreter        : YES"
    )

    print(
        "Nearest DOL rule       : NO"
    )

    print(
        "Numeric DOL score      : NO"
    )

    print(
        "Brute-force timeline   : NO"
    )

    print(
        "CSV modified           : NO"
    )

    print()
    print(
        "OUTPUT"
    )

    print(
        f"JSON                 : "
        f"{OUTPUT_JSON}"
    )

    print(
        f"Objectives CSV       : "
        f"{OUTPUT_OBJECTIVES}"
    )

    print(
        f"Events CSV           : "
        f"{OUTPUT_EVENTS}"
    )

    print()
    print(
        "=" * 78
    )

    print(
        "PHASE 2 COMPLETE"
    )

    print(
        "=" * 78
    )


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":

    main()